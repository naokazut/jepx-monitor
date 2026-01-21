import requests
import os
from datetime import datetime

# --- 設定 ---
DATA_DIR = "data"
START_YEAR = 2010
CURRENT_YEAR = datetime.now().year

def download_jepx(year):
    """年度に応じたJEPX CSVをダウンロード（URL候補を複数試行）"""
    # 候補1: 標準的な最新形式
    # 候補2: 過去データアーカイブ用URL（年度によって異なる場合があるため）
    urls = [
        f"https://www.jepx.org/market/excel/spot_{year}.csv",
        f"https://www.jepx.org/market/excel/spot_{year}_daily.csv"
    ]
    
    file_path = os.path.join(DATA_DIR, f"spot_{year}.csv")
    
    for url in urls:
        print(f"Trying: {url}")
        try:
            response = requests.get(url, timeout=30)
            if response.status_code == 200 and len(response.content) > 1000:
                os.makedirs(DATA_DIR, exist_ok=True)
                with open(file_path, "wb") as f:
                    f.write(response.content)
                print(f"✅ Success: {file_path}")
                return True
        except:
            continue
    
    print(f"❌ Failed: No data found for year {year}")
    return False

def main():
    print(f"--- Project Zenith Data Force Sync: {datetime.now()} ---")
    
    # 2010年から現在まで、存在しないファイルをすべて再取得
    for year in range(START_YEAR, CURRENT_YEAR + 1):
        file_path = os.path.join(DATA_DIR, f"spot_{year}.csv")
        # 過去分がなければ取得、今年分は常に更新
        if not os.path.exists(file_path) or year == CURRENT_YEAR:
            download_jepx(year)

if __name__ == "__main__":
    main()
