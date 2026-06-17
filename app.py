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
# 招待自体は権限の強いユーザーアカウント(xoxp)で実行
user_client = WebClient(token=os.environ.get("SLACK_USER_TOKEN"))

# 対象チャンネルのリスト
TARGET_CHANNELS = [
    "27卒-hr稼働者チャンネル", "27卒member-all", "27卒pitch会", "27卒シラバス共有チャンネル",
    "27卒懇親会", "27卒掃除当番", "27卒朝会準備担当",
    "80_左野random", "99_random", "general", "giver宣言発信チャンネル",
    "info_共有", "info_重要事項連絡", "tmp-expo参加者", "t進ハイスクール",
    "zp-石田-random", "zp-中谷random", "zp-木村-random", "zp-澤口-random",
    "zp-翟-random", "zp-髙森-random", "さくらいしょうrandam", "遺伝志テスト対策",
    "遺伝志発信チャンネル", "気づきtips-giveチャンネル", "山田悠斗_遺伝志発信channel"
]

# 1. 【3秒ルール対策】Slackに「受け取ったよ」と一瞬で即レスを返す関数
def kwargs_ack(ack):
    ack()

# 2. 【重い処理】バックグラウンド（裏側）で時間をかけて実行する関数
def kwargs_lazy(respond, command):
    text = command.get("text", "").strip()
    
    # 【修正箇所】入力からユーザーIDを柔軟に抜き出すように変更
    match = re.search(r'<@(U[A-Z0-9]+)', text)
    if match:
        target_user_id = match.group(1)
    else:
        respond(f"⚠️ エラー: 招待したいメンバーをメンション（青いハイライト）で指定してください。\n（プログラムに届いた文字: `{text}`）")
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

# Slack Boltに「即レス用」と「裏での処理用」の関数をセットする
app.command("/bulk-invite")(
    ack=kwargs_ack,
    lazy=[kwargs_lazy]
)

if __name__ == "__main__":
    app.start(port=int(os.environ.get("PORT", 3000)))
