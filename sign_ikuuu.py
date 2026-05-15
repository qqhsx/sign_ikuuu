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


# ─────────────────────────────
# 邮箱脱敏
# ─────────────────────────────
def mask_email(email):
    """
    abc123@gmail.com
    -> a****3@gmail.com
    """

    if '@' not in email:
        return email

    name, domain = email.split('@', 1)

    if len(name) <= 1:
        masked = name

    elif len(name) == 2:
        masked = name[0] + '*'

    else:
        masked = (
            name[0]
            + '*' * (len(name) - 2)
            + name[-1]
        )

    return f'{masked}@{domain}'


# ─────────────────────────────
# Playwright 登录获取 Cookie
# ─────────────────────────────
def playwright_login(email, passwd):

    safe_email = mask_email(email)

    print(f'\n启动浏览器进行登录：{safe_email}')

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


# ─────────────────────────────
# 单账号签到
# ─────────────────────────────
def checkin_one_account(email, passwd):

    safe_email = mask_email(email)

    check_url = 'https://ikuuu.win/user/checkin'

    header = {
        'origin': 'https://ikuuu.win',
        'user-agent': USER_AGENT
    }

    try:

        # 登录获取 Cookie
        pw_cookies = playwright_login(email, passwd)

        if not pw_cookies:
            raise Exception('未获取到 Cookie')

        print('创建 requests session...')

        session = requests.session()

        # 导入 Cookie
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

        return f'✅ {safe_email} -> {content}'

    except Exception as e:

        err = f'❌ {safe_email} -> {str(e)}'

        print(err)

        return err


# ─────────────────────────────
# 主函数
# ─────────────────────────────
def handler(event=None, context=None):

    try:

        # 多账号环境变量
        # 格式：
        # aaa@qq.com:123456
        # bbb@qq.com:abcdef

        accounts_str = os.environ.get('ACCOUNTS')

        if not accounts_str:
            raise Exception('未配置 ACCOUNTS 环境变量')

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
