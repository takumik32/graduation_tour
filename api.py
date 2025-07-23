import http.client
import json
from datetime import datetime, timedelta
import time

API_KEY = "sk_9mp0DC1MwflYGpQJINrEn3WmEWLO0m0GCfqdrupoBiKduOH6316IsXUQiib70NQF"
headers = {
    'Content-Type': 'application/json',
    'x-api-token': API_KEY
}

# 都市間ルートと設定
route = ["NRT", "IST", "CAI", "RAK", "NRT"]
start_date_base = datetime.strptime("2026-03-01", "%Y-%m-%d")
end_date = datetime.strptime("2026-03-31", "%Y-%m-%d")

results = []

# リクエスト送信＆再試行
def send_flight_request(payload, max_retries=3, retry_wait=2):
    conn = http.client.HTTPSConnection("api.scrapeless.com")
    for attempt in range(1, max_retries + 1):
        try:
            conn.request("POST", "/api/v1/scraper/request", payload, headers)
            res = conn.getresponse()
            data = res.read().decode("utf-8")

            if res.status == 200 or res.status == 201:
                return res.status, data
            else:
                print(f"⚠️ Attempt {attempt}: リクエスト失敗 (status: {res.status})")

        except Exception as e:
            print(f"❌ Attempt {attempt}: リクエスト例外発生: {e}")

        if attempt < max_retries:
            print(f"🔁 {retry_wait}秒待機して再試行します...")
            time.sleep(retry_wait)

    return None, None

# タスクポーリング
def poll_task(task_id, max_retries=10, interval=3):
    conn = http.client.HTTPSConnection("api.scrapeless.com")
    for attempt in range(max_retries):
        conn.request("GET", f"/api/v1/scraper/result/{task_id}", headers=headers)
        res = conn.getresponse()
        data = res.read().decode("utf-8")
        if res.status == 200:
            return json.loads(data)
        elif res.status == 201:
            print(f"⏳ Polling... ({attempt+1}/{max_retries})")
            time.sleep(interval)
        else:
            print(f"❌ Error during polling: {res.status}")
            break
    return {"error": "Polling failed"}

# 日ごと＆セグメントごとに全ループ
current_date = start_date_base
while current_date <= end_date:
    for i in range(len(route) - 1):
        departure = route[i]
        arrival = route[i + 1]
        outbound_date = current_date.strftime("%Y-%m-%d")

        payload = json.dumps({
            "actor": "scraper.google.flights",
            "hl": "ja",
            "gl": "JP",
            "input": {
                "data_type": 2,
                "departure_id": departure,
                "arrival_id": arrival,
                "outbound_date": outbound_date,
                "adults": 1,
                "travel_class": 1
            }
        })

        status, data = send_flight_request(payload)

        result_entry = {
            "segment": f"{departure} → {arrival}",
            "outbound_date": outbound_date,
        }

        if status == 200:
            print(f"✅ {outbound_date} {departure}→{arrival} 即時成功")
            result_entry["response"] = json.loads(data)
        elif status == 201:
            task_id = json.loads(data)["taskId"]
            print(f"⏳ {outbound_date} {departure}→{arrival} タスクキュー taskId: {task_id}")
            result_entry["response"] = poll_task(task_id)
        else:
            print(f"❌ {outbound_date} {departure}→{arrival} リクエスト最終的に失敗")
            result_entry["response"] = {"error": f"HTTP {status or 'No Response'}"}

        results.append(result_entry)

    current_date += timedelta(days=1)

# 保存
output_path = "/home/takos/vscode_ubuntu/3_python/graduation_tour/one_way_flight_results.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print(f"✅ 完了しました：{len(results)}件を {output_path} に保存しました。")

import subprocess

# api.py の処理の後
subprocess.run(["python3", "analyze.py"])