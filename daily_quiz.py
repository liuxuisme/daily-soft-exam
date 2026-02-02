import os
import json
import requests
import datetime
import random
import base64
import re
import urllib.parse

# ================= 配置区 =================
# 🔴 请替换为你自己的 GitHub Pages 地址
WEB_PAGE_URL = "https://liuxuisme.github.io/daily-soft-exam/" 
# =========================================

# 🏛️ 架构师专用大纲 (保持不变，覆盖全考点)
SYLLABUS = {
    2: [
        "运筹学与数学建模(线性规划/最大流/决策论)", "操作系统(PV/死锁/嵌入式OS)", 
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
    random.seed(today.strftime("%Y%m%d")) 
    return random.choice(topics)

def get_ai_content(topic):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key: return None

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    # 📝 优化 Prompt：明确禁止 LaTeX 单反斜杠，防止 JSON 炸裂
    prompt_text = f"""
    你是一位**软考系统架构设计师（高级）金牌培训讲师**。
    今天是备考冲刺日，主题是【{topic}】。
    
    请严格基于**历年真题（2015-2025）**，生成一份包含"学、记、练"的全方位学习数据。
    
    【重要格式要求】：
    1. 返回纯 JSON 格式。
    2. **严禁在字符串中使用未转义的 LaTeX 反斜杠（如 \sum, \alpha）**。请使用纯文本符号代替（如 sum, alpha），或者使用 markdown 代码块。
    3. 如果必须包含公式，请确保反斜杠被转义（例如写成 \\sum 而不是 \sum）。
    
    JSON 结构如下：
    {{
        "topic": "{topic}",
        "core_concept": "核心考点提炼（Markdown）。列出3-5个考点。",
        "knowledge_explanation": "深度精讲（Markdown）。包含原理、**记忆口诀**或对比表格。如果涉及数学公式，请用通俗易懂的文本描述。",
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
        print(f"🚀 [架构师备战] 正在生成【{topic}】的全套资料(10题+精讲)...")
        resp = requests.post(url, headers=headers, json=payload, timeout=90)
        
        if resp.status_code != 200:
            print(f"❌ AI 请求失败: {resp.text}")
            return None
            
        result = resp.json()
        text = result['candidates'][0]['content']['parts'][0]['text'].strip()
        
        # --- 🧹 数据清洗区 (核心修复) ---
        # 1. 去除 Markdown 代码块标记
        text = text.replace("```json", "").replace("```", "").strip()
        
        # 2. 正则修复：将所有“不合法的反斜杠”替换为“双反斜杠”
        # 逻辑：查找所有并不是紧跟在 " \ / b f n r t u 这里的反斜杠
        # 这样可以保留 \n \t \" 等合法转义，修复 \s \a \l 等非法转义
        try:
            return json.loads(text)
        except json.decoder.JSONDecodeError:
            print("⚠️ 检测到 JSON 格式非法，尝试自动修复 LaTeX 反斜杠...")
            # 这是一个强力修复正则：把所有 \ 变成 \\ (除了已经是转义符的)
            # 但简单点，我们直接把单个 \ 替换为 / 或者直接双写，这里用保守策略：
            # 替换掉所有导致报错的单斜杠
            text = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)
            return json.loads(text)

    except Exception as e:
        print(f"❌ 解析出错 (原始内容可能包含非法字符): {e}")
        # 打印出前100个字符方便调试
        if 'text' in locals(): print(f"Raw text start: {text[:100]}...")
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

    text = f"""### 🏛️ 架构师备考：{data['topic']}

**🔥 今日任务清单：**
1. 🧠 **核心精讲**：原理 + 记忆口诀
2. 📝 **论文/案例**：写作与解题技巧
3. ⚔️ **真题实战**：{len(data['questions'])} 道高频真题

---
👇 **点击开始深度学习**
[👉 进入特训系统]({full_url})

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
        exit(1)
