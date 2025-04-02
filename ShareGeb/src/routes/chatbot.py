from flask import Blueprint, request, jsonify
import google.generativeai as genai
import os
import logging
from src.templates.chatbot_templates.prompts import CHATBOT_PROMPT

# Set up logging
logging.basicConfig(level=logging.INFO)

chatbot_bp = Blueprint("chatbot", __name__)

# Initialize API key as None - sẽ được cấu hình sau khi tải biến môi trường
GEMINI_API_KEY = None

# Cấu hình API key động - chỉ được gọi khi cần thiết
def configure_gemini_api():
    global GEMINI_API_KEY
    if GEMINI_API_KEY is None:
        GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
        logging.info(f"GEMINI_API_KEY is set: {GEMINI_API_KEY is not None}")
        
        if not GEMINI_API_KEY:
            logging.error("GEMINI_API_KEY is not set in the environment variables.")
            raise ValueError("GEMINI_API_KEY must be set.")
            
        genai.configure(api_key=GEMINI_API_KEY)

@chatbot_bp.route("/chat", methods=["POST"])
def chat():
    # Đảm bảo API key được cấu hình trước khi sử dụng
    configure_gemini_api()
    
    data = request.json
    user_message = data.get("message", "")

    if not user_message:
        return jsonify({"response": "Xin lỗi, vui lòng nhập nội dung câu hỏi."})

    try:
        model = genai.GenerativeModel("gemini-2.0-flash")  # Ensure the model name is correct
        response = model.generate_content(f"{CHATBOT_PROMPT}\n\nKhách hàng: {user_message}\nChuyên viên:")
        
        bot_reply = response.text.strip() if response and response.text else "Xin lỗi, tôi không hiểu câu hỏi của bạn."

        return jsonify({"response": bot_reply})

    except Exception as e:
        logging.error("Error in chatbot API call: %s", e)
        return jsonify({"response": "Có lỗi xảy ra khi kết nối với hệ thống hỗ trợ. Vui lòng thử lại sau."})