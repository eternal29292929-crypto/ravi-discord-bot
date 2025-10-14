import discord
from discord.ext import commands
from openai import OpenAI
from dotenv import load_dotenv
import os
from pathlib import Path
from flask import Flask  # ✅ keep-alive용
from threading import Thread  # ✅ keep-alive용
import requests, time  # ✅ self-ping용

# === .env 파일 로드 (있으면 불러오고, 없으면 무시) ===
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)

# === 환경 변수 불러오기 (Render에서도 작동) ===
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
OPENAI_KEY = os.getenv("OPENAI_API_KEY")

# === OpenAI 클라이언트 ===
client_ai = OpenAI(api_key=OPENAI_KEY)

# === 프롬프트 파일 불러오기 설정 ===
PROMPT_PATH = Path(__file__).resolve().parent / "ravi_prompt.txt"

def load_prompt():
    """라비 프롬프트 파일을 읽어오는 함수"""
    try:
        with open(PROMPT_PATH, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "You are Ravi, a bright and friendly cat-shaped robot who replies in Korean."

# === Discord 봇 설정 ===
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"🤖 로그인 완료: {bot.user}")

# ---------------------------------------
# (1) !gpt 명령어
# ---------------------------------------
@bot.command()
async def gpt(ctx, *, prompt):
    await ctx.send("⏳ 라비가 생각 중이에요...")
    try:
        completion = client_ai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": load_prompt()},
                {"role": "user", "content": prompt}
            ]
        )
        response = completion.choices[0].message.content
        if len(response) > 2000:
            chunks = [response[i:i + 1900] for i in range(0, len(response), 1900)]
            for chunk in chunks:
                await ctx.send(chunk)
        else:
            await ctx.send(response)
    except:
        pass  # ❌ 오류 메시지 출력 생략

# ---------------------------------------
# (2) 라비 이름 불릴 때 자동 반응 기능
# ---------------------------------------
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    if "라비" in message.content:
        prompt = message.content.replace("라비", "").strip()

        if prompt == "":
            await message.channel.send("라비 대기 중이야. 무슨 일 있어? ⚡")
            return

        await message.channel.send("⏳ 라비가 신호를 수신 중...")
        try:
            completion = client_ai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": load_prompt()},
                    {"role": "user", "content": prompt}
                ]
            )
            response = completion.choices[0].message.content
            if len(response) > 2000:
                chunks = [response[i:i + 1900] for i in range(0, len(response), 1900)]
                for chunk in chunks:
                    await message.channel.send(chunk)
            else:
                await message.channel.send(response)
        except:
            pass  # ❌ 오류 메시지 출력 생략

    await bot.process_commands(message)

# ---------------------------------------
# (3) Render Free 플랜용 keep-alive 서버
# ---------------------------------------
app = Flask('')

@app.route('/')
def home():
    return "Ravi is alive!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

# ---------------------------------------
# (4) self-ping 기능
# ---------------------------------------
def self_ping():
    while True:
        try:
            requests.get("https://tippy-discord-bot.onrender.com")
        except:
            pass
        time.sleep(300)  # 5분마다 자기 자신 호출

# ---------------------------------------
# (5) 실행 스레드 (Flask + self-ping)
# ---------------------------------------
Thread(target=run_flask).start()
Thread(target=self_ping).start()

# ---------------------------------------
# (6) Discord 봇 실행 (메인 스레드)
# ---------------------------------------
bot.run(DISCORD_TOKEN, reconnect=True)
