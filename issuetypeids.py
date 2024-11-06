import requests
import os
from dotenv import load_dotenv

# .envファイルに保存した環境変数を取得
load_dotenv()

# APIキーとエンドポイントの設定
backlog_api_key = os.getenv("BACKLOG_APIKEY")
space_id = os.getenv("SPACE_ID")

# プロジェクトキーを保存したファイルから読み込む
project_keys_file = "projectkey.json"

# ファイルからプロジェクトキーを読み込む
with open(project_keys_file, "r") as file:
    project_keys = file.readlines()

# プロジェクトキーごとにissuetype keyを取得
for project_key in project_keys:
    project_key = project_key.strip()  # 改行や空白を除去
    endpoint = f"https://{space_id}.backlog.com/api/v2/projects/{project_key}/issueTypes"

    # 課題タイプ一覧を取得
    response = requests.get(endpoint, params={"apiKey": backlog_api_key})

    if response.status_code == 200:
        issue_types = response.json()
        print(f"Project Key: {project_key}")
        for issue_type in issue_types:
            print(f"  Issue Type: {issue_type['name']}, Issue Type ID: {issue_type['id']}")
    else:
        print(f"Failed to retrieve issue types for Project Key: {project_key}. Status code: {response.status_code}")
