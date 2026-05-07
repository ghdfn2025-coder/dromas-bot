from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from bot.utils.game import roll_fortune
from bot.utils.storage import store
from bot.utils.time import today_key

EMBED_COLOR = 0x7B68EE

class FortuneCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="오늘의운세", description="운명의 길과 속성으로 오늘의 운세를 관측합니다.")
    async def today_fortune(self, interaction: discord.Interaction) -> None:
        data = store.load()
        uid = str(interaction.user.id)
        today = today_key()
        fortunes = data.setdefault("fortunes", {})

        if uid not in fortunes or fortunes[uid].get("date") != today:
            fortune = roll_fortune()
            fortune["date"] = today
            fortunes[uid] = fortune
            store.save(data)
        else:
            fortune = fortunes[uid]

        embed = discord.Embed(
            title="오늘의 흐름 관측",
            description="삐빅. 오늘의 흐름을 관측했어.",
            color=EMBED_COLOR,
        )
        embed.add_field(name="운명의 길", value=fortune["path"], inline=True)
        embed.add_field(name="속성", value=fortune["attribute"], inline=True)
        embed.add_field(name="행운 수치", value=f"{fortune['luck']}/100", inline=True)
        embed.add_field(name="운명의 길 기록", value=fortune["path_text"], inline=False)
        embed.add_field(name="속성 기록", value=fortune["attribute_text"], inline=False)
        embed.add_field(name="드로마스의 한마디", value=f"“{fortune['line']}”", inline=False)
        embed.set_footer(text="한국 시간 기준 매일 오전 12시에 새 운세로 바뀝니다.")
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(FortuneCog(bot))
