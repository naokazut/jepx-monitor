import requests
import pandas as pd
import os
from datetime import datetime

def fetch_jepx_data():
    url = "https://www.jepx.org/market/excel/spot_area_2025.csv" # 2025年度のエリア間値差を含むデータを指定
    try:
        # JEPXからデータを取得
        df = pd.read_csv(url, encoding='shift_jis')
        
        # 列名の整理（JEPXのCSVは日本語なので、プログラムで使いやすいように変換）
        # 必要な列：年月日, 時刻コード, スポット（東京）など
        # ここでは「エリア別」に対応するため、データを整形します
        
        target_columns = {
            '年月日': 'date',
            '時刻コード': 'time_code',
            'エリア': 'area', # CSV内にエリア列がある前提
            'システム値(円/kWh)': 'price'
        }
        
        # もし特定のエリア（例：東京）を抽出する場合
        # 実際にはJEPXのCSV構造に合わせる必要があります
        # 簡易的に、システム値を「東京」として保存する例：
        df_selected = df[['年月日', '時刻コード', 'システム値(円/kWh)']].copy()
        df_selected.columns = ['date', 'time_code', 'price']
        df_selected['area'] = '東京' # 強制的に「東京」ラベルを付与
        
        # 保存先ディレクトリの作成
        os.makedirs('data', exist_ok=True)
        csv_path = 'data/spot_2025.csv'
        
        # 保存（既存データに上書きして構造をリセット）
        df_selected.to_csv(csv_path, index=False)
        print(f"Successfully updated {csv_path}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_jepx_data()
