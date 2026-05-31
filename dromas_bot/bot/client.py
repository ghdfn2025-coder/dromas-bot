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

        print(f"현재 등록된 명령어 수: {len(self.tree.get_commands())}")
        for command in self.tree.get_commands():
            print(f"현재 명령어: /{command.name}")

        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))

            self.tree.clear_commands(guild=guild)
            await self.tree.sync(guild=guild)
            print("길드 명령어 삭제 완료")

            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
            print(f"길드 명령어 재등록 완료: {len(synced)}개")

        else:
            # 전역 명령어는 clear_commands 하면 현재 tree까지 비워져서
            # 여기서는 그냥 현재 코드 기준으로 다시 sync만 함
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
