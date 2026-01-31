import os
import json
import requests
import base64
import urllib.parse
import random
import time

# ================= 配置区 =================
# 替换为你自己的 GitHub Pages 地址 (末尾不要带 /index.html)
WEB_PAGE_URL = "https://liuxuisme.github.io/daily-soft-exam/" 

SUBJECTS = ["软件设计师", "系统架构设计师", "网络工程师", "数据库系统工程师"]
# =========================================

def get_ai_quiz():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("Error: 缺少 GOOGLE_API_KEY")
        return None
    
    # ---------------------------------------------------------
    # 核心修改：直接使用 HTTP 请求，不再依赖 Google Python SDK
    # 使用最新的 gemini-1.5-flash 模型
    # ---------------------------------------------------------
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    subject = random.choice(SUBJECTS)
    
    # 提示词
    prompt_text = f"""
    请针对【{subject}】考试，生成一道单项选择题。
    必须严格按照以下 JSON 格式返回，不要包含 Markdown 格式标记（如 ```json）：
    {{
        "question": "题目内容",
        "options": ["A. 选项1", "B. 选项2", "C. 选项3", "D. 选项4"],
        "answer": "B",
        "analysis": "这里写详细的解析（100字左右）"
    }}
    """
    
    payload = {
        "contents": [{
            "parts": [{"text": prompt_text}]
        }]
    }
    
    headers = {'Content-Type': 'application/json'}

    try:
        # 发送请求
        response = requests.post(url, headers=headers, json=payload)
        
        # 打印一下原始响应，方便调试
        # print("AI Response status:", response.status_code)
        
        if response.status_code != 200:
            print(f"AI 请求失败: {response.text}")
            return None

        result = response.json()
        
        # 解析返回的 JSON 结构
        # Google API 返回结构深：candidates -> content -> parts -> text
        text = result['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # 清洗 Markdown 标记
        if text.startswith("```json"): text = text[7:]
        if text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
        
        return json.loads(text)

    except Exception as e:
        print(f"解析出错: {e}")
        return None

def send_dingtalk(quiz):
    webhook = os.environ.get("DINGTALK_WEBHOOK")
    if not webhook or not quiz: 
        print("Error: 缺少 Webhook 或 题目为空")
        return

    # 1. 生成加密参数
    json_str = json.dumps(quiz, ensure_ascii=False)
    b64_data = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
    url_param = urllib.parse.quote(b64_data)
    
    # 2. 拼接完整跳转链接
    full_url = f"{WEB_PAGE_URL}/index.html?data={url_param}"
    print(f"生成答题链接: {full_url}")

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
    
    try:
        r = requests.post(webhook, json=data)
        print(f"钉钉发送结果: {r.text}")
    except Exception as e:
        print(f"钉钉发送报错: {e}")

if __name__ == "__main__":
    print("开始运行...")
    quiz = get_ai_quiz()
    if quiz:
        send_dingtalk(quiz)
    else:
        print("任务终止：未获取到题目")
