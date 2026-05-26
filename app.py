import os, logging
from flask import Flask, render_template, jsonify

TOKEN = "8934522015:AAHJuYuqOu9-CYyhTZavQ-MDlCn1Sw4T4vw"
PORT = int(os.environ.get("PORT", 8080))
WEB_URL = os.environ.get("WEB_URL", "http://localhost:8080")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates', static_folder='static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/products')
def get_products():
    return jsonify({'status': 'ok', 'products': [
        {'id': 1, 'name': 'LUNA', 'type': 'Сумка', 'price': 12990, 'currency': 'RUB'},
        {'id': 2, 'name': 'AURORA', 'type': 'Кроссовки', 'price': 7450, 'currency': 'RUB'},
        {'id': 3, 'name': 'SKY', 'type': 'Очки', 'price': 4100, 'currency': 'RUB'},
    ]})

@app.route('/api/webapp/init')
def webapp_init():
    """Инициализация для Telegram WebApp"""
    return jsonify({'status': 'ok', 'web_url': WEB_URL})

if __name__ == '__main__':
    logger.info(f"🚀 TRIFFERI Server: http://0.0.0.0:{PORT}")
    logger.info(f"🔗 WebApp URL: {WEB_URL}")
    app.run(host='0.0.0.0', port=PORT, debug=False)
