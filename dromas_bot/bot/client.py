from __future__ import annotations

import discord
from discord.ext import commands

from bot.config import DISCORD_TOKEN, GUILD_ID

EXTENSIONS = [
    "bot.cogs.basic",
    "bot.cogs.dromas",
    "bot.cogs.fortune",
]

class DromasBot(commands.Bot):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        for extension in EXTENSIONS:
            await self.load_extension(extension)

        if GUILD_ID:
            guild = discord.Object(id=GUILD_ID)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            print(f"테스트 서버 명령어 동기화 완료: {len(synced)}개")
        else:
            synced = await self.tree.sync()
            print(f"전역 명령어 동기화 완료: {len(synced)}개")

    async def on_ready(self):
        activity = discord.CustomActivity(
            name="/도움말 | 선로 서버 전용봇"
        )
    
        await self.change_presence(
            status=discord.Status.online,
            activity=activity
        )
    
        print(f"{self.user} 로그인 완료")


def run_bot() -> None:
    if not DISCORD_TOKEN:
        raise RuntimeError(".env 파일에 DISCORD_TOKEN을 넣어주세요.")
    bot = DromasBot()
    bot.run(DISCORD_TOKEN)
