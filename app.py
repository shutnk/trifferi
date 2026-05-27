import os, logging, threading
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

@app.route('/catalog')
def catalog():
    return render_template('catalog.html')

@app.route('/wishlist')
def wishlist():
    return render_template('wishlist.html')

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
    await update.message.reply_text(f"👋 *Привет, {user.first_name}!*\n\nДобро пожаловать в *TRIFFERI* ✨", reply_markup=InlineKeyboardMarkup(kb), parse_mode='Markdown')

async def shop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    webapp_url = f"{WEB_URL}?startapp=shop"
    kb = [[InlineKeyboardButton("🛒 Каталог", web_app=WebAppInfo(url=webapp_url))]]
    await update.message.reply_text("🛍 Каталог:", reply_markup=InlineKeyboardMarkup(kb))

def run_flask():
    logger.info(f"🚀 Flask server: http://0.0.0.0:{PORT}")
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

def run_bot():
    logger.info("🤖 Запуск бота...")
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("shop", shop_cmd))
    logger.info("✅ Бот запущен и слушает команды...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    logger.info(f"🚀 TRIFFERI starting on port {PORT}")
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    run_bot()

@app.route('/cart')
def cart():
    return render_template('cart.html')
