import os
import json
import asyncio
import logging
import random
from flask import Flask, request, jsonify, send_from_directory
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='templates', static_url_path='')

# ===========================================================
# NASTROIKI
# ===========================================================
SHOP_TOKEN = "8934522015:AAHJuYuqOu9-CYyhTZavQ-MDlCn1Sw4T4vw"
PAY_TOKEN = "8441860983:AAFMuNBnImWdFc17Fg8fYPZcVPl5YkwuQp4"
STOCK_TOKEN = "8666600867:AAHSTjcwfKJQv5KVb3x0QBgJXdmXDHTQGEc"
ADMIN_ID = 5468112563
WEBAPP_URL = "https://trifferi.onrender.com"

# ===========================================================
# INICIALIZATION BOTOV
# ===========================================================
shop_bot = Bot(token=SHOP_TOKEN)
pay_bot = Bot(token=PAY_TOKEN)
stock_bot = Bot(token=STOCK_TOKEN)

dp_shop = Dispatcher()
dp_pay = Dispatcher()
dp_stock = Dispatcher()

# ===========================================================
# FLASK ROUTY
# ===========================================================
@app.route('/')
def index():
    return send_from_directory('templates', 'index.html')

@app.route('/api/order', methods=['POST'])
async def api_order():
    try:
        data = await request.get_json()
        logger.info(f"Poluchen zakaz: {data}")
        
        if not data:
            return jsonify({"status": "error", "error": "No data"}), 400
        
        customer = data.get('customer', {})
        items = data.get('items', [])
        total = data.get('total', 0)
        user_id = data.get('userId')
        
        if not user_id:
            return jsonify({"status": "error", "error": "No userId"}), 400
        
        order_id = f"#{random.randint(1000, 9999)}"
        
        # Soobshenie klientu cherez PAY bota
        items_text = "\n".join([f"{i['n']} - {i['p']} ‽" for i in items])
        
        client_msg = f"✅ Zakaz {order_id} soozdan! \n\nSostav:\n{items_text}\n\nSumma: {total} €\n\nStatus: R Obrabotke."
        
        try:
            await pay_bot.send_message(user_id, client_msg, parse_mode='HTML')
            logger.info(f"Otpravleno klientu {user_id}")
        except Exception as e:
            logger.error(f"Oshibka otpravki klientu: {e}")
        
        # Soobshenie adminu cherez STOCK bota
        admin_msg = f"🌙 NOVYI ZAKAZ {order_id}\n\nKlient ID: {user_id}\nImya: {customer.get('name')}\nTelefon: {customer.get('phone')}\nAdres: {customer.get('address')}\n\nTovary:\n{items_text}\n\nItogo: {total} ‽"
        
        kb = InlineKeyboardBuilder()
        kb.button(text="✅ PRINYT'", callback_data=f"accept_{user_id}_{order_id}")
        kb.button(text="⌘ OTKAZAT', callback_data=f"reject_{user_id}_{order_id}")
        
        try:
            await stock_bot.send_message(ADMIN_ID, admin_msg, reply_markup=kb.as_markup(), parse_mode='HTML')
            logger.info(f"Otpravleno adminu {ADMIN_ID}")
        except Exception as e:
            logger.error(f"Oshibka otpravki adminu: {e}")
        
        return jsonify({"status": "success", "order_id": order_id})
        
    except Exception as e:
        logger.error(f"Oshibka v api/order: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

# ===========================================================
# SHOP BOT
# ===========================================================
@dp_shop.message(Command('start'))
async def cmd_start(message: types.Message):
    k = InlineKeyboardBuilder()
    kb.button(text="🛋 OTKRYTM MAGAZyIN", web_app=WebAppInfo(url=WEBAPP_URL))
    await message.answer("Dobro pojalovat v TRIFFERI!", reply_markup=kb.as_markup())

# ===========================================================
# STOCK BOT
# ===========================================================
@dp_stock.callback_query(F.data.startswith('accept_') | F.data.startswith('reject_'))
async def handle_admin_decision(callback_query: types.CallbackQuery):
    try:
        action, user_id, order_id = callback_query.data.split('_', 2)
        
        if action == 'accept':
            text = f"✅ Zakaz {order_id} PRINYT! Ozhidaite dostavku."
            await pay_bot.send_message(user_id, text, parse_mode='HTML')
            await callback_query.answer("✅ VY prinyli zaKaz!")
        elif action == 'reject':
            text = f"⌈ Zakaz {order_id} otklonen."
            await pay_bot.send_message(user_id, text, parse_mode='HTML')
            await callback_query.answer("⌈ Vy otkazali.")
    except Exception as e:
        logger.error(f"Oshibka v callback: {e}")

# ===========================================================
# PAY BOT
# ===========================================================
@dp_pay.message(Command('start'))
async def pay_start(message: types.Message):
    await message.answer("👫 Eto bot dly uvedomleniy o zakazak.")

# ===========================================================
# ZAPUSH
# ===========================================================
async def main():
    if os.getenv('RENDER'):
        logger.info("Zapusheno na Render - tolko Flask")
        return
    
    logger.info("Zapusk botov...")
    await asyncio.gather(
        dp_shop.start_polling(shop_bot),
        dp_pay.start_polling(pay_bot),
        dp_stock.start_polling(stock_bot)
    )

if __name__ == '__main__':
    logger.info("Zapusk Flask...")
    app.run(host='0.0.0.0', port=10000, threaded=True)
