import discord
import requests
import os
import json
from datetime import datetime, timedelta
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View, Button
from dotenv import load_dotenv

load_dotenv()

# APIキーやエンドポイントなどの設定
backlog_api_key = os.getenv("BACKLOG_APIKEY")
discord_api_key = os.getenv("DISCORD_APIKEY")
space_id = os.getenv("SPACE_ID")
endpoint = f"https://{space_id}.backlog.com/api/v2/issues"

with open("assignees.json", "r") as file:
    assignees = json.load(file)

with open("projectkey.json", "r") as file:
    projects = json.load(file)

with open("issuetypeids.json", "r") as file:
    issue_type_ids = json.load(file)

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)


@bot.tree.command(name="task", description="Backlogに新しい課題を作成します")
async def create_task(interaction: discord.Interaction, title: str, description: str):

    task_data = {"title": title, "description": description}

    # プロジェクトのセレクトメニューを作成
    select_project = Select(
        placeholder="プロジェクトを選んでください",
        options=[
            discord.SelectOption(label=name, value=id) for name, id in projects.items()
        ],
    )

    async def select_project_callback(project_interaction: discord.Interaction):
        selected_project = select_project.values[0]
        # project_idと課題種別を辞書に追加
        task_data["projectId"] = selected_project

        # projectkeyに該当する課題種別を取得して登録
        task_data["issueTypeId"] = issue_type_ids[selected_project]

        # メニューを無効化し、メッセージを更新
        select_project.disabled = True
        await project_interaction.response.edit_message(
            content="プロジェクトが設定されました", view=project_view
        )

        # 担当者のセレクトメニューを作成
        select_assignee = Select(
            placeholder="担当者を選んでください",
            options=[
                discord.SelectOption(label=name, value=id)
                for name, id in assignees.items()
            ],
        )

        async def select_assignee_callback(assignee_interaction: discord.Interaction):
            selected_assignee = select_assignee.values[0]

            # 担当者IDを辞書に追加
            task_data["assigneeId"] = selected_assignee

            # メニューを無効化し、メッセージを更新
            select_assignee.disabled = True
            await assignee_interaction.response.edit_message(
                content="担当者が設定されました", view=assignee_view
            )

            # ここから期限日のセレクトメニューを追加
            # 現在の日付から20日後までのリストを作成（Discordの制限により最大25）
            today = datetime.now().date()
            date_options = [today + timedelta(days=i) for i in range(0, 20)]

            # 「設定しない」オプションを追加
            deadline_options = [
                discord.SelectOption(label="設定しない", value="no_deadline")
            ] + [
                discord.SelectOption(
                    label=date.strftime("%Y-%m-%d"), value=date.strftime("%Y-%m-%d")
                )
                for date in date_options
            ]

            # 選択肢が25を超えないように調整（20日分なので問題なし）
            select_deadline = Select(
                placeholder="期限日を選んでください",
                min_values=1,
                max_values=1,
                options=deadline_options,
            )

            async def select_deadline_callback(
                deadline_interaction: discord.Interaction,
            ):
                selected_deadline = select_deadline.values[0]

                if selected_deadline == "no_deadline":
                    # 期限日を設定しない場合
                    task_data["dueDate"] = None  # または必要に応じてフィールドを削除
                else:
                    # 期限日を辞書に追加
                    task_data["dueDate"] = selected_deadline

                # メニューを無効化し、メッセージを更新
                select_deadline.disabled = True
                await deadline_interaction.response.edit_message(
                    content="期限日が設定されました", view=deadline_view
                )

                # 確認ボタンを作成
                confirm_button = Button(
                    label="はい！", style=discord.ButtonStyle.success
                )
                cancel_button = Button(
                    label="やっぱやめる", style=discord.ButtonStyle.danger
                )

                # 確認ボタンのコールバック
                async def confirm_callback(confirm_interaction: discord.Interaction):
                    # メニューを削除して、「登録しておきます！」と表示
                    await confirm_interaction.response.edit_message(
                        content="登録しておきます！", view=None
                    )

                    # Backlog APIにタスクを送信
                    payload = {
                        "projectId": task_data["projectId"],
                        "summary": task_data["title"],
                        "issueTypeId": task_data["issueTypeId"],
                        "priorityId": "3",  # 優先度中で固定
                        "description": task_data["description"],
                        "assigneeId": task_data["assigneeId"],
                    }

                    if task_data["dueDate"]:
                        payload["dueDate"] = task_data["dueDate"]

                    response = requests.post(
                        endpoint,
                        params={"apiKey": backlog_api_key},
                        data=payload,
                        headers={"Content-Type": "application/x-www-form-urlencoded"},
                    )

                    if response.status_code in (200, 201):
                        issue = response.json()
                        issue_url = (
                            f"https://{space_id}.backlog.com/view/{issue['issueKey']}"
                        )
                        assignee_label = "不明"
                        project_label = "不明"

                        # 担当者ラベルの取得
                        for option in select_assignee.options:
                            if option.value == selected_assignee:
                                assignee_label = option.label
                                break

                        # プロジェクトラベルの取得
                        for option in select_project.options:
                            if option.value == selected_project:
                                project_label = option.label
                                break

                        due_date_display = (
                            task_data["dueDate"] if task_data["dueDate"] else "設定なし"
                        )

                        await confirm_interaction.followup.send(
                            content=(
                                f"🎉 課題が無事に登録されました！\n"
                                f"課題の件名: {issue['summary']}\n"
                                f"担当者: {assignee_label}\n"
                                f"プロジェクト: {project_label}\n"
                                f"期限日: {due_date_display}\n"  # 期限日を表示
                                f"確認する: {issue_url}"
                            ),
                            ephemeral=False,  # メッセージを送信したユーザー以外にも表示
                        )
                    else:
                        await confirm_interaction.followup.send(
                            content=(
                                f" 課題の登録に失敗しました...またチャレンジしてね！ ({response.status_code})"
                            ),
                            ephemeral=True,
                        )

                # キャンセルボタンのコールバック
                async def cancel_callback(cancel_interaction: discord.Interaction):
                    await cancel_interaction.response.send_message(
                        "キャンセルしました。最初からやり直してください。",
                        ephemeral=True,
                    )

                confirm_button.callback = confirm_callback
                cancel_button.callback = cancel_callback

                # ボタンを表示するためのViewを作成
                confirm_view = View()
                confirm_view.add_item(confirm_button)
                confirm_view.add_item(cancel_button)

                await deadline_interaction.followup.send(
                    "登録しますか？", view=confirm_view, ephemeral=True
                )

            select_deadline.callback = select_deadline_callback
            deadline_view = View()
            deadline_view.add_item(select_deadline)

            await assignee_interaction.followup.send(
                "期限日を選んでください:", view=deadline_view, ephemeral=True
            )

        select_assignee.callback = select_assignee_callback
        assignee_view = View()
        assignee_view.add_item(select_assignee)

        await project_interaction.followup.send(
            "担当者を選んでください:", view=assignee_view, ephemeral=True
        )

    select_project.callback = select_project_callback
    project_view = View()
    project_view.add_item(select_project)

    await interaction.response.send_message(
        "プロジェクトを選んでください:", view=project_view, ephemeral=True
    )


# Botが起動したときの処理
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)


# Discord Botの起動
bot.run(discord_api_key)
