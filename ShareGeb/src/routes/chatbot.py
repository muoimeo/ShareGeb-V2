from flask import Blueprint, request, jsonify
import google.generativeai as genai
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

chatbot_bp = Blueprint("chatbot", __name__)

# Configure Gemini API using environment variable
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Ensure the API key is set in your environment

if not GEMINI_API_KEY:
    logging.error("GEMINI_API_KEY is not set in the environment variables.")
    raise ValueError("GEMINI_API_KEY must be set.")

genai.configure(api_key=GEMINI_API_KEY)

# Chatbot prompt template
CHATBOT_PROMPT = """
Bạn là 1 chuyên viên hỗ trợ trong công việc giới thiệu và hướng dẫn khách hàng, 
phục vụ và hướng dẫn khách hàng sử dụng dịch vụ của trang web. 
Hãy trả lời câu hỏi của khách hàng một cách chuyên nghiệp và thân thiện.
"""

@chatbot_bp.route("/chat", methods=["POST"])
def chat():
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