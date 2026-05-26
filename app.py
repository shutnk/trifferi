import os, logging, asyncio, threading
from flask import Flask, render_template, jsonify
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8934522015:AAHJuYuqOu9-CYyhTZavQ-MDlCn1Sw4T4vw"
PORT = int(os.environ.get("PORT", 8080))
WEB_URL = os.environ.get("WEB_URL", "http://localhost:8080")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/products')
def get_products():
    return jsonify({
        'status': 'ok',
        'products': [
            {'id': 1, 'name': 'LUNA', 'type': 'Сумка', 'price': 12990},
            {'id': 2, 'name': 'AURORA', 'type': 'Кроссовки', 'price': 7450},
            {'id': 3, 'name': 'SKY', 'type': 'Очки', 'price': 4100},
        ]
    })

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    webapp_url = f"{WEB_URL}?startapp=main&user_id={user.id}"
    kb = [[InlineKeyboardButton("🛍 Открыть магазин", web_app=WebAppInfo(url=webapp_url))]]
    await update.message.reply_text(
        f"👋 *Привет, {user.first_name}!*\n\nДобро пожаловать в *TRIFFERI* ✨",
        reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown'
    )

async def shop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    webapp_url = f"{WEB_URL}?startapp=shop"
    kb = [[InlineKeyboardButton("🛒 Каталог", web_app=WebAppInfo(url=webapp_url))]]
    await update.message.reply_text("🛍 Каталог:", reply_markup=InlineKeyboardMarkup(kb))

def run_bot():
    """Запуск бота с созданием event loop"""
    async def start_bot():
        application = Application.builder().token(TOKEN).build()
        application.add_handler(CommandHandler("start", start_cmd))
        application.add_handler(CommandHandler("shop", shop_cmd))
        logger.info("🤖 Бот запущен...")
        await application.start_polling(allowed_updates=Update.ALL_TYPES)
    
    # Создаём новый event loop для этого потока
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(start_bot())

if __name__ == '__main__':
    logger.info(f"🚀 Server: http://0.0.0.0:{PORT}")
    
    # Запускаем бота в фоне
    t = threading.Thread(target=run_bot, daemon=True)
    t.start()
    
    # Запускаем Flask
    app.run(host='0.0.0.0', port=PORT, debug=False)
