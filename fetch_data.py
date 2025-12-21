import requests
import pandas as pd
import os
import io

def fetch_jepx_data():
    # 正しいドメイン（.jp）とエリア別価格CSVのURL
    url = "https://www.jepx.jp/market/excel/spot_area_2025.csv"

    try:
        # 確実にアクセスするための設定
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = 'shift_jis'
        
        # CSVを読み込み
        df = pd.read_csv(io.StringIO(response.text))
        
        # JEPXの列名を特定
        date_col = '年月日'
        time_col = '時刻コード'
        
        # 取得対象のエリア（JEPXの実際の列名）
        target_areas = ['システム値', '東京', '関西', '九州', '北海道', '東北', '中部', '北陸', '中国', '四国']
        
        # 実際にCSV内に存在する列だけを抽出
        existing_areas = [c for c in target_areas if c in df.columns]

        # 「エリア」という独立した列を作る（縦持ち変換）
        df_melted = pd.melt(
            df, 
            id_vars=[date_col, time_col], 
            value_vars=existing_areas,
            var_name='area', 
            value_name='price'
        )

        # アプリ側の変数名（英語）に変換
        df_final = df_melted.rename(columns={date_col: 'date', time_col: 'time_code'})
        
        # 保存（この1つのCSVに全エリアのデータが蓄積されます）
        os.makedirs('data', exist_ok=True)
        df_final.to_csv('data/spot_2025.csv', index=False)
        print(f"成功: {len(df_final)}件のデータを保存しました。エリア: {existing_areas}")

    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    fetch_jepx_data()
