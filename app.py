import os
from flask import Flask, redirect, render_template_string, request, session, url_for
import requests

app = Flask(__name__)
app.secret_key = os.urandom(24)

GITHUB_CLIENT_ID = "Iv23libgx7qvJ0ICF7Te"
GITHUB_CLIENT_SECRET = "ff274386956b45b6b07318c0428d769c4c442cc8"


# --- HOME PAGE TEMPLATE ---
HOME_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Shahajjo - Cloud APK Builder</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Inter', sans-serif; }</style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen flex items-center justify-center p-4">
    <div class="max-w-md w-full bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl text-center">
        <div class="inline-flex p-3 bg-blue-600/10 rounded-xl text-blue-500 mb-4">
            <svg class="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4"/></svg>
        </div>
        <h1 class="text-2xl font-bold tracking-tight text-white mb-2">Shahajjo APK Builder</h1>
        <p class="text-slate-400 text-sm mb-6">Build native APKs directly from your GitHub repositories securely using cloud workflows.</p>
        
        {% if user %}
            <div class="bg-slate-800/50 border border-slate-700/50 rounded-xl p-4 mb-6 flex items-center gap-4 text-left">
                <img src="{{ user.avatar_url }}" class="w-12 h-12 rounded-full border border-blue-500/30">
                <div>
                    <p class="font-semibold text-white">{{ user.name or user.login }}</p>
                    <p class="text-xs text-slate-400">@{{ user.login }}</p>
                </div>
            </div>
            <div class="space-y-3">
                <a href="/dashboard" class="w-full inline-block bg-blue-600 hover:bg-blue-500 text-white font-medium py-2.5 px-4 rounded-xl transition duration-200 text-center shadow-lg shadow-blue-600/20">Go to Dashboard</a>
                <a href="/logout" class="w-full inline-block bg-slate-800 hover:bg-slate-700 text-slate-300 font-medium py-2.5 px-4 rounded-xl transition duration-200 text-center">Logout</a>
            </div>
        {% else %}
            <a href="/login" class="w-full flex items-center justify-center gap-3 bg-slate-900 hover:bg-slate-800 border border-slate-700 text-white font-medium py-3 px-4 rounded-xl transition duration-200 shadow-lg group">
                <svg class="w-5 h-5 fill-current" viewBox="0 0 24 24"><path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/></svg>
                Sign in with GitHub
            </a>
        {% endif %}
    </div>
</body>
</html>
"""


# --- DASHBOARD TEMPLATE WITH REPO SELECTOR & CUSTOM LINK ---
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Shahajjo</title>
    <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>body { font-family: 'Inter', sans-serif; }</style>
</head>
<body class="bg-slate-950 text-slate-100 min-h-screen p-6">
    <div class="max-w-2xl mx-auto">
        <!-- Top Profile Bar -->
        <div class="flex justify-between items-center bg-slate-900 border border-slate-800 rounded-2xl p-6 mb-6 shadow-xl">
            <div class="flex items-center gap-4">
                <img src="{{ user.avatar_url }}" class="w-12 h-12 rounded-full border border-blue-500/30">
                <div>
                    <h2 class="text-lg font-bold text-white">Dashboard</h2>
                    <p class="text-xs text-slate-400">@{{ user.login }}</p>
                </div>
            </div>
            <a href="/" class="bg-slate-800 hover:bg-slate-700 text-slate-300 px-4 py-2 rounded-xl text-sm font-medium transition">Home</a>
        </div>
        
        <!-- Build Configuration Card -->
        <div class="bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-xl">
            <h3 class="text-xl font-semibold mb-2">Build Your APK</h3>
            <p class="text-slate-400 text-sm mb-6">Select one of your repositories or paste any public repository link below.</p>
            
            <form action="/start-build" method="POST" class="space-y-5">
                <!-- Option 1: Select from User Repos -->
                <div>
                    <label class="block text-sm font-medium text-slate-300 mb-2">Select Your Repository</label>
                    <select name="selected_repo" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-slate-200 focus:outline-none focus:border-blue-500">
                        <option value="">-- Choose from your repositories --</option>
                        {% for repo in repos %}
                            <option value="{{ repo.clone_url }}">{{ repo.full_name }}</option>
                        {% endfor %}
                    </select>
                </div>

                <div class="text-center text-xs text-slate-500 font-semibold">— OR —</div>

                <!-- Option 2: Custom Public Repo Link -->
                <div>
                    <label class="block text-sm font-medium text-slate-300 mb-2">Paste Public Repository URL</label>
                    <input type="url" name="custom_repo" placeholder="https://github.com/username/repository" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500">
                </div>

                <!-- App Customization Fields -->
                <div>
                    <label class="block text-sm font-medium text-slate-300 mb-2">App Name</label>
                    <input type="text" name="app_name" required placeholder="My Awesome App" class="w-full bg-slate-950 border border-slate-800 rounded-xl p-3 text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500">
                </div>

                <button type="submit" class="w-full bg-blue-600 hover:bg-blue-500 text-white font-medium py-3 px-4 rounded-xl transition duration-200 shadow-lg shadow-blue-600/20 cursor-pointer">
                    Configure & Proceed to Build 🚀
                </button>
            </form>
        </div>
    </div>
</body>
</html>
"""


@app.route("/")
def home():
    return render_template_string(HOME_TEMPLATE, user=session.get("user"))


@app.route("/login")
def login():
    github_auth_url = f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&scope=repo,workflow"
    return redirect(github_auth_url)


@app.route("/auth/callback")
def auth_callback():
    code = request.args.get("code")
    if not code:
        return "Error: No code provided from GitHub", 400

    token_url = "https://github.com/login/oauth/access_token"
    headers = {"Accept": "application/json"}
    data = {
        "client_id": GITHUB_CLIENT_ID,
        "client_secret": GITHUB_CLIENT_SECRET,
        "code": code,
    }

    response = requests.post(token_url, json=data, headers=headers)
    result = response.json()
    access_token = result.get("access_token")

    if not access_token:
        return f"Failed to get access token from GitHub: {result}", 400

    user_headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    user_response = requests.get("https://api.github.com/user", headers=user_headers)
    user_data = user_response.json()

    session["user"] = user_data
    session["access_token"] = access_token

    return redirect(url_for("home"))


@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("home"))
    
    access_token = session.get("access_token")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json"
    }
    
    # Fetch user's GitHub repositories
    repos_response = requests.get("https://api.github.com/user/repos?per_page=100&sort=updated", headers=headers)
    repos = repos_response.json() if repos_response.status_code == 200 else []
    
    return render_template_string(DASHBOARD_TEMPLATE, user=session["user"], repos=repos)


@app.route("/start-build", methods=["POST"])
def start_build():
    if "user" not in session:
        return redirect(url_for("home"))
    
    selected_repo = request.form.get("selected_repo")
    custom_repo = request.form.get("custom_repo")
    app_name = request.form.get("app_name")
    
    # Target repo thik kora (jodi custom link dey tahole seta, nahole dropdown er ta)
    target_repo = custom_repo if custom_repo else selected_repo
    
    if not target_repo:
        return "Error: Please select a repository or enter a public repo link!", 400

    return f"Build requested successfully for Repo: {target_repo} | App Name: {app_name}! Ekhon amra GitHub Action trigger korar backend logic add korbo."


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)