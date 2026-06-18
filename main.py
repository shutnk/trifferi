import os
import logging
import random
from flask import Flask, request, jsonify, send_from_directory

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder="templates", static_url_path="")

@app.route("/")
def index():
    return send_from_directory("templates", "index.html")

@app.route("/api/order", methods=["POST"])
async def api_order():
    try:
        data = await request.get_json()
        logger.info("Order received: " + str(data))
        
        if not data:
            return jsonify({"status": "error"}), 400
        
        user_id = data.get("userId")
        if not user_id:
            return jsonify({"status": "error"}), 400
            
        order_id = "#" + str(random.randint(1000, 9999))
        
        # Просто логируем заказ (ботов добавим позже)
        logger.info("Order " + order_id + " for user " + str(user_id))
        
        return jsonify({"status": "success", "order_id": order_id})
        
    except Exception as e:
        logger.error("Error: " + str(e))
        return jsonify({"status": "error"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    logger.info("Starting Flask on port " + str(port))
    app.run(host="0.0.0.0", port=port, threaded=True)
