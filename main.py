import os, json, asyncio, logging, random
from flask import Flask, request, jsonify, send_from_directory
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="templates", static_url_path="")

# Tokens
SHOP_TOKEN = "8934522015:AAHJuYuqOu9-CYyhTZavQ-MDlCn1Sw4T4vw"
PAY_TOKEN = "8441860983:AAFMuNBnImWdFc17Fg8fYPzcVPl5YkwuQp4"
STOCK_TOKEN = "8666600867:AAHSTjcwfKJQv5KVb3x0QBgJXdmXDHTQGEc"
ADMIN_ID = 5468112563
WEBAPP_URL = "https://trifferi.onrender.com"

# Bots init
shop_bot = Bot(token=SHOP_TOKEN)
pay_bot = Bot(token=PAY_TOKEN)
stock_bot = Bot(token=STOCK_TOKEN)
dp_shop = Dispatcher()
dp_pay = Dispatcher()
dp_stock = Dispatcher()

@app.route("/")
def index():
    return send_from_directory("templates", "index.html")

@app.route("/api/order", methods=["POST"])
async def api_order():
    try:
        data = await request.get_json()
        if not data: return jsonify({"status":"error"}), 400
        customer = data.get("customer", {})
        items = data.get("items", [])
        total = data.get("total", 0)
        user_id = data.get("userId")
        if not user_id: return jsonify({"status":"error"}), 400
        order_id = f"#{random.randint(1000,9999)}"
        items_text = "\\n".join([f"{i[\"n\"]} - {i[\"p\"]} RUB" for i in items])echo         client_msg = f"Order {order_id} created!\\n\\nItems:\\n{items_text}\\n\\nTotal: {total} RUB\\n\\nStatus: Processing."
        try:
            await pay_bot.send_message(user_id, client_msg)
        except Exception as e: logger.error(f"Client send error: {e}")
        admin_msg = f"NEW ORDER {order_id}\\n\\nUser: {user_id}\\nName: {customer.get(\"name\")}\\nPhone: {customer.get(\"phone\")}\\nAddress: {customer.get(\"address\")}\\n\\nItems:\\n{items_text}\\n\\nTotal: {total} RUB"
        kb = InlineKeyboardBuilder()
        kb.button(text="ACCEPT", callback_data=f"accept_{user_id}_{order_id}")
        kb.button(text="REJECT", callback_data=f"reject_{user_id}_{order_id}")
        try:
            await stock_bot.send_message(ADMIN_ID, admin_msg, reply_markup=kb.as_markup())
        except Exception as e: logger.error(f"Admin send error: {e}")
        return jsonify({"status":"success","order_id":order_id})
    except Exception as e:
        logger.error(f"API error: {e}")
        return jsonify({"status":"error"}), 500

@dp_shop.message(Command("start"))
async def cmd_start(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="Open Shop", web_app=WebAppInfo(url=WEBAPP_URL))
    await message.answer("Welcome to TRIFFERI!", reply_markup=kb.as_markup())

@dp_stock.callback_query(F.data.startswith("accept_") | F.data.startswith("reject_"))
async def handle_admin(callback_query: types.CallbackQuery):
    try:
        action, uid, oid = callback_query.data.split("_", 2)
        if action == "accept":
            await pay_bot.send_message(uid, f"Order {oid} ACCEPTED! Wait for delivery.")
            await callback_query.answer("Accepted!")
        elif action == "reject":
            await pay_bot.send_message(uid, f"Order {oid} rejected.")
            await callback_query.answer("Rejected.")
    except Exception as e: logger.error(f"Callback error: {e}")

@dp_pay.message(Command("start"))
async def pay_start(message: types.Message):
    await message.answer("TRIFFERI Pay bot for order notifications.")

async def main():
    if os.getenv("RENDER"):
        logger.info("Running on Render - Flask only")
        return
    logger.info("Starting bots...")
    await asyncio.gather(
        dp_shop.start_polling(shop_bot),
        dp_pay.start_polling(pay_bot),
        dp_stock.start_polling(stock_bot)
    )

if __name__ == "__main__":echo     logger.info("Starting Flask...")
    app.run(host="0.0.0.0", port=10000, threaded=True)
