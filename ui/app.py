import os
import sys
import time
import json
import requests
import streamlit as st

# Configure Page
st.set_page_config(
    page_title="Mossad-pentast-ai | Autonomous Cyber Copilot",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Cyber Dark Theme Styling
st.markdown("""
<style>
    /* Main Background & Fonts */
    .stApp {
        background-color: #0b0f19;
        color: #e2e8f0;
        font-family: 'Inter', -apple-system, sans-serif;
    }
    
    /* Header Styling */
    .cyber-title {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #ff4b4b 0%, #ff8a00 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0px;
    }
    
    .cyber-subtitle {
        color: #94a3b8;
        font-size: 1rem;
        margin-bottom: 20px;
    }
    
    /* Cards & Containers */
    .metric-card {
        background: #151d30;
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
    }
    
    .metric-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #38bdf8;
    }
    
    .metric-label {
        font-size: 0.85rem;
        color: #94a3b8;
    }
    
    /* Status Badge */
    .status-badge-live {
        background-color: rgba(34, 197, 94, 0.15);
        color: #4ade80;
        border: 1px solid #22c55e;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
    }
</style>
""", unsafe_allow_html=True)

# Add Agent directory to path
REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_DIR not in sys.path:
    sys.path.append(REPO_DIR)

try:
    from agent.hexstrike_agent_bridge import HexStrikeAgentBridge
except ImportError:
    HexStrikeAgentBridge = None

GATEWAY_URL = "http://127.0.0.1:8080/v1"

def check_gateway():
    try:
        r = requests.get("http://127.0.0.1:8080/health", timeout=2)
        if r.status_code == 200:
            return r.json()
    except Exception:
        pass
    return None

def query_brain_chat(messages, max_tokens=1024):
    try:
        payload = {
            "model": "Mossad-pentast-ai",
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": max_tokens
        }
        r = requests.post(f"{GATEWAY_URL}/chat/completions", json=payload, timeout=180)
        if r.status_code == 200:
            return r.json().get("choices", [{}])[0].get("message", {}).get("content", "")
    except Exception as e:
        return f"[!] خطأ في الاتصال بالبوابة: {e}. تأكد من تشغيل ./start_session.sh"
    return "[!] لم يتم استلام رد من النموذج."

# Initialize Session State
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [
        {"role": "assistant", "content": "أهلاً بك! أنا **Mossad-pentast-ai**، مساعدك السيبراني المستقل المدرب بـ 50 مصدراً استخباراتياً والمدمج كنموذج مستقل كامل. يمكنك توجيه الأسئلة لي في وضع الشات، أو إدخال هدف لفحصه فحصاً حقيقياً بالأدوات الحية (Nmap, HTTP Probes, Reflection Probes) في وضع الفحص الميداني!"}
    ]

if "assessment_logs" not in st.session_state:
    st.session_state.assessment_logs = []

if "latest_report" not in st.session_state:
    st.session_state.latest_report = None

# Sidebar Controls
gw_info = check_gateway()
with st.sidebar:
    st.markdown("### ⚙️ قمرة التحكم بالمنظومة")
    if gw_info:
        st.markdown(f'<div class="status-badge-live">● البوابة متصلة ({gw_info.get("active_brain", "Online")})</div>', unsafe_allow_html=True)
    else:
        st.warning("⚠️ البوابة غير متصلة (شغّل ./start_session.sh)")
        
    st.write("")
    st.markdown("---")
    mode = st.radio("وضع التشغيل (Operation Mode):", ["🚀 فحص واختراق حقيقي لهدف (Autonomous Audit)", "💬 محادثة مباشرة مع النموذج (Chat)"])
    
    st.markdown("---")
    st.markdown("#### 📊 مواصفات النموذج والبيئة:")
    st.write("• **الاسم**: `Mossad-pentast-ai`")
    st.write("• **البنية**: `Standalone Float16 Merged`")
    st.write("• **المصادر**: `50 مصدراً استخباراتياً (30,000+ عينة)`")
    st.write("• **الأدوات النشطة**: `Nmap, Curl, Python Probes, HexStrike`")
    st.write("• **البوابة المحلية**: `http://127.0.0.1:8080/v1`")
    
    st.markdown("---")
    if st.button("🗑️ مسح سجل المحادثة (Clear Chat)"):
        st.session_state.chat_history = [
            {"role": "assistant", "content": "تم مسح السجل. جاهز لأوامرك الجديدة!"}
        ]
        st.rerun()

# Main Header
st.markdown('<div class="cyber-title">🛡️ Mossad-pentast-ai Autonomous Copilot</div>', unsafe_allow_html=True)
st.markdown('<div class="cyber-subtitle">Real-World Offensive Security Agent • Live Tool Probing & Neural Threat Reasoning</div>', unsafe_allow_html=True)

# TAB 1: Autonomous Target Audit Mode (Default)
if mode == "🚀 فحص واختراق حقيقي لهدف (Autonomous Audit)":
    st.markdown("### 🎯 إطلاق الفحص الميداني الحقيقي (Live Target Assessment)")
    st.info("أدخل رابط الهدف المصرح به قانونياً. سيقوم العميل بتنفيذ فحص فعلي عبر Nmap و HTTP Probes وتحليل استجابات الخادم الحقيقية وربطها بذكاء Mossad-pentast-ai.")

    target_options = [
        "http://scanme.nmap.org (هدف مصرح به رسمياً لفحص المنافذ والخدمات)",
        "http://127.0.0.1:5000 (بيئة فحص محلية معزولة)",
        "رابط مخصص آخر (Custom URL)"
    ]
    selected_target = st.selectbox("اختر هدفاً مصرحاً به:", target_options)
    
    if "Custom" in selected_target:
        target_url = st.text_input("أدخل الرابط المخصص:", "http://scanme.nmap.org")
    elif "scanme.nmap.org" in selected_target:
        target_url = "http://scanme.nmap.org"
    else:
        target_url = "http://127.0.0.1:5000"

    if st.button("⚡ بدء الفحص الحقيقي الآن (Launch Real Audit)"):
        if not target_url:
            st.error("يرجى إدخال عنوان الهدف أولاً!")
        else:
            status_box = st.status("🚀 جاري بدء الفحص الميداني بأدوات حقيقية...", expanded=True)
            
            with status_box:
                st.write(f"📡 **الهدف الجاري فحصه**: `{target_url}`")
                st.write("🔍 **المرحلة 1**: تشغيل Nmap بفحص المنافذ والخدمات الفعلية (-Pn -sV)...")
                
                log_placeholder = st.empty()
                logs = []
                def on_event(phase, ev_type, data):
                    logs.append(f"[{phase.upper()}] {data}")
                    log_placeholder.code("\n".join(logs[-8:]), language="text")

                if HexStrikeAgentBridge:
                    agent = HexStrikeAgentBridge(callback=on_event)
                    result = agent.run_full_assessment(target_url)
                    st.session_state.latest_report = result.get("report_markdown")
                else:
                    st.error("HexStrikeAgentBridge not found!")

                status_box.update(label="✅ اكتمل الفحص الأمني الحقيقي والتحليل بنجاح!", state="complete", expanded=False)

    # Display Report if available
    if st.session_state.latest_report:
        st.markdown("---")
        st.markdown("### 📋 التقرير الفني الحقيقي الصادر من العميل:")
        st.markdown(st.session_state.latest_report)
        st.download_button(
            label="📥 تحميل التقرير الكامل بصيغة Markdown",
            data=st.session_state.latest_report,
            file_name=f"mossad_audit_report_{int(time.time())}.md",
            mime="text/markdown"
        )

# TAB 2: Chat Mode
else:
    st.markdown("### 💬 الدردشة والاستشارة الأمنية المباشرة")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    if user_prompt := st.chat_input("اكتب سؤالك الأمني أو التكتيكي هنا..."):
        st.session_state.chat_history.append({"role": "user", "content": user_prompt})
        with st.chat_message("user"):
            st.markdown(user_prompt)

        with st.chat_message("assistant"):
            with st.spinner("جاري استشارة عقل Mossad-pentast-ai عبر البوابة..."):
                messages = [
                    {"role": "system", "content": "You are Mossad-pentast-ai, an Elite Offensive Security & Bug Bounty AI Copilot. You provide expert, deeply technical, and structured red-team & penetration testing guidance."},
                    {"role": "user", "content": user_prompt}
                ]
                reply = query_brain_chat(messages)
                st.markdown(reply)
                st.session_state.chat_history.append({"role": "assistant", "content": reply})
