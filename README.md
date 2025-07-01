### ✅ 第一步：Fork 本仓库

打开本项目页面
点击右上角 Fork 按钮（复制到你自己的 GitHub 账号下）

### ✅ 第二步：设置变量

回到你的 GitHub 仓库页面 → 点上方 Settings → 左侧 Secrets and variables → Actions→ 点 New repository secret：

Name: IKUUU_EMAIL
Value: 这里填你的IKUUU账号
Name: IKUUU_PASSWORD
Value: 这里填你的IKUUU密码


下面为企业微信消息推送（选填）
Name: WX_AGENTID
Value:填你的企业微信应用ID

Name: WX_CORPID
Value:填你的企业微信ID

Name: WX_CORPSECRET
Value:填你的企业微信应用密钥


### ✅ 第三步：测试运行

点击上方 Actions

首次 Fork 在 Actions 页面点击 Enable workflows 以启用自动任务。

选择 Auto Sign-in for BBS

点击右侧 Run workflow → 等待运行完成
