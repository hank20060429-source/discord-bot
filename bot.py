import discord
from discord.ext import commands
from discord import app_commands
import feedparser
import asyncio
import os
import random
from pixivpy import AppPixivAPI

# ====================== 環境變數 ======================
TOKEN = os.environ.get('DISCORD_TOKEN')
if not TOKEN:
    raise RuntimeError("❌ 缺少 DISCORD_TOKEN")

YT_RSS_URL = os.environ.get('YT_RSS_URL', 'https://rss.app/feeds/2VOFkD9cN2lUEILD.xml')
X_RSS_URL = os.environ.get('X_RSS_URL', 'https://rss.app/feeds/LVhaUIOmUJPrRdhI.xml')

VIDEO_CHANNEL_ID = int(os.environ.get('VIDEO_CHANNEL_ID', '1501136787500830731'))
LIVE_CHANNEL_ID  = int(os.environ.get('LIVE_CHANNEL_ID',  '1501138912389894234'))
POST_CHANNEL_ID  = int(os.environ.get('POST_CHANNEL_ID',  '1501138866868981901'))
X_CHANNEL_ID     = int(os.environ.get('X_CHANNEL_ID',     '1501143513843241041'))

# ====================== Pixiv ======================
pixiv_api = None

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    global pixiv_api
    print(f'✅ {bot.user} 已成功上線！')

    # Pixiv 初始化
    try:
        pixiv_api = AppPixivAPI()
        sessid = os.environ.get("PIXIV_PHPSESSID")
        if sessid:
            pixiv_api.requests.headers.update({'Cookie': f'PHPSESSID={sessid}'})
            print("✅ Pixiv 初始化成功")
    except Exception as e:
        print(f"Pixiv 初始化失敗: {e}")

    try:
        await bot.tree.sync()
        print("✅ /pixiv 已同步")
    except:
        pass

# ====================== 基本指令 ======================
@bot.command()
async def hello(ctx):
    await ctx.send(f'哈囉！{ctx.author.mention} 👋')

# ====================== /pixiv ======================
@bot.tree.command(name="pixiv", description="從 Pixiv 隨機抽圖")
@app_commands.describe(tags="可輸入多個 #tag")
async def pixiv(interaction: discord.Interaction, tags: str = None):
    ALLOWED_CHANNELS = [1501131000368074873]   # ← 改成你的頻道ID

    if interaction.channel_id not in ALLOWED_CHANNELS:
        await interaction.response.send_message("❌ 此指令只能在指定頻道使用！", ephemeral=True)
        return

    await interaction.response.send_message("🔍 **正在從 Pixiv 找圖片...** 請稍等～")

    try:
        if tags:
            tag_list = [t.strip('# ') for t in tags.split() if t.startswith('#')]
            keyword = " ".join(tag_list)
            result = pixiv_api.search_illust(keyword)
        else:
            result = pixiv_api.illust_ranking(mode='day')

        candidates = [i for i in result.get('illusts', []) if i.get('total_bookmarks', 0) >= 100]

        if not candidates:
            await interaction.edit_original_response(content="❌ 找不到符合的圖片")
            return

        illust = random.choice(candidates)
        image_url = illust['image_urls'].get('large') or illust['image_urls']['medium']

        embed = discord.Embed(
            title=illust['title'],
            url=f"https://www.pixiv.net/artworks/{illust['id']}",
            description=f"❤️ 按讚 {illust.get('total_bookmarks', 0)}　👤 {illust['user']['name']}",
            color=0xFF69B4
        )
        embed.set_image(url=image_url)

        await interaction.edit_original_response(content=None, embed=embed)

    except Exception as e:
        await interaction.edit_original_response(content="❌ Pixiv 連線失敗")
        print(f"Pixiv 錯誤: {e}")

# ====================== 背景任務（YouTube + X） ======================
async def background_check():
    await bot.wait_until_ready()
    while True:
        # YouTube 簡化版
        try:
            feed = feedparser.parse(YT_RSS_URL)
            if feed.entries:
                latest = feed.entries[0]
                ch = bot.get_channel(VIDEO_CHANNEL_ID)
                if ch:
                    embed = discord.Embed(title=latest.title, url=latest.link, color=0xFF0000)
                    await ch.send("🎥 **新影片上傳！** @everyone", embed=embed)
        except:
            pass

        # X 推文
        try:
            x_feed = feedparser.parse(X_RSS_URL)
            if x_feed.entries:
                tweet = x_feed.entries[0]
                ch = bot.get_channel(X_CHANNEL_ID)
                if ch:
                    embed = discord.Embed(title="📝 新推文", description=tweet.title[:400], url=tweet.link, color=0x1DA1F2)
                    await ch.send("🐦 **@everyone X新推文！**", embed=embed)
        except:
            pass

        await asyncio.sleep(60)

# ====================== 啟動 ======================
bot.loop.create_task(background_check())
bot.run(TOKEN)
