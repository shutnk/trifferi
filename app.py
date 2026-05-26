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
            {'id': 1, 'name': 'LUNA', 'type': 'Сумка', 'price': 12990, 'image': 'bag.png'},
            {'id': 2, 'name': 'AURORA', 'type': 'Кроссовки', 'price': 7450, 'image': 'sneakers.png'},
            {'id': 3, 'name': 'SKY', 'type': 'Очки', 'price': 4100, 'image': 'sunglasses.png'},
            {'id': 4, 'name': 'SILK', 'type': 'Шарф', 'price': 3200, 'image': 'scarf.png'},
        ]
    })

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    user = update.effective_user
    webapp_url = f"{WEB_URL}?startapp=main&user_id={user.id}"
    
    keyboard = [
        [InlineKeyboardButton("🛍 Открыть магазин", web_app=WebAppInfo(url=webapp_url))]
    ]
    
    await update.message.reply_text(
        f"👋 *Привет, {user.first_name}!*\n\n"
        f"Добро пожаловать в *TRIFFERI* — твой магазин стильных вещей! ✨\n\n"
        f"Нажми кнопку ниже, чтобы открыть магазин:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )
async def shop_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /shop"""
    user = update.effective_user
    webapp_url = f"{WEB_URL}?startapp=shop&user_id={user.id}"
    
    keyboard = [
        [InlineKeyboardButton("🛒 Перейти в каталог", web_app=WebAppInfo(url=webapp_url))]
    ]
    
    await update.message.reply_text(
        "🛍 *Открываю каталог TRIFFERI...*\n\n"
        "Здесь ты найдёшь новинки и хиты продаж!",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    await update.message.reply_text(
        "📌 *Доступные команды:*\n\n"
        "/start — Открыть главный экран магазина\n"
        "/shop — Перейти в каталог\n"
        "/help — Показать эту справку\n\n"
        "Или нажми кнопку меню слева от поля ввода 🛍",
        parse_mode='Markdown'
    )

def run_bot():
    """Запуск бота в отдельном потоке"""
    async def start_polling():
        application = Application.builder().token(TOKEN).build()
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler("start", start_cmd))
        application.add_handler(CommandHandler("shop", shop_cmd))
        application.add_handler(CommandHandler("help", help_cmd))
        application.add_handler(CommandHandler("menu", start_cmd))
        
        logger.info("🤖 Бот запущен и слушает команды...")
        
        # Запускаем polling
        await application.start_polling(allowed_updates=Update.ALL_TYPES)
    
    # Запускаем asyncio event loop
    asyncio.run(start_polling())

if __name__ == '__main__':
    logger.info(f"🚀 TRIFFERI Server starting on port {PORT}")
    logger.info(f"🔗 WebApp URL: {WEB_URL}")
    logger.info(f"🤖 Bot: @trifferishopbot")    
    # Запускаем бота в фоновом потоке
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    
    # Запускаем Flask сервер
    app.run(host='0.0.0.0', port=PORT, debug=False)
