import datetime
import os
import sys
import urllib.parse
from typing import List

import requests


DEFAULT_DAILY_URL = "https://ruankaodaren.com/exam/#/answertest/answertest?reset=0&type=8"
DEFAULT_REDIRECT_BASE_URL = "https://liuxuisme.github.io/daily-soft-exam/go.html"
DEFAULT_EXAM_MONTH = 5
DEFAULT_EXAM_DAY = 24
DEFAULT_MESSAGE_STYLE = "link"


def parse_webhooks(raw: str) -> List[str]:
    return [item.strip() for item in raw.split(",") if item.strip()]


def parse_exam_date(today: datetime.date) -> datetime.date:
    # EXAM_DATE format: YYYY-MM-DD. Fallback to current year 05-24.
    exam_date_raw = os.getenv("EXAM_DATE", "").strip()
    if exam_date_raw:
        try:
            return datetime.datetime.strptime(exam_date_raw, "%Y-%m-%d").date()
        except ValueError:
            print(f"❌ Invalid EXAM_DATE: {exam_date_raw}, expected YYYY-MM-DD")
            sys.exit(1)
    return datetime.date(today.year, DEFAULT_EXAM_MONTH, DEFAULT_EXAM_DAY)


def build_markdown_text(days_left: int, daily_url: str) -> str:
    return f"""### ⏳ 距离软考还有 {days_left} 天

**今日任务：每日一练（真题来源站点）**

---
👇 点击开始今日学习打卡 [👉 进入每日一练]({daily_url})
"""


def build_payload(days_left: int, daily_url: str, message_style: str) -> dict:
    title = f"距离软考还有 {days_left} 天"

    if message_style == "markdown":
        return {
            "msgtype": "markdown",
            "markdown": {
                "title": title,
                "text": build_markdown_text(days_left, daily_url),
            },
        }

    if message_style == "link":
        return {
            "msgtype": "link",
            "link": {
                "title": title,
                "text": "今日任务：每日一练（真题来源站点）",
                "picUrl": "",
                "messageUrl": daily_url,
            },
        }

    # Default and recommended: action card with a dedicated jump button.
    return {
        "msgtype": "actionCard",
        "actionCard": {
            "title": title,
            "text": (
                f"### ⏳ {title}\n\n"
                "**今日任务：每日一练（真题来源站点）**\n\n"
                "> 点击下方按钮开始今日学习打卡"
            ),
            "singleTitle": "👉 进入每日一练",
            "singleURL": daily_url,
        },
    }


def bool_env(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def build_jump_url(daily_url: str, redirect_base_url: str, use_redirect: bool) -> str:
    if not use_redirect:
        return daily_url
    encoded_target = urllib.parse.quote(daily_url, safe="")
    separator = "&" if "?" in redirect_base_url else "?"
    return f"{redirect_base_url}{separator}to={encoded_target}"


def send_to_dingtalk(webhooks: List[str], payload: dict) -> int:
    ok_count = 0
    for idx, webhook in enumerate(webhooks):
        try:
            resp = requests.post(webhook, json=payload, timeout=10)
            body_text = resp.text.strip()
            body_json = {}
            try:
                body_json = resp.json()
            except Exception:
                body_json = {}

            errcode = body_json.get("errcode")
            is_success = resp.status_code == 200 and (errcode in (None, 0))

            if is_success:
                ok_count += 1
                print(f"✅ 第 {idx + 1} 个群发送成功")
            else:
                print(f"❌ 第 {idx + 1} 个群发送失败: HTTP {resp.status_code}, body: {body_text}")
        except Exception as exc:
            print(f"❌ 第 {idx + 1} 个群请求报错: {exc}")
    return ok_count


def main() -> int:
    webhook_env = os.getenv("DINGTALK_WEBHOOK", "").strip()
    webhooks = parse_webhooks(webhook_env) if webhook_env else []

    daily_url = os.getenv("DAILY_PRACTICE_URL", DEFAULT_DAILY_URL).strip()
    redirect_base_url = os.getenv("REDIRECT_BASE_URL", DEFAULT_REDIRECT_BASE_URL).strip()
    use_redirect = bool_env("USE_REDIRECT", True)
    jump_url = build_jump_url(daily_url, redirect_base_url, use_redirect)
    message_style = os.getenv("DINGTALK_MESSAGE_STYLE", DEFAULT_MESSAGE_STYLE).strip().lower()
    dry_run = os.getenv("DRY_RUN", "false").strip().lower() in {"1", "true", "yes"}

    today = datetime.date.today()
    exam_date = parse_exam_date(today)
    days_left = max((exam_date - today).days + 1, 0)

    payload = build_payload(days_left, jump_url, message_style)

    print(f"📆 Today: {today.isoformat()}")
    print(f"🎯 Exam date: {exam_date.isoformat()}")
    print(f"🔗 Daily URL: {daily_url}")
    print(f"↪️ Jump URL: {jump_url}")
    print(f"🔁 Use redirect: {use_redirect}")
    print(f"💬 Message style: {message_style}")
    print(f"🧪 Dry-run: {dry_run}")

    if dry_run:
        print("📝 Payload preview:")
        print(payload)
        return 0

    if not webhooks:
        print("❌ Missing DINGTALK_WEBHOOK")
        return 1

    print(f"📢 准备推送到 {len(webhooks)} 个群...")
    ok_count = send_to_dingtalk(webhooks, payload)
    if ok_count == 0:
        print("❌ 所有群发送失败")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
