import streamlit as st
import json
from datetime import datetime
from urllib.parse import quote

# 空港名→都市名マッピング
airport_to_city = {
    "Narita": "東京",
    "Istanbul": "イスタンブール",
    "Cairo": "カイロ",
    "Marrakesh": "マラケシュ",
    "Marrakesh Menara": "マラケシュ",
}

EXCHANGE_RATE = 150  # USD to JPY

# top10_itineraries.json の読み込み
with open("top10_itineraries.json", "r", encoding="utf-8") as f:
    top10 = json.load(f)

st.title("最安日程プラン")

# URLパラメータ取得
query_params = st.query_params
selected_index = int(query_params["plan"][0]) if "plan" in query_params else None

if selected_index is None:
    # 表形式で表示
    import pandas as pd

    rows = []
    links = []

    for i, item in enumerate(top10):
        flights = item["flights"]
        total_price = int(item["total_price"] * EXCHANGE_RATE)
        url = f"?plan={i}"

        # 各時刻取得
        t0 = datetime.strptime(flights[0]["flights"][0]["departure_airport"]["time"], "%Y-%m-%d %H:%M")
        t1_arr = datetime.strptime(flights[0]["flights"][-1]["arrival_airport"]["time"], "%Y-%m-%d %H:%M")
        t1_dep = datetime.strptime(flights[1]["flights"][0]["departure_airport"]["time"], "%Y-%m-%d %H:%M")
        t2_arr = datetime.strptime(flights[1]["flights"][-1]["arrival_airport"]["time"], "%Y-%m-%d %H:%M")
        t2_dep = datetime.strptime(flights[2]["flights"][0]["departure_airport"]["time"], "%Y-%m-%d %H:%M")
        t3_arr = datetime.strptime(flights[2]["flights"][-1]["arrival_airport"]["time"], "%Y-%m-%d %H:%M")
        t3_dep = datetime.strptime(flights[3]["flights"][0]["departure_airport"]["time"], "%Y-%m-%d %H:%M")
        t4 = datetime.strptime(flights[3]["flights"][-1]["arrival_airport"]["time"], "%Y-%m-%d %H:%M")

        row = {
            "東京出発": t0.strftime("%-m/%-d %H:%M"),
            "イスタンブール滞在": f"{t1_arr.strftime('%-m/%-d %H:%M')}〜{t1_dep.strftime('%-m/%-d %H:%M')}",
            "カイロ滞在": f"{t2_arr.strftime('%-m/%-d %H:%M')}〜{t2_dep.strftime('%-m/%-d %H:%M')}",
            "マラケシュ滞在": f"{t3_arr.strftime('%-m/%-d %H:%M')}〜{t3_dep.strftime('%-m/%-d %H:%M')}",
            "東京到着": t4.strftime("%-m/%-d %H:%M"),
            "費用": f"[{total_price:,} 円]({url})"
        }
        rows.append(row)

    df = pd.DataFrame(rows)
    st.markdown("### 最安日程一覧（クリックで詳細）")
    st.write(df.to_markdown(index=False), unsafe_allow_html=True)

else:
    # 詳細ページ
    item = top10[selected_index]
    flights = item["flights"]
    itin = item["itinerary"]
    total_price = int(item["total_price"] * EXCHANGE_RATE)

    st.header(f"日程プラン {selected_index + 1}")

    for i, flight in enumerate(flights):
        segs = flight["flights"]
        main_dep = segs[0]["departure_airport"]
        main_arr = segs[-1]["arrival_airport"]
        main_dep_time = datetime.strptime(main_dep["time"], "%Y-%m-%d %H:%M")

        main_dep_city = airport_to_city.get(main_dep["name"].split()[0], main_dep["name"])
        main_arr_city = airport_to_city.get(main_arr["name"].split()[0], main_arr["name"])

        st.markdown(f"### {main_dep_city} → {main_arr_city}（{main_dep_time.month}月{main_dep_time.day}日）")

        layovers = []
        for k, seg in enumerate(segs):
            dep = seg["departure_airport"]
            arr = seg["arrival_airport"]
            dep_time = datetime.strptime(dep["time"], "%Y-%m-%d %H:%M")
            arr_time = datetime.strptime(arr["time"], "%Y-%m-%d %H:%M")

            dep_city = airport_to_city.get(dep["name"].split()[0], dep["name"])
            arr_city = airport_to_city.get(arr["name"].split()[0], arr["name"])

            indent = "・"
            st.markdown(f"<div style='font-size:16px;'>{indent}{dep_city}（{dep_time.strftime('%m/%d %H:%M')}） → {arr_city}（{arr_time.strftime('%m/%d %H:%M')}）</div>", unsafe_allow_html=True)
            st.markdown(f"<div style='padding-left:2em;'>航空会社：{seg['airline']}</div>", unsafe_allow_html=True)

            if k < len(segs) - 1:
                # 修正前
                next_dep = datetime.strptime(segs[k+1]["departure_airport"]["time"], "%Y-%m-%d %H:%M")
                layover = next_dep - arr_time
                total_minutes = layover.total_seconds() // 60
                layover_hours = int(total_minutes // 60)
                layover_minutes = int(total_minutes % 60)
                layover_city = airport_to_city.get(arr["name"].split()[0], arr["name"])
                layovers.append(
                    f"経由：{layover_city}（{arr_time.month}月{arr_time.day}日{arr_time.strftime('%H:%M')}着、"
                    f"{next_dep.month}月{next_dep.day}日{next_dep.strftime('%H:%M')}発、滞在時間：{layover_hours}時間{layover_minutes}分）"
                )

        if layovers:
            st.markdown(" ")  # 改行（空行）を挿入
        for l in layovers:
            st.markdown(f"{l}</div>", unsafe_allow_html=True)



        st.markdown("---")

    st.subheader("合計価格")
    st.write(f"{total_price:,} 円")

    st.markdown("[← ランキングに戻る](./)")