# LikeGirl · 两个人的小世界

参考 [Cleanwn/LikeGirl](https://github.com/Cleanwn/LikeGirl)，使用 **Vue 3 + TypeScript + FastAPI + SQLAlchemy + MySQL 8.4 + Docker Compose** 重写。没有 PHP 文件，也不依赖 PHP、Apache 或原版安装器。

## 已实现

- 首页：原站插画封面、双人头像、爱心、波浪、实时相恋计时、六个功能入口与最新故事。
- 点点滴滴：故事列表、详情、封面、作者、日期、草稿与发布。
- 走过的地方：在本地中国地图点亮到访的省份和城市，按城市收藏地点、日期、照片和旅行手记。
- 恋爱相册：分页加载、图片预览、日期与拍摄地点。
- 恋爱清单：已完成 / 待实现筛选、进度、完成日期与纪念照片。
- 纪念日：支持单次日期或每年重复，按北京时间显示已经过去的天数和下一次纪念倒计时；2 月 29 日在平年按 2 月 28 日纪念。
- 邮箱提醒：每个纪念日前两个自然日的北京时间 09:00 起，后端每分钟检查一次，并向情侣配置中的双方 QQ 邮箱分别发信。相同邮箱只收一封。当天稍晚新增日期、启动服务或启用邮箱，也会在当日补发。服务需运行且系统邮箱已启用。明确失败的投递当日每小时可重试，提交结果不明时避免重复发送。可在「邮箱配置 → 最近投递与配置记录」查看结果。
- 关于我们：可在后台编辑的分步对话。
- 管理后台：登录、内容增删改查、小站设置、头像与封面上传、修改密码、退出登录。
- 内容填写弹窗：自动保存本浏览器草稿，误点外部、关闭弹窗或刷新后重新打开可继续填写；按管理员、栏目和记录分别保留，保存成功或确认放弃后清除。
- Argon2 密码哈希、HttpOnly Cookie、JWT 会话撤销、写入来源校验、上传图片解码后重编码。
- 移动端布局、键盘操作、可见焦点、原生对话框、减少动态效果支持。

## Docker 启动（推荐，使用 MySQL）

需要 Docker Desktop / Docker Engine + Compose，以及用于生成配置的 Python 3.12+。

```powershell
python scripts/configure.py
docker compose up -d --build
docker compose ps
```

访问：

- 小站：http://localhost:8080
- 管理：http://localhost:8080/admin
- API 文档：http://localhost:8080/api/docs；接口定义：http://localhost:8080/api/openapi.json
- 健康检查：http://localhost:8080/api/health
- 当前部署源码：http://localhost:8080/source.tar.gz

初始账号：`admin`。**初始密码在自动生成的 `.env` 文件的 `ADMIN_PASSWORD` 中**，不是固定密码。脚本不会覆盖现有 `.env`。在管理后台“账号安全”中可以修改密码，修改后旧会话失效。

首次启动创建表、初始化管理员和站点设置。默认放入少量明确的演示内容；空白安装请在首次启动前设置 `SEED_DEMO=false`。种子数据只在首次创建站点设置时写入，不会在每次重启时恢复已删除的示例。

Docker 服务与持久化：

| 服务 | 用途 | 对外端口 / 持久化 |
| --- | --- | --- |
| web | Nginx 托管 Vue 静态文件，代理 API 和图片 | 默认 8080 |
| api | FastAPI + Alembic 数据库迁移 | 不直接暴露端口；`uploads` 数据卷 |
| db | MySQL 8.4，utf8mb4 | 不直接暴露端口；`mysql_data` 数据卷 |

数据库就绪后才启动 API，API 健康后才启动前端。`docker compose down` 保留数据卷，**不要使用 `down -v`，除非确实要删除全部数据**。

## 配置与上线

运行 `python scripts/configure.py` 会在项目根目录生成本机专用的 `.env` 和随机密码。环境文件、上传的相册照片和数据库备份均在 Git 忽略规则内。

- `APP_PORT`：本机映射端口，默认 8080。
- `CORS_ORIGINS`：允许提交的完整来源列表（协议、域名、端口），上线时加入自己的域名；修改端口时也要同步更新。只列出实际使用的来源。
- `COOKIE_SECURE`：HTTPS 部署设为 `true`；本机 HTTP 测试保持 `false`。
- `ADMIN_USERNAME` / `ADMIN_PASSWORD`：仅用于首次创建管理员；已有管理员的密码在后台修改，改变环境变量不会重置数据库中的密码。
- `MYSQL_*`：首次初始化数据库时使用；已有数据卷的数据库密码不能只通过修改 `.env` 更换，需要同时更改 MySQL 用户密码。
- `SECRET_KEY`：随机会话密钥，更换后全部登录失效。
- `SOURCE_URL`：部署源码地址，默认 `/source.tar.gz`，Docker 构建会生成此文件。

域名上线时，在前方使用 HTTPS 反向代理转发到 web 服务。Nginx 只信任自己设置的访客地址；API 容器不要直接映射到公网。当前频率限制在单个 API 进程内实现，适合个人小站；扩展多个进程或实例时应改为 Redis 共享限流。

后台可修改双方姓名、头像、相恋起点（北京时间）、封面、对话内容、备案号、页脚。故事正文使用纯文本，保留换行，避免运行任意 HTML / JS。图片支持 JPG / PNG / WebP，最大 8MB、2500 万像素，转换为不含原始 EXIF 的 WebP，最长边压到 2560 像素。后台删除内容不自动删除上传文件，避免误删其他记录仍在使用的图片。

## 本地开发

前端需要 Node.js 24，后端需要 Python 3.12+。生产部署默认 MySQL，不会自动退回 SQLite。

若已有 `.env`，保留其中的密码和密钥。通过 `DATABASE_URL` 显式指定自己的开发 MySQL：

```dotenv
DATABASE_URL=mysql+pymysql://用户名:URL编码后的密码@127.0.0.1:3306/likegirl_dev?charset=utf8mb4
```

没有本机 MySQL 时，可在全新项目运行 `python scripts/configure.py --local`，显式启用 SQLite 开发；已有 `.env` 则手动加 `DATABASE_URL=sqlite:///./likegirl.db`。Docker Compose 始终覆盖这个值并使用 MySQL。

后端（Windows PowerShell，从项目根目录）：

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r backend/requirements.txt
cd backend
../.venv/Scripts/python -m alembic upgrade head
../.venv/Scripts/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

新终端启动前端：

```powershell
cd frontend
npm ci
npm run dev
```

前端 http://localhost:5173，后端文档 http://127.0.0.1:8000/api/docs。Vite 代理 `/api` 和 `/uploads`，无需跨端口保存 Cookie。本地开发不生成源码归档；需要测试源码下载时使用 Docker 构建。

## 验证

```powershell
# 在 backend 目录执行；测试使用独立内存数据库，不触碰站点数据
../.venv/Scripts/python -m pytest -q

# 在 frontend 目录执行：TypeScript 检查与生产构建
npm run build

# 在项目根目录、Docker 服务启动后执行：真实 MySQL / Nginx / FastAPI 联调
python scripts/smoke.py
```

联调脚本从 `.env` 读取初始管理员密码；如果你已经通过后台改过密码，请设置环境变量 `SMOKE_ADMIN_PASSWORD` 为当前密码再运行。脚本创建随机名称的测试记录，检查并删除这些记录，不删除其他内容，不修改站点设置。

## 数据备份

至少备份 MySQL 和图片两个数据卷。建议在维护窗口进行一致性备份：

```powershell
docker compose stop api web
docker compose exec -T db sh -c 'MYSQL_PWD="$MYSQL_ROOT_PASSWORD" mysqldump -uroot --single-transaction --default-character-set=utf8mb4 "$MYSQL_DATABASE" > /tmp/likegirl.sql'
docker compose cp db:/tmp/likegirl.sql ./likegirl-backup.sql
docker compose cp api:/app/uploads ./uploads-backup
docker compose start api web
```

恢复请先在新数据库实例导入 SQL，并恢复图片文件；不要在未备份的现有站点上尝试恢复。妥善保存备份，其中包含私密内容和密码哈希。

## 项目结构

```text
backend/app/          FastAPI 路由、模型、校验、鉴权和种子数据
backend/migrations/  Alembic 版本化数据库迁移
backend/tests/       后端行为与安全边界测试
frontend/src/        Vue 3 页面、组件和样式
frontend/public/     本地静态资源
scripts/             配置生成与 Docker 联调
compose.yaml         Nginx + FastAPI + MySQL
NOTICE.md            原项目作者、资源来源与许可说明
```

后台「基本设置 → 情侣配置」支持双方昵称、QQ 号和相恋时间。输入 5–11 位 QQ 号即可预览 QQ 头像，保存后同步到首页。清空 QQ 号后使用自定义头像，图片加载失败时自动回退到备用或本地默认头像。

## 私密小站与 QQ 邮箱登录

小站默认需要登录，无注册入口。访客在 `/enter` 输入后台配置的男主或女主 QQ 号对应的 `@qq.com` 邮箱，通过验证码进入。未登录不能读取小站资料、文章、相册、心愿、足迹和纪念日、上传图片及源码下载。管理员保留 `/login` 的账号密码入口，用于管理设置；邮箱验证只授予浏览权限，不授予后台权限。

发件邮箱在后台「邮箱配置」管理。QQ 邮箱推荐 `smtp.qq.com`、端口 `465`、`SSL / TLS`。填写发件邮箱账号和 SMTP 授权码，保存后立即生效，无需重启。已有授权码不回显，留空保存会保留原值；更换发件账号时需要重新填写授权码。可以停用系统发送，停用后无法获取新的登录验证码。

首次部署也可在 `.env` 填写以下初始配置（请勿提交此文件）。首次启动会导入数据库；之后后台配置是唯一生效来源，重启不会用环境变量覆盖它：

```dotenv
SMTP_HOST=smtp.qq.com
SMTP_PORT=465
SMTP_SECURITY=ssl
SMTP_USERNAME=你的发件QQ号码@qq.com
SMTP_PASSWORD=QQ邮箱的SMTP授权码
SMTP_FROM=
```

发件邮箱需要开启 SMTP 服务。授权码不是 QQ 密码；发件地址留空时使用发件邮箱账号。收件邮箱来自情侣配置，SMTP 发件邮箱可以是另一个邮箱。没有有效邮件配置时，小站保持锁定，发送会提示失败，不会显示或返回验证码。

「登录邮件与测试」区域选择男主或女主邮箱，手动点击「发送测试邮件」会发送一封真实测试邮件；未保存修改时不能测试。测试不含登录验证码。最近 30 条投递与配置记录会显示发送结果和脱敏错误说明，邮箱地址脱敏，不记录授权码、验证码或正文。投递每次只尝试一次，失败由用户手动重试，避免网络超时时重复发信；测试每个管理员 5 分钟最多 3 次。

数据库中的 SMTP 授权码使用 Fernet 加密，密钥从服务端 `SECRET_KEY` 派生。备份和恢复时同时妥善保管 `.env` 和数据库。更换 `SECRET_KEY` 后必须在后台重新填写授权码；不能使用旧密钥加密的数据。API 校验错误也不会回显原始输入。

验证码 6 位、5 分钟有效、单次使用；每个邮箱间隔 60 秒发送，每小时最多 5 次，每个验证码最多验证错误 5 次，另有 IP 频率限制。数据库只保存验证码摘要和登录令牌摘要。登录有效期 12 小时，使用 HttpOnly / SameSite Cookie；退出时服务端撤销令牌，修改任一情侣 QQ 号会撤销已有情侣登录和验证码。部署 HTTPS 时设置 `COOKIE_SECURE=true`。

私人照片请使用后台上传，让本站的访问校验保护原图；外部图片地址仍由对应图片服务控制访问。登录页不读取情侣昵称、QQ 号、纪念日或照片。测试邮件发送使用 mock，不读取真实 SMTP 密钥、不对外投递。

原作者 **Ki.**，参考仓库 **Cleanwn/LikeGirl**。保留资源归属，使用 AGPL-3.0；完整许可见 LICENSE，具体复用资源见 NOTICE.md。当前实现没有移植原版第三方图床、Live2D、音乐播放器和 IP 地域查询。
