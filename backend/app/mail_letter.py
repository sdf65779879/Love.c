from dataclasses import dataclass
from html import escape
from pathlib import Path
from string import Template

_TEMPLATE = Template(
    (Path(__file__).parent / "templates" / "letter.html").read_text(encoding="utf-8")
)


@dataclass(frozen=True)
class Letter:
    text: str
    html: str


def couple_letter(name: str, *, code: str | None = None) -> Letter:
    greeting = f"亲爱的{name}，" if name else "亲爱的你，"
    if code is not None:
        heading = "给你留了盏灯。"
        preview = "一封来自 LOVE.C 的回家小笺，登录验证码在信里。"
        note = "那些一起拍的照片，还有没讲完的小事，都在老地方等你。输入下面的验证码，就到家啦。"
        label, highlight, size = "登录验证码", code, "36px"
        detail = "5 分钟内有效 · 仅可使用一次"
        reminder = "如果这次登录不是你发起的，忽略这封信就好。请把验证码留给自己。"
    else:
        heading = "第一封信，寄给你。"
        preview = "这是我们小站寄出的测试来信。"
        note = "试着从我们的小站寄出一封信。你读到这里，我就知道，以后写给你的话，也能找到你了。"
        label, highlight, size = "邮箱投递测试", "见信如面", "24px"
        detail = "一封写给你的测试来信"
        reminder = "这次只是试寄，无需回复。下次登录时，验证码也会寄到这里。"
    text = f"{greeting}\n\n{heading}\n{note}\n\n{label}\n{highlight}\n{detail}\n\n{reminder}\n\n爱你的，我们的小站 · LOVE.C"
    html = _TEMPLATE.substitute(
        greeting=escape(greeting),
        heading=heading,
        note=note,
        label=label,
        highlight=escape(highlight),
        detail=detail,
        reminder=reminder,
        preview=preview,
        size=size,
    )
    return Letter(text, html)
