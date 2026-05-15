from playwright.sync_api import sync_playwright
import requests
import json
import os
import time
from wxmsg import send_wx

# 企业微信配置
corpid = os.environ.get('WX_CORPID') or ''
corpsecret = os.environ.get('WX_CORPSECRET') or ''
agentid = os.environ.get('WX_AGENTID') or ''

USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
    'AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/120.0.0.0 Safari/537.36'
)


def playwright_login(email, passwd):

    print('启动浏览器进行登录...')

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled'
            ]
        )

        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 800},
            locale="zh-CN"
        )

        # 隐藏自动化特征
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = context.new_page()

        # 打开登录页
        page.goto(
            'https://ikuuu.win/auth/login',
            wait_until='networkidle'
        )

        print('填写账号密码...')

        # 输入账号密码
        page.fill('#email', email)
        page.fill('#password', passwd)

        print('点击验证按钮...')

        # 点击 “点我开始验证”
        try:
            page.click('.geetest_btn_click', timeout=5000)
            print('验证按钮点击成功')
        except:
            print('未找到验证按钮，继续登录')

        time.sleep(2)

        print('点击登录按钮...')

        # 点击登录
        page.click('button[type="submit"]')

        # 等待跳转
        time.sleep(5)

        print('获取 Cookie...')

        # 获取浏览器 Cookie
        cookies = context.cookies()

        browser.close()

        return cookies


def handler(event=None, context=None):

    email = os.environ.get('IKUUU_EMAIL') or ''
    passwd = os.environ.get('IKUUU_PASSWORD') or ''

    check_url = 'https://ikuuu.win/user/checkin'

    header = {
        'origin': 'https://ikuuu.win',
        'user-agent': USER_AGENT
    }

    try:

        # ───────────── 登录获取 Cookie ─────────────
        pw_cookies = playwright_login(email, passwd)

        if not pw_cookies:
            raise Exception('未获取到 Cookie')

        print('创建 requests session...')

        session = requests.session()

        # 把 Playwright Cookie 导入 requests
        for c in pw_cookies:

            name = c.get('name')
            value = c.get('value')

            if name and value:
                session.cookies.set(name, value)

        print('开始签到...')

        # requests 执行签到
        result = session.post(
            url=check_url,
            headers=header,
            timeout=20
        ).json()

        print(result)

        content = result.get('msg', '未知结果')

        print(content)

        # 企业微信通知
        send_wx(
            f"[ikuuu] 签到结果：{content}",
            corpid,
            corpsecret,
            agentid
        )

    except Exception as e:

        content = f'签到失败：{str(e)}'

        print(content)

        send_wx(
            f"[ikuuu] 签到结果：{content}",
            corpid,
            corpsecret,
            agentid
        )

    return '任务完成'


if __name__ == "__main__":
    handler()
