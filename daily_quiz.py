import os
import json
import requests
import base64
import urllib.parse
import random

# ================= 配置区 =================
# 🔴 请替换为你自己的 GitHub Pages 地址 (末尾不要带 /index.html)
WEB_PAGE_URL = "https://liuxuisme.github.io/daily-soft-exam/" 

SUBJECTS = ["软件设计师", "系统架构设计师", "网络工程师", "数据库系统工程师"]
# =========================================

def get_available_models(api_key):
    """诊断函数：查看当前 Key 能用什么模型"""
    url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
    try:
        resp = requests.get(url)
        data = resp.json()
        if 'models' in data:
            # 筛选出支持 generateContent 的模型
            valid_models = [m['name'] for m in data['models'] if 'generateContent' in m.get('supportedGenerationMethods', [])]
            print(f"🔍 你的 Key 支持以下模型: {valid_models}")
            return valid_models
        else:
            print(f"⚠️ 无法获取模型列表: {data}")
            return []
    except Exception as e:
        print(f"⚠️ 诊断请求失败: {e}")
        return []

def get_ai_quiz():
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ Error: 环境变量中未找到 GOOGLE_API_KEY")
        return None

    # --- 1. 智能选择模型 ---
    # 优先尝试 v1 版本的 flash，如果失败会自动回退
    target_model = "models/gemini-2.5-flash"
    
    # 这里的 v1 是关键，之前报错是因为用了 v1beta
    url = f"https://generativelanguage.googleapis.com/v1/{target_model}:generateContent?key={api_key}"
    
    subject = random.choice(SUBJECTS)
    print(f"🚀 正在尝试使用模型: {target_model} 出题...")

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
    
    payload = { "contents": [{ "parts": [{"text": prompt_text}] }] }
    headers = {'Content-Type': 'application/json'}

    try:
        response = requests.post(url, headers=headers, json=payload)
        
        # --- 2. 错误处理与诊断 ---
        if response.status_code != 200:
            print(f"❌ 请求失败 (Code {response.status_code})")
            print(f"❌ 错误详情: {response.text}")
            
            # 如果失败，尝试列出可用模型，方便排查
            print("\n--- 开始诊断 ---")
            get_available_models(api_key)
            print("--- 诊断结束 ---\n")
            return None

        # --- 3. 解析数据 ---
        result = response.json()
        try:
            text = result['candidates'][0]['content']['parts'][0]['text'].strip()
        except KeyError:
            print(f"❌ AI 返回了意外的数据结构: {result}")
            return None
        
        # 清洗 Markdown
        if text.startswith("```json"): text = text[7:]
        if text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
        
        return json.loads(text)

    except Exception as e:
        print(f"❌ 脚本执行出错: {e}")
        return None

def send_dingtalk(quiz):
    webhook = os.environ.get("DINGTALK_WEBHOOK")
    if not webhook or not quiz: return

    json_str = json.dumps(quiz, ensure_ascii=False)
    b64_data = base64.b64encode(json_str.encode('utf-8')).decode('utf-8')
    url_param = urllib.parse.quote(b64_data)
    full_url = f"{WEB_PAGE_URL}/index.html?data={url_param}"

    print(f"🔗 生成链接: {full_url}")

    data = {
        "msgtype": "actionCard",
        "actionCard": {
            "title": "软考每日一练", 
            "text": f"### 📅 软考每日打卡\n\n**{quiz['question']}**\n\n{chr(10).join(quiz['options'])}\n\n---",
            "btnOrientation": "0", 
            "btns": [{"title": "✏️ 开始答题 & 看解析", "actionURL": "https://liuxuisme.github.io/daily-soft-exam/"}]
        }
    }
    
    try:
        r = requests.post(webhook, json=data)
        print(f"✅ 钉钉发送成功: {r.text}")
    except Exception as e:
        print(f"❌ 钉钉发送失败: {e}")

if __name__ == "__main__":
    quiz = get_ai_quiz()
    if quiz:
        send_dingtalk(quiz)
