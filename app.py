from flask import Flask, request, Response
import sqlite3
import os
import requests

app = Flask(__name__)
DB_PATH = 'hellocorp.db'

def init_db():
    """টেস্টের জন্য ডেমো ডাটাবেস ও টেবিল তৈরি করে যা পরে আপডেট করা যাবে"""
    if not os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS dns_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                domain_name TEXT UNIQUE,
                target_host TEXT
            )
        ''')
        # একটি ডেমো এন্ট্রি যোগ করা যাক (যেমন: corporation.hello টার্গেট করবে google.com বা অন্য কিছু)
        cursor.execute("INSERT OR IGNORE INTO dns_records (domain_name, target_host) VALUES (?, ?)", 
                       ("corporation.hello", "example.com"))
        conn.commit()
        conn.close()

@app.before_request
def reverse_proxy_middleware():
    """কাস্টম ডোমেইন রিকোয়েস্ট ধরে প্রক্সি করবে"""
    host = request.host.split(':')[0]
    
    # লোকাল রেন্ডার ডোমেইন হলে প্রক্সি বাইপাস করবে যাতে হোমপেজ দেখা যায়
    if "onrender.com" in host or "localhost" in host:
        return None
        
    # ডাটাবেস থেকে টার্গেট হোস্টিং খোঁজা
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT target_host FROM dns_records WHERE domain_name = ?", (host,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            target_backend = row[0]
            target_url = f"https://{target_backend}{request.path}"
            if request.query_string:
                target_url += f"?{request.query_string.decode('utf-8')}"
                
            resp = requests.request(
                method=request.method,
                url=target_url,
                headers={key: value for (key, value) in request.headers if key != 'Host'},
                data=request.get_data(),
                cookies=request.cookies,
                allow_redirects=False,
                timeout=10
            )
            
            excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
            headers = [(name, value) for (name, value) in resp.raw.headers.items() if name.lower() not in excluded_headers]
            
            return Response(resp.content, resp.status_code, headers)
    except Exception as e:
        return f"Hello Corporation Gateway Error: {str(e)}", 502

@app.route('/')
def home():
    return "Hello Corporation Autonomous Gateway is Live and Ready for Testing!"

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
