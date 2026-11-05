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
GITHUB_BUILDER_OWNER = os.getenv("GITHUB_BUILDER_OWNER")
GITHUB_BUILDER_REPO = os.getenv("GITHUB_BUILDER_REPO")

# ---------- Landing ----------
@app.route("/")
def landing():
    return render_template("landing.html")

# ---------- Auth ----------
@app.route("/login")
def login():
    # store where to go after login
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
        return "Sign in failed. Please try again.", 400

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
    repos = [
        {"name": r.name, "full_name": r.full_name, "private": r.private, "url": r.html_url}
        for r in user.get_repos()
    ]
    return jsonify(repos)

@app.route("/api/create-project", methods=["POST"])
def create_project():
    """Creates a new repo for the user by copying the builder template."""
    if "token" not in session:
        return jsonify({"error": "not signed in"}), 401

    data = request.json or {}
    repo_name = data.get("repo_name", "").strip()
    if not repo_name:
        return jsonify({"error": "repo name required"}), 400

    gh = Github(session["token"])
    user = gh.get_user()
    source = gh.get_repo(f"{GITHUB_BUILDER_OWNER}/{GITHUB_BUILDER_REPO}")

    try:
        new_repo = user.create_repo(repo_name, auto_init=False)
    except GithubException as e:
        if e.status == 422:
            new_repo = user.get_repo(repo_name)
        else:
            return jsonify({"error": "Could not create project."}), 400

    copied = 0
    try:
        items = source.get_contents("")
        while items:
            item = items.pop(0)
            if item.type == "file":
                try:
                    new_repo.create_file(item.path, f"Import {item.path}", item.decoded_content)
                    copied += 1
                except GithubException:
                    pass
            elif item.type == "dir":
                items.extend(source.get_contents(item.path))
    except GithubException:
        pass

    return jsonify({"repo": new_repo.full_name, "copied": copied})

# ---------- Editor ----------
@app.route("/editor")
def editor():
    if "token" not in session:
        return redirect(url_for("login"))
    repo = request.args.get("repo", "")
    if not repo:
        return redirect(url_for("select_repo"))
    return render_template("editor.html", repo=repo)

# ---------- File APIs ----------
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

# ---------- Build ----------
@app.route("/api/build", methods=["POST"])
def build():
    if "token" not in session:
        return jsonify({"error": "not signed in"}), 401
    data = request.json
    repo_full = data["repo"]
    branch = data.get("branch", "main")
    gh = Github(session["token"])
    repo = gh.get_repo(repo_full)

    workflow_path = ".github/workflows/build.yml"
    workflow_content = open("workflow_template.yml").read()
    try:
        existing = repo.get_contents(workflow_path)
        repo.update_file(workflow_path, "Update build workflow", workflow_content, existing.sha)
    except GithubException:
        repo.create_file(workflow_path, "Add build workflow", workflow_content)

    url = f"https://api.github.com/repos/{repo_full}/actions/workflows/build.yml/dispatches"
    r = requests.post(
        url,
        headers={
            "Authorization": f"Bearer {session['token']}",
            "Accept": "application/vnd.github+json",
        },
        json={"ref": branch},
    )
    if r.status_code not in (204, 201):
        return jsonify({"error": "Build could not be started."}), 400
    return jsonify({"status": "building"})

@app.route("/api/build-status")
def build_status():
    if "token" not in session:
        return jsonify({"error": "not signed in"}), 401
    repo_full = request.args.get("repo")
    gh = Github(session["token"])
    repo = gh.get_repo(repo_full)
    runs = repo.get_workflow_runs()
    if not runs.totalCount:
        return jsonify({"status": "no runs"})
    latest = runs[0]
    result = {
        "status": latest.status,
        "conclusion": latest.conclusion,
        "url": latest.html_url,
        "artifacts": [],
    }
    try:
        for a in latest.get_artifacts():
            result["artifacts"].append({"name": a.name, "url": a.archive_download_url})
    except GithubException:
        pass
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)