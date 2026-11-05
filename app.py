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
    return redirect(url_for("select_repo"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))

# ==========================================
# REPO SELECT & API
# ==========================================
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
    gh = Github(session["token"])
    user = gh.get_user()
    try:
        new_repo = user.create_repo(repo_name, auto_init=True)
        return jsonify({"repo": new_repo.full_name})
    except GithubException as e:
        return jsonify({"error": "Could not create project."}), 400

# ==========================================
# EDITOR & FILE APIs
# ==========================================
@app.route("/editor")
def editor():
    if "token" not in session:
        return redirect(url_for("login"))
    repo = request.args.get("repo", "")
    if not repo:
        return redirect(url_for("select_repo"))
    return render_template("editor.html", repo=repo)

@app.route("/api/file", methods=["GET"])
def get_file():
    if "token" not in session:
        return jsonify({"error": "not signed in"}), 401
    repo_full = request.args.get("repo")
    path = request.args.get("path", "lib/main.dart")
    
    # যদি লিংক দেওয়া থাকে, তবে সেটা থেকে user/repo ফরম্যাট বানানো
    if "github.com/" in repo_full:
        repo_full = repo_full.split("github.com/")[-1].strip("/")
        
    gh = Github(session["token"])
    try:
        repo = gh.get_repo(repo_full)
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
    
    if "github.com/" in repo_full:
        repo_full = repo_full.split("github.com/")[-1].strip("/")

    path = data["path"]
    content = data["content"]
    gh = Github(session["token"])
    try:
        repo = gh.get_repo(repo_full)
        existing = repo.get_contents(path)
        repo.update_file(path, f"Update {path}", content, existing.sha)
        return jsonify({"status": "saved"})
    except GithubException:
        try:
            repo.create_file(path, f"Create {path}", content)
            return jsonify({"status": "saved"})
        except Exception as e:
            return jsonify({"error": str(e)}), 400

# ==========================================
# BUILD API (Clone to Admin Repo & Build)
# ==========================================
@app.route("/api/build", methods=["POST"])
def build():
    if "token" not in session:
        return jsonify({"error": "not signed in"}), 401
    
    data = request.json
    source_repo = data.get("repo")
    if not source_repo:
        return jsonify({"error": "No repository provided"}), 400

    # লিংক থেকে user/repo বের করা
    if "github.com/" in source_repo:
        source_repo = source_repo.split("github.com/")[-1].strip("/")

    try:
        user_gh = Github(session["token"])
        admin_gh = Github(GITHUB_TOKEN)
        
        # ১. ইউজারের রিপো অ্যাক্সেস করা
        try:
            src_repo = user_gh.get_repo(source_repo)
        except GithubException:
            # যদি ইউজারের প্রাইভেট রিপো হয় বা অ্যাক্সেস না থাকে, তবে সরাসরি পাবলিক হিসেবে ট্রাই করা
            try:
                src_repo = Github().get_repo(source_repo)
            except:
                return jsonify({"error": "Repository not found or not accessible."}), 400

        # ২. আপনার বিল্ডার রিপো (hello-backend)
        builder_repo = admin_gh.get_repo(f"{GITHUB_BUILDER_OWNER}/{GITHUB_BUILDER_REPO}")

        # ৩. মূল ফাইলগুলো (pubspec.yaml, lib/main.dart) কপি করা
        files_to_copy = ["pubspec.yaml", "lib/main.dart"]
        copied = 0
        
        for path in files_to_copy:
            try:
                src_content = src_repo.get_contents(path)
                content_data = src_content.decoded_content
                
                try:
                    existing = builder_repo.get_contents(path)
                    builder_repo.update_file(path, f"Update {path} from {source_repo}", content_data, existing.sha)
                except GithubException:
                    builder_repo.create_file(path, f"Create {path} from {source_repo}", content_data)
                copied += 1
            except GithubException:
                pass # ফাইল না থাকলে স্কিপ করবে

        # ৪. ওয়ার্কফ্লো আপডেট
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
        workflow_path = ".github/workflows/build.yml"
        try:
            existing = builder_repo.get_contents(workflow_path)
            builder_repo.update_file(workflow_path, "Update workflow", workflow_content, existing.sha)
        except GithubException:
            builder_repo.create_file(workflow_path, "Add workflow", workflow_content)

        # ৫. ট্রিগার বিল্ড
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
            
        return jsonify({"status": "building", "copied_files": copied})
        
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