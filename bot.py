import discord
import os

intents = discord.Intents.default()
intents.message_content = True

bot = discord.Client(intents=intents)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} 已成功上線！（診斷模式）')
    print('現在請在 Discord 輸入 !hello 測試')

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.content.lower() == '!hello':
        await message.channel.send(f'哈囉！{message.author.mention} 👋 測試成功！')

bot.run(os.environ.get('DISCORD_TOKEN'))
