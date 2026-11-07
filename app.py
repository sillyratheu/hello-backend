from flask import Flask, render_template_string, request
import whois
import socket

app = Flask(__name__)

# সুন্দর এবং আধুনিক একটি ডার্ক-থিম UI (HTML + Tailwind CSS)
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cyber Shield - Scam & Gambling Tracker</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex flex-col items-center justify-center p-4">
    <div class="max-w-xl w-full bg-slate-900 border border-slate-800 rounded-2xl p-6 shadow-2xl">
        <div class="text-center mb-6">
            <span class="bg-red-500/10 text-red-400 text-xs font-semibold px-3 py-1 rounded-full border border-red-500/20">Trust & Safety Shield</span>
            <h1 class="text-2xl font-bold mt-2 text-white">Scam & Gambling Domain Detector</h1>
            <p class="text-sm text-slate-400 mt-1">জুয়ার সাইট ও ফিশিং ডোমেইন ট্র্যাক করে রিপোর্ট জেনারেট করুন</p>
        </div>

        <form method="POST" class="space-y-4">
            <div>
                <label class="block text-xs font-medium text-slate-300 mb-1">Target Domain (যেমন: 1xbet.com)</label>
                <input type="text" name="domain" required placeholder="domain.com" 
                    class="w-full bg-slate-950 border border-slate-700 rounded-xl px-4 py-3 text-white focus:outline-none focus:border-red-500 transition">
            </div>
            <button type="submit" 
                class="w-full bg-red-600 hover:bg-red-700 text-white font-medium py-3 rounded-xl transition shadow-lg shadow-red-600/20">
                🚀 Scan & Generate Report
            </button>
        </form>

        {% if result %}
        <div class="mt-6 p-4 bg-slate-950 border border-slate-800 rounded-xl space-y-3 text-sm">
            <h3 class="font-semibold text-red-400 border-b border-slate-800 pb-2">📊 Scan Results:</h3>
            <p><strong class="text-slate-400">Target:</strong> <span class="text-white">{{ result.domain }}</span></p>
            <p><strong class="text-slate-400">Registrar:</strong> <span class="text-yellow-400">{{ result.registrar }}</span></p>
            <p><strong class="text-slate-400">Server IP:</strong> <span class="text-green-400">{{ result.ip }}</span></p>
            
            <div class="mt-4 pt-3 border-t border-slate-800">
                <h4 class="font-semibold text-blue-400 mb-1">📝 Ready-to-Send Abuse Report:</h4>
                <div class="bg-slate-900 p-3 rounded-lg text-xs text-slate-300 font-mono select-all border border-slate-800">
                    Subject: Urgent: Report on Illegal Gambling/Phishing Domain ({{ result.domain }})<br><br>
                    Dear Abuse Department ({{ result.registrar }}),<br>
                    This domain is actively involved in illegal online gambling/scam promotion targeting minors and violating local cyber laws. Server IP: {{ result.ip }}. Please suspend this domain immediately.
                </div>
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
    if request.method == "POST":
        domain = request.form.get("domain", "").strip().replace("https://", "").replace("http://", "").split("/")[0]
        try:
            w = whois.whois(domain)
            registrar = str(w.registrar) if w.registrar else "Unknown Registrar"
            ip_address = socket.gethostbyname(domain)
            
            result = {
                "domain": domain,
                "registrar": registrar,
                "ip": ip_address
            }
        except Exception as e:
            error = f"[-] Could not fetch domain details. It might be blocked or invalid. ({e})"
            
    return render_template_string(HTML_TEMPLATE, result=result, error=error)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
