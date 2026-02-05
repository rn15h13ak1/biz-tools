import csv
import json
import ssl
from datetime import datetime

import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from urllib3.util.ssl_ import create_urllib3_context

# ==========================================
# 設定エリア
# ==========================================
NETCOOL_HOST = "https://your-netcool-host:8443"  # HTTPSの場合はポートが変わることが多いです(例:8443)
USERNAME = "root"
PASSWORD = "password"
OUTPUT_FILE = f"netcool_alerts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

COLUMNS = [
    "Node",
    "Summary",
    "Severity",
    "FirstOccurrence",
    "LastOccurrence",
    "Tally",
    "Identifier",
]


# ==========================================
# SSLエラー対策用のアダプタークラス
# ==========================================
class LegacyHTTPAdapter(HTTPAdapter):
    """古いSSL/TLSバージョンや弱い暗号スイートを許可するアダプター"""

    def init_poolmanager(self, connections, maxsize, block=False):
        # SSLコンテキストを作成
        ctx = create_urllib3_context()

        # 対策1: セキュリティレベルを下げる（最近のLinux/Python環境で必須の場合あり）
        # OpenSSL 3.0以上対策: SECLEVEL=1 にして古い暗号化を許可
        try:
            ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        except Exception:
            # Windowsなど非OpenSSL環境や古いOpenSSLではそのまま
            pass

        # 対策2: サーバー証明書の検証を無効化
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

        # プールマネージャーに適用
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=ctx,
        )


def fetch_alerts():
    # URL生成
    url = f"{NETCOOL_HOST}/objectserver/restapi/alerts/status"
    params = {"collist": ",".join(COLUMNS), "filter": "Severity > 0"}

    print(f"[{datetime.now()}] Netcoolからデータを取得中(Legacy SSL)...")

    # セッションを作成してアダプターを適用
    session = requests.Session()
    session.mount("https://", LegacyHTTPAdapter())

    try:
        # verify=False はアダプター内で設定済みだが念のため指定
        response = session.get(
            url, auth=(USERNAME, PASSWORD), params=params, verify=False
        )
        response.raise_for_status()

        data = response.json()
        rows = data.get("rowset", {}).get("rows", [])

        print(f"-> {len(rows)} 件のアラートを取得しました。")
        return rows

    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return []


def save_to_csv(rows):
    if not rows:
        print("保存するデータがありません。")
        return

    try:
        with open(
            OUTPUT_FILE, mode="w", newline="", encoding="utf-8_sig"
        ) as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writeheader()
            for row in rows:
                writer.writerow({col: row.get(col) for col in COLUMNS})
        print("-> 書き出し完了！")
    except Exception as e:
        print(f"ファイル書き込みエラー: {e}")


if __name__ == "__main__":
    # SSL警告（InsecureRequestWarning）を非表示にする
    import urllib3

    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    alerts = fetch_alerts()
    save_to_csv(alerts)
