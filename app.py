import os
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from github import Github, GithubException
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") 
GITHUB_BUILDER_OWNER = os.getenv("GITHUB_BUILDER_OWNER", "sillyratheu")
GITHUB_BUILDER_REPO = os.getenv("GITHUB_BUILDER_REPO", "hello-backend")

# ==========================================
# LANDING & AUTH
# ==========================================
@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/login")
def login():
    session["next"] = request.args.get("next", "select")
    url = (
        "https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        "&scope=repo,workflow"
    )
    return redirect(url)

@app.route("/callback")
def callback():
    code = request.args.get("code")
    if not code:
        return "Authorization failed.", 400
    resp = requests.post(
        "https://github.com/login/oauth/access_token",
        headers={"Accept": "application/json"},
        data={
            "client_id": GITHUB_CLIENT_ID,
            "client_secret": GITHUB_CLIENT_SECRET,
            "code": code,
        },
    )
    token = resp.json().get("access_token")
    if not token:
        return "Sign in failed.", 400
    session["token"] = token
    return redirect(url_for("editor"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))

# ==========================================
# EDITOR PAGE
# ==========================================
@app.route("/editor")
def editor():
    if "token" not in session:
        return redirect(url_for("login"))
    # ইউজারের রিপো ডিটেইলস আর লাগবে না, আমরা সবসময় আপনার hello-backend দেখাবো
    return render_template("editor.html", repo=f"{GITHUB_BUILDER_OWNER}/{GITHUB_BUILDER_REPO}")

# ==========================================
# FILE APIs (Reads/Writes to ADMIN's Repo)
# ==========================================
@app.route("/api/file", methods=["GET"])
def get_file():
    if "token" not in session:
        return jsonify({"error": "not signed in"}), 401
    path = request.args.get("path", "lib/main.dart")
    
    # অ্যাডমিন টোকেন দিয়ে আপনার hello-backend রিপো থেকে কোড পড়া
    admin_gh = Github(GITHUB_TOKEN)
    try:
        repo = admin_gh.get_repo(f"{GITHUB_BUILDER_OWNER}/{GITHUB_BUILDER_REPO}")
        content = repo.get_contents(path)
        return jsonify({"content": content.decoded_content.decode("utf-8")})
    except GithubException:
        return jsonify({"content": None})

@app.route("/api/file", methods=["POST"])
def save_file():
    if "token" not in session:
        return jsonify({"error": "not signed in"}), 401
    data = request.json
    path = data["path"]
    content = data["content"]
    
    # অ্যাডমিন টোকেন দিয়ে আপনার hello-backend রিপোতে কোড সেভ করা
    admin_gh = Github(GITHUB_TOKEN)
    try:
        repo = admin_gh.get_repo(f"{GITHUB_BUILDER_OWNER}/{GITHUB_BUILDER_REPO}")
        existing = repo.get_contents(path)
        repo.update_file(path, f"Update {path} via Shahajjo Studio", content, existing.sha)
        return jsonify({"status": "saved"})
    except GithubException:
        try:
            repo.create_file(path, f"Create {path} via Shahajjo Studio", content)
            return jsonify({"status": "saved"})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

# ==========================================
# BUILD API (Trigger Build in ADMIN's Repo)
# ==========================================
@app.route("/api/build", methods=["POST"])
def build():
    if "token" not in session:
        return jsonify({"error": "not signed in"}), 401
    
    try:
        workflow_content = """name: Build APK
on:
  workflow_dispatch:
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-java@v4
        with:
          distribution: 'temurin'
          java-version: '17'
      - uses: subosito/flutter-action@v2
        with:
          channel: 'stable'
      - run: flutter pub get
      - run: flutter build apk --release
      - uses: actions/upload-artifact@v4
        with:
          name: app-release
          path: build/app/outputs/flutter-apk/app-release.apk
"""
        admin_gh = Github(GITHUB_TOKEN)
        builder_repo = admin_gh.get_repo(f"{GITHUB_BUILDER_OWNER}/{GITHUB_BUILDER_REPO}")

        workflow_path = ".github/workflows/build.yml"
        try:
            existing = builder_repo.get_contents(workflow_path)
            builder_repo.update_file(workflow_path, "Update workflow", workflow_content, existing.sha)
        except GithubException:
            builder_repo.create_file(workflow_path, "Add workflow", workflow_content)

        # ট্রিগার বিল্ড
        url = f"https://api.github.com/repos/{GITHUB_BUILDER_OWNER}/{GITHUB_BUILDER_REPO}/actions/workflows/build.yml/dispatches"
        r = requests.post(
            url,
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
            },
            json={"ref": builder_repo.default_branch},
        )
        
        if r.status_code not in (204, 201):
            return jsonify({"error": f"GitHub API Error: {r.text}"}), 400
            
        return jsonify({"status": "building"})
        
    except Exception as e:
        return jsonify({"error": f"Server Error: {str(e)}"}), 500

# ==========================================
# BUILD STATUS
# ==========================================
@app.route("/api/build-status")
def build_status():
    if "token" not in session:
        return jsonify({"error": "not signed in"}), 401
    
    try:
        admin_gh = Github(GITHUB_TOKEN)
        builder_repo = admin_gh.get_repo(f"{GITHUB_BUILDER_OWNER}/{GITHUB_BUILDER_REPO}")
        
        runs = builder_repo.get_workflow_runs()
        if not runs.totalCount:
            return jsonify({"status": "no runs yet"})
        
        latest = runs[0]
        artifacts = []
        if latest.conclusion == "success":
            for a in latest.get_artifacts():
                if a.name == "app-release":
                    artifacts.append({"name": a.name, "url": a.archive_download_url})

        return jsonify({
            "status": latest.status,
            "conclusion": latest.conclusion,
            "artifacts": artifacts
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)