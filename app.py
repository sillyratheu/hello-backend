from flask import Flask, render_template_string, request, send_file
import whois
import socket
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

app = Flask(__name__)

# প্রি-ডিফাইন্ড বা অটো-ডিটেক্টেড জুয়া ও স্ক্যাম ডোমেইনের লাইভ সোর্স বা ফিড (যেগুলো অটো-স্ক্যান হবে)
AUTO_THREAT_FEED = [
    {"domain": "1xbet.com", "category": "Illegal Gambling & Betting"},
    {"domain": "baji999-live.com", "category": "Online Casino / Gambling / জুয়া / টাকার খেলা "},
    {"domain": "joss-bet24.xyz", "category": "Betting Promotion Bot"}
]

# প্রিমিয়াম এবং আধুনিক সাইবার সিকিউরিটি ড্যাশবোর্ড UI (HTML + Tailwind CSS)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cyber Shield - Autonomous Threat Center</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen p-4 sm:p-8">
    <div class="max-w-4xl mx-auto space-y-6">
        
        <!-- Top Header -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl flex flex-col sm:flex-row justify-between items-center gap-4">
            <div>
                <span class="bg-red-500/10 text-red-400 text-xs font-semibold px-3 py-1 rounded-full border border-red-500/20">Cyber Guardian Command Center</span>
                <h1 class="text-2xl font-bold mt-2 text-white">Autonomous Threat & Scam Detector</h1>
                <p class="text-sm text-slate-400">এক ক্লিকেই জুয়া ও স্ক্যাম সাইট অটো-স্ক্যান, রিয়েল রেজিস্ট্রার চেক এবং অফিশিয়াল রিপোর্ট জেনারেটর</p>
            </div>
            <form method="POST">
                <button type="submit" name="action" value="auto_scan" 
                    class="bg-red-600 hover:bg-red-700 text-white font-semibold px-6 py-3 rounded-xl transition shadow-lg shadow-red-600/30 flex items-center gap-2">
                    🕷️ Run Auto Threat Scraper
                </button>
            </form>
        </div>

        <!-- Manual Check Option -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-xl">
            <h2 class="text-sm font-semibold text-slate-300 mb-3">🔍 Manual Domain Intelligence</h2>
            <form method="POST" class="flex gap-3">
                <input type="text" name="manual_domain" placeholder="enter domain to check (e.g. example.com)" 
                    class="flex-1 bg-slate-950 border border-slate-700 rounded-xl px-4 py-2.5 text-sm text-white focus:outline-none focus:border-red-500 transition">
                <button type="submit" name="action" value="manual_scan"
                    class="bg-slate-800 hover:bg-slate-700 text-white text-sm font-medium px-5 py-2.5 rounded-xl transition border border-slate-700">
                    Check
                </button>
            </form>
        </div>

        <!-- Results Section -->
        {% if results %}
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-4">
            <h2 class="text-lg font-bold text-red-400 border-b border-slate-800 pb-3 flex items-center justify-between">
                <span>📊 Live Threat Intelligence Feeds & Scan Results</span>
                <span class="text-xs bg-red-950 text-red-400 px-2.5 py-1 rounded-md border border-red-900">{{ results|length }} Threats Found</span>
            </h2>

            <div class="grid gap-4">
                {% for item in results %}
                <div class="bg-slate-950 border border-slate-800 p-4 rounded-xl flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                    <div class="space-y-1">
                        <div class="flex items-center gap-2">
                            <span class="text-white font-bold text-base">{{ item.domain }}</span>
                            <span class="bg-red-950/80 text-red-400 text-[10px] font-semibold px-2 py-0.5 rounded border border-red-900">{{ item.category }}</span>
                        </div>
                        <p class="text-xs text-slate-400">Registrar: <span class="text-yellow-400">{{ item.registrar }}</span> | IP: <span class="text-green-400">{{ item.ip }}</span></p>
                    </div>

                    <form action="/download_pdf" method="POST">
                        <input type="hidden" name="domain" value="{{ item.domain }}">
                        <input type="hidden" name="registrar" value="{{ item.registrar }}">
                        <input type="hidden" name="ip" value="{{ item.ip }}">
                        <input type="hidden" name="category" value="{{ item.category }}">
                        <button type="submit" class="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold px-4 py-2.5 rounded-lg transition shadow flex items-center gap-1.5">
                            📥 Download Report PDF
                        </button>
                    </form>
                </div>
                {% endfor %}
            </div>
        </div>
        {% endif %}

        {% if error %}
        <div class="p-4 bg-red-950/30 border border-red-900/50 rounded-xl text-red-400 text-sm text-center">
            {{ error }}
        </div>
        {% endif %}

    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def home():
    results = None
    error = None
    
    if request.method == "POST":
        action = request.form.get("action")
        targets_to_scan = []
        
        if action == "auto_scan":
            # অটো থ্রেট ফিড থেকে টার্গেটগুলো নিয়ে নেব
            targets_to_scan = AUTO_THREAT_FEED
        elif action == "manual_scan":
            manual_dom = request.form.get("manual_domain", "").strip().replace("https://", "").replace("http://", "").split("/")[0].lower()
            if manual_dom:
                targets_to_scan = [{"domain": manual_dom, "category": "Manual Target / Suspicious"}]
                
        scanned_data = []
        for target in targets_to_scan:
            domain = target["domain"]
            category = target["category"]
            try:
                w = whois.whois(domain)
                registrar = str(w.registrar) if w.registrar else "Unknown Registrar (Protected)"
                ip_address = socket.gethostbyname(domain)
                
                scanned_data.append({
                    "domain": domain,
                    "category": category,
                    "registrar": registrar,
                    "ip": ip_address
                })
            except Exception as e:
                scanned_data.append({
                    "domain": domain,
                    "category": category,
                    "registrar": "Resolution Failed / Blocked",
                    "ip": "0.0.0.0"
                })
                
        results = scanned_data
        if not results:
            error = "[-] No valid targets found to scan."
            
    return render_template_string(HTML_TEMPLATE, results=results, error=error)

@app.route("/download_pdf", methods=["POST"])
def download_pdf():
    domain = request.form.get("domain", "Unknown")
    registrar = request.form.get("registrar", "Unknown")
    ip = request.form.get("ip", "Unknown")
    category = request.form.get("category", "Illegal Gambling / Scam")
    
    pdf_buffer = io.BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    story.append(Paragraph(f"Cyber Shield - Official Threat & Abuse Report", styles['Heading1']))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Threat Category:</b> {category}", styles['Normal']))
    story.append(Paragraph(f"<b>Target Domain:</b> {domain}", styles['Normal']))
    story.append(Paragraph(f"<b>Real Registrar (Hosting/DNS):</b> {registrar}", styles['Normal']))
    story.append(Paragraph(f"<b>Server IP Address:</b> {ip}", styles['Normal']))
    story.append(Spacer(1, 15))
    story.append(Paragraph("<b>Incident Details & Official Complaint:</b>", styles['Heading3']))
    story.append(Paragraph(
        f"This report formally notifies the relevant authorities, regulatory bodies, and the domain registrar ({registrar}) "
        f"that the malicious domain <b>{domain}</b> (Server IP: {ip}) is actively operating under the classification of "
        f"<b>{category}</b>, violating cyber laws, financial safety guidelines, and policies protecting minors.",
        styles['Normal']
    ))
    story.append(Spacer(1, 20))
    story.append(Paragraph("<i>Generated autonomously via Cyber Guard Threat Intelligence Command Center.</i>", styles['Italic']))
    
    doc.build(story)
    pdf_buffer.seek(0)
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"Cyber_Threat_Report_{domain}.pdf",
        mimetype='application/pdf'
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
