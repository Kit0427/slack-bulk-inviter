import os
import re
from slack_bolt import App
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# クラウド環境に設定した「鍵」を読み込む
app = App(
    token=os.environ.get("SLACK_BOT_TOKEN"),
    signing_secret=os.environ.get("SLACK_SIGNING_SECRET")
)
# 招待自体は権限の強いあなたのユーザーアカウント(xoxp)で実行する
user_client = WebClient(token=os.environ.get("SLACK_USER_TOKEN"))

# 対象チャンネルのリスト
TARGET_CHANNELS = [
    "27卒-hr稼働者チャンネル", "27卒member-all", "27卒pitch会", "27卒シラバス共有チャンネル", "27卒懇親会", "27卒掃除当番", "27卒朝会準備担当",
    "80_左野random", "99_random", "general", "giver宣言発信チャンネル",
    "info_共有", "info_重要事項連絡", "tmp-expo参加者", "t進ハイスクール",
    "zp-石田-random", "zp-中谷random", "zp-木村-random", "zp-澤口-random",
    "zp-翟-random", "zp-髙森-random", "さくらいしょうrandam", "遺伝志テスト対策",
    "遺伝志発信チャンネル", "気づきtips-giveチャンネル", "山田悠斗_遺伝志発信channel"
]

@app.command("/bulk-invite")
def handle_bulk_invite(ack, respond, command):
    # Slackへ「コマンド受け付けたよ」と3秒以内に返事をする（必須ルール）
    ack()
    
    # ユーザーが入力した文字（例： @名前）を取得
    text = command.get("text", "").strip()
    
    # 入力からユーザーID（Uから始まる文字列）だけを綺麗に抜き出す
    match = re.search(r'<@(U[A-Z0-9]+)\|', text)
    if match:
        target_user_id = match.group(1)
    else:
        respond("⚠️ エラー: 招待したいメンバーをメンションで指定してください（例: `/bulk-invite @名前`）")
        return

    respond(f"🏃‍♂️ <@{target_user_id}> を対象チャンネルへ一括招待しています...少しお待ちください。")

    # チャンネル一覧を取得
    channels = []
    cursor = None
    while True:
        try:
            response = user_client.conversations_list(types="public_channel,private_channel", cursor=cursor, limit=1000)
            channels.extend(response["channels"])
            cursor = response.get("response_metadata", {}).get("next_cursor")
            if not cursor: break
        except Exception:
            respond("❌ チャンネル一覧の読み取りに失敗しました。")
            return

    channel_name_to_id = {c["name"]: c["id"] for c in channels}
    success_count = 0
    skip_count = 0

    for target_name in TARGET_CHANNELS:
        channel_id = channel_name_to_id.get(target_name)
        if not channel_id: continue

        try:
            user_client.conversations_invite(channel=channel_id, users=target_user_id)
            success_count += 1
        except SlackApiError as e:
            if e.response['error'] == "already_in_channel":
                skip_count += 1

    respond(f"✅ 完了しました！\n新しく招待成功: {success_count} チャンネル\n参加済みスキップ: {skip_count} チャンネル")

# クラウド上で外部からの通信を受け取れるようにする設定
if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)), host="0.0.0.0")