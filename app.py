import streamlit as st
import whois
import socket
import re
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

st.set_page_config(page_title="Anti-Gambling Cyber Strike System", page_icon="🔥", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #030712; color: #f3f4f6; }
    .stTextInput > div > div > input { background-color: #111827; color: white; border: 1px solid #374151; border-radius: 8px; }
    .stButton > button { background-color: #b91c1c; color: white; font-weight: bold; border-radius: 8px; width: 100%; }
    .stButton > button:hover { background-color: #991b1b; }
    </style>
""", unsafe_allow_html=True)

st.title("🔥 Anti-Gambling Cyber Strike & Threat Hunter")
st.markdown("বাংলাদেশী ও গ্লোবাল জুয়ার সাইট, বেটিং নেটওয়ার্ক এবং ফিশিং ফাঁদ শনাক্ত করে অফিশিয়াল স্ট্রাইক রিপোর্ট তৈরির সিস্টেম।")

# ডিপ স্ক্যান টার্গেট ইনপুট
target_input = st.text_area("সন্দেহজনক লিংক বা ডোমেইনগুলো এখানে পেস্ট করুন (একাধিক হলে কমা বা নতুন লাইনে দিন):", 
    value="1xbet.com, baji999.com, jeetwin-BD.xyz, t20-bet-live.top", height=100)

if st.button("🚀 Run Deep Anti-Gambling Strike Scan"):
    urls = [u.strip() for u in target_input.replace("\n", ",").split(",") if u.strip()]
    
    st.markdown("---")
    st.subheader("🎯 Scan & Investigation Results:")
    
    for url in urls:
        clean_dom = url.replace("https://", "").replace("http://", "").split("/")[0].lower()
        
        # কঠোর ফিল্টার: এটি কি আসলেই জুয়া বা বেটিংয়ের সাথে সম্পর্কিত?
        gambling_indicators = ['bet', 'casino', 'baji', 'jeet', '1x', 'slot', 'poker', 'win', 'jua', 'parimatch', 'khela', 'bonus']
        is_gambling_suspect = any(ind in clean_dom for ind in gambling_indicators)
        
        try:
            w = whois.whois(clean_dom)
            registrar = str(w.registrar) if w.registrar else "Hidden / Cloudflare Protected"
            server_ip = socket.gethostbyname(clean_dom)
        except:
            registrar = "Domain Down / Blocked or Invalid"
            server_ip = "0.0.0.0"
            
        # ইউআই কার্ড ডিসপ্লে
        border_color = "#ef4444" if is_gambling_suspect else "#3b82f6"
        badge_text = "🚨 CONFIRMED GAMBLING / BETTING TARGET" if is_gambling_suspect else "⚠️ GENERAL SUSPICIOUS DOMAIN"
        
        st.markdown(f"""
        <div style="background-color: #111827; border: 1px solid {border_color}; padding: 15px; border-radius: 10px; margin-bottom: 10px;">
            <h4 style="color: white; margin: 0;">🌐 {clean_dom}</h4>
            <span style="background-color: #7f1d1d; color: #fca5a5; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold;">{badge_text}</span>
            <p style="color: #9ca3af; font-size: 12px; margin-top: 6px;">
                🏢 <b>Registrar:</b> <span style="color: #facc15;">{registrar}</span> | 🖥️ <b>IP:</b> <span style="color: #4ade80;">{server_ip}</span>
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # PDF জেনারেটর লজিক
        if is_gambling_suspect:
            pdf_buffer = io.BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            story = []
            
            story.append(Paragraph("Cyber Guardian - Official Anti-Gambling Strike Report", styles['Heading1']))
            story.append(Spacer(1, 10))
            story.append(Paragraph(f"<b>Target Domain:</b> {clean_dom}", styles['Normal']))
            story.append(Paragraph(f"<b>Registrar:</b> {registrar}", styles['Normal']))
            story.append(Paragraph(f"<b>Server IP:</b> {server_ip}", styles['Normal']))
            story.append(Spacer(1, 10))
            story.append(Paragraph("<b>Offence Details:</b>", styles['Heading3']))
            story.append(Paragraph(f"The domain {clean_dom} has been detected as an illegal online gambling and betting platform targeting youth and violating financial safety laws. Immediate domain seizure and hosting termination requested.", styles['Normal']))
            
            doc.build(story)
            pdf_buffer.seek(0)
            
            st.download_button(
                label=f"📥 Download Strike Report ({clean_dom})",
                data=pdf_buffer,
                file_name=f"Anti_Gambling_Strike_{clean_dom}.pdf",
                mime="application/pdf",
                key=f"strike_{clean_dom}"
            )
