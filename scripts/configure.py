"""Generate local configuration once. Never print credentials into logs."""

import argparse
import secrets
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description="初始化 LikeGirl 环境配置")
    parser.add_argument(
        "--local",
        action="store_true",
        help="显式使用 SQLite 本地开发；Docker 部署始终使用 MySQL",
    )
    args = parser.parse_args()
    target = ROOT / ".env"
    if target.exists():
        print(".env 已存在，未覆盖。请直接编辑现有配置。")
        return
    values = {
        "MYSQL_PASSWORD": secrets.token_urlsafe(24),
        "MYSQL_ROOT_PASSWORD": secrets.token_urlsafe(32),
        "SECRET_KEY": secrets.token_urlsafe(48),
        "ADMIN_PASSWORD": secrets.token_urlsafe(18),
    }
    defaults = {
        "APP_PORT": "8080",
        "MYSQL_DATABASE": "likegirl",
        "MYSQL_USER": "likegirl",
        "ADMIN_USERNAME": "admin",
        **values,
        "CORS_ORIGINS": "http://localhost:8080,http://127.0.0.1:8080,http://localhost:5173,http://127.0.0.1:5173",
        "COOKIE_SECURE": "false",
        "SEED_DEMO": "true",
        "SOURCE_URL": "/source.tar.gz",
        "SMTP_HOST": "smtp.qq.com",
        "SMTP_PORT": "465",
        "SMTP_SECURITY": "ssl",
        "SMTP_USERNAME": "",
        "SMTP_PASSWORD": "",
        "SMTP_FROM": "",
    }
    content = "".join(f"{key}={value}\n" for key, value in defaults.items())
    if args.local:
        content += "\n# Explicit local development database; Docker overrides this with MySQL.\nDATABASE_URL=sqlite:///./likegirl.db\n"
    target.write_text(content, encoding="utf-8")
    try:
        target.chmod(0o600)
    except OSError:
        pass
    print("已生成 .env。管理员账号为 admin，初始密码见 .env 中的 ADMIN_PASSWORD。")
    print(".env 已被 Git 和 Docker 构建上下文忽略，请妥善保管。")


if __name__ == "__main__":
    main()
