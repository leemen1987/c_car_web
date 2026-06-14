"""
企业微信工具模块
提供企业微信API调用功能
"""

import json
import time
import hashlib
import urllib.request
import urllib.error
from datetime import datetime, timedelta


class WxWorkClient:
    """企业微信客户端"""

    def __init__(self, corp_id, agent_id, secret):
        self.corp_id = corp_id
        self.agent_id = agent_id
        self.secret = secret
        self._access_token = None
        self._token_expires_at = 0

    def get_access_token(self):
        """获取access_token，带缓存"""
        # 检查缓存是否有效（提前5分钟过期）
        if self._access_token and time.time() < self._token_expires_at - 300:
            return self._access_token

        url = f'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={self.corp_id}&corpsecret={self.secret}'

        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

                if data.get('errcode') == 0:
                    self._access_token = data['access_token']
                    self._token_expires_at = time.time() + data.get('expires_in', 7200)
                    return self._access_token
                else:
                    raise Exception(f"获取access_token失败: {data.get('errmsg', '未知错误')}")
        except Exception as e:
            raise Exception(f"请求access_token异常: {str(e)}")

    def send_text_message(self, userid, content):
        """发送文本消息"""
        token = self.get_access_token()
        url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}'

        data = {
            "touser": userid,
            "msgtype": "text",
            "agentid": self.agent_id,
            "text": {
                "content": content
            }
        }

        return self._post_request(url, data)

    def send_textcard_message(self, userid, title, description, url, btntxt="详情"):
        """发送文本卡片消息（内部员工）"""
        token = self.get_access_token()
        api_url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}'

        data = {
            "touser": userid,
            "msgtype": "textcard",
            "agentid": self.agent_id,
            "textcard": {
                "title": title,
                "description": description,
                "url": url,
                "btntxt": btntxt
            }
        }

        return self._post_request(api_url, data)

    def send_external_link_message(self, external_userid, sender, title, description, url, picurl=''):
        """发送链接消息给外部联系人（微信客户）

        API文档: https://developer.work.weixin.qq.com/document/path/95818
        """
        token = self.get_access_token()
        api_url = f'https://qyapi.weixin.qq.com/cgi-bin/externalcontact/message/send?access_token={token}'

        data = {
            "chat_type": "single",
            "external_userid": [external_userid],
            "sender": sender,
            "text": {
                "content": f"📋 任务确认通知\n{description}\n请点击查看详情"
            },
            "link": {
                "title": title,
                "description": description,
                "url": url,
            }
        }
        if picurl:
            data["link"]["picurl"] = picurl

        try:
            json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(
                api_url,
                data=json_data,
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))

                if result.get('errcode') == 0:
                    return {
                        'success': True,
                        'errcode': 0,
                        'errmsg': 'ok',
                        'msgid': result.get('msgid', '')
                    }
                else:
                    return {
                        'success': False,
                        'errcode': result.get('errcode'),
                        'errmsg': result.get('errmsg', '未知错误')
                    }
        except urllib.error.HTTPError as e:
            body = ''
            try:
                body = e.read().decode('utf-8')
            except:
                pass
            return {
                'success': False,
                'errcode': e.code,
                'errmsg': f'HTTP {e.code}: {body}'
            }
        except Exception as e:
            return {
                'success': False,
                'errcode': -1,
                'errmsg': str(e)
            }

    def get_external_contacts(self, userid, cursor='', limit=100):
        """获取指定员工的外部联系人列表"""
        token = self.get_access_token()
        url = f'https://qyapi.weixin.qq.com/cgi-bin/externalcontact/list?userid={userid}&access_token={token}'

        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

                if data.get('errcode') == 0:
                    return {
                        'success': True,
                        'external_userid': data.get('external_userid', []),
                    }
                else:
                    return {
                        'success': False,
                        'errmsg': data.get('errmsg', '获取外部联系人失败')
                    }
        except Exception as e:
            return {
                'success': False,
                'errmsg': str(e)
            }

    def get_external_contact_detail(self, external_userid):
        """获取外部联系人详情"""
        token = self.get_access_token()
        url = f'https://qyapi.weixin.qq.com/cgi-bin/externalcontact/get?external_userid={external_userid}&access_token={token}'

        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))

                if data.get('errcode') == 0:
                    external_contact = data.get('external_contact', {})
                    return {
                        'success': True,
                        'external_userid': external_contact.get('external_userid', ''),
                        'name': external_contact.get('name', ''),
                        'avatar': external_contact.get('avatar', ''),
                        'corp_name': external_contact.get('corp_name', ''),
                        'corp_full_name': external_contact.get('corp_full_name', ''),
                        'follow_user': data.get('follow_user', []),
                    }
                else:
                    return {
                        'success': False,
                        'errmsg': data.get('errmsg', '获取外部联系人详情失败')
                    }
        except Exception as e:
            return {
                'success': False,
                'errmsg': str(e)
            }

    def send_markdown_message(self, userid, content):
        """发送Markdown消息"""
        token = self.get_access_token()
        url = f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}'

        data = {
            "touser": userid,
            "msgtype": "markdown",
            "agentid": self.agent_id,
            "markdown": {
                "content": content
            }
        }

        return self._post_request(url, data)

    def _post_request(self, url, data):
        """发送POST请求"""
        try:
            json_data = json.dumps(data, ensure_ascii=False).encode('utf-8')
            req = urllib.request.Request(
                url,
                data=json_data,
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read().decode('utf-8'))

                if result.get('errcode') == 0:
                    return {
                        'success': True,
                        'errcode': 0,
                        'errmsg': 'ok',
                        'msgid': result.get('msgid', '')
                    }
                else:
                    return {
                        'success': False,
                        'errcode': result.get('errcode'),
                        'errmsg': result.get('errmsg', '未知错误')
                    }
        except Exception as e:
            return {
                'success': False,
                'errcode': -1,
                'errmsg': str(e)
            }


def create_wx_work_client(config):
    """从配置创建企业微信客户端"""
    return WxWorkClient(
        corp_id=config.get('WX_WORK_CORP_ID', ''),
        agent_id=config.get('WX_WORK_AGENT_ID', ''),
        secret=config.get('WX_WORK_SECRET', '')
    )


def format_confirm_message(task_info, confirm_url):
    """格式化确认消息内容"""
    title = "任务确认通知"

    description = f"""<div class="gray">任务编号：{task_info.get('task_no', '')}</div>
<div class="normal">出车时间：{task_info.get('departure_time', '')}</div>
<div class="normal">出发地：{task_info.get('departure', '')}</div>
<div class="normal">目的地：{task_info.get('destination', '')}</div>
<div class="normal">车辆类型：{task_info.get('vehicle_type', '')}</div>
<div class="highlight">请点击确认任务</div>"""

    return {
        'title': title,
        'description': description,
        'url': confirm_url,
        'btntxt': '确认任务'
    }


def format_external_confirm_message(task_info, confirm_url):
    """格式化外部联系人确认消息内容（链接消息格式）"""
    title = "任务确认通知"
    lines = []
    if task_info.get('task_no'):
        lines.append(f"任务编号：{task_info['task_no']}")
    if task_info.get('departure_time'):
        lines.append(f"出车时间：{task_info['departure_time']}")
    if task_info.get('departure'):
        lines.append(f"出发地：{task_info['departure']}")
    if task_info.get('destination'):
        lines.append(f"目的地：{task_info['destination']}")
    if task_info.get('vehicle_type'):
        lines.append(f"车辆类型：{task_info['vehicle_type']}")
    lines.append("请点击查看详情并确认任务")
    description = '\n'.join(lines)

    return {
        'title': title,
        'description': description,
        'url': confirm_url
    }


def get_oauth_url(corp_id, agent_id, redirect_uri, state=''):
    """获取企业微信OAuth2授权URL"""
    import urllib.parse
    params = {
        'appid': corp_id,
        'agentid': agent_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'snsapi_base',
        'state': state
    }
    url = 'https://open.weixin.qq.com/connect/oauth2/authorize?' + urllib.parse.urlencode(params) + '#wechat_redirect'
    return url


def get_userinfo_by_code(client, code):
    """通过OAuth2 code获取用户信息"""
    token = client.get_access_token()
    url = f'https://qyapi.weixin.qq.com/cgi-bin/auth/getuserinfo?access_token={token}&code={code}'

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

            if data.get('errcode') == 0:
                return {
                    'success': True,
                    'userid': data.get('userid', ''),
                    'user_ticket': data.get('user_ticket', ''),
                    'openid': data.get('openid', ''),
                }
            else:
                return {
                    'success': False,
                    'errmsg': data.get('errmsg', '获取用户信息失败')
                }
    except Exception as e:
        return {
            'success': False,
            'errmsg': str(e)
        }


def get_user_detail(client, userid):
    """获取用户详细信息（包括手机号）"""
    token = client.get_access_token()
    url = f'https://qyapi.weixin.qq.com/cgi-bin/user/get?access_token={token}&userid={userid}'

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))

            if data.get('errcode') == 0:
                return {
                    'success': True,
                    'userid': data.get('userid', ''),
                    'name': data.get('name', ''),
                    'mobile': data.get('mobile', ''),
                    'email': data.get('email', ''),
                    'avatar': data.get('avatar', ''),
                    'department': data.get('department', []),
                }
            else:
                return {
                    'success': False,
                    'errmsg': data.get('errmsg', '获取用户详情失败')
                }
    except Exception as e:
        return {
            'success': False,
            'errmsg': str(e)
        }
