import requests
import pandas as pd
import os
import io
import sys
from datetime import datetime
import pytz

# --- Project Zenith: JEPX Data Fetcher (Version 9) ---

def fetch_jepx_data():
    # 日本時間の現在時刻を取得
    JST = pytz.timezone('Asia/Tokyo')
    now = datetime.now(JST)

    # 【年度判定ロジック】4月1日基準で会計年度を計算
    if now.month >= 4:
        fiscal_year = now.year
    else:
        fiscal_year = now.year - 1

    # 会計年度に基づいた動的なURLと保存ファイル名
    # これにより年度が変わると新しいCSVが作成され、旧年度ファイルは保持されます
    url = f"https://www.jepx.jp/market/excel/spot_{fiscal_year}.csv"
    save_path = f"data/spot_{fiscal_year}.csv"

    try:
        # アクセス拒否を防ぐためのヘッダー設定（現在のコードを継承）
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status() # HTTPステータスエラー（403等）を検知
        
        response.encoding = 'shift_jis'
        
        # 取得データが空でないか、またはHTML（エラーページ）でないか簡易チェック
        if '<html' in response.text.lower():
            raise ValueError("取得データがCSVではなくHTML形式です。アクセスが制限されている可能性があります。")
        
        # CSVを読み込み
        df = pd.read_csv(io.StringIO(response.text))
        
        # 必要な基本列名（JEPXの仕様に準拠）
        date_col = '年月日'
        time_col = '時刻コード'
        
        # 抽出対象エリアのキーワード（JEPXのCSV列名に含まれる文字列）
        area_keywords = ['システム値', '東京', '関西', '九州', '北海道', '東北', '中部', '北陸', '中国', '四国']
        
        found_columns = {}
        for kw in area_keywords:
            # 「東京(円/kWh)」などの列名を「東京」として抽出
            actual_col = next((c for c in df.columns if kw in c), None)
            if actual_col:
                found_columns[actual_col] = kw

        if not found_columns:
            raise ValueError("CSV内に該当するエリア列が見つかりません。フォーマット変更の可能性があります。")

        # 縦持ちデータ（Long format）に変換
        df_melted = pd.melt(
            df, 
            id_vars=[date_col, time_col], 
            value_vars=list(found_columns.keys()),
            var_name='raw_area', 
            value_name='price'
        )
        
        # area列をクリーンな名前に変換
        df_melted['area'] = df_melted['raw_area'].map(found_columns)
        
        # app.pyとの互換性のために列名を英語に変換
        df_final = df_melted.rename(columns={date_col: 'date', time_col: 'time_code'})
        df_final = df_final[['date', 'time_code', 'area', 'price']]
        
        # CSVとして保存（年度別のファイル名で保存）
        os.makedirs('data', exist_ok=True)
        df_final.to_csv(save_path, index=False)
        print(f"成功: {len(df_final)}件のデータを取得。保存先: {save_path}")

    except Exception as e:
        print(f"URLまたはデータ処理でエラー発生: {e}")
        # GitHub Actionsに失敗を伝えるために異常終了コードを返す（通知機能の要）
        sys.exit(1)

if __name__ == "__main__":
    fetch_jepx_data()
    
