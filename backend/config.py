import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'charter-bus-scheduling-secret-2024')
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:a26348464@113.107.137.103:1024/charter_bus'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 连接池：空闲超时自动断开重连，避免长时间不操作后查询报500
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 300,       # 连接最多存活5分钟，超时自动回收
        'pool_pre_ping': True,     # 每次取连接前先 ping，断开则自动重连
        'pool_timeout': 10,        # 获取连接超时10秒
    }

    # 云之家审批配置
    YUNZHIJIA_APP_ID = 'SP11228529'
    YUNZHIJIA_EID = '11228529'
    YUNZHIJIA_SECRET = 'z69nc1A9qyCXGugKYV49vvzUMElCAK'
    YUNZHIJIA_HOST = 'https://www.yunzhijia.com'
    YUNZHIJIA_TOKEN_URL = 'https://yunzhijia.com/gateway/oauth2/token/getAccessToken'
    YUNZHIJIA_FORM_CODE_ID = '0e1d321692a9441fa24db3bb3776a7d9'
    YUNZHIJIA_CREATOR_OPENID = '5b078855e4b098424c8c3f7f'
    # 回调解密配置（从云之家开发者后台获取）
    YUNZHIJIA_CALLBACK_TOKEN = ''  # 回调Token
    YUNZHIJIA_CALLBACK_AES_KEY = 'FB5daoyipm49K58y'  # 开发者key（16位）

    # 企业微信配置
    WX_WORK_CORP_ID = os.environ.get('WX_WORK_CORP_ID', 'ww856b23e58ff4738f')  # 企业ID
    WX_WORK_AGENT_ID = os.environ.get('WX_WORK_AGENT_ID', '1000002')  # 应用AgentId
    WX_WORK_SECRET = os.environ.get('WX_WORK_SECRET', 'sKmi2wUiRKXwMf694hJYGf14lcX6PdtibKEvYu1YycQ')  # 应用Secret

    # 确认页面域名（公网访问地址）
    CONFIRM_BASE_URL = os.environ.get('CONFIRM_BASE_URL', 'http://www.dzcz.top:8008')
