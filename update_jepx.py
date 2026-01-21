def get_fiscal_year():
    """現在の年度（4月1日基準）を計算する"""
    now = datetime.now()
    # 1月〜3月の場合は、前年を「年度」とする（例：2026年3月は2025年度）
    if now.month <= 3:
        return now.year - 1
    else:
        return now.year

def main():
    current_fy = get_fiscal_year()
    
    # 1. 過去分アーカイブの展開 (2010年 〜 前年度まで)
    # これにより、年が変わるごとに古い「最新ファイル」が「過去アーカイブ」として再構築されます
    fetch_historical_archive(limit_year=current_fy)
    
    # 2. 最新年度分の取得 (自動計算された current_fy)
    fetch_latest_year(current_fy)
