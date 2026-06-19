import os
import logging
import random
from flask import Flask, request, jsonify, send_from_directory
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='templates', static_url_path='')

# Токены
SHOP_TOKEN = "8934522015:AAHJuYuqOu9-CYyhTZavQ-MDlCn1Sw4T4vw"
PAY_TOKEN = "8441860983:AAFMuNBnImWdFc17Fg8fYPzcVPl5YkwuQp4"
STOCK_TOKEN = "8666600867:AAHSTjcwfKJQv5KVb3x0QBgJXdmXDHTQGEc"
ADMIN_ID = 5468112563
WEBAPP_URL = "https://trifferi.onrender.com"

# Инициализация ботов
shop_bot = Bot(token=SHOP_TOKEN)
pay_bot = Bot(token=PAY_TOKEN)
stock_bot = Bot(token=STOCK_TOKEN)

dp_shop = Dispatcher()
dp_pay = Dispatcher()
dp_stock = Dispatcher()

# Роут Flask
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

# Логика оформления заказа (Webhook от сайта)
@app.route('/api/order', methods=['POST'])
async def api_order():
    try:
        data = await request.get_json()
        if not data: return jsonify({"status": "error"}), 400
        
        user_id = data.get("userId")
        if not user_id: return jsonify({"status": "error"}), 400
        
        order_id = f"#{random.randint(1000, 9999)}"
        items = data.get("items", [])
        total = data.get("total", 0)
        customer = data.get("customer", {})
        
        items_text = "\n".join([f"{i['n']} - {i['p']} RUB" for i in items])
        
        # 1. Сообщение клиенту (через Pay Bot)
        client_msg = f"✅ Заказ {order_id} создан!\n\nСостав:\n{items_text}\n\nИтого: {total} RUB\n\nСтатус: Ожидает подтверждения."
        try: await pay_bot.send_message(user_id, client_msg)
        except Exception as e: logger.error(f"Pay Bot error: {e}")
        
        # 2. Сообщение админу (через Stock Bot)
        admin_msg = f"🔥 НОВЫЙ ЗАКАЗ {order_id}\n\nКлиент ID: {user_id}\nИмя: {customer.get('name')}\nТелефон: {customer.get('phone')}\nАдрес: {customer.get('address')}\n\nТовары:\n{items_text}\n\nИтого: {total} RUB"
        kb = InlineKeyboardBuilder()
        kb.button(text="✅ ПРИНЯТЬ", callback_data=f"accept_{user_id}_{order_id}")
        kb.button(text="❌ ОТКАЗАТЬ", callback_data=f"reject_{user_id}_{order_id}")
        try: await stock_bot.send_message(ADMIN_ID, admin_msg, reply_markup=kb.as_markup())
        except Exception as e: logger.error(f"Stock Bot error: {e}")
        
        return jsonify({"status": "success", "order_id": order_id})
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({"status": "error"}), 500

# Команда /start для основного бота
@dp_shop.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🛍 Открыть магазин", web_app=WebAppInfo(url=WEBAPP_URL))
    await message.answer("Добро пожаловать в TRIFFERI!", reply_markup=kb.as_markup())

# Обработка кнопок админа
@dp_stock.callback_query(F.data.startswith("accept_") | F.data.startswith("reject_"))
async def handle_admin(callback_query: types.CallbackQuery):
    try:
        action, uid, oid = callback_query.data.split("_", 2)
        if action == "accept":
            await pay_bot.send_message(uid, f"✅ Заказ {oid} ПРИНЯТ! Оператор свяжется с вами.")
            await callback_query.answer("Заказ принят!")
        elif action == "reject":
            await pay_bot.send_message(uid, f"❌ Заказ {oid} отклонен.")
            await callback_query.answer("Заказ отклонен.")
    except Exception as e: logger.error(f"Callback error: {e}")

@dp_pay.message(Command("start"))
async def pay_start(message: types.Message):
    await message.answer("👋 Бот для уведомлений о заказах.")

# Запуск приложения
async def main():
    if os.getenv("RENDER"):
        logger.info("Running on Render (Flask only)")
        return
    logger.info("Starting bots...")
    await dp_shop.start_polling(shop_bot)
    await dp_pay.start_polling(pay_bot)
    await dp_stock.start_polling(stock_bot)

if __name__ == "__main__":
    logger.info("Starting Flask...")
    app.run(host="0.0.0.0", port=10000, threaded=True)
