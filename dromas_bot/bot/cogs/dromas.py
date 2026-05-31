from __future__ import annotations

import random

import discord
from discord import app_commands
from discord.ext import commands

from bot.config import (
    MAX_DROMAS_NAME_LENGTH,
    MAX_DROMAS_PER_USER,
    MIN_DROMAS_NAME_LENGTH,
)
from bot.utils.game import required_exp
from bot.utils.storage import store
from bot.utils.time import unix_now

EMBED_COLOR = 0xA487FF
ERROR_COLOR = 0xE07070

ENHANCE_COOLDOWN_SECONDS = 60


def validate_name(name: str) -> str | None:
    name = name.strip()
    if len(name) < MIN_DROMAS_NAME_LENGTH or len(name) > MAX_DROMAS_NAME_LENGTH:
        return f"우웅... 이름은 {MIN_DROMAS_NAME_LENGTH}자 이상 {MAX_DROMAS_NAME_LENGTH}자 이하로 정해줘."
    return None


def enhance_rates(level: int) -> tuple[int, int, int]:
    if level < 80:
        flower_chance = 0
    elif level < 140:
        flower_chance = 1
    elif level < 200:
        flower_chance = 2
    else:
        flower_chance = 3

    fail_chance = min(8 + level // 5, 50)

    success_chance = 100 - fail_chance - flower_chance
    return success_chance, fail_chance, flower_chance


def random_success_gain(level: int) -> int:
    weights = []

    for gain in range(1, 11):
        weight = max(1, 35 - level // 4 - gain * 3)

        if level < 30:
            weight += max(0, 14 - gain)

        if level >= 100 and gain >= 7:
            weight = max(1, weight // 3)

        if level >= 160 and gain >= 8:
            weight = 1

        if level >= 200 and gain >= 6:
            weight = 1

        weights.append(weight)

    return random.choices(
        population=list(range(1, 11)),
        weights=weights,
        k=1,
    )[0]


def random_fail_loss(level: int) -> int:
    if level < 30:
        return random.randint(1, 2)

    if level < 80:
        return random.randint(2, 6)

    if level < 140:
        return random.randint(5, 15)

    if level < 200:
        return random.randint(10, 30)

    return random.randint(20, 50)


def profile_embed(dromas: dict) -> discord.Embed:
    level = int(dromas.get("level", 1))
    exp = int(dromas.get("exp", 0))
    req = required_exp(level)

    embed = discord.Embed(
        title=f"{dromas['name']}의 기록",
        description="삐빅. 드로마스 정보를 불러왔어.",
        color=EMBED_COLOR,
    )
    embed.add_field(name="레벨", value=f"Lv.{level}", inline=True)
    embed.add_field(name="경험치", value=f"{exp}/{req}", inline=True)
    embed.add_field(name="친밀도", value=str(dromas.get("bond", 0)), inline=True)
    embed.add_field(
        name="상태",
        value=f"{dromas['name']}은 조용히 네 곁에 머물고 있어.\n우웅...",
        inline=False,
    )
    return embed


class ReleaseConfirmView(discord.ui.View):
    def __init__(self, owner_id: int, dromas_name: str, timeout: float = 30) -> None:
        super().__init__(timeout=timeout)
        self.owner_id = owner_id
        self.dromas_name = dromas_name

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                "우웅... 이 버튼은 명령어를 사용한 개척자만 누를 수 있어.",
                ephemeral=True,
            )
            return False
        return True

    @discord.ui.button(label="떠나보내기", style=discord.ButtonStyle.danger)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        data = store.load()
        user_data = store.get_user(data, self.owner_id)
        dromases = user_data.get("dromases", [])
        target = store.find_dromas(user_data, self.dromas_name)

        if not target:
            await interaction.response.edit_message(
                content="우웅... 해당 이름의 드로마스를 찾지 못했어.",
                embed=None,
                view=None,
            )
            return

        user_data["dromases"] = [
            d for d in dromases
            if d.get("name") != self.dromas_name
        ]
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
        await interaction.response.edit_message(
            content="웅. 방생을 취소했어. 드로마스가 네 곁에 그대로 있어.",
            embed=None,
            view=None,
        )


class DromasCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(
        name="드로마스입양",
        description="새 드로마스를 입양합니다. 사용자당 최대 5마리까지 가능합니다.",
    )
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
            await interaction.response.send_message(
                "우우웅... 이미 같은 이름의 드로마스가 있어. 다른 이름을 붙여줘.",
                ephemeral=True,
            )
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
            await interaction.response.send_message(
                "우웅... 아직 함께하는 드로마스가 없어.\n먼저 /드로마스입양 으로 첫 드로마스를 데려와줘!",
                ephemeral=True,
            )
            return

        lines = [
            f"{idx}. **{d['name']}** — Lv.{d.get('level', 1)}"
            for idx, d in enumerate(dromases, start=1)
        ]

        embed = discord.Embed(
            title="내 드로마스 목록",
            description="삐빅! 개척자가 돌보고 있는 드로마스 목록이야.\n\n" + "\n".join(lines),
            color=EMBED_COLOR,
        )
        embed.set_footer(text="보고 싶은 드로마스가 있다면 /드로마스보기 를 사용해줘.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="드로마스순위", description="서버 전체 드로마스 레벨 순위를 봅니다.")
    async def ranking(self, interaction: discord.Interaction) -> None:
        data = store.load()
        users = data.get("users", {})

        ranking_list = []

        for user_id, user_data in users.items():
            for dromas in user_data.get("dromases", []):
                ranking_list.append({
                    "user_id": user_id,
                    "name": dromas.get("name", "이름 없는 드로마스"),
                    "level": int(dromas.get("level", 1)),
                })

        if not ranking_list:
            await interaction.response.send_message(
                "우웅... 아직 순위에 등록된 드로마스가 없어.",
                ephemeral=True,
            )
            return

        ranking_list.sort(key=lambda item: item["level"], reverse=True)

        top_list = ranking_list[:10]

        lines = []
        for idx, item in enumerate(top_list, start=1):
            lines.append(
                f"**{idx}위.** <@{item['user_id']}> — **{item['name']}** / Lv.{item['level']}"
            )

        embed = discord.Embed(
            title="드로마스 레벨 순위",
            description="\n".join(lines),
            color=EMBED_COLOR,
        )
        embed.set_footer(text="매주 월요일 기준으로 기록이 초기화됩니다.")

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="드로마스보기", description="특정 드로마스의 상태를 확인합니다.")
    @app_commands.describe(이름="확인할 드로마스의 이름")
    async def view(self, interaction: discord.Interaction, 이름: str) -> None:
        data = store.load()
        user_data = store.get_user(data, interaction.user.id)
        dromas = store.find_dromas(user_data, 이름.strip())

        if not dromas:
            await interaction.response.send_message(
                "우웅... 해당 이름의 드로마스를 찾지 못했어. 이름을 다시 확인해줘.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(embed=profile_embed(dromas))

    @app_commands.command(
        name="드로마스강화",
        description="드로마스를 강화합니다. 성공하면 레벨 상승, 실패하면 하락하거나 꽃바다로 갈 수 있습니다.",
    )
    @app_commands.describe(이름="강화할 드로마스의 이름")
    async def enhance(self, interaction: discord.Interaction, 이름: str) -> None:
        data = store.load()
        user_data = store.get_user(data, interaction.user.id)
        dromas = store.find_dromas(user_data, 이름.strip())

        if not dromas:
            await interaction.response.send_message(
                "우웅... 해당 이름의 드로마스를 찾지 못했어. 이름을 다시 확인해줘.",
                ephemeral=True,
            )
            return

        store.ensure_daily(dromas)
        daily = dromas["daily"]

        now = unix_now()
        elapsed = now - int(daily.get("last_enhance", 0))

        if elapsed < ENHANCE_COOLDOWN_SECONDS:
            remain = ENHANCE_COOLDOWN_SECONDS - elapsed
            await interaction.response.send_message(
                f"우웅... 강화 장치가 아직 식지 않았어.\n**{remain}초** 뒤에 다시 시도해줘.",
                ephemeral=True,
            )
            return

        level = int(dromas.get("level", 1))
        success_chance, fail_chance, flower_chance = enhance_rates(level)

        roll = random.randint(1, 100)
        daily["last_enhance"] = now

        if roll <= flower_chance:
            name = dromas["name"]

            user_data["dromases"] = [
                item for item in user_data.get("dromases", [])
                if item.get("name") != name
            ]
            store.save(data)

            embed = discord.Embed(
                title="꽃바다",
                description=(
                    f"강화 장치가 조용히 멈췄어.\n\n"
                    f"**{name}**은 잠시 너를 올려다보다가,\n"
                    "저승의 꽃바다 너머로 천천히 사라졌어.\n\n"
                    "기록 장치에 남은 것은 아주 희미한 울음소리뿐이야.\n\n"
                    "“우웅...”"
                ),
                color=ERROR_COLOR,
            )
            embed.set_footer(
                text=f"성공 {success_chance}% / 실패 {fail_chance}% / 꽃바다 {flower_chance}%"
            )
            await interaction.response.send_message(embed=embed)
            return

        if roll <= flower_chance + fail_chance:
            old_level = level
            loss = random_fail_loss(level)
            new_level = max(1, level - loss)

            dromas["level"] = new_level
            dromas["exp"] = 0
            store.save(data)

            embed = discord.Embed(
                title="강화 실패",
                description=(
                    f"우우웅... **{dromas['name']}**의 강화가 실패했어.\n\n"
                    f"Lv.{old_level} → Lv.{new_level}\n"
                    f"하락 폭: **-{old_level - new_level}**\n\n"
                    "드로마스가 살짝 흔들렸지만, 아직 네 곁에 있어."
                ),
                color=ERROR_COLOR,
            )
            embed.set_footer(
                text=f"성공 {success_chance}% / 실패 {fail_chance}% / 꽃바다 {flower_chance}%"
            )
            await interaction.response.send_message(embed=embed)
            return

        old_level = level
        gain = random_success_gain(level)
        new_level = level + gain

        dromas["level"] = new_level
        dromas["exp"] = 0
        store.save(data)

        embed = discord.Embed(
            title="강화 성공",
            description=(
                f"삐빅삐빅! **{dromas['name']}**의 강화가 성공했어!\n\n"
                f"Lv.{old_level} → Lv.{new_level}\n"
                f"상승 폭: **+{gain}**\n\n"
                "몸집이 아주 조금 더 동그래지고, 기록 장치가 반짝였어.\n"
                "“우웅!”"
            ),
            color=EMBED_COLOR,
        )
        embed.set_footer(
            text=f"성공 {success_chance}% / 실패 {fail_chance}% / 꽃바다 {flower_chance}%"
        )
        await interaction.response.send_message(embed=embed)

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
            await interaction.response.send_message(
                "우웅... 이름을 바꿀 수 없어. 해당 이름의 드로마스를 찾지 못했어.",
                ephemeral=True,
            )
            return

        if store.find_dromas(user_data, 새이름):
            await interaction.response.send_message(
                "우우웅... 이미 같은 이름의 드로마스가 있어. 다른 이름을 붙여줘.",
                ephemeral=True,
            )
            return

        old = target["name"]
        target["name"] = 새이름
        store.save(data)

        await interaction.response.send_message(
            f"기록을 수정했어.\n\n"
            f"이전 이름: **{old}**\n"
            f"새 이름: **{새이름}**\n\n"
            f"{새이름}도 마음에 드는 것 같아. 작게 “우웅...” 하고 울었어."
        )

    @app_commands.command(name="드로마스방생", description="확인 버튼을 거쳐 드로마스를 떠나보냅니다.")
    @app_commands.describe(이름="떠나보낼 드로마스의 이름")
    async def release(self, interaction: discord.Interaction, 이름: str) -> None:
        data = store.load()
        user_data = store.get_user(data, interaction.user.id)
        target = store.find_dromas(user_data, 이름.strip())

        if not target:
            await interaction.response.send_message(
                "우웅... 해당 이름의 드로마스를 찾지 못했어. 이름을 다시 확인해줘.",
                ephemeral=True,
            )
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
        await interaction.response.send_message(
            embed=embed,
            view=ReleaseConfirmView(interaction.user.id, 이름.strip()),
            ephemeral=True,
        )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DromasCog(bot))
