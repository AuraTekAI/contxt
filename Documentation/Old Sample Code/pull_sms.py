from flask import Flask, request, jsonify
import json
import hmac
import hashlib
import logging
from variables import API_KEY

app = Flask(__name__)
app.config['DEBUG'] = True  # Enable debug mode for detailed error messages
logging.basicConfig(level=logging.INFO)

def verify_webhook(api_key, timestamp, request_signature, request_payload):
    if not timestamp or not request_signature:
        logging.error('Missing timestamp or request_signature')
        return False

    my_signature = hmac.new(api_key.encode('utf-8'), (timestamp + request_payload).encode('utf-8'), hashlib.sha256).hexdigest()
    return hmac.compare_digest(request_signature, my_signature)

@app.route('/smsapi', methods=['POST'])
def handle_sms():
    content_length = request.content_length
    post_data = request.get_data(as_text=True)

    request_signature = request.headers.get('X-textbelt-signature')
    timestamp = request.headers.get('X-textbelt-timestamp')

    logging.info(f"Request headers: {request.headers}")
    logging.info(f"Request data: {post_data}")

    if not verify_webhook(API_KEY, timestamp, request_signature, post_data):
        logging.error('Invalid webhook signature')
        return jsonify({'success': False, 'error': 'Invalid signature'}), 403

    data = json.loads(post_data)
    text_id = data.get('textId')
    from_number = data.get('fromNumber')
    text = data.get('text')

    logging.info(f"Received reply from {from_number} for text ID {text_id}: {text}")

    return jsonify({'success': True})

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000)  # Development server, internal port
