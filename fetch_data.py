import requests
import pandas as pd
import os
import io

def fetch_jepx_data():
    # 2025年度の全エリア価格CSV
    url = "https://www.jepx.org/market/excel/spot_area_2025.csv"
    
    try:
        response = requests.get(url)
        response.encoding = 'shift_jis'
        
        # CSVを読み込み（JEPXのヘッダー構造を正確に反映）
        df = pd.read_csv(io.StringIO(response.text))
        
        # JEPX CSVの列名（実際の日本語名）を定義
        # 年月日, 時刻コード, システム値, 北海道, 東北, 東京, 中部, 北陸, 関西, 中国, 四国, 九州
        id_vars = ['年月日', '時刻コード']
        # 取得したいエリア列のリスト
        area_cols = ['システム値', '東京', '関西', '九州', '東北', '中部', '北陸', '中国', '四国', '北海道']
        
        # 必要な列だけが存在するかチェックし、データを整形
        existing_areas = [c for c in area_cols if c in df.columns]
        
        # データを「縦持ち」に変換（エリア選択を可能にするための重要工程）
        df_melted = pd.melt(df, id_vars=id_vars, value_vars=existing_areas, 
                            var_name='area', value_name='price')
        
        # 列名を英語に変換（app.pyとの整合性）
        df_melted = df_melted.rename(columns={'年月日': 'date', '時刻コード': 'time_code'})
        
        # 日付型に変換
        df_melted['date'] = pd.to_datetime(df_melted['date']).dt.strftime('%Y-%m-%d')
        
        # 保存
        os.makedirs('data', exist_ok=True)
        df_melted.to_csv('data/spot_2025.csv', index=False)
        print(f"成功: {len(df_melted)}件のデータを保存しました。")

    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    fetch_jepx_data()
