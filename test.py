import csv
import json
import time
from datetime import datetime

import requests

# ==========================================
# 設定エリア (環境に合わせて書き換えてください)
# ==========================================
NETCOOL_HOST = "http://your-netcool-host:8080"  # NetcoolのAPIのエンドポイント
USERNAME = "root"  # Netcoolへのログインユーザー
PASSWORD = "password"  # Netcoolへのログインパスワード

# 出力するファイル名（日時をつける）
OUTPUT_FILE = f"netcool_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

# 取得したい7つの必須項目 (SQLクエリ用)
COLUMNS = [
    "Node",
    "Summary",
    "Severity",
    "FirstOccurrence",
    "LastOccurrence",
    "Tally",
    "Identifier",
]


def fetch_alerts():
    """Netcoolからアラート情報を取得する"""

    # Netcool OMNIbusのREST APIエンドポイント (環境によりパスが異なる場合があります)
    # 一般的には /objectserver/restapi/alerts/status などを叩きます
    url = f"{NETCOOL_HOST}/objectserver/restapi/alerts/status"

    # SQLのようなクエリパラメータを作成
    # 必要なカラムだけを指定して取得
    params = {
        "collist": ",".join(COLUMNS),
        "filter": "Severity > 0",  # (例) 解決済み(0)以外を取得するフィルタ
    }

    print(f"[{datetime.now()}] Netcoolからデータを取得中...")

    try:
        # Basic認証でリクエスト
        response = requests.get(
            url, auth=(USERNAME, PASSWORD), params=params, verify=False
        )
        response.raise_for_status()  # エラーなら例外発生

        data = response.json()
        rows = data.get("rowset", {}).get("rows", [])

        print(f"-> {len(rows)} 件のアラートを取得しました。")
        return rows

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return []


def save_to_csv(rows):
    """取得したデータをCSVに保存する"""
    if not rows:
        print("保存するデータがありません。")
        return

    print(f"[{datetime.now()}] CSVファイル '{OUTPUT_FILE}' に書き出し中...")

    try:
        with open(
            OUTPUT_FILE, mode="w", newline="", encoding="utf-8_sig"
        ) as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writeheader()

            for row in rows:
                # APIの返却形式に合わせてデータを整形
                # NetcoolのAPIは通常 {"Node": "server1", ...} のような辞書リストを返す
                writer.writerow({col: row.get(col) for col in COLUMNS})

        print("-> 書き出し完了！")

    except Exception as e:
        print(f"ファイル書き込みエラー: {e}")


if __name__ == "__main__":
    alerts = fetch_alerts()
    save_to_csv(alerts)
