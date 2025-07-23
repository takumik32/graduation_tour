import json
from datetime import datetime, timedelta
from itertools import product

import re

def fix_time_format(t):
    # 例: '2026-03-13 :55' → '2026-03-13 00:55'
    if re.match(r"^\d{4}-\d{2}-\d{2} :\d{2}$", t):
        return t.replace(" :", " 00:")
    return t


# 読み込み
with open("one_way_flight_results.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 区間順序と滞在日数の範囲
route = ["NRT", "IST", "CAI", "RAK", "NRT"]
stay_range = range(3, 6)  # 3〜5日

# 各区間ごとの日付別最安価格フライトを格納
from collections import defaultdict
segment_dict = defaultdict(lambda: defaultdict(list))

for entry in data:
    segment = entry.get("segment")
    date = entry.get("outbound_date")
    best_flights = entry.get("response", {}).get("flights_result", {}).get("best_flights", [])

    if not best_flights:
        continue

    key = segment
    best = min(best_flights, key=lambda x: x.get("price", float('inf')))
        # 時刻フォーマット補正
    for segment in best.get("flights", []):
        if "time" in segment.get("departure_airport", {}):
            segment["departure_airport"]["time"] = fix_time_format(segment["departure_airport"]["time"])
        if "time" in segment.get("arrival_airport", {}):
            segment["arrival_airport"]["time"] = fix_time_format(segment["arrival_airport"]["time"])
    segment_dict[key][date].append(best)

# 探索：NRT→IST→CAI→RAK→NRT
results = []

for d1 in segment_dict["NRT → IST"]:
    date1 = datetime.strptime(d1, "%Y-%m-%d")
    for s1 in stay_range:
        date2 = date1 + timedelta(days=s1)
        d2 = date2.strftime("%Y-%m-%d")
        if d2 not in segment_dict["IST → CAI"]:
            continue

        for s2 in stay_range:
            date3 = date2 + timedelta(days=s2)
            d3 = date3.strftime("%Y-%m-%d")
            if d3 not in segment_dict["CAI → RAK"]:
                continue

            for s3 in stay_range:
                date4 = date3 + timedelta(days=s3)
                d4 = date4.strftime("%Y-%m-%d")
                if d4 not in segment_dict["RAK → NRT"]:
                    continue

                # 各区間の最安フライト取得
                flight1 = min(segment_dict["NRT → IST"][d1], key=lambda x: x["price"])
                flight2 = min(segment_dict["IST → CAI"][d2], key=lambda x: x["price"])
                flight3 = min(segment_dict["CAI → RAK"][d3], key=lambda x: x["price"])
                flight4 = min(segment_dict["RAK → NRT"][d4], key=lambda x: x["price"])

                total_price = sum([f["price"] for f in [flight1, flight2, flight3, flight4]])

                results.append({
                    "itinerary": {
                        "NRT → IST": d1,
                        "IST → CAI": d2,
                        "CAI → RAK": d3,
                        "RAK → NRT": d4,
                    },
                    "total_price": total_price,
                    "flights": [flight1, flight2, flight3, flight4]
                })

# 安い順にソートして上位10件取得
top10 = sorted(results, key=lambda x: x["total_price"])[:20]
# 空港名→都市名マッピング
airport_to_city = {
    "Narita": "東京",
    "Istanbul": "イスタンブール",
    "Cairo": "カイロ",
    "Marrakesh": "マラケシュ",
    "Marrakesh Menara": "マラケシュ",  # 念のため正式名でも
}
EXCHANGE_RATE = 150  # 1ドル = 150円

# 出力：人間が読みやすい形式で（出発日はカッコ内）
with open("best_itineraries.txt", "w", encoding="utf-8") as f:
    for idx, item in enumerate(top10, 1):
        flights = item["flights"]
        total_price_usd = item["total_price"]
        total_price_jpy = total_price_usd * EXCHANGE_RATE

        route_parts = []
        for i, flight in enumerate(flights):
            dep_airport = flight["flights"][0]["departure_airport"]
            arr_airport = flight["flights"][-1]["arrival_airport"]

            dep_city_en = dep_airport["name"].split()[0]
            arr_city_en = arr_airport["name"].split()[0]

            dep_city = airport_to_city.get(dep_city_en, dep_city_en)
            arr_city = airport_to_city.get(arr_city_en, arr_city_en)

            dep_time = datetime.strptime(dep_airport["time"], "%Y-%m-%d %H:%M")

            if i == 0:
                route_parts.append(f"{dep_city}（{dep_time.month}月{dep_time.day}日）→{arr_city}")
            else:
                route_parts.append(f"（{dep_time.month}月{dep_time.day}日）→{arr_city}")

        last_dep_time = datetime.strptime(flights[-1]["flights"][0]["departure_airport"]["time"], "%Y-%m-%d %H:%M")
        route_parts[-1] += f"（{last_dep_time.month}月{last_dep_time.day}日）"

        route_str = "".join(route_parts)
        f.write(f"{idx}. {route_str}：{int(total_price_jpy):,}円\n")

with open("top10_itineraries.json", "w", encoding="utf-8") as f_json:
    json.dump(top10, f_json, ensure_ascii=False, indent=2)