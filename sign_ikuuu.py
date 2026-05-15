from playwright.sync_api import sync_playwright
import requests
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

LOGIN_URL = 'https://ikuuu.win/auth/login'
CHECK_URL = 'https://ikuuu.win/user/checkin'


# ─────────────────────────────
# Playwright 登录
# ─────────────────────────────
def playwright_login(email, passwd):

    print(f'\n启动浏览器登录：{email}')

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )

        context = browser.new_context(
            user_agent=USER_AGENT,
            viewport={"width": 1280, "height": 800},
            locale="zh-CN"
        )

        # 去 webdriver 特征
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

        page = context.new_page()

        try:

            # 打开登录页
            print('打开登录页面...')
            page.goto(
                LOGIN_URL,
                wait_until='networkidle',
                timeout=60000
            )

            # 输入账号密码
            print('填写账号密码...')
            page.fill('#email', email)
            page.fill('#password', passwd)

            # 点击验证
            print('点击验证按钮...')

            try:
                page.click('.geetest_btn_click', timeout=10000)
                print('验证按钮点击成功')
            except:
                print('未找到验证按钮')

            time.sleep(2)

            # 点击登录
            print('点击登录按钮...')
            page.click('button[type="submit"]')

            # 等待登录成功
            print('等待登录成功...')

            try:

                page.wait_for_url(
                    lambda url: '/user' in url,
                    timeout=30000
                )

                print('登录成功，页面已跳转')

            except:
                print('未检测到页面跳转')

            time.sleep(3)

            # 获取 Cookie
            cookies = context.cookies()

            if not cookies:
                raise Exception('未获取到 Cookie')

            print(f'获取到 {len(cookies)} 个 Cookie')

            return cookies

        finally:

            browser.close()


# ─────────────────────────────
# 单账号签到
# ─────────────────────────────
def checkin_one_account(email, passwd):

    header = {
        'origin': 'https://ikuuu.win',
        'user-agent': USER_AGENT
    }

    try:

        # Playwright 登录
        pw_cookies = playwright_login(email, passwd)

        # requests session
        session = requests.session()

        # 导入 Cookie
        for c in pw_cookies:

            name = c.get('name')
            value = c.get('value')

            if name and value:
                session.cookies.set(name, value)

        # 开始签到
        print('开始签到...')

        resp = session.post(
            url=CHECK_URL,
            headers=header,
            timeout=20
        )

        print('签到接口返回：')
        print(resp.text)

        # JSON解析
        result = resp.json()

        content = result.get('msg', '未知结果')

        print(content)

        return f'✅ {email} -> {content}'

    except Exception as e:

        err = f'❌ {email} -> {str(e)}'

        print(err)

        return err


# ─────────────────────────────
# 主函数
# ─────────────────────────────
def handler(event=None, context=None):

    try:

        # 多账号
        # 格式：
        # aaa@qq.com:123456
        # bbb@qq.com:abcdef

        accounts_str = os.environ.get('ACCOUNTS') or '''
aaa@qq.com:123456
'''

        accounts = []

        for line in accounts_str.strip().splitlines():

            line = line.strip()

            if line and ':' in line:

                email, passwd = line.split(':', 1)

                accounts.append(
                    (email.strip(), passwd.strip())
                )

        if not accounts:
            raise Exception('未读取到账号')

        print(f'\n共发现 {len(accounts)} 个账号')

        all_result = []

        # 逐个账号签到
        for idx, (email, passwd) in enumerate(accounts, 1):

            print('\n' + '=' * 50)
            print(f'开始处理第 {idx} 个账号')
            print('=' * 50)

            result = checkin_one_account(email, passwd)

            all_result.append(result)

        # 汇总
        final_msg = '\n'.join(all_result)

        print('\n最终结果：')
        print(final_msg)

        # 企业微信通知
        send_wx(
            f"[ikuuu] 签到结果：\n{final_msg}",
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
