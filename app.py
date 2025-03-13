# app.py
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'  # Replace with a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///maintenance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/images/'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Import db from database.py
from database import db

# Initialize db with the app
db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Import models after db is initialized
from models import User, Equipment, Maintenance, Notification

# Allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp', 'tiff'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Import routes after app and extensions are initialized
from routes import *

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # equip = Equipment.query.first() or Equipment(name="Test Pump")
        # db.session.add(equip)
        # db.session.commit()
        # for temp in [22, 23, 25, 24]:
        #     db.session.add(HealthData(equipment_id=equip.id, temperature=temp, timestamp=datetime.utcnow()))
        # db.session.commit()

    app.run(debug=True)