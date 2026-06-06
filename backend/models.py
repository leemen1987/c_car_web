from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, user
    permissions = db.Column(db.Text, default='[]')  # JSON array of page permissions
    created_at = db.Column(db.DateTime, default=datetime.now)

    def get_permissions(self):
        try:
            return json.loads(self.permissions) if self.permissions else []
        except:
            return []

    def set_permissions(self, perms):
        self.permissions = json.dumps(perms, ensure_ascii=False)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'permissions': self.get_permissions(),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class Driver(db.Model):
    __tablename__ = 'drivers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default='available')  # available, busy, inactive
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'phone': self.phone,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plate_number = db.Column(db.String(20), unique=True, nullable=False)
    vehicle_type = db.Column(db.String(50), nullable=False)
    company = db.Column(db.String(50), default='')  # 所属公司：国顺司、国开司、外单位
    status = db.Column(db.String(20), default='available')  # available, busy, maintenance
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'plate_number': self.plate_number,
            'vehicle_type': self.vehicle_type,
            'company': getattr(self, 'company', '') or '',
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class LocationLaborRate(db.Model):
    __tablename__ = 'location_labor_rates'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    location = db.Column(db.String(100), nullable=False)
    labor_rate = db.Column(db.Float, nullable=False)  # total rate in yuan
    days = db.Column(db.Integer, default=1)  # number of days for this rate
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'location': self.location,
            'labor_rate': self.labor_rate,
            'days': self.days
        }


class Client(db.Model):
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.String(200), default='')
    created_at = db.Column(db.DateTime, default=datetime.now)

    contacts = db.relationship('ClientContact', backref='client', cascade='all,delete-orphan', lazy='dynamic')

    def to_dict(self, include_contacts=False):
        d = {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }
        if include_contacts:
            d['contacts'] = [c.to_dict() for c in self.contacts.all()]
        return d


class ClientContact(db.Model):
    __tablename__ = 'client_contacts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20), default='')
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'name': self.name,
            'phone': self.phone
        }


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    client_type = db.Column(db.String(20), default='personal')  # personal, company
    client_name = db.Column(db.String(100), nullable=False)  # 个人姓名或单位名称
    client_phone = db.Column(db.String(20), default='')  # 联系电话
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)  # 关联单位
    contact_id = db.Column(db.Integer, db.ForeignKey('client_contacts.id'), nullable=True)  # 关联联系人
    departure = db.Column(db.String(200), nullable=False)  # 出发地点
    destination = db.Column(db.String(200), nullable=False)  # 目的地
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=True)
    departure_time = db.Column(db.DateTime, nullable=False)  # 出车时间
    return_time = db.Column(db.DateTime, nullable=True)  # 回程时间
    rental_days = db.Column(db.Float, default=1)  # 租用天数(自动计算)
    vehicle_type = db.Column(db.String(50))  # 车辆类型
    mileage = db.Column(db.Float, default=0)  # 任务里程(km)
    rental_fee = db.Column(db.Float, default=0)  # 租车费(元)
    fuel_fee = db.Column(db.Float, default=0)  # 油电费(预计)
    bridge_fee = db.Column(db.Float, default=0)  # 桥路费(预计)
    labor_fee = db.Column(db.Float, default=0)  # 司机人工费(预计)
    estimated_cost = db.Column(db.Float, default=0)  # 预计成本
    estimated_profit = db.Column(db.Float, default=0)  # 预估利润
    actual_fuel_fee = db.Column(db.Float, default=0)  # 实际油电费
    actual_bridge_fee = db.Column(db.Float, default=0)  # 实际桥路费
    actual_labor_fee = db.Column(db.Float, default=0)  # 实际司机人工费
    other_fee = db.Column(db.Float, default=0)  # 其他费用
    actual_cost = db.Column(db.Float, default=0)  # 实际成本
    final_profit = db.Column(db.Float, default=0)  # 最终利润
    status = db.Column(db.String(20), default='pending')  # pending, scheduled, completed
    yzj_approval_status = db.Column(db.String(20), default='')  # 审批状态：空=未发起, submitted=已发起, approved=已通过, rejected=已拒绝
    yzj_flow_inst_id = db.Column(db.String(50), default='')  # 云之家流程实例ID
    yzj_form_inst_id = db.Column(db.String(50), default='')  # 云之家表单实例ID
    yzj_serial = db.Column(db.String(100), default='')  # 审批流水号
    change_log = db.Column(db.Text, default='[]')  # JSON array of changes
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    vehicle = db.relationship('Vehicle', backref='tasks')
    driver = db.relationship('Driver', backref='tasks')

    def get_change_log(self):
        try:
            return json.loads(self.change_log) if self.change_log else []
        except:
            return []

    def add_changes(self, changes, snapshot):
        """changes: list of {'field': label, 'old_value': str, 'new_value': str}
           snapshot: dict of all task fields at the time of change"""
        if not changes:
            return
        logs = self.get_change_log()
        logs.append({
            'changed_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'changes': changes,
            'snapshot': snapshot
        })
        self.change_log = json.dumps(logs, ensure_ascii=False)

    client = db.relationship('Client', backref='tasks', foreign_keys=[client_id])
    contact = db.relationship('ClientContact', backref='tasks', foreign_keys=[contact_id])

    def to_dict(self):
        return {
            'id': self.id,
            'client_type': self.client_type,
            'client_name': self.client_name,
            'client_phone': self.client_phone,
            'client_id': self.client_id,
            'client_company': self.client.name if self.client else None,
            'contact_id': self.contact_id,
            'departure': self.departure,
            'destination': self.destination,
            'vehicle_id': self.vehicle_id,
            'driver_id': self.driver_id,
            'vehicle_plate': self.vehicle.plate_number if self.vehicle else None,
            'vehicle_company': self.vehicle.company if self.vehicle else '',
            'driver_name': self.driver.name if self.driver else None,
            'driver_phone': self.driver.phone if self.driver else None,
            'departure_time': self.departure_time.strftime('%Y-%m-%d %H:%M') if self.departure_time else None,
            'return_time': self.return_time.strftime('%Y-%m-%d %H:%M') if self.return_time else None,
            'rental_days': self.rental_days,
            'vehicle_type': self.vehicle_type,
            'mileage': self.mileage,
            'rental_fee': self.rental_fee,
            'fuel_fee': self.fuel_fee,
            'bridge_fee': self.bridge_fee,
            'labor_fee': self.labor_fee,
            'estimated_cost': self.estimated_cost,
            'estimated_profit': self.estimated_profit,
            'actual_fuel_fee': self.actual_fuel_fee,
            'actual_bridge_fee': self.actual_bridge_fee,
            'actual_labor_fee': self.actual_labor_fee,
            'other_fee': self.other_fee,
            'actual_cost': self.actual_cost,
            'final_profit': self.final_profit,
            'status': self.status,
            'yzj_approval_status': getattr(self, 'yzj_approval_status', ''),
            'yzj_serial': getattr(self, 'yzj_serial', ''),
            'change_log': self.get_change_log(),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }
