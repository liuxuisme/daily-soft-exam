import os
import json
import requests
import google.generativeai as genai
import base64
import urllib.parse
import random

# ================= 配置区 =================
# 下面这个 URL 必须换成你刚才在 GitHub Pages 里生成的那个网址！
# 注意：末尾不要带 /index.html，只要目录即可
WEB_PAGE_URL = "https://liuxuisme.github.io/daily-soft-exam/" 

SUBJECTS = ["软件设计师", "系统架构设计师", "网络工程师", "数据库系统工程师"]
# =========================================

def get_ai_quiz():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key: return None
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')
    
    subject = random.choice(SUBJECTS)
    
    # 强制 AI 输出 JSON 的提示词
    prompt = f"""
    请针对【{subject}】考试，生成一道单项选择题。
    必须严格按照以下 JSON 格式返回，不要包含 Markdown 格式标记（如 ```json）：
    {{
        "question": "题目内容",
        "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
        "answer": "B",
        "analysis": "这里写详细的解析（100字左右）"
    }}
    """
    
    try:
        resp = model.generate_content(prompt)
        text = resp.text.strip()
        # 清洗数据，防止 AI 加了 markdown 符号
        if text.startswith("```json"): text = text[7:]
        if text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
        return json.loads(text)
    except Exception as e:
        print(f"AI Error: {e}")
        return None

def send_dingtalk(quiz):
    webhook = os.environ.get("DINGTALK_WEBHOOK")
    if not webhook or not quiz: return

    # 1. 生成加密参数
    json_str = json.dumps(quiz, ensure_ascii=False)
    # Base64 编码
    b64_data = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
    # URL 编码
    url_param = urllib.parse.quote(b64_data)
    
    # 2. 拼接完整跳转链接
    full_url = f"{WEB_PAGE_URL}/index.html?data={url_param}"
    print(f"Generated URL: {full_url}")

    # 3. 发送 ActionCard 消息
    data = {
        "msgtype": "actionCard",
        "actionCard": {
            "title": "软考每日一练", 
            "text": f"### 📅 软考每日打卡\n\n**{quiz['question']}**\n\n{chr(10).join(quiz['options'])}\n\n---",
            "btnOrientation": "0", 
            "btns": [
                {"title": "✏️ 开始答题 & 看解析", "actionURL": full_url}
            ]
        }
    }
    
    requests.post(webhook, json=data)

if __name__ == "__main__":
    quiz = get_ai_quiz()
    if quiz:
        send_dingtalk(quiz)
    else:
        print("出题失败")
