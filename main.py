import asyncio, json, os, logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from flask import Flask, send_from_directory, render_template_string
import threading

# --- НАСТРОЙКИ ---
TOKEN_MAIN = os.getenv("TOKEN_MAIN")
TOKEN_PAY = os.getenv("TOKEN_PAY")
TOKEN_STOCK = os.getenv("TOKEN_STOCK")
ADMIN_ID = int(os.getenv("ADMIN_CHAT_ID"))

# --- ХРАНИЛИЩЕ ---
ORDERS_FILE = "orders.json"
orders = {}

def load_orders():
    global orders
    if os.path.exists(ORDERS_FILE):
        with open(ORDERS_FILE, 'r', encoding='utf-8') as f:
            orders = json.load(f)

def save_orders():
    with open(ORDERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(orders, f, ensure_ascii=False, indent=2)

load_orders()

# --- БОТЫ ---
bot_main = Bot(token=TOKEN_MAIN)
dp_main = Dispatcher()

bot_pay = Bot(token=TOKEN_PAY)
dp_pay = Dispatcher()

bot_stock = Bot(token=TOKEN_STOCK)
dp_stock = Dispatcher()

# --- FLASK ДЛЯ RENDER ---
@app.route('/')
def home():
    """Отдаёт магазин (WebApp)"""
    try:
        with open('templates/index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "<h1>Shop not found</h1>", 404
    except Exception as e:
        return f"<h1>Error:</h1> {str(e)}", 500

# ===== МАРШРУТЫ ДЛЯ WEBAPP =====
@app.route('/shop')
@app.route('/store')
def shop():
    try:
        with open('templates/index.html', 'r', encoding='utf-8') as f:
            html = f.read()
        return render_template_string(html)
    except Exception as e:
        return f"Error loading shop: {e}", 500
# Маршрут для статики (CSS, JS, images)
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


# ==========================================# 🤖 1. ОСНОВНОЙ БОТ (@trifferi)
# ==========================================

# Команда /start для основного бота с кнопкой магазина
@dp_main.message(Command("start"))
async def cmd_start_main(msg: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛍 Открыть магазин", web_app=WebAppInfo(url="https://trifferi.onrender.com"))]
        ],
        resize_keyboard=True
    )
    await msg.answer(
        "✨ Добро пожаловать в TRIFFERI!\n\nНажмите на кнопку ниже, чтобы открыть магазин:",
        reply_markup=kb
    )

@dp_main.message(F.web_app_data)
async def handle_webapp(msg: types.Message):
    try:
        data = json.loads(msg.web_app_data.data)
        order_id = f"TRF-{len(orders)+1:04d}"
        
        orders[order_id] = {
            "user_id": msg.from_user.id,
            "username": msg.from_user.username or "unknown",
            "client": data.get("client", {}),
            "items": data.get("items", []),
            "total": data.get("total", 0),
            "status": "pending"
        }
        save_orders()
        
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🔗 Подтвердить заказ в @trifferipaybot", url=f"https://t.me/trifferipaybot?start={order_id}")
        ]])
        await msg.answer(f"✅ Заказ {order_id} создан!\nПерейдите в @trifferipaybot для подтверждения.", reply_markup=kb)
    except Exception as e:
        logging.error(f"Webapp error: {e}")
        await msg.answer("⚠️ Ошибка оформления заказа.")

# ==========================================
# 💳 2. ПЛАТЕЖНЫЙ БОТ (@trifferipaybot)
# ==========================================
@dp_pay.message(Command("start"))
async def cmd_start_pay(msg: types.Message):
    args = msg.text.split()
    if len(args) > 1:
        order_id = args[1]
        if order_id in orders and orders[order_id]["status"] == "pending":
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_{order_id}")],
                [InlineKeyboardButton(text="❌ Отменить", callback_data=f"cancel_{order_id}")]
            ])
            items_text = "\n".join([f"• {i['n']} x{i['q']} = {i['p']*i['q']} ₽" for i in orders[order_id]["items"]])
            await msg.answer(f"🛒 Заказ {order_id}\n\n{items_text}\n\n💰 Итого: {orders[order_id]['total']} ₽\n\nПодтвердите заказ:", reply_markup=kb)
            return
    await msg.answer("Добро пожаловать! Используйте кнопку подтверждения из основного бота.")

@dp_pay.callback_query(F.data.startswith("confirm_"))
async def confirm_order(cb: types.CallbackQuery):
    order_id = cb.data.split("_")[1]
    if order_id not in orders: return
    orders[order_id]["status"] = "processing"
    save_orders()    
    await cb.message.edit_text(f"✅ Заказ {order_id} подтвержден!\n⏳ Статус: В обработке...")
    
    kb_stock = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📥 Принять в обработку", callback_data=f"accept_{order_id}")
    ]])
    client = orders[order_id]["client"]
    txt = f"🔥 НОВЫЙ ЗАКАЗ {order_id}\n\n👤 {client.get('name','')} {client.get('surname','')}\n📞 {client.get('phone','')}\n✈️ @{client.get('tg','')}\n📍 {client.get('city','')}, {client.get('street','')} д.{client.get('house','')} кв.{client.get('flat','')}\n\n💰 Сумма: {orders[order_id]['total']} ₽"
    await bot_stock.send_message(ADMIN_ID, txt, reply_markup=kb_stock)
    await cb.answer()

@dp_pay.callback_query(F.data.startswith("cancel_"))
async def cancel_order(cb: types.CallbackQuery):
    order_id = cb.data.split("_")[1]
    if order_id in orders:
        orders[order_id]["status"] = "cancelled"
        save_orders()
        await cb.message.edit_text(f"❌ Заказ {order_id} отменен.")
    await cb.answer()

# ==========================================
# 📦 3. СКЛАДСКОЙ БОТ (@trifferistockbot)
# ==========================================
@dp_stock.callback_query(F.data.startswith("accept_"))
async def accept_order_stock(cb: types.CallbackQuery):
    order_id = cb.data.split("_")[1]
    if order_id not in orders: return
    
    orders[order_id]["status"] = "accepted"
    save_orders()
    
    await cb.message.edit_text(f"✅ Заказ {order_id} принят в обработку.\nОжидает отправки.")
    
    user_id = orders[order_id]["user_id"]
    try:
        await bot_pay.send_message(user_id, f"✅ Ваш заказ {order_id} принят в работу!\nМы свяжемся с вами для уточнения доставки.")
    except: pass
    await cb.answer()

# ==========================================
# 🚀 ЗАПУСК
# ==========================================
async def main():
    logging.basicConfig(level=logging.INFO)
    print("🤖 Запуск 3 ботов...")
    # Запускаем Flask сервер в фоне для Render
    threading.Thread(target=run_server, daemon=True).start()
    await asyncio.gather(
        dp_main.start_polling(bot_main),
        dp_pay.start_polling(bot_pay),        dp_stock.start_polling(bot_stock)
    )

if __name__ == "__main__":
    asyncio.run(main())
