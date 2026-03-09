import discord
from discord.ext import commands
from discord import app_commands
import os

class Agamotto(commands.Bot):
    def __init__(self):
        # Intents는 몽땅 켜놔야 입장 로그를 잡는다
        super().__init__(command_prefix="!", intents=discord.Intents.all())
        self.sessions = {} # 서버별 소환사 및 로그 채널 기억용

    async def setup_hook(self):
        await self.tree.sync()
        print("아가모토의 눈 가동 완료.")

bot = Agamotto()

@bot.tree.command(name="소환", description="아가모토의 눈을 현재 음성 채널에 소환한다.")
async def summon(interaction: discord.Interaction):
    # 음성 채널에 있는지 확인 (명령어 제한 효과)
    if not interaction.user.voice or not interaction.user.voice.channel:
        await interaction.response.send_message("야, 너부터 음성 채널에 들어가고 불러.", ephemeral=True)
        return

    target_vc = interaction.user.voice.channel
    guild_id = interaction.guild.id

    # 소환사 및 명령어를 친 텍스트 채널 저장
    bot.sessions[guild_id] = {
        'summoner_id': interaction.user.id,
        'log_channel': interaction.channel
    }

    bot_vc = interaction.guild.voice_client
    if bot_vc:
        await bot_vc.move_to(target_vc)
        await interaction.response.send_message(f"이미 소환돼 있어서 {target_vc.name}(으)로 이동했다.")
    else:
        await target_vc.connect()
        await interaction.response.send_message(f"아가모토의 눈, {target_vc.name} 채널에 소환 완료.")

@bot.tree.command(name="소환해제", description="아가모토의 눈을 돌려보낸다.")
async def unsummon(interaction: discord.Interaction):
    bot_vc = interaction.guild.voice_client
    if bot_vc:
        await bot_vc.disconnect()
        bot.sessions.pop(interaction.guild.id, None)
        await interaction.response.send_message("퇴근한다.")
    else:
        await interaction.response.send_message("소환된 적도 없는데 어딜 가라는 거냐?", ephemeral=True)

@bot.event
async def on_voice_state_update(member, before, after):
    if member.bot: return # 봇끼리는 무시

    guild_id = member.guild.id
    bot_vc = member.guild.voice_client

    if not bot_vc or guild_id not in bot.sessions:
        return

    session = bot.sessions[guild_id]
    summoner_id = session['summoner_id']
    log_channel = session['log_channel']

    # 1. 소환자가 나갔을 때 (음성 채널을 아예 떠났거나 다른 방으로 튀었을 때)
    if member.id == summoner_id:
        if not after.channel or after.channel.id != bot_vc.channel.id:
            await bot_vc.disconnect()
            bot.sessions.pop(guild_id, None)
            await log_channel.send(f"<@{summoner_id}> 소환자가 도망갔으므로 나도 퇴근한다.")
            return

    # 2. 누군가 봇이 있는 채널에 들어왔을 때 (입장 로그)
    if after.channel and after.channel.id == bot_vc.channel.id:
        if before.channel is None or before.channel.id != after.channel.id:
            await log_channel.send(f"[{member.display_name}] 입장.")

# 환경변수에서 토큰 가져와서 실행
bot.run(os.environ.get("DISCORD_TOKEN"))