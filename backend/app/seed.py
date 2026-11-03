from datetime import date

from sqlalchemy import select

from .config import settings
from .database import SessionLocal
from .models import Article, Gift, MailSettings, Photo, SiteSettings, User, Wish
from .secrets import encrypt_secret
from .security import password_hash


def seed():
    with SessionLocal() as db:
        if not db.get(MailSettings, 1):
            db.add(
                MailSettings(
                    id=1,
                    host=settings.smtp_host,
                    port=settings.smtp_port,
                    username=settings.smtp_username,
                    from_address=settings.smtp_from,
                    security=settings.smtp_security,
                    encrypted_password=encrypt_secret(settings.smtp_password),
                )
            )
        if not db.scalar(select(User).limit(1)):
            db.add(
                User(
                    username=settings.admin_username,
                    password_hash=password_hash.hash(settings.admin_password),
                )
            )
        if not db.get(SiteSettings, 1):
            db.add(SiteSettings(id=1))
            if settings.seed_demo:
                db.add_all(
                    [
                        Article(
                            title="把平凡的日子，过成我们的纪念日",
                            content="今天没有特别的安排，只是一起吃了晚饭，沿着熟悉的小路散步。\n\n你突然说，今天的晚霞真好看。我转过头，觉得身边的人比晚霞还要温柔。\n\n原来值得记录的，从来不只是盛大的瞬间。还有每一个，有你在身边的普通日子。",
                            author="小满",
                            date=date(2024, 6, 1),
                            cover="/images/cover.png",
                        ),
                        Article(
                            title="你好呀，我的全世界",
                            content="想了很久，要用什么方式收藏我们的故事。\n\n于是有了这个小站。一些碎碎念，一些照片，还有好多想和你一起完成的事。\n\n第一篇，就从这句开始吧：遇见你，真好。",
                            author="阿辰",
                            date=date(2024, 5, 20),
                        ),
                        Photo(
                            title="在街角，收藏一整个夏天",
                            image="/images/cover.png",
                            date=date(2024, 6, 1),
                            location="我们的第一站",
                        ),
                        Wish(
                            title="一起看一场日落",
                            completed=True,
                            date=date(2024, 5, 20),
                        ),
                        Wish(
                            title="一起漫无目的地散步",
                            completed=True,
                            date=date(2024, 6, 1),
                        ),
                        Wish(title="一起去海边，听风也听你"),
                        Wish(title="拍一组只属于我们的照片"),
                        Wish(title="一起做一顿有点笨拙的晚餐"),
                        Wish(title="写一封信，寄给未来的我们"),
                        Gift(
                            title="一封手写的信",
                            description="字迹有些歪歪扭扭，喜欢却认认真真。\n这是示例礼物，在后台换成你们的回忆吧。",
                            sender="阿辰",
                            date=date(2024, 5, 20),
                        ),
                    ]
                )
        db.commit()
