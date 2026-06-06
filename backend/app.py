from flask import Flask, request, jsonify, session
from flask_cors import CORS
from config import Config
from models import db, User, Driver, Vehicle, Task, LocationLaborRate, Client, ClientContact
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from functools import wraps
import json
import time
import uuid
import urllib.request
import urllib.parse
import urllib.error

app = Flask(__name__)
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
    contact = ClientContact(client_id=client_id, name=data.get('name', ''), phone=data.get('phone', ''))
    db.session.add(contact)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '添加成功', 'data': contact.to_dict()})


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


def build_yzj_approval_body(task):
    """将一条包车任务转换为云之家审批明细行"""
    client_display = task.client_name or ''
    if task.client_type == 'company':
        client_display = task.client_name or ''
    contact_display = f"{task.client_name} {task.client_phone}".strip() if task.client_name else ''

    return {
        '_id_': str(int(time.time() * 1000)),
        'Te_0': client_display,       # 用车方
        'Te_1': contact_display,      # 联系人
        'Te_2': task.departure or '',          # 出发地点
        'Te_3': task.destination or '',        # 目的地
        'Te_4': task.vehicle.plate_number if task.vehicle else '',  # 车牌号
        'Te_5': task.driver.name if task.driver else '',            # 驾驶司机
        'Te_6': task.departure_time.strftime('%Y-%m-%d %H:%M') if task.departure_time else '',  # 出车时间
        'Te_7': task.return_time.strftime('%Y-%m-%d %H:%M') if task.return_time else '',        # 回程时间
        'Te_8': str(task.rental_days) if task.rental_days else '',  # 天数
        'Te_9': task.vehicle_type or '',        # 车辆类型
        'Te_10': str(task.mileage) if task.mileage else '',  # 里程
        'Te_11': str(task.rental_fee) if task.rental_fee else '',  # 租车费
        'Te_12': str(task.fuel_fee) if task.fuel_fee else '',     # 油电费
        'Te_13': str(task.bridge_fee) if task.bridge_fee else '', # 桥路费
        'Te_14': str(task.labor_fee) if task.labor_fee else '',   # 司机人工费
        'Te_15': str(task.estimated_cost) if task.estimated_cost else '',   # 预计成本
        'Te_16': str(task.estimated_profit) if task.estimated_profit else '', # 预估利润
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

    # 过滤掉已发起过审批的任务
    already = [t for t in eligible if getattr(t, 'yzj_approval_status', '') == 'submitted']
    if already:
        eligible = [t for t in eligible if t not in already]

    if not eligible:
        return jsonify({'code': 400, 'msg': '所选任务均已发起过审批'})

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

        detail_rows = [build_yzj_approval_body(t) for t in group_tasks]

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


@app.route('/api/yunzhijia/callback', methods=['POST'])
def yunzhijia_callback():
    """
    云之家审批回调接口。

    审批状态变更时，云之家会 POST 此接口通知。
    需在云之家开发者后台配置回调地址：
        https://你的域名/api/yunzhijia/callback

    回调 body 示例（以实际云之家文档为准）：
    {
        "flowInstId": "xxx",
        "formInstId": "xxx",
        "formCodeId": "xxx",
        "actionType": "agree" / "reject" / "revoke",
        "nodeName": "节点名称",
        ...
    }
    """
    data = request.get_json(force=True, silent=True) or {}
    app.logger.info(f"云之家回调: {json.dumps(data, ensure_ascii=False)[:500]}")

    flow_inst_id = data.get('flowInstId', '')
    form_inst_id = data.get('formInstId', '')
    action_type = data.get('actionType', '')

    if not flow_inst_id and not form_inst_id:
        return jsonify({'code': 400, 'msg': '缺少flowInstId或formInstId'})

    # 根据 flowInstId 或 formInstId 查找关联的任务
    tasks = Task.query.filter(
        (Task.yzj_flow_inst_id == flow_inst_id) | (Task.yzj_form_inst_id == form_inst_id)
    ).all()

    if not tasks:
        app.logger.warning(f"回调未找到关联任务: flowInstId={flow_inst_id}")
        return jsonify({'code': 200, 'msg': '无关联任务'})

    # 更新审批状态
    status_map = {
        'agree': 'approved',
        'approved': 'approved',
        'reject': 'rejected',
        'rejected': 'rejected',
        'revoke': '',        # 撤销则清空状态，允许重新发起
        'revokeAll': '',
    }
    new_status = status_map.get(action_type, '')

    for t in tasks:
        t.yzj_approval_status = new_status
    db.session.commit()

    app.logger.info(f"已更新 {len(tasks)} 条任务审批状态为: {new_status or '(已撤销)'}")
    return jsonify({'code': 200, 'msg': 'ok'})


# ==================== Reports ====================

@app.route('/api/reports/by-client', methods=['GET'])
@login_required
def report_by_client():
    client = request.args.get('client', '')
    month = request.args.get('month', '')
    year = request.args.get('year', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = Task.query
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
    month = request.args.get('month', '')
    year = request.args.get('year', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = Task.query.filter(Task.driver_id.isnot(None))
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
    month = request.args.get('month', '')
    year = request.args.get('year', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = Task.query.filter(Task.vehicle_id.isnot(None))
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
    ]:
        try:
            db.session.execute(db.text(f"ALTER TABLE tasks ADD COLUMN {col} {typedef}"))
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
        admin.set_permissions(['task', 'report', 'permission', 'driver', 'vehicle', 'labor_rate'])
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
    app.run(debug=True, host='0.0.0.0', port=5000)
