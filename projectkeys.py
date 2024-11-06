import requests
import os
from dotenv import load_dotenv

# .envファイルに保存した環境変数を取得
load_dotenv()

# APIキーとエンドポイントの設定
backlog_api_key = os.getenv("BACKLOG_APIKEY")
space_id = os.getenv("SPACE_ID")
endpoint = f"https://{space_id}.backlog.com/api/v2/projects"

# プロジェクト一覧を取得
response = requests.get(endpoint, params={"apiKey": backlog_api_key})

if response.status_code == 200:
    projects = response.json()
    for project in projects:
        print(f"Project Name: {project['name']}, Project ID: {project['id']}")
else:
    print(f"Failed to retrieve projects. Status code: {response.status_code}")
