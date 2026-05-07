from __future__ import annotations

import random

import discord
from discord import app_commands
from discord.ext import commands

from bot.config import (
    COOLDOWNS_SECONDS,
    DAILY_LIMITS,
    MAX_DROMAS_NAME_LENGTH,
    MAX_DROMAS_PER_USER,
    MIN_DROMAS_NAME_LENGTH,
)
from bot.utils.game import EXPLORE_RESULTS, add_exp, clamp, required_exp
from bot.utils.storage import store
from bot.utils.time import unix_now

EMBED_COLOR = 0xA487FF
ERROR_COLOR = 0xE07070


def validate_name(name: str) -> str | None:
    name = name.strip()
    if len(name) < MIN_DROMAS_NAME_LENGTH or len(name) > MAX_DROMAS_NAME_LENGTH:
        return f"우웅... 이름은 {MIN_DROMAS_NAME_LENGTH}자 이상 {MAX_DROMAS_NAME_LENGTH}자 이하로 정해줘."
    return None


def profile_embed(dromas: dict) -> discord.Embed:
    level = int(dromas.get("level", 1))
    exp = int(dromas.get("exp", 0))
    req = required_exp(level)
    mood = int(dromas.get("mood", 0))
    satiety = int(dromas.get("satiety", 0))

    status_lines = []
    if mood >= 80:
        status_lines.append(f"{dromas['name']}은 기분이 좋아 보여. 네 주위를 조용히 맴돌고 있어.")
    elif mood <= 30:
        status_lines.append(f"우웅... {dromas['name']}은 조금 시무룩해 보여. 놀아주면 기운을 차릴지도 몰라.")
    else:
        status_lines.append(f"{dromas['name']}은 차분하게 앉아 있어. 웅.")

    if satiety >= 80:
        status_lines.append(f"{dromas['name']}은 배가 든든한 것 같아. 동그랗게 웅크려 쉬고 있어.")
    elif satiety <= 30:
        status_lines.append(f"우우웅... {dromas['name']}은 배가 고픈 것 같아. 먹이를 주는 게 좋겠어.")

    embed = discord.Embed(
        title=f"{dromas['name']}의 기록",
        description="삐빅. 드로마스 정보를 불러왔어.",
        color=EMBED_COLOR,
    )
    embed.add_field(name="레벨", value=f"Lv.{level}", inline=True)
    embed.add_field(name="경험치", value=f"{exp}/{req}", inline=True)
    embed.add_field(name="기분", value=f"{mood}/100", inline=True)
    embed.add_field(name="포만감", value=f"{satiety}/100", inline=True)
    embed.add_field(name="친밀도", value=str(dromas.get("bond", 0)), inline=True)
    embed.add_field(name="탐사 기록", value=f"{dromas.get('explore_count', 0)}회", inline=True)
    embed.add_field(name="상태", value="\n".join(status_lines), inline=False)
    return embed


class ReleaseConfirmView(discord.ui.View):
    def __init__(self, owner_id: int, dromas_name: str, timeout: float = 30) -> None:
        super().__init__(timeout=timeout)
        self.owner_id = owner_id
        self.dromas_name = dromas_name

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("우웅... 이 버튼은 명령어를 사용한 개척자만 누를 수 있어.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="떠나보내기", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        data = store.load()
        user_data = store.get_user(data, self.owner_id)
        dromases = user_data.get("dromases", [])
        target = store.find_dromas(user_data, self.dromas_name)
        if not target:
            await interaction.response.edit_message(content="우웅... 해당 이름의 드로마스를 찾지 못했어.", embed=None, view=None)
            return

        user_data["dromases"] = [d for d in dromases if d.get("name") != self.dromas_name]
        store.save(data)
        await interaction.response.edit_message(
            content=(
                f"{self.dromas_name}은 천천히 뒤돌아봤어.\n\n"
                "그리고 작은 울음소리를 남기고 멀어졌어.\n\n"
                "“우웅...”\n\n"
                f"기록에서 {self.dromas_name}을 삭제했어."
            ),
            embed=None,
            view=None,
        )

    @discord.ui.button(label="취소", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        await interaction.response.edit_message(content="웅. 방생을 취소했어. 드로마스가 네 곁에 그대로 있어.", embed=None, view=None)


class DromasCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="드로마스입양", description="새 드로마스를 입양합니다. 사용자당 최대 5마리까지 가능합니다.")
    @app_commands.describe(이름="입양할 드로마스의 이름. 2~10자.")
    async def adopt(self, interaction: discord.Interaction, 이름: str) -> None:
        이름 = 이름.strip()
        error = validate_name(이름)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return

        data = store.load()
        user_data = store.get_user(data, interaction.user.id)
        if len(user_data["dromases"]) >= MAX_DROMAS_PER_USER:
            await interaction.response.send_message(
                f"삐빅... 더 이상 새 드로마스를 데려올 수 없어.\n지금은 최대 {MAX_DROMAS_PER_USER}마리까지만 돌볼 수 있어.",
                ephemeral=True,
            )
            return
        if store.find_dromas(user_data, 이름):
            await interaction.response.send_message("우우웅... 이미 같은 이름의 드로마스가 있어. 다른 이름을 붙여줘.", ephemeral=True)
            return

        dromas = store.create_dromas(이름)
        user_data["dromases"].append(dromas)
        store.save(data)

        embed = discord.Embed(
            title="새로운 드로마스 입양",
            description=(
                f"삐빅! 새로운 드로마스가 찾아왔어.\n\n"
                f"이름: **{이름}**\n\n"
                "작고 동그란 드로마스가 네 주위를 빙글빙글 돌고 있어.\n"
                "오늘부터 이 아이는 개척자와 함께할 거야.\n\n"
                "드로마스가 살짝 몸을 흔들었어.\n“우웅...”"
            ),
            color=EMBED_COLOR,
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="내드로마스", description="내가 돌보고 있는 드로마스 목록을 봅니다.")
    async def my_dromases(self, interaction: discord.Interaction) -> None:
        data = store.load()
        user_data = store.get_user(data, interaction.user.id)
        dromases = user_data.get("dromases", [])
        if not dromases:
            await interaction.response.send_message("우웅... 아직 함께하는 드로마스가 없어.\n먼저 /드로마스입양 으로 첫 드로마스를 데려와줘!", ephemeral=True)
            return

        lines = [f"{idx}. **{d['name']}** — Lv.{d.get('level', 1)}" for idx, d in enumerate(dromases, start=1)]
        embed = discord.Embed(
            title="내 드로마스 목록",
            description="삐빅! 개척자가 돌보고 있는 드로마스 목록이야.\n\n" + "\n".join(lines),
            color=EMBED_COLOR,
        )
        embed.set_footer(text="보고 싶은 드로마스가 있다면 /드로마스보기 를 사용해줘.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="드로마스보기", description="특정 드로마스의 상태를 확인합니다.")
    @app_commands.describe(이름="확인할 드로마스의 이름")
    async def view(self, interaction: discord.Interaction, 이름: str) -> None:
        data = store.load()
        user_data = store.get_user(data, interaction.user.id)
        dromas = store.find_dromas(user_data, 이름.strip())
        if not dromas:
            await interaction.response.send_message("우웅... 해당 이름의 드로마스를 찾지 못했어. 이름을 다시 확인해줘.", ephemeral=True)
            return
        await interaction.response.send_message(embed=profile_embed(dromas))

    async def _action_common(self, interaction: discord.Interaction, name: str, action: str) -> tuple[dict, dict, dict] | None:
        data = store.load()
        user_data = store.get_user(data, interaction.user.id)
        dromas = store.find_dromas(user_data, name.strip())
        if not dromas:
            await interaction.response.send_message("우웅... 해당 이름의 드로마스를 찾지 못했어. 이름을 다시 확인해줘.", ephemeral=True)
            return None

        store.ensure_daily(dromas)
        daily = dromas["daily"]
        now = unix_now()
        last_key = f"last_{action}"
        elapsed = now - int(daily.get(last_key, 0))
        cooldown = COOLDOWNS_SECONDS[action]
        if elapsed < cooldown:
            remain = cooldown - elapsed
            await interaction.response.send_message(f"우웅... 아직 조금 이른 것 같아. {remain}초 뒤에 다시 해줘.", ephemeral=True)
            return None
        if int(daily.get(action, 0)) >= DAILY_LIMITS[action]:
            labels = {"feed": "먹이주기", "play": "놀아주기", "explore": "탐사"}
            await interaction.response.send_message(f"삐빅... 오늘의 {labels[action]}는 여기까지야. 한국 시간 자정이 지나면 다시 할 수 있어.", ephemeral=True)
            return None
        return data, dromas, daily

    @app_commands.command(name="드로마스먹이주기", description="드로마스에게 먹이를 줍니다. 하루 5회, 쿨타임 1분.")
    @app_commands.describe(이름="먹이를 줄 드로마스의 이름")
    async def feed(self, interaction: discord.Interaction, 이름: str) -> None:
        result = await self._action_common(interaction, 이름, "feed")
        if result is None:
            return
        data, dromas, daily = result
        if int(dromas.get("satiety", 0)) >= 100:
            await interaction.response.send_message(f"우우웅... {dromas['name']}은 이미 배가 불러. 조금 있다가 다시 챙겨줘!", ephemeral=True)
            return

        satiety_gain = random.randint(15, 25)
        mood_gain = random.randint(3, 8)
        dromas["satiety"] = clamp(int(dromas.get("satiety", 0)) + satiety_gain)
        dromas["mood"] = clamp(int(dromas.get("mood", 0)) + mood_gain)
        daily["feed"] = int(daily.get("feed", 0)) + 1
        daily["last_feed"] = unix_now()
        store.save(data)

        await interaction.response.send_message(
            f"삐빅! **{dromas['name']}**에게 먹이를 줬어.\n\n"
            f"포만감이 **{satiety_gain}** 올랐어.\n"
            f"기분도 **{mood_gain}** 좋아진 것 같아.\n\n"
            "“우우웅...”"
        )

    @app_commands.command(name="드로마스놀아주기", description="드로마스와 놀아줍니다. 하루 10회, 쿨타임 1분.")
    @app_commands.describe(이름="놀아줄 드로마스의 이름")
    async def play(self, interaction: discord.Interaction, 이름: str) -> None:
        result = await self._action_common(interaction, 이름, "play")
        if result is None:
            return
        data, dromas, daily = result
        if int(dromas.get("mood", 0)) >= 100:
            await interaction.response.send_message(f"웅. {dromas['name']}은 이미 엄청 신나 보여. 그래도 옆에 있어주면 좋아할 거야.", ephemeral=True)
            return

        mood_gain = random.randint(8, 14)
        bond_gain = 1
        satiety_loss = random.randint(2, 5)
        dromas["mood"] = clamp(int(dromas.get("mood", 0)) + mood_gain)
        dromas["bond"] = int(dromas.get("bond", 0)) + bond_gain
        dromas["satiety"] = clamp(int(dromas.get("satiety", 0)) - satiety_loss)
        daily["play"] = int(daily.get("play", 0)) + 1
        daily["last_play"] = unix_now()
        store.save(data)

        await interaction.response.send_message(
            f"개척자, **{dromas['name']}**이랑 놀아줬어.\n\n"
            f"기분이 **{mood_gain}** 올랐어.\n"
            f"친밀도도 **{bond_gain}** 가까워졌어.\n\n"
            f"{dromas['name']}이 네 옆에 바짝 붙었어. 웅."
        )

    @app_commands.command(name="드로마스탐사", description="드로마스를 짧은 탐사에 보냅니다. 하루 3회, 쿨타임 2분.")
    @app_commands.describe(이름="탐사에 보낼 드로마스의 이름")
    async def explore(self, interaction: discord.Interaction, 이름: str) -> None:
        result = await self._action_common(interaction, 이름, "explore")
        if result is None:
            return
        data, dromas, daily = result
        if int(dromas.get("satiety", 0)) < 20:
            await interaction.response.send_message(f"우우웅... {dromas['name']}은 배가 고파서 탐사를 갈 수 없어. 먼저 먹이를 챙겨줘!", ephemeral=True)
            return
        if int(dromas.get("mood", 0)) < 20:
            await interaction.response.send_message(f"우웅... {dromas['name']}은 지금 기운이 없어 보여. 조금 놀아준 뒤 다시 보내자.", ephemeral=True)
            return

        exp_gain = random.randint(30, 55)
        leveled, old_level, new_level = add_exp(dromas, exp_gain)
        dromas["satiety"] = clamp(int(dromas.get("satiety", 0)) - random.randint(8, 14))
        dromas["mood"] = clamp(int(dromas.get("mood", 0)) - random.randint(4, 8))
        dromas["explore_count"] = int(dromas.get("explore_count", 0)) + 1
        daily["explore"] = int(daily.get("explore", 0)) + 1
        daily["last_explore"] = unix_now()
        store.save(data)

        line = random.choice(EXPLORE_RESULTS).format(name=dromas["name"])
        message = (
            f"삐빅! **{dromas['name']}**이 짧은 탐사를 다녀왔어.\n\n"
            f"획득 경험치: **{exp_gain}**\n"
            f"탐사 기록: **{dromas['explore_count']}회**\n\n"
            f"{line}"
        )
        if leveled:
            message += (
                f"\n\n삐빅삐빅! **{dromas['name']}**이 성장했어!\n"
                f"Lv.{old_level} → Lv.{new_level}\n"
                "몸집이 아주 조금 더 동그래진 것 같아."
            )
        await interaction.response.send_message(message)

    @app_commands.command(name="드로마스이름변경", description="드로마스의 이름을 변경합니다.")
    @app_commands.describe(기존이름="현재 이름", 새이름="새 이름. 2~10자.")
    async def rename(self, interaction: discord.Interaction, 기존이름: str, 새이름: str) -> None:
        새이름 = 새이름.strip()
        error = validate_name(새이름)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
            return

        data = store.load()
        user_data = store.get_user(data, interaction.user.id)
        target = store.find_dromas(user_data, 기존이름.strip())
        if not target:
            await interaction.response.send_message("우웅... 이름을 바꿀 수 없어. 해당 이름의 드로마스를 찾지 못했어.", ephemeral=True)
            return
        if store.find_dromas(user_data, 새이름):
            await interaction.response.send_message("우우웅... 이미 같은 이름의 드로마스가 있어. 다른 이름을 붙여줘.", ephemeral=True)
            return

        old = target["name"]
        target["name"] = 새이름
        store.save(data)
        await interaction.response.send_message(
            f"기록을 수정했어.\n\n이전 이름: **{old}**\n새 이름: **{새이름}**\n\n{새이름}도 마음에 드는 것 같아. 작게 “우웅...” 하고 울었어."
        )

    @app_commands.command(name="드로마스방생", description="확인 버튼을 거쳐 드로마스를 떠나보냅니다.")
    @app_commands.describe(이름="떠나보낼 드로마스의 이름")
    async def release(self, interaction: discord.Interaction, 이름: str) -> None:
        data = store.load()
        user_data = store.get_user(data, interaction.user.id)
        target = store.find_dromas(user_data, 이름.strip())
        if not target:
            await interaction.response.send_message("우웅... 해당 이름의 드로마스를 찾지 못했어. 이름을 다시 확인해줘.", ephemeral=True)
            return

        embed = discord.Embed(
            title="드로마스 방생 확인",
            description=(
                f"정말 **{이름}**을 떠나보낼 거야?\n\n"
                "이 선택은 되돌릴 수 없어.\n"
                "드로마스가 조용히 너를 바라보고 있어."
            ),
            color=ERROR_COLOR,
        )
        await interaction.response.send_message(embed=embed, view=ReleaseConfirmView(interaction.user.id, 이름.strip()), ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DromasCog(bot))
