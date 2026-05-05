import discord
from discord.ext import commands
import feedparser
import asyncio
import os
TOKEN = os.environ.get('DISCORD_TOKEN')
if not TOKEN:
    raise RuntimeError("缺少 DISCORD_TOKEN 環境變數")
YT_RSS_URL = os.environ.get('YT_RSS_URL', 'https://rss.app/feeds/2VOFkD9cN2lUEILD.xml')
X_RSS_URL = os.environ.get('X_RSS_URL', 'https://rss.app/feeds/LVhaUIOmUJPrRdhI.xml')
VIDEO_CHANNEL_ID = int(os.environ.get('VIDEO_CHANNEL_ID', '1501136787500830731'))
LIVE_CHANNEL_ID  = int(os.environ.get('LIVE_CHANNEL_ID',  '1501138912389894234'))
POST_CHANNEL_ID  = int(os.environ.get('POST_CHANNEL_ID',  '1501138866868981901'))
X_CHANNEL_ID     = int(os.environ.get('X_CHANNEL_ID',     '1501143513843241041'))
last_video = None
last_live  = None
last_post  = None
last_tweet = None
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)
@bot.event
async def on_ready():
    print(f'✅ {bot.user} 已成功上線！')
    bot.loop.create_task(background_check())
async def background_check():
    global last_video, last_live, last_post, last_tweet
    await bot.wait_until_ready()
    while True:
        try:
            feed = feedparser.parse(YT_RSS_URL)
            if feed.entries:
                latest = feed.entries[0]
                entry_id = latest.id
                title_lower = latest.title.lower()
                link = latest.link
                is_live = any(word in title_lower for word in ["直播", "live", "正在直播", "stream"])
                is_community = "community" in link.lower() or "post" in link.lower()
                if not is_live and not is_community and entry_id != last_video:
                    ch = bot.get_channel(VIDEO_CHANNEL_ID)
                    if ch:
                        embed = discord.Embed(title=latest.title, url=link, color=0xFF0000)
                        if 'media_thumbnail' in latest:
                            embed.set_thumbnail(url=latest.media_thumbnail[0]['url'])
                        await ch.send("🎥 **新影片上傳！** @everyone", embed=embed)
                        last_video = entry_id
                elif is_live and entry_id != last_live:
                    ch = bot.get_channel(LIVE_CHANNEL_ID)
                    if ch:
                        embed = discord.Embed(title=latest.title, url=link, color=0x00FF00)
                        if 'media_thumbnail' in latest:
                            embed.set_thumbnail(url=latest.media_thumbnail[0]['url'])
                        await ch.send("🔴 **直播開始了！** @everyone", embed=embed)
                        last_live = entry_id
                elif is_community and entry_id != last_post:
                    ch = bot.get_channel(POST_CHANNEL_ID)
                    if ch:
                        embed = discord.Embed(title=latest.title[:256], url=link, color=0x7289DA)
                        await ch.send("📢 **Community 新貼文！** @everyone", embed=embed)
                        last_post = entry_id
        except Exception as e:
            print(f"YouTube 檢查錯誤: {e}")
        try:
            x_feed = feedparser.parse(X_RSS_URL)
            if x_feed.entries:
                latest_tweet = x_feed.entries[0]
                tweet_id = latest_tweet.id
                if tweet_id != last_tweet:
                    ch = bot.get_channel(X_CHANNEL_ID)
                    if ch:
                        description = latest_tweet.title
                        if len(description) > 400:
                            description = description[:400] + "..."
                        embed = discord.Embed(
                            title="📝 新推文",
                            description=description,
                            url=latest_tweet.link,
                            color=0x1DA1F2
                        )
                        await ch.send("🐦 **X 新推文！**", embed=embed)
                        last_tweet = tweet_id
        except Exception as e:
            print(f"X 推文檢查錯誤: {e}")
        await asyncio.sleep(60)
@bot.command()
async def hello(ctx):
    await ctx.send(f'哈囉！{ctx.author.mention} 👋')
bot.run(TOKEN)