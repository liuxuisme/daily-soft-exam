import os
import json
import requests
import datetime
import random
import time

# ================= 配置区 =================
# 🔴 替换为你自己的 GitHub Pages 地址 (不带 index.html)
WEB_PAGE_URL = "https://liuxuisme.github.io/daily-soft-exam/" 
# =========================================

# 📅 软考复习排期表 (The Brain)
# 根据月份决定复习重点
SYLLABUS = {
    2: ["计算机组成与体系结构", "操作系统原理", "数据库系统基础", "计算机网络基础"],
    3: ["软件工程与项目管理", "结构化开发方法", "面向对象技术", "UML建模", "设计模式"],
    4: ["信息安全技术", "数据结构与算法", "法律法规与标准化", "系统架构设计(高级)"],
    5: ["历年真题模拟", "案例分析专项", "论文写作技巧(架构师)", "考前押题与查漏补缺"]
}

def get_today_topic():
    today = datetime.datetime.now()
    month = today.month
    
    # 获取当月的主题列表，如果不在2-5月，默认用5月的
    topics = SYLLABUS.get(month, SYLLABUS[5])
    
    # 简单策略：根据日期的一位随机选一个，或者完全随机
    # 这样能保证一天内多次运行主题不变，或者你可以直接 random.choice(topics)
    return random.choice(topics)

def get_ai_content(topic):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        print("❌ 缺少 API KEY")
        return None

    # 使用 Gemini 2.0 Flash (它支持长文本和复杂 JSON)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-3.0-flash:generateContent?key={api_key}"
    
    # 📝 核心 Prompt：要求生成知识点 + 10道题
    prompt_text = f"""
    你是一位软考金牌讲师。今天是软考备考日。
    请针对主题【{topic}】，生成一份每日学习计划数据。
    
    要求返回一个纯 JSON 对象，包含以下字段：
    1. "topic": "{topic}"
    2. "knowledge_point": "这里写一段约300-500字的核心知识点讲解，包含概念定义、核心原理和记忆口诀。使用Markdown格式，重点可以用**加粗**。"
    3. "questions": 一个包含10个对象的数组。每个对象包含：
       - "question": "题干"
       - "options": ["A. x", "B. x", "C. x", "D. x"]
       - "answer": "B"
       - "analysis": "详细解析"
       
    请确保 JSON 格式合法，不要包含 ```json 标记。
    """
    
    payload = { "contents": [{ "parts": [{"text": prompt_text}] }] }
    headers = {'Content-Type': 'application/json'}

    try:
        print(f"🚀 正在请求 AI 生成【{topic}】的 10 道题...")
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if resp.status_code != 200:
            print(f"❌ AI 请求失败: {resp.text}")
            return None
            
        result = resp.json()
        text = result['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # 清洗
        if text.startswith("```json"): text = text[7:]
        if text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
        
        data = json.loads(text)
        return data
    except Exception as e:
        print(f"❌ 解析或请求出错: {e}")
        return None

def save_to_file(data):
    # 获取今日日期，例如 "2024-02-17"
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # 确保目录存在 docs/data
    os.makedirs("docs/data", exist_ok=True)
    
    file_path = f"docs/data/{date_str}.json"
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 文件已保存: {file_path}")
    return date_str

def send_dingtalk(date_str, topic):
    webhook = os.environ.get("DINGTALK_WEBHOOK")
    if not webhook: return

    # 生成链接，带上 date 参数
    full_url = f"{WEB_PAGE_URL}/index.html?date={date_str}"
    print(f"🔗 访问链接: {full_url}")

    text = f"""### 📅 软考特训：{topic}

**今日任务：**
1. 📖 学习核心知识点
2. ✍️ 完成 10 道精选真题

---
👇 **点击开始今日学习**
[👉 进入刷题系统]({full_url})

*(链接如果无法打开，请复制到浏览器访问)*
"""
    
    data = {
        "msgtype": "markdown",
        "markdown": {
            "title": f"软考特训：{topic}",
            "text": text
        }
    }
    requests.post(webhook, json=data)

if __name__ == "__main__":
    topic = get_today_topic()
    data = get_ai_content(topic)
    
    if data:
        # 1. 保存 JSON 文件
        date_str = save_to_file(data)
        # 2. 发送通知 (此时文件还在本地，Action 后续步骤会 Push 到仓库)
        send_dingtalk(date_str, topic)
    else:
        print("❌ 任务失败")
        exit(1) # 让 Action 报错
