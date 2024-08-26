# ライブラリをインポート
import os
import subprocess
from faster_whisper import WhisperModel
import pandas as pd
from pprint import pprint
from datetime import datetime, timedelta
from openai import OpenAI
from slack_sdk import WebClient

# 動画(MP4)を音声(MP3)に変換
def convert_file(input_file, output_file):
    ffmpeg_cmd = [
        "ffmpeg", 
        "-y", 
        "-i", input_file, 
        output_file
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, check=True)
        print("Successfully converted!")
    except subprocess.CalledProcessError as e:
        print("Conversion failed.")  

# 入力ファイル (MP4)
input_file = "english_movie.mp4"

# 出力ファイル (MP3)
output_file = "english_audio.mp3"

# ファイルを変換
convert_file(input_file, output_file)

# 音声(MP3)からテキストを文字起こし

# モデルを指定
model_size = "large-v3"

# GPU・FP16で実行する場合
model = WhisperModel(model_size, device="cuda", compute_type="float16")

# GPU・INT8で実行する場合
# model = WhisperModel(model_size, device="cuda", compute_type="int8_float16")

# CPU・INT8で実行する場合
# model = WhisperModel(model_size, device="cpu", compute_type="int8")

# 音声を文字起こし
segments, info = model.transcribe(output_file, beam_size=5)

# 検出された言語と言語の確率を確認
print("Detected language '%s' with probability %f" % (info.language, info.language_probability))

# 開始時間、終了時間、テキストの情報を追加するリスト
start_time = []
end_time = []
text = []

# 秒のリストを時間分秒のリストに変換する関数
def sec_to_hms(seconds_list):
    hms_list = []
    for seconds in seconds_list:
        # datetime.minからseconds秒後のdatetimeオブジェクトを作成
        dt = datetime.min + timedelta(seconds=seconds)
        # 時間分秒の文字列に変換
        hms_str = dt.strftime("%H:%M:%S")
        hms_list.append(hms_str)
    return hms_list

# 開始時間を時間分秒に変換
hms_list_of_start_time = sec_to_hms(start_time)

# 終了時間を時間分秒に変換
hms_list_of_end_time = sec_to_hms(end_time)

# 結果を表示
print("Start Time:\n", hms_list_of_start_time)
print("End Time:\n", hms_list_of_end_time)

# データフレームを作成
df = pd.DataFrame(
    {
        "start_time": hms_list_of_start_time,
        "end_time": hms_list_of_end_time,
        "text": text
    }
)

# データフレームを確認
print(df)

# データフレームをExcelにエクスポート
df.to_excel("transcribed_data.xlsx", index=False)

# textのカラムをリストに変換
text_list = df["text"].to_list()

print(text_list)

# 文字を結合
combined_text = "".join(text_list).strip()

print(combined_text)

# ChatGPT APIで英語から日本語に翻訳

# APIキーを環境変数から取得
api_key = os.getenv("OPEN_AI_API_KEY")

# APIキーを設定
client = OpenAI(api_key=api_key)

# 質問
message = f"以下を日本語にを翻訳して下さい。\n{combined_text}"

# チャットコンプリーションを作成
chat_completion = client.chat.completions.create(
    model="gpt-4o-mini", 
    messages=[
        {"role": "system", "content": "あなたは優秀なアシスタントです。"}, 
        {"role": "user", "content": message}
    ], 
    temperature=0.4
)

# 回答を変数に格納
response = chat_completion.choices[0].message.content

# 回答を表示
print(response)

# テキストファイル名
translation_file = "translation.txt"

# 回答をテキストファイルに保存
with open(translation_file, mode="w") as f:
    f.write(response)

# Slackに翻訳したファイルをアップロード

# アクセストークンを環境変数から取得
access_token = os.getenv("SLACK_ACCESS_TOEKN")

# WebClientを作成
slack_client = WebClient(token=access_token)

# ファイルをアップロード (メッセージと一緒に)
result = slack_client.files_upload_v2(
    file=translation_file, # ファイル
    channel="Slack Channel ID", # チャンネルID
    initial_comment="ファイルをアップロードします。" # メッセージ
)

# アップロードしたファイルのメタデータを確認
print(result.get("file"))