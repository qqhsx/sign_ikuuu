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
# Playwright 登录获取 Cookie
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

        # 隐藏自动化特征
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

            # 点击验证按钮
            print('点击验证按钮...')

            try:
                page.click('.geetest_btn_click', timeout=5000)
                print('验证按钮点击成功')
            except:
                print('未找到验证按钮，继续登录')

            time.sleep(2)

            # 点击登录
            print('点击登录按钮...')
            page.click('button[type="submit"]')

            # 等待登录
            time.sleep(5)

            # 获取 Cookie
            print('获取 Cookie...')
            cookies = context.cookies()

            if not cookies:
                raise Exception('未获取到 Cookie')

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

        # 创建 requests session
        print('创建 requests session...')
        session = requests.session()

        # 导入 Cookie
        for c in pw_cookies:

            name = c.get('name')
            value = c.get('value')

            if name and value:
                session.cookies.set(name, value)

        # 开始签到
        print('开始签到...')

        result = session.post(
            url=CHECK_URL,
            headers=header,
            timeout=20
        ).json()

        print(result)

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

        # 多账号环境变量
        # 格式：
        # 邮箱1:密码1
        # 邮箱2:密码2
        accounts_str = os.environ.get('ACCOUNTS')

        accounts = []

        # 优先使用多账号
        if accounts_str and accounts_str.strip():

            for line in accounts_str.strip().splitlines():

                line = line.strip()

                if line and ':' in line:

                    email, passwd = line.split(':', 1)

                    accounts.append(
                        (email.strip(), passwd.strip())
                    )

        else:

            # 兼容旧单账号模式
            email = os.environ.get('IKUUU_EMAIL') or ''
            passwd = os.environ.get('IKUUU_PASSWORD') or ''

            accounts.append((email, passwd))

        print(f'\n共发现 {len(accounts)} 个账号')

        all_result = []

        # 逐个账号签到
        for idx, (email, passwd) in enumerate(accounts, 1):

            print('\n' + '=' * 50)
            print(f'开始处理第 {idx} 个账号')
            print('=' * 50)

            result = checkin_one_account(email, passwd)

            all_result.append(result)

        # 汇总结果
        final_msg = '\n'.join(all_result)

        print('\n最终结果：')
        print(final_msg)

        # 企业微信通知
        send_wx(
            f"[ikuuu] 多账号签到结果：\n{final_msg}",
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
