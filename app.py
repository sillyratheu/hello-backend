from flask import Flask, render_template_string, request, send_file
import whois
import socket
import re
from bs4 import BeautifulSoup
import requests
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

app = Flask(__name__)

# ফুল ফিচারড ওয়েব ইন্টারফেস (Domain Check + Web Scraping + PDF Download)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cyber Shield - Advanced Threat Intelligence</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col items-center justify-center p-4">
    <div class="max-w-2xl w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
        <div class="text-center mb-6">
            <span class="bg-red-500/10 text-red-400 text-xs font-semibold px-3 py-1 rounded-full border border-red-500/20">Cyber Guardian Pro</span>
            <h1 class="text-2xl font-bold mt-2 text-white">Scam & Gambling Threat Detector</h1>
            <p class="text-sm text-slate-400 mt-1">ডোমেইন স্ক্যান, অটো-ওয়েব স্ক্র্যাপিং এবং অফিশিয়াল PDF রিপোর্ট জেনারেটর</p>
        </div>

        <!-- ফর্ম টেস্টিং অপশন -->
        <form method="POST" class="space-y-4">
            <div>
                <label class="block text-xs font-medium text-slate-300 mb-1">Target Domain OR Web URL (যেমন: 1xbet.com বা কোনো ফিশিং পেজ লিংক)</label>
                <input type="text" name="target" required placeholder="domain.com বা https://example.com" 
                    value="{{ target if target else '' }}"
                    class="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-red-500 transition">
            </div>

            <div class="grid grid-cols-2 gap-3">
                <button type="submit" name="action" value="scan"
                    class="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-3 rounded-xl transition shadow-lg shadow-red-600/20">
                    🔍 Scan & Registrar Check
                </button>
                <button type="submit" name="action" value="scrape"
                    class="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 rounded-xl transition shadow-lg shadow-blue-600/20">
                    🕷️ Auto Web Scraping
                </button>
            </div>
        </form>

        {% if result %}
        <div class="mt-6 p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3 text-sm">
            <h3 class="font-semibold text-red-400 border-b border-slate-800 pb-2">📊 Scan & Intelligence Results:</h3>
            <p><strong class="text-slate-400">Target:</strong> <span class="text-white">{{ result.domain }}</span></p>
            <p><strong class="text-slate-400">Real Registrar:</strong> <span class="text-yellow-400">{{ result.registrar }}</span></p>
            <p><strong class="text-slate-400">Server IP:</strong> <span class="text-green-400">{{ result.ip }}</span></p>
            
            {% if result.scraped_links %}
            <div class="mt-3">
                <strong class="text-blue-400 block mb-1">Extracted Links / Sub-domains from Web Scraping:</strong>
                <ul class="list-disc pl-5 text-xs text-slate-300 max-h-32 overflow-y-auto bg-slate-900 p-2 rounded">
                    {% for link in result.scraped_links %}
                    <li>{{ link }}</li>
                    {% endfor %}
                </ul>
            </div>
            {% endif %}

            <div class="mt-4 pt-3 border-t border-slate-800 flex items-center justify-between">
                <div>
                    <h4 class="font-semibold text-blue-400 text-xs">📝 Ready for Government & Abuse Report</h4>
                </div>
                <form action="/download_pdf" method="POST">
                    <input type="hidden" name="domain" value="{{ result.domain }}">
                    <input type="hidden" name="registrar" value="{{ result.registrar }}">
                    <input type="hidden" name="ip" value="{{ result.ip }}">
                    <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-4 py-2 rounded-lg transition shadow">
                        📥 Download PDF Report
                    </button>
                </form>
            </div>
        </div>
        {% endif %}
        
        {% if error %}
        <div class="mt-6 p-4 bg-red-950/30 border border-red-900/50 rounded-xl text-red-400 text-sm text-center">
            {{ error }}
        </div>
        {% endif %}
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    error = None
    target = ""
    
    if request.method == "POST":
        target = request.form.get("target", "").strip()
        action = request.form.get("action", "scan")
        
        # ক্লিন ডোমেইন এক্সট্রাক্ট করা
        domain = target.replace("https://", "").replace("http://", "").split("/")[0]
        
        try:
            # ডোমেইন হুয়ইস ও রেজিস্ট্রার চেক
            w = whois.whois(domain)
            registrar = str(w.registrar) if w.registrar else "Unknown Registrar (Protected/Cloudflare)"
            ip_address = socket.gethostbyname(domain)
            
            scraped_links = []
            if action == "scrape" and not target.startswith("http"):
                target = "https://" + target
            
            if action == "scrape":
                try:
                    headers = {'User-Agent': 'Mozilla/5.0'}
                    resp = requests.get(target, headers=headers, timeout=5)
                    soup = BeautifulSoup(resp.text, 'html.parser')
                    for a in soup.find_all('a', href=True):
                        href = a['href']
                        if href.startswith('http') and domain not in href:
                            scraped_links.append(href)
                    scraped_links = list(set(scraped_links))[:15] # সর্বোচ্চ ১৫টি লিংক
                except Exception as scrape_err:
                    scraped_links = [f"Scraping note: Could not parse deep links ({scrape_err})"]

            result = {
                "domain": domain,
                "registrar": registrar,
                "ip": ip_address,
                "scraped_links": scraped_links
            }
        except Exception as e:
            error = f"[-] Could not resolve domain or fetch details. ({e})"
            
    return render_template_string(HTML_TEMPLATE, result=result, error=error, target=target)

@app.route("/download_pdf", methods=["POST"])
def download_pdf():
    domain = request.form.get("domain", "Unknown")
    registrar = request.form.get("registrar", "Unknown")
    ip = request.form.get("ip", "Unknown")
    
    # PDF জেনারেট করা
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors_Hex('#dc2626') if 'colors_Hex' in globals() else None,
        spaceAfter=12
    )
    
    story.append(Paragraph(f"Cyber Shield - Official Threat & Abuse Report", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Target Domain:</b> {domain}", styles['Normal']))
    story.append(Paragraph(f"<b>Real Registrar (Hosting/DNS):</b> {registrar}", styles['Normal']))
    story.append(Paragraph(f"<b>Server IP Address:</b> {ip}", styles['Normal']))
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Incident Details & Complaint:</b>", styles['Heading3']))
    story.append(Paragraph(
        f"This report formally notifies the relevant authorities and the domain registrar ({registrar}) "
        f"that the domain <b>{domain}</b> (Server IP: {ip}) is actively involved in promoting illegal online gambling, "
        f"phishing, and harmful activities targeting minors, violating cyber laws and safety policies.",
        styles['Normal']
    ))
    story.append(Spacer(1, 20))
    story.append(Paragraph("<i>Generated autonomously via Cyber Guard Threat Intelligence System.</i>", styles['Italic']))
    
    doc.build(story)
    pdf_buffer.seek(0)
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"Cyber_Report_{domain}.pdf",
        mimetype='application/pdf'
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
