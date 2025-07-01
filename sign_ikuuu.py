import requests
import json
import os
from wx_msg import send_wx  # 从外部模块引入

# 企业微信配置（你可以放环境变量里，这里为了方便测试直接写死）
corpid = os.environ.get('WX_CORPID') or ''       # 企业ID
corpsecret = os.environ.get('WX_CORPSECRET') or ''  # 应用密钥
agentid = os.environ.get('WX_AGENTID') or ''                # 应用ID


def handler(event=None, context=None):
    # 本地测试建议直接写账号密码（或保留 os.environ 也可以）
    email = os.environ.get('IKUUU_EMAIL') or ''
    passwd = os.environ.get('IKUUU_PASSWORD') or ''

    session = requests.session()

    login_url = 'https://ikuuu.one/auth/login'
    check_url = 'https://ikuuu.one/user/checkin'

    header = {
        'origin': 'https://ikuuu.one',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
    }

    data = {
        'email': email,
        'passwd': passwd
    }

    try:
        print('进行登录...')
        response = session.post(url=login_url, headers=header, data=data).json()
        print(response['msg'])

        # 进行签到
        result = session.post(url=check_url, headers=header).json()
        print(result['msg'])
        content = result['msg']

        # 调用 send_wx 通知结果
        send_wx(f"[ikuuu] 签到结果：{content}", corpid, corpsecret, agentid)
    except Exception as e:
        content = f'签到失败：{str(e)}'
        print(content)
        send_wx(f"[ikuuu] 签到结果：{content}", corpid, corpsecret, agentid)

    return '任务完成'

if __name__ == "__main__":
    handler()
