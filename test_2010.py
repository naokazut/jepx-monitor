import requests
import sys

def test_connection():
    # ターゲット：2010年度スポット価格CSV
    # JEPXは歴史的にhttpが標準のため、httpで指定
    url = "http://www.jepx.org/market/excel/spot_2025.csv"
    
    print(f"--- JEPX Connection Test ---")
    print(f"Target: {url}")
    
    try:
        # タイムアウトを長めに設定し、サーバーからの応答を待つ
        response = requests.get(url, timeout=30)
        
        print(f"HTTP Status Code: {response.status_code}")
        
        if response.status_code == 200:
            content_size = len(response.content)
            print(f"✅ Success! Data size: {content_size} bytes")
            # 先頭100文字を表示して、中身がHTML（エラー画面）ではなくCSVであることを確認
            print("--- Content Preview (First 100 chars) ---")
            print(response.text[:100])
        else:
            print(f"❌ Failed: Server returned status {response.status_code}")
            sys.exit(1) # GitHub Actions側に失敗を知らせる
            
    except Exception as e:
        print(f"❌ Critical Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_connection()
