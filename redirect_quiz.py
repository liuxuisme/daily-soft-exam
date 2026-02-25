import requests
import datetime
import os
import json

# ================= 配置区 =================
# 软考达人-系统架构设计师-每日一练
TARGET_URL = "https://ruankaodaren.com/exam/#/answertest/answertest?reset=0&type=8"
# =========================================

def get_days_left():
    """计算距离软考还有多少天"""
    today = datetime.datetime.now()
    current_year = today.year
    
    # 设定考试日期：5月24日
    exam_date = datetime.datetime(current_year, 5, 24)
    
    # 如果今天已经过了今年的考试时间，计算明年的
    if today > exam_date:
        exam_date = datetime.datetime(current_year + 1, 5, 24)
        
    delta = exam_date - today
    return delta.days + 1

def send_dingtalk():
    webhook_env = os.environ.get("DINGTALK_WEBHOOK")
    if not webhook_env:
        print("❌ 未配置 DINGTALK_WEBHOOK")
        return

    # 支持多个 Webhook
    webhooks = [w.strip() for w in webhook_env.split(',') if w.strip()]
    
    days = get_days_left()
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")

    # 纯净版 Markdown 文案
    title = f"软考倒计时：{days}天"
    
    text = f"""### ⏳ {title}

**{today_str}**

**今日任务：**
每日一练 (真题来源：软考达人)

---
👇 点击开始今日学习打卡
[👉 进入每日一练]({TARGET_URL})
"""

    # 使用 Markdown 消息类型（和你之前的风格保持一致）
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": title, 
            "text": text
        }
    }

    print(f"📢 准备推送通知...")
    for webhook in webhooks:
        try:
            requests.post(webhook, json=data, timeout=10)
            print("✅ 推送成功")
        except Exception as e:
            print(f"❌ 推送失败: {e}")

if __name__ == "__main__":
    send_dingtalk()
