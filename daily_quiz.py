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
        "操作系统-进程与线程基础",
        "操作系统-进程调度算法(FCFS/SJF/RR/优先级)",
        "操作系统-PV操作与经典同步问题",
        "操作系统-死锁条件与预防避免",
        "操作系统-银行家算法与安全序列",
        "操作系统-页式存储与地址变换",
        "操作系统-页面置换算法(FIFO/LRU/OPT)",
        "操作系统-段页式存储与TLB",
        "操作系统-文件索引(i-node)与位示图",
        "操作系统-磁盘调度(FCFS/SSTF/SCAN/C-SCAN)",
        "操作系统-中断机制与DMA",
        "数据库-ER模型与关系模式转换",
        "数据库-函数依赖与候选键",
        "数据库-三范式与反规范化设计",
        "数据库-索引结构(B+树/Hash)与适用场景",
        "数据库-查询优化与执行计划",
        "数据库-事务ACID与隔离级别",
        "数据库-并发控制(锁/MVCC)",
        "数据库-日志恢复(REDO/UNDO/检查点)",
        "数据库-分布式事务(2PC/3PC)",
        "数据库-CAP/BASE与一致性模型",
        "数据库-Redis数据结构与持久化",
        "数据库-缓存一致性与缓存三大问题",
        "计算机网络-TCP/IP分层与协议职责",
        "计算机网络-TCP可靠传输与流量控制",
        "计算机网络-IPv4/IPv6与CIDR子网划分",
        "数学-线性规划与单纯形法",
        "数学-决策论(最大最小/后悔值)"
    ],
    3: [
        "架构风格-数据流风格(批处理/管道)",
        "架构风格-调用返回(主程序/OO/层次)",
        "架构风格-独立构件(事件驱动/消息驱动)",
        "架构风格-虚拟机与解释器",
        "架构风格-分层与分区",
        "架构风格-管道过滤器",
        "架构风格-仓库风格与黑板模型",
        "架构风格-面向服务架构(SOA)基础",
        "架构评估-ATAM(架构权衡分析法)",
        "架构评估-SAAM(软件架构分析法)",
        "架构评估-CBAM(成本效益分析)",
        "质量属性-性能场景与响应时间",
        "质量属性-可用性战术(冗余/故障转移)",
        "质量属性-安全性战术(认证/授权/审计)",
        "质量属性-可修改性与可测试性",
        "设计模式-创建型(工厂/单例/原型)",
        "设计模式-结构型(适配器/桥接/组合)",
        "设计模式-行为型(策略/观察者/责任链)",
        "设计原则-SOLID与高内聚低耦合",
        "UML-用例图与类图",
        "UML-时序图/活动图/状态图",
        "需求工程-需求获取与规格说明",
        "开发过程-RUP/敏捷/DevOps",
        "面向对象分析设计-领域建模",
        "软件复用-构件复用与框架",
        "接口设计-RESTful规范与幂等性",
        "数据建模-概念模型到物理模型",
        "测试策略-单元/集成/系统/验收",
        "配置管理-版本/变更/基线控制",
        "项目管理-进度网络图与关键路径",
        "项目管理-成本估算与挣值分析"
    ],
    4: [
        "分布式-微服务拆分原则与边界划分",
        "分布式-服务注册与发现",
        "分布式-RPC通信与序列化",
        "分布式-API网关与限流熔断",
        "分布式-消息队列(Kafka/RabbitMQ)",
        "分布式-分布式锁与幂等设计",
        "分布式-一致性协议(Raft/Paxos)",
        "分布式-链路追踪与可观测性",
        "云原生-Docker镜像与容器隔离",
        "云原生-K8s核心对象(Pod/Deployment/Service)",
        "云原生-K8s调度与弹性伸缩",
        "云原生-ServiceMesh服务网格",
        "云原生-Serverless无服务器架构",
        "云原生-CI/CD流水线设计",
        "大数据-Hadoop生态与组件协作",
        "大数据-Spark计算模型",
        "大数据-批流一体(Lambda/Kappa)",
        "数据治理-数据质量与主数据管理",
        "安全架构-身份认证与单点登录(SSO/OAuth2)",
        "安全架构-访问控制(DAC/MAC/RBAC/ABAC)",
        "安全架构-密码学基础(摘要/签名/证书)",
        "安全架构-PKI体系与TLS",
        "安全架构-Web安全(SQL注入/XSS/CSRF)",
        "高并发-负载均衡算法",
        "高并发-数据库读写分离与分库分表",
        "高并发-缓存架构与热点治理",
        "高并发-限流/降级/熔断策略",
        "存储架构-DAS/NAS/SAN与对象存储",
        "网络架构-CDN与边缘计算",
        "网络架构-SDN与网络虚拟化"
    ],
    5: [
        "综合冲刺-操作系统高频计算题",
        "综合冲刺-数据库高频计算题",
        "综合冲刺-网络高频计算题",
        "综合冲刺-架构风格与质量属性辨析",
        "综合冲刺-设计模式选型题",
        "综合冲刺-架构评估ATAM/CBAM",
        "综合冲刺-微服务与分布式治理",
        "综合冲刺-云原生与容器编排",
        "综合冲刺-信息安全高频考点",
        "综合冲刺-大数据与数据治理",
        "案例分析-需求分析与约束提炼",
        "案例分析-架构方案比选与权衡",
        "案例分析-高可用架构设计",
        "案例分析-高并发性能优化",
        "案例分析-数据库设计与SQL优化",
        "案例分析-缓存与一致性方案",
        "案例分析-消息队列与异步解耦",
        "案例分析-安全与权限体系设计",
        "案例分析-容灾备份与故障恢复(RTO/RPO)",
        "案例分析-监控告警与容量规划",
        "论文写作-摘要与背景段模板",
        "论文写作-架构设计段模板",
        "论文写作-关键技术段模板",
        "论文写作-质量属性与权衡段模板",
        "论文写作-风险与改进段模板",
        "论文写作-微服务架构专题",
        "论文写作-高可用高并发专题",
        "论文写作-数据治理与中台专题",
        "真题复盘-近5年上午错题回顾",
        "真题复盘-近5年案例题回顾",
        "真题复盘-近5年论文题回顾"
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
