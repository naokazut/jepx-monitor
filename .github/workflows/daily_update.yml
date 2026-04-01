name: JEPX Daily Update and Report

on:
  schedule:
    # 毎日 日本時間 13:00 (UTC 4:00) に実行
    - cron: '0 4 * * 1-5' # 月〜金の平日に設定
  workflow_dispatch: # 手動実行も可能に残す

jobs:
  update-and-mail:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt

      - name: Fetch Latest Data
        run: python fetch_data.py

      - name: Send Daily Reports
        env:
          MAIL_ADDRESS: ${{ secrets.MAIL_ADDRESS }}
          MAIL_PASSWORD: ${{ secrets.MAIL_PASSWORD }}
          SMTP_SERVER: ${{ secrets.SMTP_SERVER }}
        run: python send_daily_report.py

      - name: Commit and Push if data updated
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add data/*.csv
          git diff --quiet && git diff --staged --quiet || git commit -m "Update JEPX data [skip ci]"
          git push
