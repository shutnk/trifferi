import os
import json
import asyncio
import logging
from flask import Flask, request, jsonify, send_from_directory
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='templates', static_url_path='')

# ================= НАСТРОЙКИ =================
SHOP_TOKEN = "8934522015:AAHJuYuqOu9-CYyhTZavQ-MDlCn1Sw4T4vw"
PAY_TOKEN = "8441860983:AAFMuNBnImWdFc17Fg8fYPzcVPl5YkwuQp4"
STOCK_TOKEN = "8666600867:AAHSTjcwfKJQv5KVb3x0QBgJXdmXDHTQGEc"
ADMIN_ID = 5468112563
WEBAPP_URL = "https://trifferi.onrender.com"

# ================= ИНИЦИАЛИЗАЦИЯ БОТОВ =================
shop_bot = Bot(token=SHOP_TOKEN)
pay_bot = Bot(token=PAY_TOKEN)
stock_bot = Bot(token=STOCK_TOKEN)

dp_shop = Dispatcher()
dp_pay = Dispatcher()
dp_stock = Dispatcher()

# ================= ФЛАКСК РОУТЫ =================
@app.route('/')
def index():
    """Отдаем index.html"""
    return send_from_directory('templates', 'index.html')

@app.route('/api/order', methods=['POST'])
async def api_order():
    """API для приема заказов"""
    try:
        data = await request.get_json()
        logger.info(f"📥 Получен заказ: {data}")
        
        if not data:
            return jsonify({"status": "error", "error": "No data"}), 400
                customer = data.get('customer', {})
        items = data.get('items', [])
        total = data.get('total', 0)
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({"status": "error", "error": "No userId"}), 400
        
        import random
        order_id = f"#{random.randint(1000, 9999)}"
        
        # 1. Сообщение клиенту через PAY бота
        items_text = "\n".join([f"📦 {i['n']} - {i['p']} ₽" for i in items])
        
        client_msg = f"""
✅ <b>Заказ {order_id} создан!</b>

📋 <b>Состав:</b>
{items_text}

💰 <b>Сумма:</b> {total} ₽

⏳ <b>Статус:</b> В обработке.
        """
        
        try:
            await pay_bot.send_message(user_id, client_msg, parse_mode='HTML')
            logger.info(f"✅ Отправлено клиенту {user_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки клиенту: {e}")
        
        # 2. Сообщение админу через STOCK бота
        admin_msg = f"""
🔥 <b>НОВЫЙ ЗАКАЗ {order_id}</b>

👤 <b>Клиент ID:</b> {user_id}
📝 <b>Имя:</b> {customer.get('name')}
📱 <b>Телефон:</b> {customer.get('phone')}
📍 <b>Адрес:</b> {customer.get('address')}

📦 <b>Товары:</b>
{items_text}

💰 <b>Итого:</b> {total} ₽
        """
        
        kb = InlineKeyboardBuilder()
        kb.button(text="✅ ПРИНЯТЬ", callback_data=f"accept_{user_id}_{order_id}")
        kb.button(text="❌ ОТКАЗАТЬ", callback_data=f"reject_{user_id}_{order_id}")
                try:
            await stock_bot.send_message(ADMIN_ID, admin_msg, reply_markup=kb.as_markup(), parse_mode='HTML')
            logger.info(f"✅ Отправлено админу {ADMIN_ID}")
        except Exception as e:
            logger.error(f"Ошибка отправки админу: {e}")
        
        return jsonify({"status": "success", "order_id": order_id})
        
    except Exception as e:
        logger.error(f"❌ Ошибка в api/order: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

# ================= SHOP BOT =================
@dp_shop.message(Command('start'))
async def cmd_start(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🛍 ОТКРЫТЬ МАГАЗИН", web_app=WebAppInfo(url=WEBAPP_URL))
    await message.answer("Добро пожаловать в TRIFFERI!", reply_markup=kb.as_markup())

# ================= STOCK BOT =================
@dp_stock.callback_query(F.data.startswith('accept_') | F.data.startswith('reject_'))
async def handle_admin_decision(callback_query: types.CallbackQuery):
    action, user_id, order_id = callback_query.data.split('_', 2)
    
    if action == 'accept':
        text = f"✅ Заказ {order_id} ПРИНЯТ! Ожидайте доставку."
        await pay_bot.send_message(user_id, text, parse_mode='HTML')
        await callback_query.answer("✅ Вы приняли заказ!")
    elif action == 'reject':
        text = f"❌ Заказ {order_id} отклонен."
        await pay_bot.send_message(user_id, text, parse_mode='HTML')
        await callback_query.answer("❌ Вы отказали.")

# ================= PAY BOT =================
@dp_pay.message(Command('start'))
async def pay_start(message: types.Message):
    await message.answer("👋 Это бот для уведомлений о заказах.")

# ================= ЗАПУСК =================
async def main():
    # Проверяем, запущены ли боты на Render
    if os.getenv('RENDER'):
        logger.info("🚀 Запущено на Render - боты не стартуют (только Flask)")
        return
    
    logger.info("🤖 Запуск ботов...")
    await asyncio.gather(
        dp_shop.start_polling(shop_bot),
        dp_pay.start_polling(pay_bot),
        dp_stock.start_polling(stock_bot)    )

if __name__ == '__main__':
    # Запуск Flask
    logger.info("🌐 Запуск Flask на порту 10000...")
    app.run(host='0.0.0.0', port=10000, threaded=True)
