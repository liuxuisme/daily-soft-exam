import os
import json
import requests
import datetime
import random
import re
import urllib.parse

# ================= 配置区 =================
# 1. 你的 GitHub Pages 地址 (深度特训)
WEB_PAGE_URL = "https://liuxuisme.github.io/daily-soft-exam/" 
# 2. 软考达人地址 (每日一练)
EXTERNAL_URL = "https://ruankaodaren.com/exam/#/answertest/answertest?reset=0&type=8"
# =========================================

# 🏛️ 架构师专用大纲
SYLLABUS = {
    2: [
        "操作系统-PV操作与前趋图", "操作系统-死锁与银行家算法", 
        "操作系统-页式存储与缺页中断计算", "操作系统-文件索引与位示图",
        "操作系统-磁盘调度与嵌入式RTOS",
        "数据库-三范式与反规范化设计", "数据库-分布式数据库(2PC/CAP/BASE)", 
        "数据库-Redis缓存策略与数据一致性", "数据库-数据仓库与商业智能(BI)",
        "计算机网络-SDN软件定义网络", "计算机网络-CDN内容分发与边缘计算", 
        "计算机网络-网络存储(DAS/NAS/SAN)", "计算机网络-IPv6与网络规划",
        "数学-线性规划与单纯形法", "数学-最大流与最小割", 
        "数学-决策论(最大最小/后悔值)", "数学-图论与关键路径法(CPM)"
    ],
    3: [
        "架构风格-数据流风格", "架构风格-调用返回",
        "架构风格-独立构件", "架构风格-虚拟机与解释器",
        "架构风格-C2风格与仓库风格",
        "架构评估-ATAM", "架构评估-SAAM",
        "架构评估-CBAM", "质量属性-效用树与质量场景",
        "质量属性-战术(可用性/性能/安全性)",
        "设计模式-创建型", "设计模式-结构型",
        "设计模式-行为型",
        "开发方法-ABSD", "开发方法-DSSA"
    ],
    4: [
        "分布式-微服务架构拆分", "分布式-SOA与ESB",
        "分布式-RPC与RESTful", "分布式-消息队列",
        "云原生-Docker与K8s", "云原生-ServiceMesh",
        "云原生-Serverless",
        "大数据-Lambda与Kappa", "大数据-Hadoop与Spark",
        "安全架构-PKI与数字签名", "安全架构-访问控制",
        "安全架构-区块链",
        "高并发-负载均衡", "高并发-读写分离与分库分表"
    ],
    5: [
        "真题集训-综合知识历年错题", "案例分析-系统架构设计试题",
        "案例分析-UML建模与数据库设计", "案例分析-嵌入式系统设计",
        "论文写作-论微服务架构的设计", "论文写作-论软件架构风格",
        "论文写作-论系统可靠性设计", "论文写作-论数据湖与湖仓一体"
    ]
}

# 状态文件路径
STATUS_FILE = "docs/data/syllabus_status.json"

def get_smart_topic():
    today = datetime.datetime.now()
    current_month = today.month
    default_topics = SYLLABUS.get(5)
    
    status = {}
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                status = json.load(f)
        except:
            status = {}
    
    saved_month = status.get("month", -1)
    pending_list = status.get("pending", [])
    
    if saved_month != current_month:
        pending_list = SYLLABUS.get(current_month, default_topics).copy()
        random.shuffle(pending_list)
        status["month"] = current_month
    
    if not pending_list:
        pending_list = SYLLABUS.get(current_month, default_topics).copy()
        random.shuffle(pending_list)
    
    today_topic = pending_list.pop(0)
    
    status["pending"] = pending_list
    os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
        
    return today_topic

def get_ai_content(topic):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key: return None

    # 使用 Gemini 2.5 Flash
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    prompt_text = f"""
    你是一位**软考系统架构设计师（高级）阅卷专家**。
    今天是备考冲刺日，具体细分考点是【{topic}】。
    
    请严格基于**历年真题（2015-2025）**，生成全方位学习数据。
    
    【重要格式要求】：
    1. 返回纯 JSON 格式。
    2. **严禁在字符串中使用未转义的 LaTeX 反斜杠**。请使用纯文本符号或转义反斜杠 (\\sum)。
    3. 所有的换行请使用 \\n，不要直接换行。
    
    JSON 结构如下：
    {{
        "topic": "{topic}",
        "core_concept": "核心考点提炼（Markdown）。列出3个关键概念或公式。",
        "knowledge_explanation": "深度精讲（Markdown）。包含原理、**记忆口诀**或对比表格。",
        "essay_guide": "论文与案例指导（Markdown）。",
        "questions": [
            {{
                "question": "题干 [年份]",
                "options": ["A. x", "B. x", "C. x", "D. x"],
                "answer": "B",
                "analysis": "解析。"
            }}
        ]
    }}
    请生成 10 道题。
    """
    
    payload = { "contents": [{ "parts": [{"text": prompt_text}] }] }
    headers = {'Content-Type': 'application/json'}

    try:
        print(f"🚀 正在调用 AI 生成内容...")
        resp = requests.post(url, headers=headers, json=payload, timeout=120)
        
        if resp.status_code != 200:
            print(f"❌ AI 请求失败: {resp.text}")
            return None
            
        result = resp.json()
        text = result['candidates'][0]['content']['parts'][0]['text'].strip()
        text = text.replace("```json", "").replace("```", "").strip()
        
        try:
            return json.loads(text, strict=False)
        except json.decoder.JSONDecodeError:
            text = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)
            return json.loads(text, strict=False)

    except Exception as e:
        print(f"❌ 解析出错: {e}")
        return None

def save_to_file(data):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    os.makedirs("docs/data", exist_ok=True)
    file_path = f"docs/data/{date_str}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return date_str

def send_dingtalk(date_str, data):
    webhook_env = os.environ.get("DINGTALK_WEBHOOK")
    if not webhook_env: return

    # 支持多个 Webhook
    webhooks = [w.strip() for w in webhook_env.split(',') if w.strip()]

    # 生成特训链接
    internal_url = f"{WEB_PAGE_URL}/index.html?date={date_str}"
    
    # 计算倒计时
    today = datetime.datetime.now()
    exam_date = datetime.datetime(today.year, 5, 24)
    days_left = (exam_date - today).days + 1
    if days_left < 0: days_left = 0

    msg_title = f"距离软考还有 {days_left} 天"

    # ==========================================
    # 🌟 核心修改：合并两个任务的 Markdown 文案
    # ==========================================
    text = f"""### ⏳ {msg_title}

**今日特训：{data['topic']}**

---
**任务 A：深度特训 (AI精讲)**
10 道专项模拟题[👉 进入特训系统 ]({internal_url})

---
**任务 B：每日一练 (开源站点)**
软考历年真题库[👉 进入每日一练 ]({EXTERNAL_URL})
"""
    
    payload = {
        "msgtype": "markdown",
        "markdown": { "title": msg_title, "text": text }
    }

    print(f"📢 准备推送到 {len(webhooks)} 个群...")
    for webhook in webhooks:
        try:
            requests.post(webhook, json=payload, timeout=10)
        except Exception:
            pass

if __name__ == "__main__":
    topic = get_smart_topic()
    data = get_ai_content(topic)
    
    if data:
        date_str = save_to_file(data)
        send_dingtalk(date_str, data)
    else:
        print("❌ 任务失败")
        exit(1)
