import os
import json
import requests
import datetime
import random
import base64
import urllib.parse

# ================= 配置区 =================
# 🔴 请替换为你自己的 GitHub Pages 地址
WEB_PAGE_URL = "https://liuxuisme.github.io/daily-soft-exam/" 
# =========================================

# 🎯 架构师专用大纲
SYLLABUS = {
    2: [
        "运筹学与数学建模(线性规划/最大流)", "操作系统(PV/死锁/嵌入式OS)", 
        "数据库(分布式/Redis/反规范化)", "计算机网络(SDN/CDN/IPv6)", 
        "系统可靠性与容错技术"
    ],
    3: [
        "软件架构风格(数据流/C2/调用返回)", "架构评估(ATAM/SAAM/质量树)", 
        "软件质量属性(战术与设计)", "设计模式(工厂/适配器/策略)", 
        "基于架构的软件开发(ABSD/DSSA)"
    ],
    4: [
        "分布式架构(微服务/SOA/RPC)", "云原生(K8s/ServiceMesh)", 
        "大数据架构(Lambda/Hadoop)", "信息安全架构(PKI/区块链)", 
        "高并发Web架构设计"
    ],
    5: [
        "历年真题集训(综合知识)", "案例分析专项(系统设计)", 
        "论文写作(架构/微服务/数据)", "考前查漏补缺"
    ]
}

def get_today_topic():
    today = datetime.datetime.now()
    month = today.month
    topics = SYLLABUS.get(month, SYLLABUS[5])
    # 结合日期做随机种子，保证同一天多次运行结果一致，方便调试
    random.seed(today.strftime("%Y%m%d")) 
    return random.choice(topics)

def get_ai_content(topic):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key: return None

    # 使用 Gemini 2.0 Flash (速度快且逻辑强)
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    # 🔥 架构师专用 Prompt
    prompt_text = f"""
    你是一位**软考系统架构设计师（高级）阅卷专家**。
    今天是备考冲刺日，主题是【{topic}】。
    
    请严格基于**软考架构师历年真题（2015-2024年）**的考点，生成一份高质量的学习数据。
    
    请返回一个纯 JSON 对象（不要包含Markdown标记），结构如下：
    
    1. "topic": "{topic}"
    2. "knowledge_point": "Markdown格式。总结该领域的3个核心考点。如果涉及'架构风格'或'分布式'，请务必列出优缺点对比。"
    3. "essay_guide": "论文写作指导（重要）。如果该主题适合写论文（如微服务、架构评估），请简述300字的写作思路（摘要重点+正文3个子论点）；如果不适合，则填写'本主题主要考察上午选择题，非论文重点'。"
    4. "questions": 一个包含 10 道**历年真题**（或高度拟真题）的数组。
       - "question": "题干（包含年份更好，如 [2021] xxx）"
       - "options": ["A. x", "B. x", "C. x", "D. x"]
       - "answer": "B"
       - "analysis": "深度解析。**必须解释为什么其他选项是错的**，并指出该题考察的架构设计原则。"
       
    注意：系统架构师考试侧重于**宏观设计、选型对比、质量属性**，请避免过于底层的代码细节。
    """
    
    payload = { "contents": [{ "parts": [{"text": prompt_text}] }] }
    headers = {'Content-Type': 'application/json'}

    try:
        print(f"🚀 [架构师备战] 正在调取【{topic}】真题库...")
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if resp.status_code != 200:
            print(f"❌ AI 请求失败: {resp.text}")
            return None
            
        result = resp.json()
        try:
            text = result['candidates'][0]['content']['parts'][0]['text'].strip()
        except KeyError:
            print(f"AI 返回结构异常: {result}")
            return None
        
        # 清洗 Markdown
        text = text.replace("```json", "").replace("```", "").strip()
        return json.loads(text)

    except Exception as e:
        print(f"❌ 出错: {e}")
        return None

def save_to_file(data):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    os.makedirs("docs/data", exist_ok=True)
    file_path = f"docs/data/{date_str}.json"
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return date_str

def send_dingtalk(date_str, data):
    webhook = os.environ.get("DINGTALK_WEBHOOK")
    if not webhook: return

    full_url = f"{WEB_PAGE_URL}/index.html?date={date_str}"
    print(f"🔗 生成链接: {full_url}")

    # 钉钉消息文案
    text = f"""### 🏛️ 架构师备考：{data['topic']}

**🔥 今日重点：**
* 核心考点复习
* 📝 **论文/案例写作指导** (架构师必看)
* ⚔️ {len(data['questions'])} 道历年真题演练

---
👇 **点击进入备考系统**
[👉 开始今日特训]({full_url})

*(链接若无法打开，请复制到浏览器访问)*
"""
    
    payload = {
        "msgtype": "markdown",
        "markdown": { "title": f"架构师特训：{data['topic']}", "text": text }
    }
    requests.post(webhook, json=payload)

if __name__ == "__main__":
    topic = get_today_topic()
    data = get_ai_content(topic)
    
    if data:
        date_str = save_to_file(data)
        send_dingtalk(date_str, data)
    else:
        print("❌ 任务失败")
        exit(1)
