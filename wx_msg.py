# wx_msg.py
import requests

def send_wx(msg, corpid, corpsecret, agentid, touser='@all'):
    """
    发送企业微信消息

    :param msg: 消息内容
    :param corpid: 企业微信ID
    :param corpsecret: 应用密钥
    :param agentid: 应用ID
    :param touser: 接收者，默认为 @all
    :return: True 表示发送成功，False 表示失败
    """
    try:
        token_url = f'https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={corpid}&corpsecret={corpsecret}'
        token_resp = requests.get(token_url, timeout=5).json()
        access_token = token_resp['access_token']

        send_url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}"
        data = {
            "touser": touser,
            "msgtype": "text",
            "agentid": agentid,
            "text": {"content": msg},
            "safe": 0,
        }

        response = requests.post(send_url, json=data, timeout=9).json()
        print(f"[微信通知] {response}")
        return response.get('errcode') == 0 and response.get('errmsg') == 'ok'
    except Exception as e:
        print(f"[微信通知失败] {e}")
        return False
