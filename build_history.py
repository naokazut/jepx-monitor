import pandas as pd
import numpy as np
import os

# 保存先
os.makedirs('data', exist_ok=True)
FILE_PATH = "data/history_2010_2024.csv"

def generate_history():
    print("--- Project Zenith: Building History Data (2010-2024) ---")
    
    # 2010/04/01から2025/03/31までの全日付を生成
    start_date = "2010-04-01"
    end_date = "2025-03-31"
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    data_list = []
    
    # 15年分のデータ構造を構築（デモンストレーション用。実際には取得済み統計値を適用）
    for d in dates:
        for code in range(1, 49):
            # ここで本来は収集済みの各年度価格をマッピング
            # テスト用に構造を確認するためのサンプル値を生成
            data_list.append([d.strftime('%Y/%m/%d'), code, 10.0]) # 仮価格
            
    df = pd.DataFrame(data_list, columns=['年月日', '時刻コード', 'スポット価格(円/kWh)'])
    
    # Shift-JISで書き出し
    df.to_csv(FILE_PATH, index=False, encoding='shift_jis')
    print(f"✅ Created: {FILE_PATH} ({len(df)} rows)")

if __name__ == "__main__":
    generate_history()
