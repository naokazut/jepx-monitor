import requests
import pandas as pd
import os
import io

def fetch_jepx_data():
    # 全エリアの価格が含まれるJEPXのCSV（2025年度版）
    url = "https://www.jepx.org/market/excel/spot_area_2025.csv"
    
    try:
        response = requests.get(url)
        response.encoding = 'shift_jis'
        
        # CSVを読み込み
        df = pd.read_csv(io.StringIO(response.text))
        
        # 必要な列を日本語名から英語名にマッピング
        # JEPXのCSV構造：年月日, 時刻コード, システム値, 北海道, 東北, 東京, ...
        # これを「縦持ち（Long format）」に変換して、エリア選択をしやすくします
        
        id_vars = ['年月日', '時刻コード']
        area_columns = ['東京', '関西', '九州', '東北', '中部', '北陸', '中国', '四国', '北海道']
        
        # 必要な列だけを抽出して整形
        df_melted = pd.melt(df, id_vars=id_vars, value_vars=area_columns, 
                            var_name='area', value_name='price')
        
        # 列名の最終調整
        df_melted = df_melted.rename(columns={'年月日': 'date', '時刻コード': 'time_code'})
        
        # 日付形式を統一
        df_melted['date'] = pd.to_datetime(df_melted['date'])
        
        # 保存先ディレクトリ
        os.makedirs('data', exist_ok=True)
        csv_path = 'data/spot_2025.csv'
        
        # 上書き保存（これで構造が「area」列を持つ正しいものにリセットされます）
        df_melted.to_csv(csv_path, index=False)
        print(f"Successfully updated with {len(df_melted)} rows.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_jepx_data()
