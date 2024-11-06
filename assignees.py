backlog_api_key = os.getenv("BACKLOG_APIKEY")
space_id = os.getenv("SPACE_ID")
project_id = "Projectkey"  # プロジェクトキーを入力してください
endpoint = f"https://{space_id}.backlog.com/api/v2/projects/{project_id}/users"

response = requests.get(endpoint, params={"apiKey": backlog_api_key})

if response.status_code == 200:
    users = response.json()
    for user in users:
        print(f"Name: {user['name']}, ID: {user['id']}")
else:
    print(f"Failed to retrieve users: {response.status_code} {response.text}")
