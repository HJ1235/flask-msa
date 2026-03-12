import os
from dotenv import load_dotenv
from flask import Flask
from diary import diary_bp

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 104857600))

app.register_blueprint(diary_bp)

@app.route("/health", methods=["GET"])
def health():
    return "ok", 200

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=5002)
