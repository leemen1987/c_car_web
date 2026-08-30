from flask import Flask, request, jsonify, session, redirect
from flask_cors import CORS
from werkzeug.middleware.proxy_fix import ProxyFix
from config import Config
from models import db, User, Driver, Vehicle, VehicleCompany, Task, TaskVehicle, LocationLaborRate, Client, ClientContact, ScheduleConfirmation, ConfirmationSnapshot, LongRentalContract, LongRentalBill, SystemConfig
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
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


def permission_required(*perms):
    """Check if user has at least one of the specified permissions."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user_id' not in session:
                return jsonify({'code': 401, 'msg': '请先登录'}), 401
            user = User.query.get(session['user_id'])
            if not user:
                return jsonify({'code': 401, 'msg': '请先登录'}), 401
            if user.role == 'admin':
                return f(*args, **kwargs)
            user_perms = user.get_permissions()
            if any(p in user_perms for p in perms):
                return f(*args, **kwargs)
            return jsonify({'code': 403, 'msg': '权限不足'}), 403
        return decorated
    return decorator


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


@app.route('/api/user/settings', methods=['PUT'])
@login_required
def update_user_settings():
    """更新当前用户的个人设置（OpenID、发送人账号）"""
    user = User.query.get(session['user_id'])
    data = request.get_json()
    if 'yunzhijia_openid' in data:
        user.yunzhijia_openid = data.get('yunzhijia_openid', '').strip()
    if 'wx_sender' in data:
        user.wx_sender = data.get('wx_sender', '').strip()
    db.session.commit()
    return jsonify({'code': 200, 'msg': '更新成功', 'data': user.to_dict()})


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


@app.route('/api/drivers/settlement-stats')
@login_required
def driver_settlement_stats():
    """获取所有司机在当前结算周期内的费用统计"""
    settlement_start, settlement_end = get_settlement_range()
    start_dt = datetime.combine(settlement_start, datetime.min.time())
    end_dt = datetime.combine(settlement_end, datetime.max.time())

    drivers = Driver.query.filter(Driver.status != 'inactive').all()
    result = []
    for driver in drivers:
        tasks = Task.query.filter(
            Task.driver_id == driver.id,
            Task.status.in_(['completed', 'scheduled']),
            Task.departure_time >= start_dt,
            Task.departure_time <= end_dt
        ).all()
        total_actual = sum(t.actual_labor_fee for t in tasks if t.status == 'completed')
        total_estimated = sum(t.labor_fee for t in tasks if t.status == 'scheduled')
        task_details = [{
            'id': t.id,
            'departure': t.departure,
            'destination': t.destination,
            'departure_time': t.departure_time.strftime('%Y-%m-%d %H:%M') if t.departure_time else '',
            'client_name': t.client_name,
            'labor_fee': t.labor_fee,
            'actual_labor_fee': t.actual_labor_fee,
            'status': t.status
        } for t in sorted(tasks, key=lambda x: x.departure_time or datetime.min, reverse=True)]
        result.append({
            'driver_id': driver.id,
            'driver_name': driver.name,
            'driver_phone': driver.phone,
            'task_count': len(tasks),
            'total_actual_labor_fee': total_actual,
            'total_estimated_labor_fee': total_estimated,
            'total_fee': total_actual + total_estimated,
            'tasks': task_details
        })

    return jsonify({
        'code': 200,
        'data': {
            'drivers': result,
            'settlement_start': settlement_start.strftime('%m月%d日'),
            'settlement_end': settlement_end.strftime('%m月%d日')
        }
    })


# ==================== Vehicles ====================

@app.route('/api/vehicles', methods=['GET'])
@login_required
def list_vehicles():
    vehicles = Vehicle.query.all()
    return jsonify({'code': 200, 'data': [v.to_dict() for v in vehicles]})


def get_settlement_range(today=None):
    """返回当前结算周期 (start_date, end_date)，每月26日至次月25日"""
    if today is None:
        today = date.today()
    if today.day >= 26:
        start = today.replace(day=26)
        if today.month == 12:
            end = today.replace(year=today.year + 1, month=1, day=25)
        else:
            end = today.replace(month=today.month + 1, day=25)
    else:
        if today.month == 1:
            start = today.replace(year=today.year - 1, month=12, day=26)
        else:
            start = today.replace(month=today.month - 1, day=26)
        end = today.replace(day=25)
    return start, end


def _parse_date(val):
    """Convert empty/falsy string to None, pass through valid date strings."""
    if not val or not str(val).strip():
        return None
    return val

def _amap_geocode(address):
    """调用高德地理编码API，返回经纬度字符串 'lng,lat' 或 None"""
    try:
        params = urllib.parse.urlencode({
            'address': address,
            'key': app.config['AMAP_KEY'],
            'output': 'json'
        })
        url = f'https://restapi.amap.com/v3/geocode/geo?{params}'
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            if data.get('status') == '1' and data.get('geocodes'):
                return data['geocodes'][0]['location']
    except Exception:
        pass
    return None

@app.route('/api/estimate-toll')
@login_required
def estimate_toll():
    """根据出发地和目的地，调用高德驾车路线规划获取过路费预估"""
    departure = request.args.get('departure', '').strip()
    destination = request.args.get('destination', '').strip()
    if not departure or not destination:
        return jsonify({'code': 400, 'msg': '出发地和目的地不能为空'})

    origin_loc = _amap_geocode(departure)
    dest_loc = _amap_geocode(destination)
    if not origin_loc or not dest_loc:
        return jsonify({'code': 400, 'msg': '地址解析失败，请检查输入'})

    try:
        params = urllib.parse.urlencode({
            'origin': origin_loc,
            'destination': dest_loc,
            'extensions': 'all',
            'strategy': 0,
            'key': app.config['AMAP_KEY']
        })
        url = f'https://restapi.amap.com/v3/direction/driving?{params}'
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            if data.get('status') == '1' and data.get('route', {}).get('paths'):
                path = data['route']['paths'][0]
                tolls = float(path.get('tolls', 0))
                distance = round(float(path.get('distance', 0)) / 1000, 1)
                duration = round(float(path.get('duration', 0)) / 60)
                return jsonify({'code': 200, 'data': {
                    'tolls': tolls,
                    'distance': distance,
                    'duration': duration
                }})
    except Exception:
        pass
    return jsonify({'code': 500, 'msg': '路线查询失败'})

@app.route('/api/system-config/<key>')
@login_required
def get_system_config(key):
    value = SystemConfig.get(key)
    return jsonify({'code': 200, 'data': value})

@app.route('/api/system-config/<key>', methods=['PUT'])
@admin_required
def update_system_config(key):
    data = request.get_json()
    value = data.get('value', '')
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)
    SystemConfig.set(key, value)
    return jsonify({'code': 200, 'msg': '保存成功'})

@app.route('/api/vehicles', methods=['POST'])
@login_required
def create_vehicle():
    data = request.get_json()
    vehicle = Vehicle(
        plate_number=data.get('plate_number', ''),
        capacity=data.get('capacity', ''),
        vehicle_type=data.get('vehicle_type', ''),
        company=data.get('company', ''),
        status=data.get('status', 'available'),
        registration_date=_parse_date(data.get('registration_date', '')),
        issue_date=_parse_date(data.get('issue_date', '')),
        usage_type=data.get('usage_type', ''),
        brand_model=data.get('brand_model', ''),
        inspection_expiry=_parse_date(data.get('inspection_expiry', '')),
        scrap_date=data.get('scrap_date', ''),
        insurance_expiry=_parse_date(data.get('insurance_expiry', ''))
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
    if 'capacity' in data:
        vehicle.capacity = data['capacity']
    if 'vehicle_type' in data:
        vehicle.vehicle_type = data['vehicle_type']
    if 'company' in data:
        vehicle.company = data['company']
    if 'status' in data:
        vehicle.status = data['status']
    if 'mileage' in data:
        vehicle.mileage = data['mileage']
    for field in ['registration_date', 'issue_date', 'usage_type', 'brand_model', 'inspection_expiry', 'scrap_date', 'insurance_expiry']:
        if field in data:
            if field in ('registration_date', 'issue_date', 'inspection_expiry', 'insurance_expiry'):
                setattr(vehicle, field, _parse_date(data[field]))
            else:
                setattr(vehicle, field, data[field])
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


# ==================== Vehicle Companies ====================

@app.route('/api/vehicle-companies', methods=['GET'])
@login_required
def list_vehicle_companies():
    companies = VehicleCompany.query.order_by(VehicleCompany.id).all()
    return jsonify({'code': 200, 'data': [c.to_dict() for c in companies]})


@app.route('/api/vehicle-companies', methods=['POST'])
@login_required
def create_vehicle_company():
    data = request.get_json()
    name = data.get('name', '').strip()
    if not name:
        return jsonify({'code': 400, 'msg': '请输入单位名称'})
    if VehicleCompany.query.filter_by(name=name).first():
        return jsonify({'code': 400, 'msg': '单位名称已存在'})
    company = VehicleCompany(
        name=name,
        contact_person=data.get('contact_person', ''),
        phone=data.get('phone', ''),
        address=data.get('address', '')
    )
    db.session.add(company)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '创建成功', 'data': company.to_dict()})


@app.route('/api/vehicle-companies/<int:company_id>', methods=['PUT'])
@login_required
def update_vehicle_company(company_id):
    company = VehicleCompany.query.get(company_id)
    if not company:
        return jsonify({'code': 404, 'msg': '单位不存在'})
    data = request.get_json()
    old_name = company.name
    company.name = data.get('name', company.name).strip()
    company.contact_person = data.get('contact_person', company.contact_person)
    company.phone = data.get('phone', company.phone)
    company.address = data.get('address', company.address)
    # 同步更新车辆表中的公司名
    if old_name != company.name:
        Vehicle.query.filter_by(company=old_name).update({'company': company.name})
    db.session.commit()
    return jsonify({'code': 200, 'msg': '更新成功', 'data': company.to_dict()})


@app.route('/api/vehicle-companies/<int:company_id>', methods=['DELETE'])
@login_required
def delete_vehicle_company(company_id):
    company = VehicleCompany.query.get(company_id)
    if not company:
        return jsonify({'code': 404, 'msg': '单位不存在'})
    db.session.delete(company)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '删除成功'})


# ==================== Long Rental Contracts ====================

def generate_contract_no():
    """生成合同编号 CZHT-YYYYMMDD-NNN"""
    today = datetime.now().strftime('%Y%m%d')
    prefix = f'CZHT-{today}-'
    last = LongRentalContract.query.filter(
        LongRentalContract.contract_no.like(f'{prefix}%')
    ).order_by(LongRentalContract.id.desc()).first()
    if last:
        seq = int(last.contract_no.split('-')[-1]) + 1
    else:
        seq = 1
    return f'{prefix}{seq:03d}'


@app.route('/api/long-rental-contracts', methods=['GET'])
@login_required
def list_long_rental_contracts():
    status = request.args.get('status', '')
    q = LongRentalContract.query
    if status:
        q = q.filter_by(status=status)
    contracts = q.order_by(LongRentalContract.id.desc()).all()
    result = []
    for c in contracts:
        d = c.to_dict()
        paid_total = sum(b.total_amount for b in c.bills if b.is_paid)
        unpaid_total = sum(b.total_amount for b in c.bills if not b.is_paid)
        d['paid_total'] = paid_total
        d['unpaid_total'] = unpaid_total
        d['bill_count'] = len(c.bills)
        result.append(d)
    return jsonify({'code': 200, 'data': result})


@app.route('/api/long-rental-contracts', methods=['POST'])
@login_required
def create_long_rental_contract():
    data = request.get_json()
    client_id = data.get('client_id')
    client = Client.query.get(client_id) if client_id else None
    contract = LongRentalContract(
        contract_no=generate_contract_no(),
        client_id=client_id,
        client_name=client.name if client else data.get('client_name', ''),
        vehicle_id=data.get('vehicle_id'),
        driver_id=data.get('driver_id'),
        start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data.get('start_date') else datetime.now().date(),
        end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data.get('end_date') else None,
        monthly_rental_fee=data.get('monthly_rental_fee', 0),
        remark=data.get('remark', ''),
        status='active'
    )
    db.session.add(contract)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '创建成功', 'data': contract.to_dict()})


@app.route('/api/long-rental-contracts/<int:contract_id>', methods=['PUT'])
@login_required
def update_long_rental_contract(contract_id):
    contract = LongRentalContract.query.get(contract_id)
    if not contract:
        return jsonify({'code': 404, 'msg': '合同不存在'})
    data = request.get_json()
    if 'client_id' in data:
        client = Client.query.get(data['client_id'])
        contract.client_id = data['client_id']
        contract.client_name = client.name if client else ''
    if 'vehicle_id' in data:
        contract.vehicle_id = data['vehicle_id']
    if 'driver_id' in data:
        contract.driver_id = data['driver_id']
    if 'start_date' in data and data['start_date']:
        contract.start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
    if 'end_date' in data:
        contract.end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data['end_date'] else None
    if 'monthly_rental_fee' in data:
        contract.monthly_rental_fee = data['monthly_rental_fee']
    if 'remark' in data:
        contract.remark = data['remark']
    if 'status' in data:
        contract.status = data['status']
    db.session.commit()
    return jsonify({'code': 200, 'msg': '更新成功', 'data': contract.to_dict()})


@app.route('/api/long-rental-contracts/<int:contract_id>', methods=['DELETE'])
@login_required
def delete_long_rental_contract(contract_id):
    contract = LongRentalContract.query.get(contract_id)
    if not contract:
        return jsonify({'code': 404, 'msg': '合同不存在'})
    LongRentalBill.query.filter_by(contract_id=contract_id).delete()
    db.session.delete(contract)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '删除成功'})


# ==================== Long Rental Bills ====================

@app.route('/api/long-rental-contracts/<int:contract_id>/bills', methods=['GET'])
@login_required
def list_long_rental_bills(contract_id):
    contract = LongRentalContract.query.get(contract_id)
    if not contract:
        return jsonify({'code': 404, 'msg': '合同不存在'})
    bills = LongRentalBill.query.filter_by(contract_id=contract_id).order_by(LongRentalBill.bill_month.desc()).all()
    return jsonify({'code': 200, 'data': [b.to_dict() for b in bills]})


@app.route('/api/long-rental-contracts/<int:contract_id>/bills', methods=['POST'])
@login_required
def create_long_rental_bill(contract_id):
    contract = LongRentalContract.query.get(contract_id)
    if not contract:
        return jsonify({'code': 404, 'msg': '合同不存在'})
    data = request.get_json()
    bill_month = data.get('bill_month', '')
    if not bill_month:
        return jsonify({'code': 400, 'msg': '请选择账单月份'})
    existing = LongRentalBill.query.filter_by(contract_id=contract_id, bill_month=bill_month).first()
    if existing:
        return jsonify({'code': 400, 'msg': f'{bill_month} 月份账单已存在'})
    rental_fee = data.get('rental_fee', contract.monthly_rental_fee)
    fuel_fee = data.get('fuel_fee', 0)
    bridge_fee = data.get('bridge_fee', 0)
    other_fee = data.get('other_fee', 0)
    bill = LongRentalBill(
        contract_id=contract_id,
        bill_month=bill_month,
        rental_fee=rental_fee,
        fuel_fee=fuel_fee,
        bridge_fee=bridge_fee,
        other_fee=other_fee,
        total_amount=rental_fee + fuel_fee + bridge_fee + other_fee,
        is_paid=data.get('is_paid', False),
        paid_date=datetime.strptime(data['paid_date'], '%Y-%m-%d').date() if data.get('paid_date') else None,
        paid_method=data.get('paid_method', ''),
        remark=data.get('remark', '')
    )
    db.session.add(bill)
    db.session.commit()
    return jsonify({'code': 200, 'msg': '创建成功', 'data': bill.to_dict()})


@app.route('/api/long-rental-bills/<int:bill_id>', methods=['PUT'])
@login_required
def update_long_rental_bill(bill_id):
    bill = LongRentalBill.query.get(bill_id)
    if not bill:
        return jsonify({'code': 404, 'msg': '账单不存在'})
    data = request.get_json()
    for field in ['rental_fee', 'fuel_fee', 'bridge_fee', 'other_fee']:
        if field in data:
            setattr(bill, field, data[field])
    bill.total_amount = bill.rental_fee + bill.fuel_fee + bill.bridge_fee + bill.other_fee
    if 'is_paid' in data:
        bill.is_paid = data['is_paid']
    if 'paid_date' in data:
        bill.paid_date = datetime.strptime(data['paid_date'], '%Y-%m-%d').date() if data['paid_date'] else None
    if 'paid_method' in data:
        bill.paid_method = data['paid_method']
    if 'remark' in data:
        bill.remark = data['remark']
    db.session.commit()
    return jsonify({'code': 200, 'msg': '更新成功', 'data': bill.to_dict()})


@app.route('/api/long-rental-bills/<int:bill_id>', methods=['DELETE'])
@login_required
def delete_long_rental_bill(bill_id):
    bill = LongRentalBill.query.get(bill_id)
    if not bill:
        return jsonify({'code': 404, 'msg': '账单不存在'})
    db.session.delete(bill)
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
    contact = ClientContact(
        client_id=client_id,
        name=data.get('name', ''),
        phone=data.get('phone', ''),
        wx_userid=data.get('wx_userid', ''),
        wx_sender=data.get('wx_sender', ''),
        external_corp_name=data.get('external_corp_name', '')
    )
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
    if 'external_corp_name' in data:
        contact.external_corp_name = data['external_corp_name']
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
        vehicle_count=data.get('vehicle_count', 1),
        self_drive=data.get('self_drive', False),
        mileage=data.get('mileage', 0),
        rental_fee=data.get('rental_fee', 0),
        fuel_fee=data.get('fuel_fee', 0),
        bridge_fee=data.get('bridge_fee', 0),
        labor_fee=data.get('labor_fee', 0),
        remark=data.get('remark', ''),
        status='pending'
    )
    task.estimated_cost = task.fuel_fee + task.bridge_fee + task.labor_fee
    task.estimated_profit = task.rental_fee - task.estimated_cost
    db.session.add(task)
    db.session.flush()
    # 自动生成任务编号：TASK-YYYYMMDD-ID
    task.task_no = f'TASK-{task.created_at.strftime("%Y%m%d")}-{task.id}'
    
    # 创建车辆分配记录
    for _ in range(task.vehicle_count):
        tv = TaskVehicle(task_id=task.id, status='pending')
        db.session.add(tv)
    
    db.session.commit()
    db.session.commit()
    return jsonify({'code': 200, 'msg': '任务创建成功', 'data': task.to_dict()})


@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@permission_required('task', 'report_edit')
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

    if 'remark' in data:
        task.remark = data['remark']

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

    # Calculate settlement period labor fee for each driver
    settlement_start, settlement_end = get_settlement_range()
    start_dt = datetime.combine(settlement_start, datetime.min.time())
    end_dt = datetime.combine(settlement_end, datetime.max.time())

    driver_fees = {}
    for driver in available_drivers:
        # Completed tasks in settlement period (by departure_time)
        total_fee = db.session.query(
            db.func.coalesce(db.func.sum(Task.actual_labor_fee), 0)
        ).filter(
            Task.driver_id == driver.id,
            Task.status == 'completed',
            Task.departure_time >= start_dt,
            Task.departure_time <= end_dt
        ).scalar()
        # Scheduled tasks in settlement period
        scheduled_fee = db.session.query(
            db.func.coalesce(db.func.sum(Task.labor_fee), 0)
        ).filter(
            Task.driver_id == driver.id,
            Task.status == 'scheduled',
            Task.departure_time >= start_dt,
            Task.departure_time <= end_dt
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
            'task_end': task_end.strftime('%Y-%m-%d %H:%M'),
            'settlement_start': settlement_start.strftime('%m月%d日'),
            'settlement_end': settlement_end.strftime('%m月%d日')
        }
    })


@app.route('/api/tasks/<int:task_id>/schedule', methods=['POST'])
@login_required
def schedule_task(task_id):
    """Assign vehicles and drivers to a task."""
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'code': 404, 'msg': '任务不存在'})
    data = request.get_json()
    
    # 支持单个和多个排班
    assignments = data.get('assignments', [])
    if not assignments:
        # 兼容旧的单个排班
        vehicle_id = data.get('vehicle_id')
        driver_id = data.get('driver_id')
        if vehicle_id and driver_id:
            assignments = [{'vehicle_id': vehicle_id, 'driver_id': driver_id}]
    
    if not assignments:
        return jsonify({'code': 400, 'msg': '请选择车辆和司机'})

    # 验证时间冲突
    task_start = task.departure_time
    task_end = task_start + timedelta(days=task.rental_days)
    is_self_drive = task.self_drive or False
    
    for a in assignments:
        vid = a.get('vehicle_id')
        did = a.get('driver_id')
        if not vid:
            return jsonify({'code': 400, 'msg': '请选择车辆'})
        if not is_self_drive and not did:
            return jsonify({'code': 400, 'msg': '请选择司机'})
        
        conflict_tasks = Task.query.filter(
            Task.id != task_id,
            Task.status.in_(['scheduled']),
            (Task.vehicle_id == vid) | (Task.driver_id == did) if did else (Task.vehicle_id == vid)
        ).all()
        
        for ct in conflict_tasks:
            ct_start = ct.departure_time
            ct_end = ct_start + timedelta(days=ct.rental_days)
            if task_start < ct_end and task_end > ct_start:
                vehicle = Vehicle.query.get(vid)
                driver = Driver.query.get(did) if did else None
                return jsonify({'code': 400, 'msg': f'{vehicle.plate_number if vehicle else ""} 或 {driver.name if driver else ""} 在此时间段已被安排'})
    
    # 清除旧的车辆分配
    TaskVehicle.query.filter_by(task_id=task_id).delete()
    
    # 创建新的车辆分配
    for a in assignments:
        tv = TaskVehicle(
            task_id=task_id,
            vehicle_id=a['vehicle_id'],
            driver_id=a.get('driver_id'),
            status='scheduled'
        )
        db.session.add(tv)
    
    # 更新备注
    remark = data.get('remark')
    if remark is not None:
        task.remark = remark
    
    # 设置主车辆/司机为第一个分配
    task.vehicle_id = assignments[0]['vehicle_id']
    task.driver_id = assignments[0].get('driver_id')
    task.status = 'scheduled'
    
    # 更新相关车辆状态
    for a in assignments:
        vehicle = Vehicle.query.get(a['vehicle_id'])
        if vehicle:
            vehicle.status = 'busy'

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
    task.remark = data.get('remark', '')
    task.is_paid = data.get('is_paid', False)
    paid_date = data.get('paid_date')
    task.paid_date = datetime.strptime(paid_date, '%Y-%m-%d') if paid_date else None
    task.paid_method = data.get('paid_method', '')
    
    # 处理里程数
    start_mileage = data.get('start_mileage', 0)
    end_mileage = data.get('end_mileage', 0)
    task.start_mileage = start_mileage
    task.end_mileage = end_mileage
    
    # 更新车辆里程数
    if task.vehicle_id and end_mileage > 0:
        vehicle = Vehicle.query.get(task.vehicle_id)
        if vehicle:
            vehicle.mileage = end_mileage
    
    task.status = 'completed'

    db.session.commit()
    return jsonify({'code': 200, 'msg': '任务已完成', 'data': task.to_dict()})


@app.route('/api/tasks/<int:task_id>/cancel', methods=['POST'])
@login_required
def cancel_task(task_id):
    """Cancel a task with a reason."""
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'code': 404, 'msg': '任务不存在'})
    if task.status == 'completed':
        return jsonify({'code': 400, 'msg': '已完成的任务不能取消'})
    if task.status == 'cancelled':
        return jsonify({'code': 400, 'msg': '任务已经是取消状态'})

    data = request.get_json() or {}
    reason = data.get('reason', '').strip()
    if not reason:
        return jsonify({'code': 400, 'msg': '请输入取消原因'})

    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    task.add_changes(
        [{'field': '任务状态', 'old_value': task.status, 'new_value': 'cancelled'},
         {'field': '取消原因', 'old_value': '', 'new_value': reason}],
        {'cancelled_at': now_str, 'cancel_reason': reason,
         'client_name': task.client_name,
         'departure': task.departure, 'destination': task.destination,
         'departure_time': task.departure_time.strftime('%Y-%m-%d %H:%M') if task.departure_time else '',
         'vehicle_type': task.vehicle_type or ''}
    )
    task.status = 'cancelled'

    db.session.commit()
    return jsonify({'code': 200, 'msg': '任务已取消', 'data': task.to_dict()})


@app.route('/api/tasks/<int:task_id>/invoice', methods=['POST'])
@login_required
def save_invoice(task_id):
    """Save invoice info for a completed task."""
    task = Task.query.get(task_id)
    if not task:
        return jsonify({'code': 404, 'msg': '任务不存在'})

    data = request.get_json() or {}
    task.invoice_type = data.get('invoice_type', '')
    task.invoice_no = data.get('invoice_no', '')
    task.invoice_amount = data.get('invoice_amount', 0)
    invoice_date = data.get('invoice_date')
    task.invoice_date = datetime.strptime(invoice_date, '%Y-%m-%d') if invoice_date else None
    task.invoice_remark = data.get('invoice_remark', '')
    task.contract_no = data.get('contract_no', '')

    db.session.commit()
    return jsonify({'code': 200, 'msg': '发票信息已保存', 'data': task.to_dict()})


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

    # 车牌号和司机：优先使用 task_vehicles（多车），回退到主车辆
    task_vehicles = list(task.task_vehicles) if hasattr(task, 'task_vehicles') else []
    if task_vehicles:
        plates = [f"{i+1}.{tv.vehicle_plate}" for i, tv in enumerate(task_vehicles) if tv.vehicle_plate]
        drivers = [f"{i+1}.{tv.driver_name}" for i, tv in enumerate(task_vehicles) if tv.driver_name]
        plate_display = ";".join(plates)
        driver_display = ";".join(drivers)
    else:
        plate_display = task.vehicle.plate_number if task.vehicle else ''
        driver_display = task.driver.name if task.driver else ''

    return {
        '_id_': str(row_id),
        'Te_0': client_display,       # 用车方
        'Te_1': contact_display,      # 联系人
        'Te_2': task.departure or '',          # 出发地点
        'Te_3': task.destination or '',        # 目的地
        'Te_4': plate_display,                  # 车牌号
        'Te_5': driver_display,                 # 驾驶司机
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

    # 大众司不走审批流程，自动跳过
    skipped_dazhong = [t for t in eligible if (t.vehicle.company if t.vehicle else '') == '大众司']
    if skipped_dazhong:
        eligible = [t for t in eligible if t not in skipped_dazhong]

    if not eligible:
        return jsonify({'code': 400, 'msg': '所选任务均为大众司车辆，无需发起审批'})

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

        # 使用当前登录用户的 OpenID，未配置则使用默认值
        current_user = User.query.get(session['user_id'])
        creator_openid = (current_user.yunzhijia_openid or '').strip() or app.config['YUNZHIJIA_CREATOR_OPENID']

        payload = {
            'formCodeId': template_id,
            'creator': creator_openid,
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
        except Exception:
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
    paid_method = request.args.get('paid_method', '')
    is_paid = request.args.get('is_paid', '')
    is_invoiced = request.args.get('is_invoiced', '')
    month = request.args.get('month', '')
    year = request.args.get('year', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = Task.query.filter(Task.status != 'cancelled')
    if client_type:
        query = query.filter(Task.client_type == client_type)
    if client:
        query = query.filter(Task.client_name.like(f'%{client}%'))
    if paid_method:
        query = query.filter(Task.paid_method == paid_method)
    if is_paid == '1':
        query = query.filter(Task.is_paid == True)
    elif is_paid == '0':
        query = query.filter(Task.is_paid == False)
    if is_invoiced == '1':
        query = query.filter(Task.invoice_no != '')
    elif is_invoiced == '0':
        query = query.filter((Task.invoice_no == '') | (Task.invoice_no.is_(None)))
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
    paid_method = request.args.get('paid_method', '')
    is_paid = request.args.get('is_paid', '')
    is_invoiced = request.args.get('is_invoiced', '')
    month = request.args.get('month', '')
    year = request.args.get('year', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = Task.query.filter(Task.driver_id.isnot(None), Task.status != 'cancelled')
    if client_type:
        query = query.filter(Task.client_type == client_type)
    if driver_id:
        query = query.filter(Task.driver_id == driver_id)
    if paid_method:
        query = query.filter(Task.paid_method == paid_method)
    if is_paid == '1':
        query = query.filter(Task.is_paid == True)
    elif is_paid == '0':
        query = query.filter(Task.is_paid == False)
    if is_invoiced == '1':
        query = query.filter(Task.invoice_no != '')
    elif is_invoiced == '0':
        query = query.filter((Task.invoice_no == '') | (Task.invoice_no.is_(None)))
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
    paid_method = request.args.get('paid_method', '')
    is_paid = request.args.get('is_paid', '')
    is_invoiced = request.args.get('is_invoiced', '')
    month = request.args.get('month', '')
    year = request.args.get('year', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = Task.query.filter(Task.vehicle_id.isnot(None), Task.status != 'cancelled')
    if client_type:
        query = query.filter(Task.client_type == client_type)
    if vehicle_id:
        query = query.filter(Task.vehicle_id == vehicle_id)
    if paid_method:
        query = query.filter(Task.paid_method == paid_method)
    if is_paid == '1':
        query = query.filter(Task.is_paid == True)
    elif is_paid == '0':
        query = query.filter(Task.is_paid == False)
    if is_invoiced == '1':
        query = query.filter(Task.invoice_no != '')
    elif is_invoiced == '0':
        query = query.filter((Task.invoice_no == '') | (Task.invoice_no.is_(None)))
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
        except Exception:
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
        except Exception:
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

    # 初始化车属单位表（从现有车辆数据中提取公司名）
    if VehicleCompany.query.count() == 0:
        existing_companies = db.session.query(Vehicle.company).distinct().all()
        for (name,) in existing_companies:
            if name:
                db.session.add(VehicleCompany(name=name))
        db.session.commit()

    # 给 vehicles 表增加 company 字段（兼容旧库）
    try:
        db.session.execute(db.text("ALTER TABLE vehicles ADD COLUMN company VARCHAR(50) DEFAULT ''"))
        db.session.commit()
    except Exception:
        app.logger.debug("ALTER TABLE vehicles.company skipped (already exists)")
        db.session.rollback()

    # 给 tasks 表增加 yzj_approval_status 字段（兼容旧库）
    try:
        db.session.execute(db.text("ALTER TABLE tasks ADD COLUMN yzj_approval_status VARCHAR(20) DEFAULT ''"))
        db.session.commit()
    except Exception:
        app.logger.debug("ALTER TABLE tasks.yzj_approval_status skipped (already exists)")
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
            app.logger.debug(f"ALTER TABLE tasks.{col} skipped (already exists)")
            db.session.rollback()

    # 给 schedule_confirmations 表增加 wx_openid 字段（兼容旧库）
    try:
        db.session.execute(db.text("ALTER TABLE schedule_confirmations ADD COLUMN wx_openid VARCHAR(64) DEFAULT ''"))
        db.session.commit()
    except Exception:
        app.logger.debug("ALTER TABLE schedule_confirmations.wx_openid skipped (already exists)")
        db.session.rollback()

    # 给 client_contacts 表增加 wx_userid 字段（兼容旧库）
    try:
        db.session.execute(db.text("ALTER TABLE client_contacts ADD COLUMN wx_userid VARCHAR(64) DEFAULT ''"))
        db.session.commit()
    except Exception:
        app.logger.debug("ALTER TABLE client_contacts.wx_userid skipped (already exists)")
        db.session.rollback()

    # 给 client_contacts 表增加 wx_sender 字段（兼容旧库）
    try:
        db.session.execute(db.text("ALTER TABLE client_contacts ADD COLUMN wx_sender VARCHAR(64) DEFAULT ''"))
        db.session.commit()
    except Exception:
        app.logger.debug("ALTER TABLE client_contacts.wx_sender skipped (already exists)")
        db.session.rollback()

    # 给 schedule_confirmations 表增加 wx_sender 字段（兼容旧库）
    try:
        db.session.execute(db.text("ALTER TABLE schedule_confirmations ADD COLUMN wx_sender VARCHAR(64) DEFAULT ''"))
        db.session.commit()
    except Exception:
        app.logger.debug("ALTER TABLE schedule_confirmations.wx_sender skipped (already exists)")
        db.session.rollback()

    # 给 client_contacts 表增加 external_corp_name 字段（兼容旧库）
    try:
        db.session.execute(db.text("ALTER TABLE client_contacts ADD COLUMN external_corp_name VARCHAR(100) DEFAULT ''"))
        db.session.commit()
    except Exception:
        app.logger.debug("ALTER TABLE client_contacts.external_corp_name skipped (already exists)")
        db.session.rollback()

    # 给 tasks 表增加收款相关字段（兼容旧库）
    for col, typedef in [
        ('remark', "TEXT"),
        ('is_paid', "TINYINT(1) DEFAULT 0"),
        ('paid_date', "DATETIME NULL"),
        ('paid_method', "VARCHAR(20) DEFAULT ''"),
        ('invoice_type', "VARCHAR(30) DEFAULT ''"),
        ('invoice_no', "VARCHAR(50) DEFAULT ''"),
        ('invoice_amount', "FLOAT DEFAULT 0"),
        ('invoice_date', "DATETIME NULL"),
        ('invoice_remark', "TEXT"),
        ('contract_no', "VARCHAR(50) DEFAULT ''"),
        ('start_mileage', "FLOAT DEFAULT 0"),
        ('end_mileage', "FLOAT DEFAULT 0"),
        ('vehicle_count', "INT DEFAULT 1"),
        ('self_drive', "TINYINT DEFAULT 0"),
    ]:
        try:
            db.session.execute(db.text(f"ALTER TABLE tasks ADD COLUMN {col} {typedef}"))
            db.session.commit()
        except Exception:
            app.logger.debug(f"ALTER TABLE tasks.{col} skipped (already exists)")
            db.session.rollback()

    # 给 users 表增加 yunzhijia_openid 字段（兼容旧库）
    try:
        db.session.execute(db.text("ALTER TABLE users ADD COLUMN yunzhijia_openid VARCHAR(64) DEFAULT ''"))
        db.session.commit()
    except Exception:
        app.logger.debug("ALTER TABLE users.yunzhijia_openid skipped (already exists)")
        db.session.rollback()

    # 给 users 表增加 wx_sender 字段（兼容旧库）
    try:
        db.session.execute(db.text("ALTER TABLE users ADD COLUMN wx_sender VARCHAR(64) DEFAULT ''"))
        db.session.commit()
    except Exception:
        app.logger.debug("ALTER TABLE users.wx_sender skipped (already exists)")
        db.session.rollback()

    # 给 vehicles 表增加新字段（兼容旧库）
    vehicle_cols = [
        ("registration_date", "VARCHAR(20) DEFAULT ''"),
        ("issue_date", "VARCHAR(20) DEFAULT ''"),
        ("usage_type", "VARCHAR(50) DEFAULT ''"),
        ("brand_model", "VARCHAR(100) DEFAULT ''"),
        ("inspection_expiry", "VARCHAR(20) DEFAULT ''"),
        ("scrap_date", "VARCHAR(20) DEFAULT ''"),
        ("insurance_expiry", "VARCHAR(20) DEFAULT ''"),
        ("mileage", "FLOAT DEFAULT 0"),
    ]
    for col_name, col_type in vehicle_cols:
        try:
            db.session.execute(db.text(f"ALTER TABLE vehicles ADD COLUMN {col_name} {col_type}"))
            db.session.commit()
        except Exception:
            app.logger.debug(f"ALTER TABLE vehicles.{col_name} skipped (already exists)")
            db.session.rollback()

    # 增加 capacity（核定在人数）列，并将旧 vehicle_type 数据迁移过去
    try:
        db.session.execute(db.text("ALTER TABLE vehicles ADD COLUMN capacity VARCHAR(20) DEFAULT ''"))
        db.session.commit()
    except Exception:
        db.session.rollback()

    # 将旧 vehicle_type 中的在人数数据（如"7座"）迁移到 capacity
    try:
        db.session.execute(db.text("UPDATE vehicles SET capacity = vehicle_type WHERE capacity = '' AND vehicle_type != ''"))
        db.session.commit()
    except Exception:
        db.session.rollback()

    # 初始化油电费费率默认配置
    default_fuel_rates = json.dumps([
        {"min": 31, "max": 51, "rate": 2.5},
        {"min": 15, "max": 17, "rate": 1.5},
        {"min": 7, "max": 7, "rate": 1},
        {"min": 5, "max": 5, "rate": 0.7}
    ], ensure_ascii=False)
    if not SystemConfig.query.get('fuel_rates'):
        db.session.add(SystemConfig(key='fuel_rates', value=default_fuel_rates))

    # 为已有任务生成任务编号
    tasks_without_no = Task.query.filter((Task.task_no == '') | (Task.task_no.is_(None))).all()
    for t in tasks_without_no:
        t.task_no = f'TASK-{t.created_at.strftime("%Y%m%d")}-{t.id}'

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
