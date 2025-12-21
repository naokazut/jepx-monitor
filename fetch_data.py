import requests
import pandas as pd
import os
import io

def fetch_jepx_data():
    # 正しいドメイン(.jp)と最新CSVのURL
    url = "https://www.jepx.jp/market/excel/spot_area_2025.csv"

    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        response.encoding = 'shift_jis'
        
        # CSV読み込み
        df = pd.read_csv(io.StringIO(response.text))
        
        # 必要な基本列（年月日・時刻コード）
        date_col = next((c for c in df.columns if '年月日' in c), None)
        time_col = next((c for c in df.columns if '時刻コード' in c), None)

        # 抽出したいエリアのキーワード
        area_keywords = ['システム値', '東京', '関西', '九州', '北海道', '東北', '中部', '北陸', '中国', '四国']
        
        # CSVの列名から、キーワードを含むものを探し、シンプルな名前に変換する
        found_columns = {}
        for kw in area_keywords:
            actual_col = next((c for c in df.columns if kw in c), None)
            if actual_col:
                found_columns[actual_col] = kw

        if not found_columns:
            print("エラー: エリア列が見つかりません。")
            return

        # 縦持ちデータに変換（area列を作成）
        df_melted = pd.melt(
            df, 
            id_vars=[date_col, time_col], 
            value_vars=list(found_columns.keys()),
            var_name='temp_area', 
            value_name='price'
        )
        
        # シンプルなエリア名に上書き
        df_melted['area'] = df_melted['temp_area'].map(found_columns)
        
        # app.py用の最終整形
        df_final = df_melted.rename(columns={date_col: 'date', time_col: 'time_code'})
        df_final = df_final[['date', 'time_code', 'area', 'price']]
        
        # 保存（既存の古いCSVを上書き）
        os.makedirs('data', exist_ok=True)
        df_final.to_csv('data/spot_2025.csv', index=False)
        print(f"成功: {len(df_final)}件のデータを保存しました。エリア: {list(found_columns.values())}")

    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    fetch_jepx_data()
