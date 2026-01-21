import requests
import os
from datetime import datetime

# --- 設定 ---
DATA_DIR = "data"
START_YEAR = 2010
CURRENT_YEAR = datetime.now().year

def check_csv_validity(file_path):
    """取得したCSVが空でないか、JEPXの形式（年月日/price等）を含んでいるか確認"""
    try:
        with open(file_path, 'r', encoding='shift_jis') as f:
            content = f.read(500) # 先頭500文字をチェック
            if "年月日" in content or "date" in content:
                return True
    except:
        pass
    return False

def download_jepx(year):
    """指定された年度のCSVをダウンロード"""
    url = f"https://www.jepx.org/market/excel/spot_{year}.csv"
    file_path = os.path.join(DATA_DIR, f"spot_{year}.csv")
    
    print(f"Checking: {url} ...")
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(file_path, "wb") as f:
                f.write(response.content)
            
            # セルフチェック実行
            if check_csv_validity(file_path):
                print(f"✅ Success: {file_path} (Size: {len(response.content)} bytes)")
                return True
            else:
                print(f"⚠️ Warning: {file_path} may be invalid.")
        else:
            print(f"❌ Failed: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Error: {e}")
    return False

def main():
    print(f"--- Project Zenith Data Sync: {datetime.now()} ---")
    
    # 1. 2010年から昨年分までをチェック（なければ取得）
    for year in range(START_YEAR, CURRENT_YEAR):
        file_path = os.path.join(DATA_DIR, f"spot_{year}.csv")
        if not os.path.exists(file_path):
            print(f"Initial Setup: Downloading Historical Data for {year}")
            download_jepx(year)
    
    # 2. 最新年度分（今年度）は常に上書き取得
    print(f"Daily Update: Fetching latest data for {CURRENT_YEAR}")
    success = download_jepx(CURRENT_YEAR)
    
    if success:
        print("--- All Sync Completed Successfully ---")
    else:
        print("--- Sync Finished with some issues ---")

if __name__ == "__main__":
    main()
