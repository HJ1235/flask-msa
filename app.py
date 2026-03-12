import os
from dotenv import load_dotenv, find_dotenv
from flask import Flask

dotenv_path = find_dotenv('/var/www/html/your_flask_app/.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24).hex())

# Blueprint 등록
from blueprints.auth import auth_bp
from blueprints.board import board_bp
from blueprints.diary import diary_bp
from blueprints.todos import todos_bp
from blueprints.study import study_bp
from blueprints.admin import admin_bp

app.register_blueprint(auth_bp)
app.register_blueprint(board_bp)
app.register_blueprint(diary_bp)
app.register_blueprint(todos_bp)
app.register_blueprint(study_bp)
app.register_blueprint(admin_bp)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
