import os
import json
import requests
import datetime
import random
import re
import urllib.parse

# ================= 配置区 =================
WEB_PAGE_URL = "https://liuxuisme.github.io/daily-soft-exam/" 
# 状态文件路径 (用于记录学到哪了)
STATUS_FILE = "docs/data/syllabus_status.json"
# =========================================

# 📚 架构师原子考点库 (Atomic Knowledge Tree)
# 将大类拆解为具体的“可出题单元”
DETAILED_SYLLABUS = {
    # 2月：底层与数学 (硬骨头)
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
    # 3月：架构核心 (灵魂)
    3: [
        "架构风格-数据流风格(批处理/管道)", "架构风格-调用返回(主程序/OO/层次)",
        "架构风格-独立构件(进程通信/事件驱动)", "架构风格-虚拟机与解释器",
        "架构风格-C2风格与仓库风格",
        "架构评估-ATAM(架构权衡分析法)", "架构评估-SAAM(软件架构分析法)",
        "架构评估-CBAM(成本效益分析)", "质量属性-效用树与质量场景",
        "质量属性-战术(可用性/性能/安全性)",
        "设计模式-创建型(工厂/单例/原型)", "设计模式-结构型(适配器/桥接/组合)",
        "设计模式-行为型(策略/观察者/责任链)",
        "开发方法-ABSD(基于架构的软件开发)", "开发方法-DSSA(特定领域软件架构)"
    ],
    # 4月：前沿与分布式 (论文重灾区)
    4: [
        "分布式-微服务架构拆分策略", "分布式-SOA与ESB企业服务总线",
        "分布式-RPC与RESTful API设计", "分布式-消息队列(Kafka/RabbitMQ)",
        "云原生-Docker容器与K8s编排", "云原生-ServiceMesh服务网格",
        "云原生-Serverless无服务器架构",
        "大数据-Lambda架构与Kappa架构", "大数据-Hadoop与Spark生态",
        "安全架构-PKI公钥体系与数字签名", "安全架构-访问控制(DAC/RBAC/MAC)",
        "安全架构-区块链与去中心化技术",
        "高并发-负载均衡算法", "高并发-数据库读写分离与分库分表"
    ],
    # 5月：冲刺 (综合)
    5: [
        "真题集训-综合知识历年错题", "案例分析-系统架构设计试题",
        "案例分析-UML建模与数据库设计", "案例分析-嵌入式系统设计",
        "论文写作-论微服务架构的设计与应用", "论文写作-论软件架构风格的选择",
        "论文写作-论系统可靠性设计", "论文写作-论数据湖与湖仓一体"
    ]
}

def get_smart_topic():
    """
    智能调度核心逻辑：
    1. 读取状态文件，看当前月份的题库学完了没。
    2. 如果没学完，挑一个没学的。
    3. 如果学完了，重置列表(开始复习)或切换月份。
    """
    today = datetime.datetime.now()
    current_month = today.month
    
    # 默认考点（防止月份越界）
    default_topics = DETAILED_SYLLABUS.get(5)
    
    # 1. 读取状态
    status = {}
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                status = json.load(f)
        except:
            print("⚠️ 状态文件损坏，重置状态")
            status = {}
    
    # 2. 检查是否跨月了，或者第一次运行
    saved_month = status.get("month", -1)
    pending_list = status.get("pending", [])
    
    if saved_month != current_month:
        print(f"📅 检测到新月份/初始化: {current_month}月")
        # 加载新月份的完整题库
        pending_list = DETAILED_SYLLABUS.get(current_month, default_topics).copy()
        # 乱序排列，增加新鲜感
        random.shuffle(pending_list)
        status["month"] = current_month
    
    # 3. 检查列表是否为空（本轮学完了吗？）
    if not pending_list:
        print("🎉 本月考点第一轮已刷完！正在重置进行第二轮复习...")
        pending_list = DETAILED_SYLLABUS.get(current_month, default_topics).copy()
        random.shuffle(pending_list)
    
    # 4. 取出今日考点 (Pop)
    today_topic = pending_list.pop(0)
    print(f"🎯 今日智能推荐考点: {today_topic} (本月剩余: {len(pending_list)})")
    
    # 5. 更新状态数据 (准备回写)
    status["pending"] = pending_list
    status["last_update"] = today.strftime("%Y-%m-%d")
    
    # 6. 保存状态文件
    os.makedirs(os.path.dirname(STATUS_FILE), exist_ok=True)
    with open(STATUS_FILE, "w", encoding="utf-8") as f:
        json.dump(status, f, ensure_ascii=False, indent=2)
        
    return today_topic

def get_ai_content(topic):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key: return None

    # 使用 Gemini 2.5 Flash
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    # 📝 Prompt
    prompt_text = f"""
    你是一位**软考系统架构设计师（高级）金牌培训讲师**。
    今天是备考冲刺日，主题是【{topic}】。
    
    请严格基于**历年真题（2015-2025）**，生成一份包含"学、记、练"的全方位学习数据。
    
    【重要格式要求】：
    1. 返回纯 JSON 格式。
    2. **严禁在字符串中使用未转义的 LaTeX 反斜杠（如 \sum, \alpha）**。请使用纯文本符号代替（如 sum, alpha），或者使用 markdown 代码块。
    3. 如果必须包含公式，请确保反斜杠被转义（例如写成 \\sum 而不是 \sum）。
    4. 所有的换行请使用 \\n，不要直接换行。
    
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
        
        # --- 🧹 数据清洗区 ---
        text = text.replace("```json", "").replace("```", "").strip()
        
        # 🛠️ 三级容错解析机制
        try:
            # 1. 尝试：开启 strict=False (允许控制字符，解决 Invalid control character)
            return json.loads(text, strict=False)
        except json.decoder.JSONDecodeError:
            print("⚠️ 初次解析失败，尝试修复 LaTeX 反斜杠...")
            
            # 2. 修复：正则处理非法反斜杠
            text = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', text)
            
            try:
                # 再次尝试解析
                return json.loads(text, strict=False)
            except json.decoder.JSONDecodeError as e:
                print(f"❌ JSON 修复失败: {e}")
                # 打印出错位置的前后文本，方便调试（虽然Action里看不了太细）
                return None

    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return None

def save_to_file(data):
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    os.makedirs("docs/data", exist_ok=True)
    file_path = f"docs/data/{date_str}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return date_str

def send_dingtalk(date_str, data):
    # 获取环境变量
    webhook_env = os.environ.get("DINGTALK_WEBHOOK")
    if not webhook_env: return

    # 🛠️ 核心修改：支持多个 Webhook (用逗号分隔)
    # 逻辑：先按逗号切分，再去除首尾空格，过滤掉空字符串
    webhooks = [w.strip() for w in webhook_env.split(',') if w.strip()]

    full_url = f"{WEB_PAGE_URL}/index.html?date={date_str}"
    print(f"🔗 生成链接: {full_url}")

    # 计算倒计时
    today = datetime.datetime.now()
    current_year = today.year
    exam_date = datetime.datetime(current_year, 5, 24)
    delta = exam_date - today
    days_left = delta.days + 1 
    if days_left < 0: days_left = 0

    msg_title = f"距离软考还有 {days_left} 天"

    text = f"""### ⏳ {msg_title}

**今日特训：{data['topic']}**

**今日任务：**
1. 学习核心知识点
2. 完成 10 道精选真题

---
👇 点击开始今日学习打卡 [👉 进入特训系统]({full_url})
"""
    
    payload = {
        "msgtype": "markdown",
        "markdown": { 
            "title": msg_title, 
            "text": text 
        }
    }

    # 🛠️ 核心修改：循环发送
    print(f"📢 准备推送到 {len(webhooks)} 个群...")
    
    for i, webhook in enumerate(webhooks):
        try:
            resp = requests.post(webhook, json=payload, timeout=10)
            if resp.status_code == 200:
                print(f"✅ 第 {i+1} 个群发送成功")
            else:
                print(f"❌ 第 {i+1} 个群发送失败: {resp.text}")
        except Exception as e:
            print(f"❌ 第 {i+1} 个群请求报错: {e}")

if __name__ == "__main__":
    # 1. 获取智能调度的考点
    topic = get_smart_topic()
    
    # 2. 生成内容
    data = get_ai_content(topic)
    
    if data:
        # 3. 保存内容文件
        date_str = save_to_file(data)
        # 4. 发送通知 (此时 status 文件也已经保存了)
        send_dingtalk(date_str, data)
    else:
        print("❌ 任务失败")
        exit(1)
