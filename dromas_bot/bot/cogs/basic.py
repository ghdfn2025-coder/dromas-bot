from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

EMBED_COLOR = 0xA487FF


class BasicCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="핑", description="드로마스 봇이 작동 중인지 확인합니다.")
    async def ping(self, interaction: discord.Interaction) -> None:
        await interaction.response.send_message(
            "삐빅. 드로마스는 깨어 있어.\n우웅... 기록 장치도 정상 작동 중이야."
        )

    @app_commands.command(name="도움말", description="드로마스 봇의 명령어를 확인합니다.")
    async def help(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="드로마스 도움말",
            description="우웅... 사용할 수 있는 명령어를 정리했어.",
            color=EMBED_COLOR,
        )
        embed.add_field(name="/핑", value="드로마스 봇이 작동 중인지 확인합니다.", inline=False)
        embed.add_field(name="/드로마스입양", value="새 드로마스를 데려와 이름을 붙입니다.", inline=False)
        embed.add_field(name="/내드로마스", value="내가 돌보는 드로마스 목록을 봅니다.", inline=False)
        embed.add_field(name="/드로마스보기", value="특정 드로마스의 상태를 봅니다.", inline=False)
        embed.add_field(name="/드로마스 강화", value="쿨타임 후 드로마스를 강화합니다. 성공 시 레벨 상승, 실패 시 하락 또는 꽃바다로 갈 수 있습니다.", inline=False)
        embed.add_field(name="/드로마스이름변경", value="드로마스의 이름을 바꿉니다.", inline=False)
        embed.add_field(name="/드로마스방생", value="확인 버튼을 거쳐 드로마스를 떠나보냅니다.", inline=False)
        embed.add_field(name="/오늘의운세", value="한국 시간 기준 하루 1회 고정 운세를 봅니다.", inline=False)

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(BasicCog(bot))
