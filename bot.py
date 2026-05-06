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
    raise RuntimeError("❌ 缺少 DISCORD_TOKEN 環境變數！")

YT_RSS_URL = os.environ.get('YT_RSS_URL', 'https://rss.app/feeds/2VOFkD9cN2lUEILD.xml')
X_RSS_URL = os.environ.get('X_RSS_URL', 'https://rss.app/feeds/LVhaUIOmUJPrRdhI.xml')

VIDEO_CHANNEL_ID = int(os.environ.get('VIDEO_CHANNEL_ID', '1501136787500830731'))
LIVE_CHANNEL_ID  = int(os.environ.get('LIVE_CHANNEL_ID',  '1501138912389894234'))
POST_CHANNEL_ID  = int(os.environ.get('POST_CHANNEL_ID',  '1501138866868981901'))
X_CHANNEL_ID     = int(os.environ.get('X_CHANNEL_ID',     '1501143513843241041'))

last_video = last_live = last_post = last_tweet = None

# ====================== YouTube 關鍵字分類 ======================
CLASSIFICATION_RULES = {
    "影片上傳": {"keywords": ["【Hololive中文翻譯】", "【MD精華剪輯】", "【VTuber中文翻譯】", "【VTuber直播精華】"], "channel_id": VIDEO_CHANNEL_ID, "emoji": "🎥", "prefix": "@everyone 新影片上傳了！"},
    "直播": {"keywords": ["直播", "live", "正在直播", "開播", "實況", "stream"], "channel_id": LIVE_CHANNEL_ID, "emoji": "🔴", "prefix": "@everyone 直播開始了！"},
    "Shorts": {"keywords": ["shorts", "短片", "short"], "channel_id": VIDEO_CHANNEL_ID, "emoji": "📱", "prefix": "@everyone 新 Shorts！"}
}
# ====================== YouTube & X 背景任務 ======================
async def background_check():
    global last_video, last_live, last_post, last_tweet
    await bot.wait_until_ready()
    while True:
        # YouTube
        try:
            feed = feedparser.parse(YT_RSS_URL)
            if feed.entries:
                latest = feed.entries[0]
                entry_id = latest.id
                title = latest.title
                link = latest.link
                title_lower = title.lower()

                target = {"channel_id": VIDEO_CHANNEL_ID, "emoji": "🎥", "prefix": "新影片上傳！"}
                for rule_name, rule in CLASSIFICATION_RULES.items():
                    if any(kw.lower() in title_lower for kw in rule["keywords"]):
                        target = rule
                        break

                ch = bot.get_channel(target["channel_id"])
                if ch and entry_id != last_video:
                    embed = discord.Embed(title=title, url=link, color=0xFF0000)
                    await ch.send(f"{target['emoji']} **{target['prefix']}**", embed=embed)
                    last_video = entry_id
        except:
            pass

        # X 推文
        try:
            x_feed = feedparser.parse(X_RSS_URL)
            if x_feed.entries and x_feed.entries[0].id != last_tweet:
                tweet = x_feed.entries[0]
                ch = bot.get_channel(X_CHANNEL_ID)
                if ch:
                    embed = discord.Embed(title="📝 新推文", description=tweet.title[:400], url=tweet.link, color=0x1DA1F2)
                    await ch.send("🐦 **@everyone X新推文！**", embed=embed)
                    last_tweet = tweet.id
        except:
            pass

        await asyncio.sleep(60)
# ====================== 基本指令 ======================
@bot.command()
async def hello(ctx):
    await ctx.send(f'哈囉！{ctx.author.mention} 👋')

# ====================== 啟動 ======================
bot.loop.create_task(background_check())
bot.run(TOKEN)
