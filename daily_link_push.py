import datetime
import os
import sys
from typing import List

import requests


DEFAULT_DAILY_URL = "https://ruankaodaren.com/exam/#/answertest/answertest?reset=0&type=8"
DEFAULT_EXAM_MONTH = 5
DEFAULT_EXAM_DAY = 24


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


def send_to_dingtalk(webhooks: List[str], payload: dict) -> int:
    ok_count = 0
    for idx, webhook in enumerate(webhooks):
        try:
            resp = requests.post(webhook, json=payload, timeout=10)
            if resp.status_code == 200:
                ok_count += 1
                print(f"✅ 第 {idx + 1} 个群发送成功")
            else:
                print(f"❌ 第 {idx + 1} 个群发送失败: {resp.status_code} {resp.text}")
        except Exception as exc:
            print(f"❌ 第 {idx + 1} 个群请求报错: {exc}")
    return ok_count


def main() -> int:
    webhook_env = os.getenv("DINGTALK_WEBHOOK", "").strip()
    webhooks = parse_webhooks(webhook_env) if webhook_env else []

    daily_url = os.getenv("DAILY_PRACTICE_URL", DEFAULT_DAILY_URL).strip()
    dry_run = os.getenv("DRY_RUN", "false").strip().lower() in {"1", "true", "yes"}

    today = datetime.date.today()
    exam_date = parse_exam_date(today)
    days_left = max((exam_date - today).days + 1, 0)

    payload = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"距离软考还有 {days_left} 天",
            "text": build_markdown_text(days_left, daily_url),
        },
    }

    print(f"📆 Today: {today.isoformat()}")
    print(f"🎯 Exam date: {exam_date.isoformat()}")
    print(f"🔗 Daily URL: {daily_url}")
    print(f"🧪 Dry-run: {dry_run}")

    if dry_run:
        print("📝 Payload preview:")
        print(payload["markdown"]["text"])
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
