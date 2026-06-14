from flask import Flask, request, jsonify, session, redirect
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config
from models import db, User, Driver, Vehicle, Task, LocationLaborRate, Client, ClientContact, ScheduleConfirmation, ConfirmationSnapshot
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import json
import time
import uuid
import hashlib
import base64
import urllib.request
import urllib.parse
import urllib.error
from utils.wx_work import WxWorkClient, format_confirm_message, format_external_confirm_message, get_userinfo_by_code, get_user_detail

def decrypt_yzj_callback(encrypted_data, developer_key):
    """
    解密云之家回调数据
    encrypted_data: Base64编码的加密数据
    developer_key: 开发者key（16位字符）
    返回解密后的JSON数据

    根据云之家JAVA DEMO，使用 AES/ECB/PKCS5Padding 模式
    """
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

    try:
        # AES密钥 = 开发者key的UTF-8字节
        aes_key = developer_key.encode('utf-8')

        # Base64解码
        encrypted_bytes = base64.b64decode(encrypted_data)

        # AES-ECB解密（云之家JAVA DEMO使用的是AES默认模式，即ECB）
        cipher = Cipher(algorithms.AES(aes_key), modes.ECB())
        decryptor = cipher.decryptor()
        decrypted = decryptor.update(encrypted_bytes) + decryptor.finalize()

        # 去除PKCS7 padding
        pad_len = decrypted[-1]
        if 1 <= pad_len <= 16:
            decrypted = decrypted[:-pad_len]

        # 解析为JSON
        text = decrypted.decode('utf-8')
        return json.loads(text)

    except Exception as e:
        app.logger.error(f"解密云之家回调数据失败: {e}")
        return None

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.config.from_object(Config)
CORS(app, supports_credentials=True)
db.init_app(app)


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'code': 401, 'msg': '请先登录'}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'code': 401, 'msg': '请先登录'}), 401
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            return jsonify({'code': 403, 'msg': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    return decorated


# ==================== Auth ====================

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if not username or not password:
        return jsonify({'code': 400, 'msg': '用户名和密码不能为空'})
    user = User.query.filter_by(username=username).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({'code': 401, 'msg': '用户名或密码错误'})
    session['user_id'] = user.id
    return jsonify({'code': 200, 'msg': '登录成功', 'data': user.to_dict()})


@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'code': 200, 'msg': '已退出登录'})


@app.route('/api/user/info', methods=['GET'])
@login_required
def user_info():
    user = User.query.get(session['user_id'])
    return jsonify({'code': 200, 'data': user.to_dict()})


# ==================== User Management (Admin) ====================

@app.route('/api/users', methods=['GET'])
@admin_required
def list_users():
    users = User.query.all()
    return jsonify({'code': 200, 'data': [u.to_dict() for u in users]})


@app.route('/api/users', methods=['POST'])
@admin_required
def create_user():
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'user')
    permissions = data.get('permissions', [])
    if not username or not password:
        return jsonify({'code': 400, 'msg': '用户名和密码不能为空'})
    if User.query.filter_by(username=username).first():
        return jsonify({'code': 400, 'msg': '用户名已存在'})
    user = User(
        username=username,
        password_hash=generate_password_hash(password),
        role=role
    )
    user.set_permissions(permissions)
    db.session.add(user)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '创建成功', 'data': user.to_dict()})


@app.route('/api/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'msg': '用户不存在'})
    data = request.get_json()
    if 'username' in data:
        user.username = data['username']
    if 'password' in data and data['password']:
        user.password_hash = generate_password_hash(data['password'])
    if 'role' in data:
        user.role = data['role']
    if 'permissions' in data:
        user.set_permissions(data['permissions'])
    db.session.commit()
    return jsonify({'code': 200, 'msg': '更新成功', 'data': user.to_dict()})


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'msg': '用户不存在'})
    if user.id == session['user_id']:
        return jsonify({'code': 400, 'msg': '不能删除自己'})
    db.session.delete(user)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '删除成功'})


# ==================== Drivers ====================

@app.route('/api/drivers', methods=['GET'])
@login_required
def list_drivers():
    drivers = Driver.query.all()
    return jsonify({'code': 200, 'data': [d.to_dict() for d in drivers]})


@app.route('/api/drivers', methods=['POST'])
@login_required
def create_driver():
    data = request.get_json()
    driver = Driver(
        name=data.get('name', ''),
        phone=data.get('phone', ''),
        status=data.get('status', 'available')
    )
    db.session.add(driver)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '创建成功', 'data': driver.to_dict()})


@app.route('/api/drivers/<int:driver_id>', methods=['PUT'])
@login_required
def update_driver(driver_id):
    driver = Driver.query.get(driver_id)
    if not driver:
        return jsonify({'code': 404, 'msg': '司机不存在'})
    data = request.get_json()
    if 'name' in data:
        driver.name = data['name']
    if 'phone' in data:
        driver.phone = data['phone']
    if 'status' in data:
        driver.status = data['status']
    db.session.commit()
    return jsonify({'code': 200, 'msg': '更新成功', 'data': driver.to_dict()})


@app.route('/api/drivers/<int:driver_id>', methods=['DELETE'])
@login_required
def delete_driver(driver_id):
    driver = Driver.query.get(driver_id)
    if not driver:
        return jsonify({'code': 404, 'msg': '司机不存在'})
    db.session.delete(driver)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '删除成功'})


# ==================== Vehicles ====================

@app.route('/api/vehicles', methods=['GET'])
@login_required
def list_vehicles():
    vehicles = Vehicle.query.all()
    return jsonify({'code': 200, 'data': [v.to_dict() for v in vehicles]})


@app.route('/api/vehicles', methods=['POST'])
@login_required
def create_vehicle():
    data = request.get_json()
    vehicle = Vehicle(
        plate_number=data.get('plate_number', ''),
        vehicle_type=data.get('vehicle_type', ''),
        company=data.get('company', ''),
        status=data.get('status', 'available')
    )
    db.session.add(vehicle)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '创建成功', 'data': vehicle.to_dict()})


@app.route('/api/vehicles/<int:vehicle_id>', methods=['PUT'])
@login_required
def update_vehicle(vehicle_id):
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        return jsonify({'code': 404, 'msg': '车辆不存在'})
    data = request.get_json()
    if 'plate_number' in data:
        vehicle.plate_number = data['plate_number']
    if 'vehicle_type' in data:
        vehicle.vehicle_type = data['vehicle_type']
    if 'company' in data:
        vehicle.company = data['company']
    if 'status' in data:
        vehicle.status = data['status']
    db.session.commit()
    return jsonify({'code': 200, 'msg': '更新成功', 'data': vehicle.to_dict()})


@app.route('/api/vehicles/<int:vehicle_id>', methods=['DELETE'])
@login_required
def delete_vehicle(vehicle_id):
    vehicle = Vehicle.query.get(vehicle_id)
    if not vehicle:
        return jsonify({'code': 404, 'msg': '车辆不存在'})
    db.session.delete(vehicle)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '删除成功'})


# ==================== Location Labor Rates ====================

@app.route('/api/labor-rates', methods=['GET'])
@login_required
def list_labor_rates():
    rates = LocationLaborRate.query.all()
    return jsonify({'code': 200, 'data': [r.to_dict() for r in rates]})


@app.route('/api/labor-rates', methods=['POST'])
@login_required
def create_labor_rate():
    data = request.get_json()
    rate = LocationLaborRate(
        location=data.get('location', ''),
        labor_rate=data.get('labor_rate', 0),
        days=data.get('days', 1)
    )
    db.session.add(rate)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '创建成功', 'data': rate.to_dict()})


@app.route('/api/labor-rates/<int:rate_id>', methods=['DELETE'])
@login_required
def delete_labor_rate(rate_id):
    rate = LocationLaborRate.query.get(rate_id)
    if not rate:
        return jsonify({'code': 404, 'msg': '记录不存在'})
    db.session.delete(rate)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '删除成功'})


# ==================== Clients ====================

@app.route('/api/clients', methods=['GET'])
@login_required
def list_clients():
    clients = Client.query.order_by(Client.created_at.desc()).all()
    return jsonify({'code': 200, 'data': [c.to_dict(include_contacts=True) for c in clients]})


@app.route('/api/clients', methods=['POST'])
@login_required
def create_client():
    data = request.get_json()
    client = Client(name=data.get('name', ''), address=data.get('address', ''))
    db.session.add(client)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '创建成功', 'data': client.to_dict(include_contacts=True)})


@app.route('/api/clients/<int:client_id>', methods=['GET'])
@login_required
def get_client(client_id):
    client = Client.query.get(client_id)
    if not client:
        return jsonify({'code': 404, 'msg': '单位不存在'})
    return jsonify({'code': 200, 'data': client.to_dict(include_contacts=True)})


@app.route('/api/clients/<int:client_id>', methods=['PUT'])
@login_required
def update_client(client_id):
    client = Client.query.get(client_id)
    if not client:
        return jsonify({'code': 404, 'msg': '单位不存在'})
    data = request.get_json()
    client.name = data.get('name', client.name)
    client.address = data.get('address', client.address)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '更新成功', 'data': client.to_dict(include_contacts=True)})


@app.route('/api/clients/<int:client_id>', methods=['DELETE'])
@login_required
def delete_client(client_id):
    client = Client.query.get(client_id)
    if not client:
        return jsonify({'code': 404, 'msg': '单位不存在'})
    db.session.delete(client)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '删除成功'})


@app.route('/api/clients/<int:client_id>/contacts', methods=['POST'])
@login_required
def add_contact(client_id):
    client = Client.query.get(client_id)
    if not client:
        return jsonify({'code': 404, 'msg': '单位不存在'})
    data = request.get_json()
    contact = ClientContact(client_id=client_id, name=data.get('name', ''), phone=data.get('phone', ''), wx_userid=data.get('wx_userid', ''), wx_sender=data.get('wx_sender', ''))
    db.session.add(contact)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '添加成功', 'data': contact.to_dict()})


@app.route('/api/clients/<int:client_id>/contacts/<int:contact_id>', methods=['PUT'])
@login_required
def update_contact(client_id, contact_id):
    contact = ClientContact.query.filter_by(id=contact_id, client_id=client_id).first()
    if not contact:
        return jsonify({'code': 404, 'msg': '联系人不存在'})
    data = request.get_json()
    if 'name' in data:
        contact.name = data['name']
    if 'phone' in data:
        contact.phone = data['phone']
    if 'wx_userid' in data:
        contact.wx_userid = data['wx_userid']
    if 'wx_sender' in data:
        contact.wx_sender = data['wx_sender']
    db.session.commit()
    return jsonify({'code': 200, 'msg': '更新成功', 'data': contact.to_dict()})


@app.route('/api/clients/<int:client_id>/contacts/<int:contact_id>', methods=['DELETE'])
@login_required
def delete_contact(client_id, contact_id):
    contact = ClientContact.query.filter_by(id=contact_id, client_id=client_id).first()
    if not contact:
        return jsonify({'code': 404, 'msg': '联系人不存在'})
    db.session.delete(contact)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '删除成功'})


# ==================== Tasks ====================

@app.route('/api/tasks', methods=['GET'])
@login_required
def list_tasks():
    tasks = Task.query.order_by(Task.created_at.desc()).all()
    return jsonify({'code': 200, 'data': [t.to_dict() for t in tasks]})


def calc_rental_days(departure_time, return_time):
    """根据出车时间和回程时间自动计算租用天数，最少半天"""
    if not return_time or not departure_time:
        return 1
    if return_time <= departure_time:
        return 0.5
    diff_hours = (return_time - departure_time).total_seconds() / 3600
    if diff_hours <= 12:
        return 0.5
    import math
    return math.ceil(diff_hours / 12) * 0.5


@app.route('/api/tasks', methods=['POST'])
@login_required
def create_task():
    data = request.get_json()
    departure_time = datetime.strptime(data['departure_time'], '%Y-%m-%d %H:%M')
    return_time = datetime.strptime(data['return_time'], '%Y-%m-%d %H:%M') if data.get('return_time') else None
    rental_days = calc_rental_days(departure_time, return_time)
    client_type = data.get('client_type', 'personal')
    client_name = data.get('client_name', '')
    client_phone = data.get('client_phone', '')
    client_id = data.get('client_id')
    contact_id = data.get('contact_id')
    # 单位模式：从联系人填充姓名和电话
    if client_type == 'company' and contact_id:
        contact = ClientContact.query.get(contact_id)
        if contact:
            client_name = contact.name
            client_phone = contact.phone
            client_id = contact.client_id
    task = Task(
        client_type=client_type,
        client_name=client_name,
        client_phone=client_phone,
        client_id=client_id,
        contact_id=contact_id,
        departure=data.get('departure', ''),
        destination=data.get('destination', ''),
        departure_time=departure_time,
        return_time=return_time,
        rental_days=rental_days,
        vehicle_type=data.get('vehicle_type', ''),
        mileage=data.get('mileage', 0),
        rental_fee=data.get('rental_fee', 0),
        fuel_fee=data.get('fuel_fee', 0),
        bridge_fee=data.get('bridge_fee', 0),
        labor_fee=data.get('labor_fee', 0),
        status='pending'
    )
    task.estimated_cost = task.fuel_fee + task.bridge_fee + task.labor_fee
    task.estimated_profit = task.rental_fee - task.estimated_cost
    db.session.add(task)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '任务创建成功', 'data': task.to_dict()})


@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@login_required
def update_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'code': 404, 'msg': '任务不存在'})
    data = request.get_json()

    # Handle client type change
    if 'client_type' in data:
        client_type = data.get('client_type', 'personal')
        task.client_type = client_type
        if client_type == 'company' and data.get('contact_id'):
            contact = ClientContact.query.get(data['contact_id'])
            if contact:
                task.client_name = contact.name
                task.client_phone = contact.phone
                task.client_id = contact.client_id
                task.contact_id = contact.id
        else:
            task.client_name = data.get('client_name', task.client_name)
            task.client_phone = data.get('client_phone', task.client_phone)
            task.client_id = None
            task.contact_id = None

    # Record changes
    change_fields = {
        'client_name': '用车联系人',
        'client_phone': '联系电话',
        'departure': '出发地点',
        'destination': '目的地',
        'departure_time': '出车时间',
        'return_time': '回程时间',
        'vehicle_type': '车辆类型',
        'mileage': '任务里程',
        'rental_fee': '租车费',
        'fuel_fee': '油电费',
        'bridge_fee': '桥路费',
        'labor_fee': '司机人工费'
    }

    # Take snapshot before applying changes
    change_list = []
    for field, label in change_fields.items():
        if field in data:
            old_val = getattr(task, field)
            new_val = data[field]
            # Normalize comparison
            if field in ('mileage', 'rental_fee', 'fuel_fee', 'bridge_fee', 'labor_fee'):
                changed = float(old_val or 0) != float(new_val or 0)
            elif field in ('departure_time', 'return_time'):
                old_str = old_val.strftime('%Y-%m-%d %H:%M') if old_val else ''
                changed = old_str != str(new_val)
            else:
                changed = str(old_val) != str(new_val)
            if changed:
                change_list.append({'field': label, 'old_value': str(old_val or ''), 'new_value': str(new_val)})
                if field in ('departure_time', 'return_time'):
                    new_val = datetime.strptime(new_val, '%Y-%m-%d %H:%M') if new_val else None
                setattr(task, field, new_val)

    # Recalculate rental_days if departure_time or return_time changed
    if 'departure_time' in data or 'return_time' in data:
        task.rental_days = calc_rental_days(task.departure_time, task.return_time)

    if change_list:
        # Take snapshot AFTER applying changes
        snapshot = {
            'client_name': task.client_name,
            'client_phone': task.client_phone,
            'departure': task.departure,
            'destination': task.destination,
            'departure_time': task.departure_time.strftime('%Y-%m-%d %H:%M') if task.departure_time else '',
            'return_time': task.return_time.strftime('%Y-%m-%d %H:%M') if task.return_time else '',
            'rental_days': task.rental_days,
            'vehicle_type': task.vehicle_type,
            'mileage': task.mileage,
            'rental_fee': task.rental_fee,
            'fuel_fee': task.fuel_fee,
            'bridge_fee': task.bridge_fee,
            'labor_fee': task.labor_fee,
        }
        task.add_changes(change_list, snapshot)

    db.session.commit()
    return jsonify({'code': 200, 'msg': '更新成功', 'data': task.to_dict()})


@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'code': 404, 'msg': '任务不存在'})
    # 先删除关联的确认记录和快照
    confirmations = ScheduleConfirmation.query.filter_by(task_id=task_id).all()
    for conf in confirmations:
        ConfirmationSnapshot.query.filter_by(confirmation_id=conf.id).delete()
    ScheduleConfirmation.query.filter_by(task_id=task_id).delete()
    db.session.delete(task)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '删除成功'})


# ==================== Scheduling ====================

@app.route('/api/tasks/<int:task_id>/available-resources', methods=['GET'])
@login_required
def get_available_resources(task_id):
    """Get available vehicles and drivers for scheduling a task."""
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'code': 404, 'msg': '任务不存在'})

    task_start = task.departure_time
    task_end = task_start + timedelta(days=task.rental_days)

    # Find vehicles that are busy during this time period
    busy_vehicle_ids = set()
    busy_driver_ids = set()

    scheduled_tasks = Task.query.filter(
        Task.status.in_(['scheduled', 'pending']),
        Task.id != task_id,
        Task.vehicle_id.isnot(None)
    ).all()

    for st in scheduled_tasks:
        st_start = st.departure_time
        st_end = st_start + timedelta(days=st.rental_days)
        # Check overlap
        if task_start < st_end and task_end > st_start:
            if st.vehicle_id:
                busy_vehicle_ids.add(st.vehicle_id)
            if st.driver_id:
                busy_driver_ids.add(st.driver_id)

    # Get available vehicles
    available_vehicles = Vehicle.query.filter(
        Vehicle.status != 'maintenance',
        ~Vehicle.id.in_(busy_vehicle_ids) if busy_vehicle_ids else True
    ).all()

    # Get available drivers
    available_drivers_query = Driver.query.filter(
        Driver.status != 'inactive',
        ~Driver.id.in_(busy_driver_ids) if busy_driver_ids else True
    )
    available_drivers = available_drivers_query.all()

    # Calculate total labor fee earned by each driver and sort ascending
    driver_fees = {}
    for driver in available_drivers:
        total_fee = db.session.query(
            db.func.coalesce(db.func.sum(Task.actual_labor_fee), 0)
        ).filter(
            Task.driver_id == driver.id,
            Task.status == 'completed'
        ).scalar()
        # Also include scheduled tasks labor fee
        scheduled_fee = db.session.query(
            db.func.coalesce(db.func.sum(Task.labor_fee), 0)
        ).filter(
            Task.driver_id == driver.id,
            Task.status == 'scheduled'
        ).scalar()
        driver_fees[driver.id] = float(total_fee) + float(scheduled_fee)

    # Sort drivers by total labor fee ascending (lower fee first)
    sorted_drivers = sorted(available_drivers, key=lambda d: driver_fees.get(d.id, 0))

    return jsonify({
        'code': 200,
        'data': {
            'vehicles': [v.to_dict() for v in available_vehicles],
            'drivers': [{
                **d.to_dict(),
                'total_labor_fee': driver_fees.get(d.id, 0)
            } for d in sorted_drivers],
            'task_start': task_start.strftime('%Y-%m-%d %H:%M'),
            'task_end': task_end.strftime('%Y-%m-%d %H:%M')
        }
    })


@app.route('/api/tasks/<int:task_id>/schedule', methods=['POST'])
@login_required
def schedule_task(task_id):
    """Assign vehicle and driver to a task."""
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'code': 404, 'msg': '任务不存在'})
    data = request.get_json()
    vehicle_id = data.get('vehicle_id')
    driver_id = data.get('driver_id')

    if not vehicle_id or not driver_id:
        return jsonify({'code': 400, 'msg': '请选择车辆和司机'})

    # Verify availability
    task_start = task.departure_time
    task_end = task_start + timedelta(days=task.rental_days)

    conflict_tasks = Task.query.filter(
        Task.id != task_id,
        Task.status.in_(['scheduled']),
        (Task.vehicle_id == vehicle_id) | (Task.driver_id == driver_id)
    ).all()

    conflict = None
    for ct in conflict_tasks:
        ct_start = ct.departure_time
        ct_end = ct_start + timedelta(days=ct.rental_days)
        if task_start < ct_end and task_end > ct_start:
            conflict = ct
            break

    if conflict:
        return jsonify({'code': 400, 'msg': '该车辆或司机在此时间段已被安排'})

    task.vehicle_id = vehicle_id
    task.driver_id = driver_id
    task.status = 'scheduled'

    # Recalculate estimated cost and profit
    task.estimated_cost = task.fuel_fee + task.bridge_fee + task.labor_fee
    task.estimated_profit = task.rental_fee - task.estimated_cost

    db.session.commit()
    return jsonify({'code': 200, 'msg': '排班成功', 'data': task.to_dict()})


# ==================== Complete Task ====================

@app.route('/api/tasks/<int:task_id>/complete', methods=['POST'])
@login_required
def complete_task(task_id):
    """Mark a task as completed with actual fees."""
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'code': 404, 'msg': '任务不存在'})
    data = request.get_json()

    task.actual_fuel_fee = data.get('actual_fuel_fee', 0)
    task.actual_bridge_fee = data.get('actual_bridge_fee', 0)
    task.actual_labor_fee = data.get('actual_labor_fee', 0)
    task.other_fee = data.get('other_fee', 0)
    task.actual_cost = task.actual_fuel_fee + task.actual_bridge_fee + task.actual_labor_fee + task.other_fee
    task.final_profit = task.rental_fee - task.actual_cost
    task.status = 'completed'

    db.session.commit()
    return jsonify({'code': 200, 'msg': '任务已完成', 'data': task.to_dict()})


# ==================== Yunzhijia Approval ====================

_yzj_token_cache = {'token': None, 'expire': 0}


def get_yunzhijia_token(force_refresh=False):
    """获取云之家 access_token，带缓存（提前5分钟刷新）"""
    now = time.time()
    if not force_refresh and _yzj_token_cache['token'] and now < _yzj_token_cache['expire']:
        return _yzj_token_cache['token']

    ts = str(int(now * 1000))
    url = (
        f"{app.config['YUNZHIJIA_TOKEN_URL']}"
        f"?appId={app.config['YUNZHIJIA_APP_ID']}"
        f"&eid={app.config['YUNZHIJIA_EID']}"
        f"&secret={app.config['YUNZHIJIA_SECRET']}"
        f"&timestamp={ts}"
        f"&scope=team"
    )
    req = urllib.request.Request(url, method='GET',
                                headers={'User-Agent': 'charter-bus/1.0'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode('utf-8'))

    if not result.get('success'):
        raise RuntimeError(f"获取云之家token失败: {result.get('error')}")

    token = result['data']['accessToken']
    expire_in = result['data'].get('expireIn', 7200)
    _yzj_token_cache['token'] = token
    _yzj_token_cache['expire'] = now + expire_in - 300
    return token


def build_yzj_approval_body(task, row_id=1):
    """将一条包车任务转换为云之家审批明细行"""
    if task.client_type == 'company':
        client_display = (task.client.name if task.client else task.client_name) or ''
    else:
        client_display = task.client_name or ''
    contact_display = f"{task.client_name} {task.client_phone}".strip() if task.client_name else ''

    return {
        '_id_': str(row_id),
        'Te_0': client_display,       # 用车方
        'Te_1': contact_display,      # 联系人
        'Te_2': task.departure or '',          # 出发地点
        'Te_3': task.destination or '',        # 目的地
        'Te_4': task.vehicle.plate_number if task.vehicle else '',  # 车牌号
        'Te_5': task.driver.name if task.driver else '',            # 驾驶司机
        'Te_6': task.departure_time.strftime('%Y-%m-%d %H:%M') if task.departure_time else '',  # 出车时间
        'Te_7': task.return_time.strftime('%Y-%m-%d %H:%M') if task.return_time else '',        # 回程时间
        'Te_8': task.vehicle_type or '',        # 车辆类型
        'Te_9': str(task.mileage) if task.mileage else '',  # 里程
        'Te_10': str(task.rental_fee) if task.rental_fee else '',  # 租车费
        'Te_11': str(task.fuel_fee) if task.fuel_fee else '',     # 油电费
        'Te_12': str(task.bridge_fee) if task.bridge_fee else '', # 桥路费
        'Te_13': str(task.labor_fee) if task.labor_fee else '',   # 司机人工费
        'Te_14': str(task.estimated_cost) if task.estimated_cost else '',   # 预计成本
        'Te_15': str(task.estimated_profit) if task.estimated_profit else '', # 预估利润
        'Te_16': str(task.rental_days) if task.rental_days else '',  # 天数
    }


# 根据车辆所属公司选择审批模板（带"测试"后缀的版本）
_APPROVAL_TEMPLATE_MAP = {
    '国顺司': '0e1d321692a9441fa24db3bb3776a7d9',
    '国开司': '3d50bcac14d947a5a006d64187b8fa5b',
    '外单位': '134dc1d64c964b68870e5a2665baac0d',
}


def get_approval_serial(token, form_inst_id, form_code_id):
    """通过 viewFormInst 获取审批流水号（_S_SERIAL）"""
    try:
        url = (
            f"{app.config['YUNZHIJIA_HOST']}"
            f"/gateway/workflow/form/thirdpart/viewFormInst"
            f"?accessToken={token}"
        )
        body = json.dumps({
            'formInstId': form_inst_id,
            'formCodeId': form_code_id,
        }, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(url, data=body, method='POST',
                                    headers={'Content-Type': 'application/json; charset=utf-8'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
        if result.get('errorCode') == 0:
            widgets = (result.get('data') or {}).get('formInfo', {}).get('widgetMap', {})
            return widgets.get('_S_SERIAL', {}).get('value', '')
    except Exception:
        pass
    return ''


@app.route('/api/tasks/submit-approval', methods=['POST'])
@login_required
def submit_approval():
    """批量发起云之家审批，task_ids 为任务ID列表，按车辆所属公司自动选模板"""
    data = request.get_json()
    task_ids = data.get('task_ids', [])
    if not task_ids:
        return jsonify({'code': 400, 'msg': '请选择至少一个任务'})

    # 查询任务（只允许已排班）
    tasks = Task.query.filter(Task.id.in_(task_ids)).all()
    if not tasks:
        return jsonify({'code': 404, 'msg': '未找到任务'})

    eligible = [t for t in tasks if t.status == 'scheduled']
    if not eligible:
        return jsonify({'code': 400, 'msg': '所选任务中没有已排班的任务'})

    # 过滤掉已过出车时间的任务
    now = datetime.now()
    past_tasks = [t for t in eligible if t.departure_time and t.departure_time <= now]
    if past_tasks:
        names = [f"ID{t.id}({t.departure}→{t.destination})" for t in past_tasks]
        return jsonify({'code': 400, 'msg': f'以下任务已过出车时间，禁止发起审批：{", ".join(names)}'})

    # 过滤掉已发起或已通过审批的任务（已拒绝/已撤销可重新发起）
    blocked_status = {'submitted', 'approved'}
    already = [t for t in eligible if getattr(t, 'yzj_approval_status', '') in blocked_status]
    if already:
        eligible = [t for t in eligible if t not in already]

    if not eligible:
        return jsonify({'code': 400, 'msg': '所选任务均已发起过审批或已通过，无法重复提交'})

    # 按车辆所属公司分组
    grouped = {}
    for t in eligible:
        company = (t.vehicle.company if t.vehicle else '') or '外单位'
        grouped.setdefault(company, []).append(t)

    # 逐组发起审批
    results = []
    for company, group_tasks in grouped.items():
        template_id = _APPROVAL_TEMPLATE_MAP.get(company, _APPROVAL_TEMPLATE_MAP['外单位'])

        first = group_tasks[0]
        if len(group_tasks) == 1:
            title = f"包车审批 - {first.departure}→{first.destination} {first.departure_time.strftime('%Y-%m-%d')}"
        else:
            title = f"包车审批 - {first.departure}→{first.destination} 等{len(group_tasks)}条"

        detail_rows = [build_yzj_approval_body(t, idx) for idx, t in enumerate(group_tasks, start=1)]

        try:
            token = get_yunzhijia_token()
        except Exception as e:
            return jsonify({'code': 500, 'msg': f'获取云之家token失败: {str(e)}'})

        payload = {
            'formCodeId': template_id,
            'creator': app.config['YUNZHIJIA_CREATOR_OPENID'],
            'skipWidgetAuthorityCheck': True,
            'useAlias': False,
            'requestId': str(uuid.uuid4()),
            'widgetValue': {'_S_TITLE': title},
            'details': {'Dd_0': {'widgetValue': detail_rows}},
        }

        def do_create_inst(accessToken):
            url = (
                f"{app.config['YUNZHIJIA_HOST']}"
                f"/gateway/workflow/form/thirdpart/createInst"
                f"?accessToken={accessToken}"
            )
            body_bytes = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(
                url, data=body_bytes, method='POST',
                headers={'Content-Type': 'application/json; charset=utf-8', 'User-Agent': 'charter-bus/1.0'},
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode('utf-8'))

        try:
            result = do_create_inst(token)
        except Exception:
            return jsonify({'code': 500, 'msg': '调用云之家接口失败，请稍后重试'})

        if result.get('errorCode') in (10000401, 1101030):
            try:
                token = get_yunzhijia_token(force_refresh=True)
                result = do_create_inst(token)
            except Exception:
                return jsonify({'code': 500, 'msg': '云之家认证失败，请稍后重试'})

        if result.get('errorCode') == 0:
            inst_data = result.get('data', {})
            form_inst_id = inst_data.get('formInstId', '')
            flow_inst_id = inst_data.get('flowInstId', '')

            # 获取流水号
            serial = get_approval_serial(token, form_inst_id, template_id)

            # 标记这批任务已发起审批，记录审批实例信息
            for t in group_tasks:
                t.yzj_approval_status = 'submitted'
                t.yzj_flow_inst_id = flow_inst_id
                t.yzj_form_inst_id = form_inst_id
                t.yzj_serial = serial
            db.session.commit()

            results.append({
                'company': company,
                'template': template_id,
                'count': len(group_tasks),
                'serial': serial,
                'flowInstId': flow_inst_id,
                'formInstId': form_inst_id,
                'data': inst_data,
            })
        else:
            error_msg = result.get('error') or result.get('msg') or '未知错误'
            return jsonify({'code': 500, 'msg': f'{company}审批失败: {error_msg}'})

    total = sum(r['count'] for r in results)
    return jsonify({
        'code': 200,
        'msg': f'审批已发起，共{total}条明细（{len(results)}个模板）',
        'data': results,
    })


@app.route('/api/yunzhijia/callback', methods=['GET', 'POST'])
def yunzhijia_callback():
    """
    云之家审批回调接口。

    审批状态变更时，云之家会 POST 此接口通知。
    需在云之家开发者后台配置回调地址：
        https://你的域名/api/yunzhijia/callback

    云之家回调数据是加密的，需要配置 Token 和 EncodingAESKey 进行解密。
    """
    # GET 请求 - 可能是云之家的验证请求
    if request.method == 'GET':
        app.logger.info(f"云之家回调(GET): args={dict(request.args)}")
        # 返回成功，云之家可能需要验证接口可用性
        return jsonify({'code': 200, 'msg': 'ok'})

    # POST 请求 - 审批状态变更通知
    raw_data = request.get_data(as_text=True)

    # 尝试解密数据
    data = {}
    aes_key = app.config.get('YUNZHIJIA_CALLBACK_AES_KEY', '')

    if aes_key and raw_data:
        try:
            # 尝试解析JSON获取加密数据
            json_data = json.loads(raw_data)
            encrypted_content = json_data.get('content', '') or json_data.get('data', '')
            if encrypted_content:
                data = decrypt_yzj_callback(encrypted_content, aes_key) or {}
        except json.JSONDecodeError:
            # 如果不是JSON，可能是直接的加密字符串
            data = decrypt_yzj_callback(raw_data, aes_key) or {}
        except Exception as e:
            app.logger.error(f"云之 decryption failed: {e}")

    # 如果解密失败，尝试直接解析
    if not data:
        try:
            data = json.loads(raw_data) if raw_data else {}
        except:
            data = {}
    if not data:
        data = dict(request.args)

    # 提取字段
    flow_inst_id = data.get('flowInstId', '') or data.get('flow_inst_id', '')
    form_inst_id = data.get('formInstId', '') or data.get('form_inst_id', '')
    action_type = data.get('actionType', '') or data.get('action_type', '') or data.get('action', '')

    # 如果顶层没有，尝试从data子对象获取
    if isinstance(data.get('data'), dict):
        inner = data['data']
        flow_inst_id = flow_inst_id or inner.get('flowInstId', '') or inner.get('flow_inst_id', '')
        form_inst_id = form_inst_id or inner.get('formInstId', '') or inner.get('form_inst_id', '')
        action_type = action_type or inner.get('actionType', '') or inner.get('action_type', '') or inner.get('action', '')

    # 从表单数据中提取流水号（云之家大众回调只发送表单数据，需要通过流水号匹配任务）
    serial_number = ''
    if isinstance(data.get('data'), dict):
        form_info = data['data'].get('formInfo', {})
        widget_map = form_info.get('widgetMap', {})
        serial_widget = widget_map.get('_S_SERIAL', {})
        serial_number = serial_widget.get('value', '')

    app.logger.info(f"云之家回调: serial={serial_number}, flowInstId={flow_inst_id}")

    # 查找关联任务
    tasks = []
    if flow_inst_id or form_inst_id:
        tasks = Task.query.filter(
            (Task.yzj_flow_inst_id == flow_inst_id) | (Task.yzj_form_inst_id == form_inst_id)
        ).all()
    elif serial_number:
        tasks = Task.query.filter(Task.yzj_serial == serial_number).all()

    if not tasks:
        app.logger.warning(f"云之家回调未找到关联任务: serial={serial_number}")
        return jsonify({'code': 200, 'msg': '无关联任务'})

    # 查询审批状态（通过云之家API）
    flow_inst_id_to_query = tasks[0].yzj_flow_inst_id
    if flow_inst_id_to_query:
        try:
            token = get_yunzhijia_token()
            query_url = (
                f"{app.config['YUNZHIJIA_HOST']}"
                f"/gateway/workflow/form/thirdpart/getFlowStatus"
                f"?accessToken={token}"
            )
            query_body = json.dumps({'flowInstId': flow_inst_id_to_query}, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(
                query_url, data=query_body, method='POST',
                headers={'Content-Type': 'application/json; charset=utf-8', 'User-Agent': 'charter-bus/1.0'},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                result = json.loads(resp.read().decode('utf-8'))

                # 解析审批状态
                if result.get('errorCode') == 0:
                    flow_data = result.get('data', {})
                    # data可能是字符串(如"FINISH")或对象
                    if isinstance(flow_data, str):
                        flow_status = flow_data
                    else:
                        flow_status = flow_data.get('flowStatus', '') if isinstance(flow_data, dict) else ''

                    # 更新任务状态
                    status_map = {
                        'FINISH': 'approved',
                        'agree': 'approved',
                        'completed': 'approved',
                        'reject': 'rejected',
                        'revoke': '',
                    }
                    new_status = status_map.get(flow_status, '')
                    for t in tasks:
                        t.yzj_approval_status = new_status
                    db.session.commit()
                    app.logger.info(f"已更新 {len(tasks)} 条任务审批状态: {serial_number} -> {new_status or flow_status}")
                else:
                    app.logger.warning(f"查询审批状态失败: {result.get('error', 'unknown')}")
        except Exception as e:
            app.logger.error(f"查询审批状态异常: {e}")

    return jsonify({'code': 200, 'msg': 'ok'})


# ==================== Reports ====================

@app.route('/api/reports/by-client', methods=['GET'])
@login_required
def report_by_client():
    client = request.args.get('client', '')
    client_type = request.args.get('client_type', '')
    month = request.args.get('month', '')
    year = request.args.get('year', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = Task.query
    if client_type:
        query = query.filter(Task.client_type == client_type)
    if client:
        query = query.filter(Task.client_name.like(f'%{client}%'))
    if month:
        query = query.filter(db.func.date_format(Task.departure_time, '%Y-%m') == month)
    if year:
        query = query.filter(db.func.date_format(Task.departure_time, '%Y') == year)
    if start_date:
        query = query.filter(Task.departure_time >= start_date)
    if end_date:
        query = query.filter(Task.departure_time <= end_date + ' 23:59:59')

    tasks = query.order_by(Task.departure_time.desc()).all()
    task_list = [t.to_dict() for t in tasks]

    total_rental = sum(t.rental_fee for t in tasks)
    total_actual_cost = sum(t.actual_cost for t in tasks)
    total_final_profit = sum(t.final_profit for t in tasks)

    return jsonify({
        'code': 200,
        'data': {
            'tasks': task_list,
            'summary': {
                'total_tasks': len(tasks),
                'total_rental_fee': total_rental,
                'total_actual_cost': total_actual_cost,
                'total_final_profit': total_final_profit
            }
        }
    })


@app.route('/api/reports/by-driver', methods=['GET'])
@login_required
def report_by_driver():
    driver_id = request.args.get('driver_id', type=int)
    client_type = request.args.get('client_type', '')
    month = request.args.get('month', '')
    year = request.args.get('year', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = Task.query.filter(Task.driver_id.isnot(None))
    if client_type:
        query = query.filter(Task.client_type == client_type)
    if driver_id:
        query = query.filter(Task.driver_id == driver_id)
    if month:
        query = query.filter(db.func.date_format(Task.departure_time, '%Y-%m') == month)
    if year:
        query = query.filter(db.func.date_format(Task.departure_time, '%Y') == year)
    if start_date:
        query = query.filter(Task.departure_time >= start_date)
    if end_date:
        query = query.filter(Task.departure_time <= end_date + ' 23:59:59')

    tasks = query.order_by(Task.departure_time.desc()).all()

    # Group by driver
    driver_stats = {}
    for t in tasks:
        did = t.driver_id
        if did not in driver_stats:
            driver_stats[did] = {
                'driver_name': t.driver.name if t.driver else '未知',
                'driver_phone': t.driver.phone if t.driver else '',
                'task_count': 0,
                'total_labor_fee': 0,
                'total_actual_labor_fee': 0,
                'tasks': []
            }
        driver_stats[did]['task_count'] += 1
        driver_stats[did]['total_labor_fee'] += t.labor_fee
        driver_stats[did]['total_actual_labor_fee'] += t.actual_labor_fee
        driver_stats[did]['tasks'].append(t.to_dict())

    return jsonify({
        'code': 200,
        'data': list(driver_stats.values())
    })


@app.route('/api/reports/by-vehicle', methods=['GET'])
@login_required
def report_by_vehicle():
    vehicle_id = request.args.get('vehicle_id', type=int)
    client_type = request.args.get('client_type', '')
    month = request.args.get('month', '')
    year = request.args.get('year', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = Task.query.filter(Task.vehicle_id.isnot(None))
    if client_type:
        query = query.filter(Task.client_type == client_type)
    if vehicle_id:
        query = query.filter(Task.vehicle_id == vehicle_id)
    if month:
        query = query.filter(db.func.date_format(Task.departure_time, '%Y-%m') == month)
    if year:
        query = query.filter(db.func.date_format(Task.departure_time, '%Y') == year)
    if start_date:
        query = query.filter(Task.departure_time >= start_date)
    if end_date:
        query = query.filter(Task.departure_time <= end_date + ' 23:59:59')

    tasks = query.order_by(Task.departure_time.desc()).all()

    vehicle_stats = {}
    for t in tasks:
        vid = t.vehicle_id
        if vid not in vehicle_stats:
            vehicle_stats[vid] = {
                'plate_number': t.vehicle.plate_number if t.vehicle else '未知',
                'vehicle_type': t.vehicle.vehicle_type if t.vehicle else '',
                'task_count': 0,
                'total_rental_fee': 0,
                'total_actual_cost': 0,
                'total_final_profit': 0,
                'tasks': []
            }
        vehicle_stats[vid]['task_count'] += 1
        vehicle_stats[vid]['total_rental_fee'] += t.rental_fee
        vehicle_stats[vid]['total_actual_cost'] += t.actual_cost
        vehicle_stats[vid]['total_final_profit'] += t.final_profit
        vehicle_stats[vid]['tasks'].append(t.to_dict())

    return jsonify({
        'code': 200,
        'data': list(vehicle_stats.values())
    })


# ==================== 企业微信外部联系人 ====================

@app.route('/api/wx-external-contacts', methods=['GET'])
@login_required
def get_wx_external_contacts():
    """获取企业微信外部联系人列表"""
    sender = request.args.get('sender', '') or app.config.get('WX_WORK_SENDER', '')
    if not sender:
        return jsonify({'code': 400, 'msg': '请指定发送人（sender）账号'})

    wx_client = get_wx_work_client()
    result = wx_client.get_external_contacts(sender)

    if not result.get('success'):
        return jsonify({'code': 500, 'msg': result.get('errmsg', '获取失败')})

    # 获取每个外部联系人的详情
    contacts = []
    for ext_id in result.get('external_userid', []):
        detail = wx_client.get_external_contact_detail(ext_id)
        if detail.get('success'):
            contacts.append({
                'external_userid': detail.get('external_userid', ''),
                'name': detail.get('name', ''),
                'corp_name': detail.get('corp_name', ''),
            })
        else:
            contacts.append({
                'external_userid': ext_id,
                'name': ext_id,
                'corp_name': '',
            })

    return jsonify({'code': 200, 'data': contacts})


# ==================== 排班确认 ====================

def get_wx_work_client():
    """获取企业微信客户端"""
    return WxWorkClient(
        corp_id=app.config.get('WX_WORK_CORP_ID', ''),
        agent_id=app.config.get('WX_WORK_AGENT_ID', ''),
        secret=app.config.get('WX_WORK_SECRET', '')
    )


@app.route('/api/task/<int:task_id>/push-confirm', methods=['POST'])
@login_required
def push_schedule_confirm(task_id):
    """推送排班确认消息给客户"""
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'code': 404, 'msg': '任务不存在'})

    # 检查任务状态
    if task.status not in ('scheduled', 'pending'):
        return jsonify({'code': 400, 'msg': '任务状态不允许推送确认'})

    # 检查是否已有待确认的记录
    existing = ScheduleConfirmation.query.filter_by(
        task_id=task_id,
        confirm_status='pending'
    ).first()
    if existing:
        return jsonify({'code': 400, 'msg': '该任务已有待确认的记录'})

    data = request.get_json() or {}
    wx_userid = data.get('wx_userid', '')
    custom_message = data.get('custom_message', '')

    # 获取联系人名称（优先使用联系人姓名，其次客户名称）
    contact_name = task.client_name
    contact_phone = task.client_phone
    if task.contact_id:
        contact = ClientContact.query.get(task.contact_id)
        if contact:
            contact_name = contact.name
            contact_phone = contact.phone or task.client_phone

    # 生成确认Token
    confirm_token = str(uuid.uuid4()).replace('-', '')

    # 创建确认记录
    confirmation = ScheduleConfirmation(
        task_id=task_id,
        customer_id=task.client_id,
        customer_name=contact_name,
        customer_phone=contact_phone,
        contact_id=task.contact_id,
        wx_userid=wx_userid,
        wx_sender=data.get('sender', ''),
        confirm_token=confirm_token,
        confirm_status='pending',
        push_time=datetime.now(),
        push_status='pending',
        created_by=session.get('user_id')
    )
    db.session.add(confirmation)
    db.session.flush()  # 获取ID

    # 保存任务快照
    task_snapshot = {
        'task_no': task.task_no or f'TASK-{task.id}' or '',
        'client_name': contact_name,
        'client_phone': contact_phone,
        'departure': task.departure,
        'destination': task.destination,
        'departure_time': task.departure_time.strftime('%Y-%m-%d %H:%M') if task.departure_time else '',
        'return_time': task.return_time.strftime('%Y-%m-%d %H:%M') if task.return_time else '',
        'vehicle_type': task.vehicle_type or '',
        'vehicle_plate': task.vehicle.plate_number if task.vehicle else '',
        'driver_name': task.driver.name if task.driver else '',
        'driver_phone': task.driver.phone if task.driver else '',
        'rental_fee': task.rental_fee,
        'rental_days': task.rental_days,
    }
    snapshot = ConfirmationSnapshot(
        confirmation_id=confirmation.id,
        snapshot_type='task',
        snapshot_data=json.dumps(task_snapshot, ensure_ascii=False)
    )
    db.session.add(snapshot)

    # 更新任务状态
    task.schedule_confirm_status = 'pending'

    # 尝试发送企业微信消息
    confirm_page_url = f"{app.config.get('CONFIRM_BASE_URL', '')}/confirm/{confirm_token}"

    # 判断是外部联系人还是内部员工
    is_external = wx_userid.startswith('wm') if wx_userid else False

    if is_external:
        # 外部联系人：直接用确认页面链接，无需OAuth
        confirm_url = confirm_page_url
    else:
        # 内部员工：使用OAuth2授权链接
        oauth_redirect_uri = f"{app.config.get('CONFIRM_BASE_URL', '')}/api/wx-oauth/callback"
        from utils.wx_work import get_oauth_url
        confirm_url = get_oauth_url(
            corp_id=app.config.get('WX_WORK_CORP_ID', ''),
            agent_id=app.config.get('WX_WORK_AGENT_ID', ''),
            redirect_uri=oauth_redirect_uri,
            state=confirm_token
        )

    if wx_userid:
        try:
            wx_client = get_wx_work_client()

            if is_external:
                # 外部联系人：企业微信不支持直接发消息，需手动发送链接
                confirmation.push_status = 'pending'
                confirmation.push_error = '外部联系人需手动发送确认链接'
            else:
                # 内部员工：使用文本卡片消息
                msg_info = format_confirm_message(task_snapshot, confirm_url)
                result = wx_client.send_textcard_message(
                    userid=wx_userid,
                    title=msg_info['title'],
                    description=msg_info['description'],
                    url=msg_info['url'],
                    btntxt=msg_info['btntxt']
                )
                if result.get('success'):
                    confirmation.push_status = 'success'
                    confirmation.msg_id = result.get('msgid', '')
                else:
                    confirmation.push_status = 'failed'
                    confirmation.push_error = result.get('errmsg', '发送失败')
        except Exception as e:
            confirmation.push_status = 'failed'
            confirmation.push_error = str(e)
    else:
        # 未配置企业微信用户ID，标记为待手动发送
        confirmation.push_status = 'pending'
        confirmation.push_error = '未配置企业微信用户ID，请手动发送确认链接'

    db.session.commit()

    return jsonify({
        'code': 200,
        'msg': '推送成功' if confirmation.push_status == 'success' else '已创建确认记录，请手动发送链接',
        'data': {
            'confirmation_id': confirmation.id,
            'confirm_url': confirm_url,
            'push_status': confirmation.push_status,
            'push_error': confirmation.push_error
        }
    })


@app.route('/api/confirmations/<int:confirmation_id>/repush', methods=['POST'])
@login_required
def repush_confirmation(confirmation_id):
    """重新推送确认消息"""
    confirmation = ScheduleConfirmation.query.get(confirmation_id)
    if not confirmation:
        return jsonify({'code': 404, 'msg': '确认记录不存在'})

    if confirmation.confirm_status != 'pending':
        return jsonify({'code': 400, 'msg': '该确认已完成，无法重新推送'})

    data = request.get_json() or {}
    wx_userid = data.get('wx_userid', '') or confirmation.wx_userid

    if not wx_userid:
        return jsonify({'code': 400, 'msg': '未配置企业微信用户ID，无法推送'})

    # 自动获取 sender：请求参数 > 确认记录 > 联系人
    sender = data.get('sender', '') or confirmation.wx_sender or ''
    if not sender and confirmation.contact_id:
        contact = ClientContact.query.get(confirmation.contact_id)
        if contact:
            sender = contact.wx_sender
    if not sender and confirmation.customer_id:
        contact = ClientContact.query.filter_by(client_id=confirmation.customer_id, wx_userid=wx_userid).first()
        if contact:
            sender = contact.wx_sender
    if not sender:
        sender = app.config.get('WX_WORK_SENDER', '')

    # 获取任务快照
    snapshot = ConfirmationSnapshot.query.filter_by(
        confirmation_id=confirmation.id,
        snapshot_type='task'
    ).first()
    task_snapshot = {}
    if snapshot:
        try:
            task_snapshot = json.loads(snapshot.snapshot_data)
        except:
            pass

    confirm_page_url = f"{app.config.get('CONFIRM_BASE_URL', '')}/confirm/{confirmation.confirm_token}"
    is_external = wx_userid.startswith('wm') if wx_userid else False

    if is_external:
        confirm_url = confirm_page_url
    else:
        oauth_redirect_uri = f"{app.config.get('CONFIRM_BASE_URL', '')}/api/wx-oauth/callback"
        from utils.wx_work import get_oauth_url
        confirm_url = get_oauth_url(
            corp_id=app.config.get('WX_WORK_CORP_ID', ''),
            agent_id=app.config.get('WX_WORK_AGENT_ID', ''),
            redirect_uri=oauth_redirect_uri,
            state=confirmation.confirm_token
        )

    # 更新wx_userid
    confirmation.wx_userid = wx_userid
    confirmation.push_time = datetime.now()

    try:
        wx_client = get_wx_work_client()

        if is_external:
            # 外部联系人：企业微信不支持直接发消息，需手动发送链接
            confirmation.push_status = 'pending'
            confirmation.push_error = '外部联系人需手动发送确认链接'
        else:
            msg_info = format_confirm_message(task_snapshot, confirm_url)
            result = wx_client.send_textcard_message(
                userid=wx_userid,
                title=msg_info['title'],
                description=msg_info['description'],
                url=msg_info['url'],
                btntxt=msg_info['btntxt']
            )
            if result.get('success'):
                confirmation.push_status = 'success'
                confirmation.msg_id = result.get('msgid', '')
                confirmation.push_error = ''
            else:
                confirmation.push_status = 'failed'
                confirmation.push_error = result.get('errmsg', '发送失败')
    except Exception as e:
        confirmation.push_status = 'failed'
        confirmation.push_error = str(e)

    db.session.commit()

    msg = '推送成功'
    if confirmation.push_status == 'pending' and is_external:
        msg = '确认链接已生成，请复制发送给客户'
    elif confirmation.push_status == 'failed':
        msg = '推送失败: ' + confirmation.push_error

    return jsonify({
        'code': 200,
        'msg': msg,
        'data': {
            'push_status': confirmation.push_status,
            'push_error': confirmation.push_error,
            'confirm_url': confirm_url if is_external else ''
        }
    })


@app.route('/api/confirm/<token>', methods=['GET'])
def get_confirm_page(token):
    """获取确认页面数据（无需登录）"""
    confirmation = ScheduleConfirmation.query.filter_by(confirm_token=token).first()

    if not confirmation:
        return jsonify({'code': 404, 'msg': '确认链接无效'})

    # 获取任务快照
    snapshot = ConfirmationSnapshot.query.filter_by(
        confirmation_id=confirmation.id,
        snapshot_type='task'
    ).first()

    task_info = {}
    if snapshot:
        try:
            task_info = json.loads(snapshot.snapshot_data)
        except:
            pass

    return jsonify({
        'code': 200,
        'data': {
            'task_info': task_info,
            'confirm_status': confirmation.confirm_status,
            'push_time': confirmation.push_time.strftime('%Y-%m-%d %H:%M:%S') if confirmation.push_time else None,
            'confirm_time': confirmation.confirm_time.strftime('%Y-%m-%d %H:%M:%S') if confirmation.confirm_time else None,
            'created_by_name': confirmation.creator.username if confirmation.creator else None,
            'customer_name': confirmation.customer_name,
        }
    })


@app.route('/api/confirm/<token>', methods=['POST'])
def submit_confirm(token):
    """提交确认结果（无需登录）"""
    confirmation = ScheduleConfirmation.query.filter_by(confirm_token=token).first()

    if not confirmation:
        return jsonify({'code': 404, 'msg': '确认链接无效'})

    if confirmation.confirm_status != 'pending':
        return jsonify({'code': 400, 'msg': '该确认已完成，请勿重复操作'})

    data = request.get_json() or {}
    action = data.get('action', 'confirm')
    remark = data.get('remark', '')
    phone = data.get('phone', '')

    # 更新确认记录
    confirmation.confirm_time = datetime.now()
    confirmation.confirm_ip = request.remote_addr or ''
    confirmation.confirm_device = request.headers.get('User-Agent', '')[:500]
    confirmation.confirm_remark = remark
    if phone:
        confirmation.customer_phone = phone

    if action == 'reject':
        confirmation.confirm_status = 'rejected'
        # 更新任务状态
        task = Task.query.get(confirmation.task_id)
        if task:
            task.schedule_confirm_status = 'rejected'
    else:
        confirmation.confirm_status = 'confirmed'
        # 更新任务状态
        task = Task.query.get(confirmation.task_id)
        if task:
            task.schedule_confirm_status = 'confirmed'

    db.session.commit()

    return jsonify({
        'code': 200,
        'msg': '确认成功' if action == 'confirm' else '已提交异议',
        'data': {
            'confirm_time': confirmation.confirm_time.strftime('%Y-%m-%d %H:%M:%S'),
            'confirm_status': confirmation.confirm_status
        }
    })


@app.route('/api/wx-oauth/callback', methods=['GET'])
def wx_oauth_callback():
    """企业微信OAuth2回调，获取用户信息"""
    code = request.args.get('code', '')
    state = request.args.get('state', '')  # 这里传递的是confirm_token

    if not code or not state:
        return jsonify({'code': 400, 'msg': '参数错误'})

    # 通过code获取用户信息
    wx_client = get_wx_work_client()
    user_result = get_userinfo_by_code(wx_client, code)

    if not user_result.get('success'):
        return jsonify({'code': 400, 'msg': user_result.get('errmsg', '获取用户信息失败')})

    userid = user_result.get('userid', '')
    openid = user_result.get('openid', '')

    # 获取用户详细信息（包括手机号）
    user_detail = get_user_detail(wx_client, userid)
    mobile = user_detail.get('mobile', '') if user_detail.get('success') else ''
    user_name = user_detail.get('name', '') if user_detail.get('success') else ''

    # 更新确认记录
    confirmation = ScheduleConfirmation.query.filter_by(confirm_token=state).first()
    if confirmation:
        confirmation.wx_userid = userid
        confirmation.wx_openid = openid
        if mobile:
            confirmation.customer_phone = mobile
        if user_name and not confirmation.customer_name:
            confirmation.customer_name = user_name
        db.session.commit()

    # 重定向到确认页面，带上用户信息
    confirm_url = f"{app.config.get('CONFIRM_BASE_URL', '')}/confirm/{state}"
    if mobile:
        confirm_url += f"?phone={mobile}&name={user_name}"

    return redirect(confirm_url)


@app.route('/api/wx-config', methods=['GET'])
def get_wx_config():
    """获取企业微信JS-SDK配置"""
    url = request.args.get('url', '')

    if not url:
        return jsonify({'code': 400, 'msg': '缺少url参数'})

    # 生成签名
    wx_client = get_wx_work_client()
    token = wx_client.get_access_token()

    # 获取jsapi_ticket
    ticket_url = f'https://qyapi.weixin.qq.com/cgi-bin/ticket/get?access_token={token}&type=jsapi'
    try:
        req = urllib.request.Request(ticket_url)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('errcode') != 0:
                return jsonify({'code': 400, 'msg': '获取ticket失败'})
            jsapi_ticket = data.get('ticket', '')
    except Exception as e:
        return jsonify({'code': 400, 'msg': str(e)})

    # 生成签名
    noncestr = str(uuid.uuid4()).replace('-', '')[:16]
    timestamp = str(int(time.time()))
    sign_str = f'jsapi={jsapi_ticket}&noncestr={noncestr}&timestamp={timestamp}&url={url}'
    signature = hashlib.sha1(sign_str.encode('utf-8')).hexdigest()

    return jsonify({
        'code': 200,
        'data': {
            'appId': app.config.get('WX_WORK_CORP_ID', ''),
            'timestamp': timestamp,
            'nonceStr': noncestr,
            'signature': signature,
            'agentId': app.config.get('WX_WORK_AGENT_ID', '')
        }
    })


@app.route('/api/task/<int:task_id>/confirmation', methods=['GET'])
@login_required
def get_task_confirmation(task_id):
    """获取任务的确认记录"""
    confirmation = ScheduleConfirmation.query.filter_by(task_id=task_id).order_by(
        ScheduleConfirmation.created_at.desc()
    ).first()

    if not confirmation:
        return jsonify({'code': 200, 'data': None})

    return jsonify({
        'code': 200,
        'data': confirmation.to_dict()
    })


@app.route('/api/confirmations', methods=['GET'])
@login_required
def list_confirmations():
    """获取确认记录列表"""
    status = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = ScheduleConfirmation.query

    if status:
        query = query.filter_by(confirm_status=status)

    # 按创建时间倒序
    query = query.order_by(ScheduleConfirmation.created_at.desc())

    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'code': 200,
        'data': {
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'items': [c.to_dict() for c in pagination.items]
        }
    })


# ==================== Init DB ====================

@app.route('/api/init-db', methods=['POST'])
def init_db():
    """Initialize database tables and create admin user."""
    db.create_all()

    # 给 vehicles 表增加 company 字段（兼容旧库）
    try:
        db.session.execute(db.text("ALTER TABLE vehicles ADD COLUMN company VARCHAR(50) DEFAULT ''"))
        db.session.commit()
    except Exception:
        db.session.rollback()  # 字段已存在则忽略

    # 给 tasks 表增加 yzj_approval_status 字段（兼容旧库）
    try:
        db.session.execute(db.text("ALTER TABLE tasks ADD COLUMN yzj_approval_status VARCHAR(20) DEFAULT ''"))
        db.session.commit()
    except Exception:
        db.session.rollback()

    # 给 tasks 表增加审批实例相关字段
    for col, typedef in [
        ('yzj_flow_inst_id', "VARCHAR(50) DEFAULT ''"),
        ('yzj_form_inst_id', "VARCHAR(50) DEFAULT ''"),
        ('yzj_serial', "VARCHAR(100) DEFAULT ''"),
        ('task_no', "VARCHAR(50) DEFAULT ''"),
        ('schedule_confirm_status', "VARCHAR(20) DEFAULT ''"),
    ]:
        try:
            db.session.execute(db.text(f"ALTER TABLE tasks ADD COLUMN {col} {typedef}"))
            db.session.commit()
        except Exception:
            db.session.rollback()

    # 给 schedule_confirmations 表增加 wx_openid 字段（兼容旧库）
    try:
        db.session.execute(db.text("ALTER TABLE schedule_confirmations ADD COLUMN wx_openid VARCHAR(64) DEFAULT ''"))
        db.session.commit()
    except Exception:
        db.session.rollback()

    # 给 client_contacts 表增加 wx_userid 字段（兼容旧库）
    try:
        db.session.execute(db.text("ALTER TABLE client_contacts ADD COLUMN wx_userid VARCHAR(64) DEFAULT ''"))
        db.session.commit()
    except Exception:
        db.session.rollback()

    # 给 client_contacts 表增加 wx_sender 字段（兼容旧库）
    try:
        db.session.execute(db.text("ALTER TABLE client_contacts ADD COLUMN wx_sender VARCHAR(64) DEFAULT ''"))
        db.session.commit()
    except Exception:
        db.session.rollback()

    # 给 schedule_confirmations 表增加 wx_sender 字段（兼容旧库）
    try:
        db.session.execute(db.text("ALTER TABLE schedule_confirmations ADD COLUMN wx_sender VARCHAR(64) DEFAULT ''"))
        db.session.commit()
    except Exception:
        db.session.rollback()

    # Create admin if not exists
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            password_hash=generate_password_hash('admin123'),
            role='admin'
        )
        admin.set_permissions(['task', 'client', 'report', 'permission', 'driver', 'vehicle', 'labor_rate'])
        db.session.add(admin)

    # Create sample drivers
    if Driver.query.count() == 0:
        sample_drivers = [
            Driver(name='张师傅', phone='13800138001'),
            Driver(name='李师傅', phone='13800138002'),
            Driver(name='王师傅', phone='13800138003'),
            Driver(name='赵师傅', phone='13800138004'),
            Driver(name='刘师傅', phone='13800138005'),
        ]
        db.session.add_all(sample_drivers)

    # Create sample vehicles
    if Vehicle.query.count() == 0:
        sample_vehicles = [
            Vehicle(plate_number='粤A12345', vehicle_type='大巴(45座)', company='国顺司'),
            Vehicle(plate_number='粤B67890', vehicle_type='中巴(25座)', company='国顺司'),
            Vehicle(plate_number='粤C11111', vehicle_type='小巴(15座)', company='国开司'),
            Vehicle(plate_number='粤D22222', vehicle_type='商务车(7座)', company='外单位'),
            Vehicle(plate_number='粤E33333', vehicle_type='大巴(45座)', company='国顺司'),
        ]
        db.session.add_all(sample_vehicles)

    # Create sample labor rates
    if LocationLaborRate.query.count() == 0:
        sample_rates = [
            LocationLaborRate(location='广州市', labor_rate=300, days=1),
            LocationLaborRate(location='深圳市', labor_rate=350, days=1),
            LocationLaborRate(location='珠海市', labor_rate=320, days=1),
            LocationLaborRate(location='佛山市', labor_rate=280, days=1),
            LocationLaborRate(location='东莞市', labor_rate=290, days=1),
        ]
        db.session.add_all(sample_rates)

    db.session.commit()
    return jsonify({'code': 200, 'msg': '数据库初始化成功，管理员账号: admin / admin123'})


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
