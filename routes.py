# routes.py
import os
from flask import render_template, request, redirect, url_for, flash, send_file, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from functools import wraps
from app import app, db, allowed_file  # Added allowed_file
from models import User, Equipment, Maintenance, Notification, HealthData
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
import qrcode
import io
from PIL import Image, UnidentifiedImageError  # Ensure UnidentifiedImageError is imported
import random
# Custom decorator for role-based access
def role_required(*roles):
    def wrapper(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role not in roles:
                flash('Unauthorized access')
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

@app.route('/')
def index():
    """Redirects the root URL to the login page."""
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=remember, duration=timedelta(hours=24))
            if user.role == 'boss':
                return redirect(url_for('boss_dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif user.role == 'engineer':
                return redirect(url_for('engineer_dashboard'))
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Dashboards
@app.route('/boss_dashboard')
@role_required('boss')
def boss_dashboard():
    return render_template('boss_dashboard.html')

@app.route('/admin_dashboard')
@role_required('admin')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/engineer_dashboard')
@role_required('engineer')
def engineer_dashboard():
    equipment_list = Equipment.query.all()
    notifications = Notification.query.filter_by(user_id=current_user.id).order_by(Notification.timestamp.desc()).limit(5).all()

    # Update health for each equipment based on recent HealthData
    for equipment in equipment_list:
        recent_health_data = HealthData.query.filter_by(equipment_id=equipment.id).order_by(HealthData.timestamp.desc()).limit(5).all()
        if recent_health_data:
            avg_temperature = sum(data.temperature for data in recent_health_data) / len(recent_health_data)
            equipment.health = max(0, min(100, 100 - (avg_temperature - 20) * 2))  # Example formula
            db.session.commit()

    # Serialize equipment_list for JavaScript
    equipment_list_json = [
        {
            'id': equip.id,
            'name': equip.name,
            'health': equip.health if equip.health is not None else 80  # Default if None
        } for equip in equipment_list
    ]

    return render_template('engineer_dashboard.html', equipment_list=equipment_list, notifications=notifications, equipment_list_json=equipment_list_json)

# User Management
@app.route('/user_management', methods=['GET', 'POST'])
@role_required('boss', 'admin')
def user_management():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
        else:
            new_user = User(username=username, role=role)
            new_user.set_password(password)
            db.session.add(new_user)
            db.session.commit()
            flash('User added successfully')
        return redirect(url_for('user_management'))
    users = User.query.all()
    return render_template('user_management.html', users=users)

@app.route('/user/edit/<int:user_id>', methods=['GET', 'POST'])
@role_required('boss', 'admin')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    if request.method == 'POST':
        user.username = request.form['username']
        user.role = request.form['role']
        if 'password' in request.form and request.form['password']:
            user.set_password(request.form['password'])
        db.session.commit()
        flash('User updated successfully')
        return redirect(url_for('user_management'))
    return render_template('edit_user.html', user=user)

@app.route('/user/delete/<int:user_id>', methods=['POST'])
@role_required('boss', 'admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully')
    return redirect(url_for('user_management'))

# Equipment Management
@app.route('/add_equipment', methods=['GET', 'POST'])
@role_required('boss', 'admin', 'engineer')
def add_equipment():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        image = request.files.get('image')
        filename = None
        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            try:
                image.save(image_path)
                img = Image.open(image_path)
                img = img.convert('RGB')
                img = img.resize((300, 300), Image.Resampling.LANCZOS)
                img.save(image_path)
            except (UnidentifiedImageError, IOError) as e:
                flash(f'Error processing image: {str(e)}. Please upload a valid image file.')
                return redirect(url_for('add_equipment'))
        equipment = Equipment(
            name=name,
            description=description,
            image=filename,
            health=random.uniform(60, 100)  # Random health between 60 and 100
        )
        db.session.add(equipment)
        db.session.commit()
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url_for('equipment_detail', equipment_id=equipment.id, _external=True))
        qr.make(fit=True)
        qr_img = qr.make_image(fill='black', back_color='white')
        qr_filename = f'qr_{equipment.id}.png'
        qr_path = os.path.join(app.config['UPLOAD_FOLDER'], qr_filename)
        qr_img.save(qr_path)
        equipment.qr_code = qr_filename
        db.session.commit()
        flash('Equipment added successfully')
        return redirect(url_for('view_equipment'))
    return render_template('add_equipment.html')

@app.route('/view_equipment')
@login_required
def view_equipment():
    equipment_list = Equipment.query.all()
    return render_template('view_equipment.html', equipment_list=equipment_list)

@app.route('/equipment/<int:equipment_id>')
@login_required
def equipment_detail(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    return render_template('equipment_detail.html', equipment=equipment)

@app.route('/qr_code/<int:equipment_id>')
@login_required
def qr_code(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    url = url_for('equipment_detail', equipment_id=equipment_id, _external=True)
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')
    img_io = io.BytesIO()
    img.save(img_io, 'PNG')
    img_io.seek(0)
    return send_file(img_io, mimetype='image/png')

# Maintenance Management
@app.route('/log_maintenance', methods=['GET', 'POST'])
@role_required('engineer', 'admin', 'boss')
def log_maintenance():
    if request.method == 'POST':
        equipment_id = request.form['equipment_id']
        description = request.form['description']
        maintenance = Maintenance(equipment_id=equipment_id, description=description, user_id=current_user.id, completed_date=datetime.utcnow())
        db.session.add(maintenance)
        db.session.commit()
        flash('Maintenance logged')
        return redirect(url_for('view_equipment'))
    equipment_list = Equipment.query.all()
    return render_template('log_maintenance.html', equipment_list=equipment_list)

@app.route('/schedule_maintenance', methods=['GET', 'POST'])
@role_required('boss', 'admin', 'engineer')
def schedule_maintenance():
    if request.method == 'POST':
        equipment_id = request.form['equipment_id']
        description = request.form['description']
        scheduled_date = datetime.strptime(request.form['scheduled_date'], '%Y-%m-%d')
        maintenance = Maintenance(equipment_id=equipment_id, description=description, scheduled_date=scheduled_date, user_id=current_user.id)
        db.session.add(maintenance)
        db.session.commit()
        flash('Maintenance scheduled')
        return redirect(url_for('view_schedules'))
    equipment_list = Equipment.query.all()
    return render_template('schedule_maintenance.html', equipment_list=equipment_list)

@app.route('/view_schedules')
@login_required
def view_schedules():
    schedules = Maintenance.query.filter(Maintenance.scheduled_date.isnot(None)).all()
    return render_template('view_schedules.html', schedules=schedules)

# Notifications and Reporting
@app.route('/report_issue', methods=['POST'])
@login_required
def report_issue():
    message = request.form['message']
    equipment_id = request.form['equipment_id']
    notification = Notification(message=f"Issue reported: {message} (Equipment ID: {equipment_id})", user_id=current_user.id)
    db.session.add(notification)
    db.session.commit()
    flash('Issue reported successfully')
    return redirect(url_for('view_equipment'))

@app.route('/notifications')
@role_required('boss', 'admin', 'engineer')
def notifications():
    notifications = Notification.query.order_by(Notification.timestamp.desc()).all()
    return render_template('notifications.html', notifications=notifications)

# Health Data Endpoint
@app.route('/get_health_data/<int:equipment_id>')
@login_required
def get_health_data(equipment_id):
    health_data = HealthData.query.filter_by(equipment_id=equipment_id).order_by(HealthData.timestamp).all()
    labels = [data.timestamp.strftime('%H:%M') for data in health_data]
    temperature = [data.temperature for data in health_data]
    data = {
        'labels': labels,
        'temperature': temperature
    }
    return jsonify(data)

# QR Code Scanning
@app.route('/scan_qr')
@login_required
def scan_qr():
    return render_template('scan_qr.html')

@app.route('/process_qr', methods=['POST'])
@login_required
def process_qr():
    qr_data = request.form.get('qr_data')
    if qr_data:
        try:
            equipment_id = int(qr_data.split('/')[-1])
            equipment = Equipment.query.get(equipment_id)
            if equipment:
                return render_template('equipment_detail.html', equipment=equipment)
            else:
                flash('Equipment not found in database')
                return redirect(url_for('scan_qr'))
        except (ValueError, IndexError):
            flash('Invalid QR code')
            return redirect(url_for('scan_qr'))
    flash('No QR code data received')
    return redirect(url_for('scan_qr'))

@app.route('/get_equipment_health/<int:equipment_id>')
@login_required
def get_equipment_health(equipment_id):
    equipment = Equipment.query.get_or_404(equipment_id)
    # Simulate a simple health trend: current health with slight variations
    labels = [datetime.utcnow().strftime('%H:%M')]  # Single point for now
    health_values = [equipment.health]
    data = {
        'labels': labels,
        'health': health_values
    }
    return jsonify(data)