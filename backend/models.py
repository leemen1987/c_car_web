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
    yunzhijia_openid = db.Column(db.String(64), default='')  # 云之家 OpenID
    wx_sender = db.Column(db.String(64), default='')  # 企业微信发送人账号（内部员工UserID）
    created_at = db.Column(db.DateTime, default=datetime.now)

    def get_permissions(self):
        try:
            return json.loads(self.permissions) if self.permissions else []
        except (json.JSONDecodeError, ValueError):
            return []

    def set_permissions(self, perms):
        self.permissions = json.dumps(perms, ensure_ascii=False)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'permissions': self.get_permissions(),
            'yunzhijia_openid': self.yunzhijia_openid or '',
            'wx_sender': self.wx_sender or '',
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


class VehicleCompany(db.Model):
    """车属单位"""
    __tablename__ = 'vehicle_companies'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), unique=True, nullable=False)  # 单位名称
    contact_person = db.Column(db.String(50), default='')  # 联系人
    phone = db.Column(db.String(20), default='')  # 手机号码
    address = db.Column(db.String(200), default='')  # 单位地址
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contact_person': self.contact_person or '',
            'phone': self.phone or '',
            'address': self.address or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    plate_number = db.Column(db.String(20), unique=True, nullable=False)
    capacity = db.Column(db.String(20), default='')  # 核定载人数
    vehicle_type = db.Column(db.String(50), default='')  # 车辆类型
    company = db.Column(db.String(50), default='')  # 所属公司：国顺司、国开司、外单位
    status = db.Column(db.String(20), default='available')  # available, busy, maintenance
    registration_date = db.Column(db.Date, nullable=True)  # 注册日期
    issue_date = db.Column(db.Date, nullable=True)  # 发证日期
    usage_type = db.Column(db.String(50), default='')  # 使用性质
    brand_model = db.Column(db.String(100), default='')  # 品牌型号
    inspection_expiry = db.Column(db.Date, nullable=True)  # 检验有效期
    scrap_date = db.Column(db.String(20), default='')  # 强制报废期
    insurance_expiry = db.Column(db.Date, nullable=True)  # 保险到期日期
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'plate_number': self.plate_number,
            'capacity': self.capacity or '',
            'vehicle_type': self.vehicle_type or '',
            'company': getattr(self, 'company', '') or '',
            'status': self.status,
            'registration_date': self.registration_date.strftime('%Y-%m-%d') if self.registration_date else '',
            'issue_date': self.issue_date.strftime('%Y-%m-%d') if self.issue_date else '',
            'usage_type': self.usage_type or '',
            'brand_model': self.brand_model or '',
            'inspection_expiry': self.inspection_expiry.strftime('%Y-%m-%d') if self.inspection_expiry else '',
            'scrap_date': self.scrap_date or '',
            'insurance_expiry': self.insurance_expiry.strftime('%Y-%m-%d') if self.insurance_expiry else '',
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
    wx_userid = db.Column(db.String(64), default='')  # 企业微信用户ID（内部员工或外部联系人）
    wx_sender = db.Column(db.String(64), default='')  # 外部联系人消息发送人（内部员工UserID）
    external_corp_name = db.Column(db.String(100), default='')  # 企业微信外部联系人所属公司
    created_at = db.Column(db.DateTime, default=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'client_id': self.client_id,
            'name': self.name,
            'phone': self.phone,
            'wx_userid': self.wx_userid,
            'wx_sender': self.wx_sender,
            'external_corp_name': self.external_corp_name
        }


class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_no = db.Column(db.String(50), unique=True, default='')  # 任务编号
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
    remark = db.Column(db.Text, default='')  # 备注
    is_paid = db.Column(db.Boolean, default=False)  # 是否已收款
    paid_date = db.Column(db.DateTime, nullable=True)  # 收款日期
    paid_method = db.Column(db.String(20), default='')  # 收款方式：转账/二维码/现金
    invoice_type = db.Column(db.String(30), default='')  # 发票类型：增值税普通发票/增值税专用发票/收据
    invoice_no = db.Column(db.String(50), default='')  # 发票号码
    invoice_amount = db.Column(db.Float, default=0)  # 发票金额
    invoice_date = db.Column(db.DateTime, nullable=True)  # 开票日期
    invoice_remark = db.Column(db.Text, default='')  # 发票备注
    status = db.Column(db.String(20), default='pending')  # pending, scheduled, completed, cancelled
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
        except (json.JSONDecodeError, ValueError):
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

    # 排班确认状态
    schedule_confirm_status = db.Column(db.String(20), default='')  # 空=未推送, pending=待确认, confirmed=已确认, rejected=已拒绝

    def to_dict(self):
        return {
            'id': self.id,
            'task_no': self.task_no or '',
            'client_type': self.client_type,
            'client_name': self.client_name,
            'client_phone': self.client_phone,
            'client_id': self.client_id,
            'client_company': self.client.name if self.client else None,
            'contact_id': self.contact_id,
            'contact_name': self.contact.name if self.contact else '',
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
            'remark': self.remark or '',
            'is_paid': self.is_paid,
            'paid_date': self.paid_date.strftime('%Y-%m-%d') if self.paid_date else None,
            'paid_method': self.paid_method or '',
            'invoice_type': self.invoice_type or '',
            'invoice_no': self.invoice_no or '',
            'invoice_amount': self.invoice_amount,
            'invoice_date': self.invoice_date.strftime('%Y-%m-%d') if self.invoice_date else None,
            'invoice_remark': self.invoice_remark or '',
            'status': self.status,
            'yzj_approval_status': getattr(self, 'yzj_approval_status', ''),
            'yzj_serial': getattr(self, 'yzj_serial', ''),
            'schedule_confirm_status': self.schedule_confirm_status or '',
            'change_log': self.get_change_log(),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class ScheduleConfirmation(db.Model):
    """排班确认记录表"""
    __tablename__ = 'schedule_confirmations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    customer_name = db.Column(db.String(100), default='')
    customer_phone = db.Column(db.String(20), default='')
    contact_id = db.Column(db.Integer, db.ForeignKey('client_contacts.id'), nullable=True)

    # 企业微信相关
    wx_userid = db.Column(db.String(64), default='')
    wx_openid = db.Column(db.String(64), default='')
    wx_corp_id = db.Column(db.String(64), default='')
    wx_sender = db.Column(db.String(64), default='')  # 外部联系人消息发送人

    # 确认信息
    confirm_token = db.Column(db.String(64), unique=True, nullable=False)
    confirm_status = db.Column(db.String(20), default='pending')  # pending/confirmed/rejected
    confirm_time = db.Column(db.DateTime, nullable=True)
    confirm_ip = db.Column(db.String(45), default='')
    confirm_device = db.Column(db.String(500), default='')
    confirm_remark = db.Column(db.Text, default='')

    # 消息推送记录
    msg_id = db.Column(db.String(64), default='')
    push_time = db.Column(db.DateTime, nullable=True)
    push_status = db.Column(db.String(20), default='pending')  # pending/success/failed
    push_error = db.Column(db.Text, default='')

    # 审计字段
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # 关系
    task = db.relationship('Task', backref='confirmations')
    customer = db.relationship('Client', backref='confirmations')
    contact = db.relationship('ClientContact', backref='confirmations')
    creator = db.relationship('User', backref='created_confirmations')

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'customer_phone': self.customer_phone,
            'contact_id': self.contact_id,
            'wx_userid': self.wx_userid,
            'wx_openid': self.wx_openid,
            'wx_sender': self.wx_sender,
            'confirm_token': self.confirm_token,
            'confirm_status': self.confirm_status,
            'confirm_time': self.confirm_time.strftime('%Y-%m-%d %H:%M:%S') if self.confirm_time else None,
            'confirm_ip': self.confirm_ip,
            'confirm_remark': self.confirm_remark,
            'msg_id': self.msg_id,
            'push_time': self.push_time.strftime('%Y-%m-%d %H:%M:%S') if self.push_time else None,
            'push_status': self.push_status,
            'push_error': self.push_error,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None,
            'created_by': self.created_by,
            'created_by_name': self.creator.username if self.creator else None,
            # 关联任务信息
            'task_no': self.task.task_no if self.task else None,
            'departure': self.task.departure if self.task else None,
            'destination': self.task.destination if self.task else None,
            'departure_time': self.task.departure_time.strftime('%Y-%m-%d %H:%M') if self.task and self.task.departure_time else None,
        }


class ConfirmationSnapshot(db.Model):
    """确认快照表 - 存储确认时的完整数据快照"""
    __tablename__ = 'confirmation_snapshots'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    confirmation_id = db.Column(db.Integer, db.ForeignKey('schedule_confirmations.id'), nullable=False)
    snapshot_type = db.Column(db.String(20))  # task/customer/vehicle/driver
    snapshot_data = db.Column(db.Text, nullable=False)  # JSON格式
    created_at = db.Column(db.DateTime, default=datetime.now)

    confirmation = db.relationship('ScheduleConfirmation', backref='snapshots')

    def to_dict(self):
        return {
            'id': self.id,
            'confirmation_id': self.confirmation_id,
            'snapshot_type': self.snapshot_type,
            'snapshot_data': self.snapshot_data,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class LongRentalContract(db.Model):
    """长租合同"""
    __tablename__ = 'long_rental_contracts'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contract_no = db.Column(db.String(50), unique=True, default='')
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    client_name = db.Column(db.String(100), default='')
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('drivers.id'), nullable=True)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    monthly_rental_fee = db.Column(db.Float, default=0)
    remark = db.Column(db.Text, default='')
    status = db.Column(db.String(20), default='active')  # active / expired / terminated
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    client = db.relationship('Client', backref='long_contracts')
    vehicle = db.relationship('Vehicle', backref='long_contracts')
    driver = db.relationship('Driver', backref='long_contracts')

    def to_dict(self):
        return {
            'id': self.id,
            'contract_no': self.contract_no or '',
            'client_id': self.client_id,
            'client_name': self.client.name if self.client else self.client_name,
            'vehicle_id': self.vehicle_id,
            'vehicle_plate': self.vehicle.plate_number if self.vehicle else '',
            'vehicle_type': self.vehicle.vehicle_type if self.vehicle else '',
            'driver_id': self.driver_id,
            'driver_name': self.driver.name if self.driver else '',
            'driver_phone': self.driver.phone if self.driver else '',
            'start_date': self.start_date.strftime('%Y-%m-%d') if self.start_date else '',
            'end_date': self.end_date.strftime('%Y-%m-%d') if self.end_date else '',
            'monthly_rental_fee': self.monthly_rental_fee,
            'remark': self.remark or '',
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class LongRentalBill(db.Model):
    """长租月度账单"""
    __tablename__ = 'long_rental_bills'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    contract_id = db.Column(db.Integer, db.ForeignKey('long_rental_contracts.id'), nullable=False)
    bill_month = db.Column(db.String(7), nullable=False)  # 格式 2026-06
    rental_fee = db.Column(db.Float, default=0)
    fuel_fee = db.Column(db.Float, default=0)
    bridge_fee = db.Column(db.Float, default=0)
    other_fee = db.Column(db.Float, default=0)
    total_amount = db.Column(db.Float, default=0)
    is_paid = db.Column(db.Boolean, default=False)
    paid_date = db.Column(db.Date, nullable=True)
    paid_method = db.Column(db.String(20), default='')
    remark = db.Column(db.Text, default='')
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    contract = db.relationship('LongRentalContract', backref='bills')

    def to_dict(self):
        return {
            'id': self.id,
            'contract_id': self.contract_id,
            'bill_month': self.bill_month,
            'rental_fee': self.rental_fee,
            'fuel_fee': self.fuel_fee,
            'bridge_fee': self.bridge_fee,
            'other_fee': self.other_fee,
            'total_amount': self.total_amount,
            'is_paid': self.is_paid,
            'paid_date': self.paid_date.strftime('%Y-%m-%d') if self.paid_date else None,
            'paid_method': self.paid_method or '',
            'remark': self.remark or '',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class SystemConfig(db.Model):
    __tablename__ = 'system_config'
    key = db.Column(db.String(50), primary_key=True)
    value = db.Column(db.Text, default='')

    @staticmethod
    def get(key, default=None):
        cfg = SystemConfig.query.get(key)
        return cfg.value if cfg else default

    @staticmethod
    def set(key, value):
        cfg = SystemConfig.query.get(key)
        if cfg:
            cfg.value = value
        else:
            cfg = SystemConfig(key=key, value=value)
            db.session.add(cfg)
        db.session.commit()
