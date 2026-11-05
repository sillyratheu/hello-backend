import os
from flask import Flask, redirect, render_template_string, request, session, url_for
import requests

app = Flask(__name__)
app.secret_key = os.urandom(24)

GITHUB_CLIENT_ID = "Iv23libgx7qvJ0ICF7Te"
GITHUB_CLIENT_SECRET = "ff274386956b45b6b07318c0428d769c4c442cc8"

GITHUB_OWNER = "sillyratheu"  # Apnar github username
GITHUB_BUILDER_REPO = "hello-backend"  # Apnar builder repo-r nam


# --- LANDING PAGE WITH TYPING ANIMATION (Black & White Minimalist Theme) ---
LANDING_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shahajjo - Cloud APK Builder</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        body { font-family: 'Geist', sans-serif; background-color: #000000; color: #ededed; }
        /* Typing cursor animation */
        .typing-effect::after {
            content: '|';
            animation: blink 1s infinite;
        }
        @keyframes blink { 0%, 100% { opacity: 1; } 50% { opacity: 0; } }
    </style>
</head>
<body class="min-h-screen flex flex-col justify-between selection:bg-white selection:text-black">
    
    <!-- Navbar -->
    <header class="w-full border-b border-neutral-900 px-6 py-4 flex justify-between items-center max-w-6xl mx-auto">
        <div class="text-lg font-bold tracking-tight text-white flex items-center gap-2">
            <span class="w-2.5 h-2.5 bg-white rounded-full"></span> Shahajjo.
        </div>
        <div>
            {% if user %}
                <a href="/dashboard" class="text-xs uppercase tracking-widest bg-white text-black font-semibold px-4 py-2 rounded-full hover:bg-neutral-200 transition">Dashboard</a>
            {% else %}
                <a href="/login" class="text-xs uppercase tracking-widest border border-neutral-800 text-neutral-300 font-medium px-4 py-2 rounded-full hover:border-white hover:text-white transition">Sign In</a>
            {% endif %}
        </div>
    </header>

    <!-- Hero Section -->
    <main class="flex-grow flex flex-col items-center justify-center text-center px-4 max-w-3xl mx-auto">
        <div class="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-neutral-800 bg-neutral-950 text-xs text-neutral-400 mb-6">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span> Cloud-Powered Native APK Compiler
        </div>
        
        <h1 class="text-4xl md:text-6xl font-extrabold tracking-tight text-white mb-6 h-24 md:h-auto">
            Build Android Apps from <br><span id="typing-text" class="text-neutral-400 typing-effect"></span>
        </h1>
        
        <p class="text-neutral-400 text-sm md:text-base max-w-xl mb-10 font-light leading-relaxed">
            Transform any GitHub repository into a production-ready native APK automatically via serverless cloud workflows. No local setup required.
        </p>

        <div class="flex flex-col sm:flex-row gap-4 w-full justify-center">
            {% if user %}
                <a href="/dashboard" class="bg-white text-black font-medium px-8 py-3.5 rounded-xl hover:bg-neutral-200 transition shadow-lg shadow-white/5">Open Dashboard</a>
            {% else %}
                <a href="/login" class="bg-white text-black font-medium px-8 py-3.5 rounded-xl hover:bg-neutral-200 transition shadow-lg shadow-white/5 flex items-center justify-center gap-2">
                    <svg class="w-4 h-4 fill-current" viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
                    Get Started with GitHub
                </a>
            {% endif %}
        </div>
    </main>

    <!-- Footer -->
    <footer class="w-full border-t border-neutral-900 py-6 text-center text-xs text-neutral-600">
        &copy; 2026 Shahajjo Corporation. All rights reserved.
    </footer>

    <!-- Typing Animation Script -->
    <script>
        const words = ["GitHub Repositories.", "Public Source Code.", "Python & Native Projects."];
        let i = 0;
        let timer;

        function typingEffect() {
            let word = words[i].split("");
            var loopTyping = function() {
                if (word.length > 0) {
                    document.getElementById('typing-text').innerHTML += word.shift();
                } else {
                    setTimeout(deletingEffect, 2000);
                    return false;
                }
                timer = setTimeout(loopTyping, 100);
            };
            loopTyping();
        }

        function deletingEffect() {
            let word = words[i].split("");
            var loopDeleting = function() {
                if (word.length > 0) {
                    word.pop();
                    document.getElementById('typing-text').innerHTML = word.join("");
                } else {
                    if (words.length > (i + 1)) {
                        i++;
                    } else {
                        i = 0;
                    }
                    setTimeout(typingEffect, 500);
                    return false;
                }
                timer = setTimeout(loopDeleting, 50);
            };
            loopDeleting();
        }

        typingEffect();
    </script>
</body>
</html>
"""


# --- DASHBOARD TEMPLATE (Black & White Minimalist Theme) ---
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Shahajjo</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link href="https://fonts.googleapis.com/css2?family=Geist:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Geist', sans-serif; background-color: #000000; color: #ededed; }</style>
</head>
<body class="min-h-screen p-6 selection:bg-white selection:text-black">
    <div class="max-w-2xl mx-auto">
        <!-- Top Bar -->
        <div class="flex justify-between items-center bg-neutral-950 border border-neutral-900 rounded-2xl p-6 mb-6 shadow-2xl">
            <div class="flex items-center gap-4">
                <img src="{{ user.avatar_url }}" class="w-11 h-11 rounded-full border border-neutral-800">
                <div>
                    <h2 class="text-sm font-semibold text-white">@{{ user.login }}</h2>
                    <p class="text-xs text-neutral-500">Active Session Secured</p>
                </div>
            </div>
            <div class="flex items-center gap-3">
                <a href="/" class="bg-neutral-900 hover:bg-neutral-800 text-neutral-300 px-4 py-2 rounded-xl text-xs font-medium transition border border-neutral-800">Home</a>
                <a href="/logout" class="bg-neutral-900 hover:bg-red-950/30 text-red-400 px-4 py-2 rounded-xl text-xs font-medium transition border border-neutral-800 hover:border-red-900/50">Logout</a>
            </div>
        </div>
        
        <!-- Build Card -->
        <div class="bg-neutral-950 border border-neutral-900 rounded-2xl p-8 shadow-2xl">
            <h3 class="text-lg font-bold text-white mb-1">Compiler Control Center</h3>
            <p class="text-neutral-500 text-xs mb-6">Select your personal repository or enter a public link to start compilation.</p>
            
            <form action="/start-build" method="POST" class="space-y-5">
                <div>
                    <label class="block text-xs font-medium text-neutral-400 mb-2 uppercase tracking-wider">Select Your Repository</label>
                    <select name="selected_repo" class="w-full bg-black border border-neutral-800 rounded-xl p-3.5 text-sm text-neutral-200 focus:outline-none focus:border-white transition">
                        <option value="">-- Choose from your repositories --</option>
                        {% for repo in repos %}
                            <option value="{{ repo.clone_url }}">{{ repo.full_name }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div class="text-center text-xs text-neutral-600 font-semibold tracking-widest">— OR —</div>

                <div>
                    <label class="block text-xs font-medium text-neutral-400 mb-2 uppercase tracking-wider">Public Repository URL</label>
                    <input type="url" name="custom_repo" placeholder="https://github.com/username/repository" class="w-full bg-black border border-neutral-800 rounded-xl p-3.5 text-sm text-neutral-200 placeholder-neutral-700 focus:outline-none focus:border-white transition">
                </div>

                <div>
                    <label class="block text-xs font-medium text-neutral-400 mb-2 uppercase tracking-wider">App Name</label>
                    <input type="text" name="app_name" required placeholder="My Awesome App" class="w-full bg-black border border-neutral-800 rounded-xl p-3.5 text-sm text-neutral-200 placeholder-neutral-700 focus:outline-none focus:border-white transition">
                </div>

                <button type="submit" class="w-full bg-white text-black font-semibold py-3.5 px-4 rounded-xl hover:bg-neutral-200 transition shadow-lg shadow-white/5 text-sm cursor-pointer mt-2">
                    Initialize Cloud Build 🚀
                </button>
            </form>
        </div>
    </div>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(LANDING_TEMPLATE, user=session.get("user"))


@app.route("/login")
def login():
    return redirect(f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&scope=repo,workflow")


@app.route("/auth/callback")
def auth_callback():
    code = request.args.get("code")
    if not code:
        return "Error", 400
    
    res = requests.post("https://github.com/login/oauth/access_token", json={
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code
    }, headers={"Accept": "application/json"}).json()
    
    token = res.get("access_token")
    if not token:
        return "Token Error", 400
    
    user = requests.get("https://api.github.com/user", headers={"Authorization": f"Bearer {token}"}).json()
    
    # Save user details and token securely in Flask session (persistent login)
    session["user"] = user
    session["access_token"] = token
    return redirect(url_for("home"))


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("home"))
    
    access_token = session.get("access_token")
    repos_response = requests.get("https://api.github.com/user/repos?per_page=100&sort=updated", headers={"Authorization": f"Bearer {access_token}"})
    repos = repos_response.json() if repos_response.status_code == 200 else []
    
    return render_template_string(DASHBOARD_TEMPLATE, user=session["user"], repos=repos if isinstance(repos, list) else [])


@app.route("/start-build", methods=["POST"])
def start_build():
    if "user" not in session:
        return redirect(url_for("home"))
    
    target_repo = request.form.get("custom_repo") or request.form.get("selected_repo")
    app_name = request.form.get("app_name")
    
    if not target_repo:
        return "Error: Please select a repository or enter a valid public repo link!", 400

    dispatch_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_BUILDER_REPO}/dispatches"
    headers = {
        "Authorization": f"Bearer {session['access_token']}",
        "Accept": "application/vnd.github+json"
    }
    payload = {
        "event_type": "build-apk",
        "client_payload": {
            "repo_url": target_repo,
            "app_name": app_name,
            "user": session["user"]["login"]
        }
    }
    
    response = requests.post(dispatch_url, json=payload, headers=headers)
    
    if response.status_code == 204:
        return """
        <body style="background:#000; color:#fff; font-family:sans-serif; text-align:center; padding-top:100px;">
            <div style="background:#0a0a0a; border:1px solid #222; max-width:420px; margin:auto; padding:35px; border-radius:20px;">
                <h2 style="color:#fff; font-size:20px; font-weight:bold; margin-bottom:10px;">Build Triggered Successfully! 🚀</h2>
                <p style="color:#888; font-size:13px; line-height:1.5; margin-bottom:25px;">Apnar builder repo-te cloud build start hoye geche. Build complete hole apnar GitHub release ba artifact theke APK download korte parben.</p>
                <a href="/dashboard" style="display:inline-block; background:#fff; color:#000; font-weight:600; padding:12px 24px; text-decoration:none; border-radius:12px; font-size:13px;">Back to Dashboard</a>
            </div>
        </body>
        """
    else:
        return f"Failed to trigger build: {response.status_code} - {response.text}", 500


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
