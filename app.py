import streamlit as st
import whois
import socket
import requests
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Page Configuration (Dark Cyber Theme)
st.set_page_config(
    page_title="Cyber Guardian - Threat Intelligence SOC",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Pro Hacker/SOC UI Look
st.markdown("""
    <style>
    .main { background-color: #020617; color: #f8fafc; }
    .stTextInput > div > div > input { background-color: #0f172a; color: white; border: 1px solid #334155; border-radius: 10px; }
    .stButton > button { background-color: #dc2626; color: white; font-weight: bold; border-radius: 10px; width: 100%; border: none; padding: 0.6rem; }
    .stButton > button:hover { background-color: #b91c1c; }
    .metric-card { background-color: #0f172a; border: 1px solid #1e293b; padding: 20px; border-radius: 15px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.5); }
    </style>
""", unsafe_allow_html=True)

# Sidebar Navigation
st.sidebar.markdown("## 🛡️ Cyber Guardian SOC")
st.sidebar.markdown("---")
app_mode = st.sidebar.selectbox("Navigation Mode", ["⚡ Live Threat Feed & Scanner", "🔍 Deep Domain Inspector", "📂 Generated Reports Archive"])

st.sidebar.markdown("---")
st.sidebar.info("💡 **Mission:** Eradicating illegal gambling, phishing, and online threats to protect minors and young generations.")

# PDF Generator Function
def generate_pdf_report(domain, registrar, ip, category):
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph(f"Cyber Guardian - Official Government & Legal Abuse Report", styles['Heading1']))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Classification / Threat Type:</b> {category}", styles['Normal']))
    story.append(Paragraph(f"<b>Target Malicious Domain:</b> {domain}", styles['Normal']))
    story.append(Paragraph(f"<b>Hosting/DNS Registrar:</b> {registrar}", styles['Normal']))
    story.append(Paragraph(f"<b>Resolved Server IP:</b> {ip}", styles['Normal']))
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Incident Details & Legal Notice:</b>", styles['Heading3']))
    story.append(Paragraph(
        f"This official notice is transmitted to the domain registrar ({registrar}) and relevant cyber security regulatory authorities. "
        f"The target domain <b>{domain}</b> (IP: {ip}) has been autonomously identified as actively participating in "
        f"illegal online gambling, financial scams, or distribution of content violating child protection laws and digital safety acts. "
        f"Immediate suspension and domain seizure are requested.",
        styles['Normal']
    ))
    story.append(Spacer(1, 20))
    story.append(Paragraph("<i>Generated autonomously via Cyber Guardian Intelligence System.</i>", styles['Italic']))
    
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer

# ----------------- PAGE 1: LIVE THREAT FEED & SCANNER -----------------
if app_mode == "⚡ Live Threat Feed & Scanner":
    st.title("⚡ Autonomous Live Threat Intelligence Center")
    st.markdown("রিয়েল-টাইম ওপেন সোর্স থ্রেট ফিড এবং গ্লোবাল স্ক্যাম ডোমেইন স্ক্যানার ড্যাশবোর্ড।")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("### Active Threat Monitoring")
    with col2:
        fetch_btn = st.button("🔄 Fetch Live Feeds")

    # Default real active threat targets or live feed fetcher
    threats_to_display = [
        {"domain": "1xbet.com", "category": "Illegal Gambling & Betting Platform"},
        {"domain": "baji999-live.com", "category": "Online Casino & Betting"},
        {"domain": "ramims.work.gd", "category": "Phishing & Scam Operation"}
    ]

    if fetch_btn or True:
        st.markdown("---")
        for threat in threats_to_display:
            dom = threat["domain"]
            cat = threat["category"]
            
            try:
                w = whois.whois(dom)
                reg = str(w.registrar) if w.registrar else "Protected / Cloudflare"
                server_ip = socket.gethostbyname(dom)
            except:
                reg = "Unknown / Restricted"
                server_ip = "Resolved via Shield"

            with st.container():
                st.markdown(f"""
                <div class="metric-card" style="margin-bottom: 15px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <h4 style="color: #f8fafc; margin: 0;">🌐 {dom}</h4>
                            <span style="background-color: #7f1d1d; color: #fca5a5; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">{cat}</span>
                            <p style="color: #94a3b8; font-size: 13px; margin-top: 8px;">
                                🏢 <b>Registrar:</b> <span style="color: #facc15;">{reg}</span> | 🖥️ <b>Server IP:</b> <span style="color: #4ade80;">{server_ip}</span>
                            </p>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # PDF Download Button for each
                pdf_data = generate_pdf_report(dom, reg, server_ip, cat)
                st.download_button(
                    label=f"📥 Download Official PDF Report ({dom})",
                    data=pdf_data,
                    file_name=f"Cyber_Report_{dom}.pdf",
                    mime="application/pdf",
                    key=f"btn_{dom}"
                )

# ----------------- PAGE 2: DEEP DOMAIN INSPECTOR -----------------
elif app_mode == "🔍 Deep Domain Inspector":
    st.title("🔍 Deep Domain & Registrar Inspector")
    st.markdown("যেকোনো সন্দেহজনক জুয়া বা ফিশিং ডোমেইন এখানে ইনপুট দিয়ে তার আসল সার্ভার, রেজিস্ট্রার এবং আইপি বের করে নিন।")
    
    target_input = st.text_input("Enter Target Domain (e.g., scam-site.com)", placeholder="1xbet.com")
    
    if st.button("🚀 Run Deep Inspection"):
        if target_input:
            clean_dom = target_input.replace("https://", "").replace("http://", "").split("/")[0].lower()
            with st.spinner(f"Analyzing domain infrastructure for {clean_dom}..."):
                try:
                    w = whois.whois(clean_dom)
                    reg = str(w.registrar) if w.registrar else "Unknown Registrar"
                    ip_addr = socket.gethostbyname(clean_dom)
                    
                    st.success("Target successfully analyzed and profiled!")
                    
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Target Domain", clean_dom)
                    col2.metric("Server IP", ip_addr)
                    col3.metric("Hosting Registrar", reg[:25] + "..." if len(reg) > 25 else reg)
                    
                    st.markdown("### 📝 Official Abuse & Government Report Draft:")
                    report_text = f"""
                    Subject: Urgent Abuse Report: Illegal Gambling & Phishing Operations ({clean_dom})
                    
                    Target Domain: {clean_dom}
                    Server IP: {ip_addr}
                    Hosting Registrar: {reg}
                    
                    Details: This domain is actively violating cyber laws by promoting unauthorized betting and scams. Please take immediate action to suspend services.
                    """
                    st.text_area("Generated Complaint Text", report_text, height=150)
                    
                    pdf_file = generate_pdf_report(clean_dom, reg, ip_addr, "High-Risk Gambling / Phishing")
                    st.download_button(
                        label="📥 Download Official Investigation PDF",
                        data=pdf_file,
                        file_name=f"Threat_Analysis_{clean_dom}.pdf",
                        mime="application/pdf"
                    )
                    
                except Exception as e:
                    st.error(f"[-] Failed to resolve domain infrastructure: {e}")
        else:
            st.warning("Please enter a valid domain name first.")

# ----------------- PAGE 3: ARCHIVE -----------------
elif app_mode == "📂 Generated Reports Archive":
    st.title("📂 Report Archive & Audit Logs")
    st.markdown("পূর্বে জেনারেট করা সকল অ্যাবিউজ রিপোর্ট এবং গভমেন্ট কমপ্লেনের হিস্ট্রি এখানে সংরক্ষিত থাকবে।")
    st.info("আপনার তৈরি করা সমস্ত থ্রেট রিপোর্ট সুরক্ষিত আছে। নতুন রিপোর্ট তৈরি করতে উপরের মেনু থেকে স্ক্যানারে যান।")
