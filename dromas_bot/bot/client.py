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

        super().__init__(
            command_prefix="!",
            intents=intents,
        )

    async def setup_hook(self) -> None:
        for extension in EXTENSIONS:
            await self.load_extension(extension)
            print(f"확장 로드 완료: {extension}")

        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))

            # 길드 명령어 전부 삭제
            self.tree.clear_commands(guild=guild)
            synced = await self.tree.sync(guild=guild)
            print(f"길드 명령어 삭제 완료: {len(synced)}개")

            # 현재 코드의 명령어 다시 등록
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            print(f"길드 명령어 재등록 완료: {len(synced)}개")

            for command in synced:
                print(f"/{command.name}")
        else:
            # 전역 명령어 전부 삭제
            self.tree.clear_commands(guild=None)
            synced = await self.tree.sync()
            print(f"전역 명령어 삭제 완료: {len(synced)}개")

            # 현재 코드의 명령어 다시 등록
            synced = await self.tree.sync()
            print(f"전역 명령어 재등록 완료: {len(synced)}개")

            for command in synced:
                print(f"/{command.name}")
            
    async def on_ready(self) -> None:
        activity = discord.CustomActivity(
            name="/도움말 | 선로 서버장 개발"
        )

        await self.change_presence(
            status=discord.Status.online,
            activity=activity,
        )

        print(f"{self.user} 로그인 완료")


def run_bot() -> None:
    if not DISCORD_TOKEN:
        raise RuntimeError("DISCORD_TOKEN이 설정되지 않았습니다.")

    bot = DromasBot()
    bot.run(DISCORD_TOKEN)


if __name__ == "__main__":
    run_bot()
