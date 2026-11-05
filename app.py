import os
import time
import requests
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from github import Github, GithubException
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev-secret-change-me")

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
# এটি আপনার গিটহাব টোকেন (Render-এ সেট করা)
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN") 
# আপনার রিপো যেখানে বিল্ড হবে
GITHUB_BUILDER_OWNER = os.getenv("GITHUB_BUILDER_OWNER", "sillyratheu")
GITHUB_BUILDER_REPO = os.getenv("GITHUB_BUILDER_REPO", "hello-backend")

# ---------- Landing ----------
@app.route("/")
def landing():
    return render_template("landing.html")

# ---------- Auth ----------
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
    return redirect(url_for("select_repo"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))

# ---------- Repo select ----------
@app.route("/select")
def select_repo():
    if "token" not in session:
        return redirect(url_for("login"))
    return render_template("select_repo.html")

@app.route("/api/repos")
def api_repos():
    if "token" not in session:
        return jsonify({"error": "not signed in"}), 401
    gh = Github(session["token"])
    user = gh.get_user()
    repos = [{"name": r.name, "full_name": r.full_name} for r in user.get_repos()]
    return jsonify(repos)

@app.route("/api/create-project", methods=["POST"])
def create_project():
    if "token" not in session:
        return jsonify({"error": "not signed in"}), 401
    data = request.json or {}
    repo_name = data.get("repo_name", "").strip()
    
    # ইউজারের টোকেন দিয়ে তার অ্যাকাউন্টে নতুন রিপো তৈরি হবে
    gh = Github(session["token"])
    user = gh.get_user()
    
    try:
        new_repo = user.create_repo(repo_name, auto_init=True)
        return jsonify({"repo": new_repo.full_name})
    except GithubException as e:
        return jsonify({"error": "Could not create project. Maybe it already exists."}), 400

# ---------- Editor ----------
@app.route("/editor")
def editor():
    if "token" not in session:
        return redirect(url_for("login"))
    repo = request.args.get("repo", "")
    if not repo:
        return redirect(url_for("select_repo"))
    return render_template("editor.html", repo=repo)

# ---------- File APIs (ইউজারের নিজের রিপোতে সেভ হবে) ----------
@app.route("/api/file", methods=["GET"])
def get_file():
    if "token" not in session:
        return jsonify({"error": "not signed in"}), 401
    repo_full = request.args.get("repo")
    path = request.args.get("path", "lib/main.dart")
    gh = Github(session["token"])
    repo = gh.get_repo(repo_full)
    try:
        content = repo.get_contents(path)
        return jsonify({"content": content.decoded_content.decode("utf-8")})
    except GithubException:
        return jsonify({"content": None})

@app.route("/api/file", methods=["POST"])
def save_file():
    if "token" not in session:
        return jsonify({"error": "not signed in"}), 401
    data = request.json
    repo_full = data["repo"]
    path = data["path"]
    content = data["content"]
    gh = Github(session["token"])
    repo = gh.get_repo(repo_full)
    try:
        existing = repo.get_contents(path)
        repo.update_file(path, f"Update {path}", content, existing.sha)
    except GithubException:
        repo.create_file(path, f"Create {path}", content)
    return jsonify({"status": "saved"})

# ---------- Build System (এখানে আপনার GITHUB_TOKEN ব্যবহার হবে) ----------
@app.route("/api/build", methods=["POST"])
def build():
    if "token" not in session:
        return jsonify({"error": "not signed in"}), 401
    
    # ইউজার যে রিপোতে কাজ করছে, সেটার নাম নেওয়া হচ্ছে
    user_repo = request.json["repo"] 
    
    # অ্যাডমিন (আপনার) টোকেন দিয়ে আপনার বিল্ডার রিপোতে অ্যাক্সেস নেওয়া হচ্ছে
    admin_gh = Github(GITHUB_TOKEN)
    try:
        builder_repo = admin_gh.get_repo(f"{GITHUB_BUILDER_OWNER}/{GITHUB_BUILDER_REPO}")
    except GithubException:
        return jsonify({"error": "Builder repository not found. Check your GITHUB_TOKEN."}), 500

    # ১. ওয়ার্কফ্লো ফাইল আপনার রিপোতে আপডেট করা
    workflow_path = ".github/workflows/build.yml"
    workflow_content = open("workflow_template.yml").read()
    try:
        existing = builder_repo.get_contents(workflow_path)
        builder_repo.update_file(workflow_path, "Update build workflow", workflow_content, existing.sha)
    except GithubException:
        builder_repo.create_file(workflow_path, "Add build workflow", workflow_content)

    # ২. আপনার রিপোতে GitHub Actions ট্রিগার করা
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
        
    # ৩. বিল্ড শুরু হয়েছে, ইউজারকে জানানো
    return jsonify({"status": "building", "user_repo": user_repo})

# ---------- Build Status + Download Link ----------
@app.route("/api/build-status")
def build_status():
    if "token" not in session:
        return jsonify({"error": "not signed in"}), 401
    
    # আপনার রিপোতে বিল্ড স্ট্যাটাস চেক করা হচ্ছে
    admin_gh = Github(GITHUB_TOKEN)
    try:
        builder_repo = admin_gh.get_repo(f"{GITHUB_BUILDER_OWNER}/{GITHUB_BUILDER_REPO}")
        runs = builder_repo.get_workflow_runs()
        if not runs.totalCount:
            return jsonify({"status": "no runs yet"})
        
        latest = runs[0]
        
        # যদি বিল্ড সফল হয়, আর্টিফ্যাক্ট (APK) লিংক খোঁজা
        artifacts = []
        if latest.conclusion == "success":
            for a in latest.get_artifacts():
                if a.name == "app-release":
                    # এই লিংকটি ডাউনলোডের জন্য
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