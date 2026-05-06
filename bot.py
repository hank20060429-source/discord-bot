import discord
from discord.ext import commands
import feedparser
import asyncio
import os

# ====================== 環境變數 ======================
TOKEN = os.environ.get('DISCORD_TOKEN')
if not TOKEN:
    raise RuntimeError("❌ 缺少 DISCORD_TOKEN 環境變數！請在 Railway Variables 設定")

YT_RSS_URL = os.environ.get('YT_RSS_URL', 'https://rss.app/feeds/2VOFkD9cN2lUEILD.xml')
X_RSS_URL = os.environ.get('X_RSS_URL', 'https://rss.app/feeds/LVhaUIOmUJPrRdhI.xml')

VIDEO_CHANNEL_ID = int(os.environ.get('VIDEO_CHANNEL_ID', '1501136787500830731'))
LIVE_CHANNEL_ID  = int(os.environ.get('LIVE_CHANNEL_ID',  '1501138912389894234'))
POST_CHANNEL_ID  = int(os.environ.get('POST_CHANNEL_ID',  '1501138866868981901'))
X_CHANNEL_ID     = int(os.environ.get('X_CHANNEL_ID',     '1501143513843241041'))

last_video = last_live = last_post = last_tweet = None

# ==================== 關鍵字分類設定 ====================
CLASSIFICATION_RULES = {
    "直播": {
        "keywords": ["直播", "live", "正在直播", "開播", "實況", "stream"],
        "channel_id": LIVE_CHANNEL_ID,
        "emoji": "🔴",
        "prefix": "直播開始了！"
    },
    "社群貼文": {
        "keywords": ["community", "post", "社群", "貼文", "問卷", "投票"],
        "channel_id": POST_CHANNEL_ID,
        "emoji": "📢",
        "prefix": "社群新貼文！"
    },
    "Shorts": {
        "keywords": ["shorts", "短片", "short"],
        "channel_id": VIDEO_CHANNEL_ID,
        "emoji": "📱",
        "prefix": "新 Shorts！"
    }
}
# ===================================================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} 已上線！關鍵字分類系統運作中...')
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
                title = latest.title
                link = latest.link
                title_lower = title.lower()

                # 預設為一般影片
                target = {
                    "channel_id": VIDEO_CHANNEL_ID,
                    "emoji": "🎥",
                    "prefix": "新影片上傳！"
                }

                # 檢查關鍵字
                for rule_name, rule in CLASSIFICATION_RULES.items():
                    if any(kw.lower() in title_lower for kw in rule["keywords"]):
                        target = rule
                        print(f"[{rule_name}] 偵測到：{title}")
                        break

                # 發送通知（避免重複）
                if (target["channel_id"] == VIDEO_CHANNEL_ID and entry_id == last_video) or \
                   (target["channel_id"] == LIVE_CHANNEL_ID and entry_id == last_live) or \
                   (target["channel_id"] == POST_CHANNEL_ID and entry_id == last_post):
                    pass
                else:
                    ch = bot.get_channel(target["channel_id"])
                    if ch:
                        embed = discord.Embed(title=title, url=link, color=0xFF0000)
                        await ch.send(f"{target['emoji']} **{target['prefix']}** @everyone", embed=embed)
                        
                        if target["channel_id"] == VIDEO_CHANNEL_ID:
                            last_video = entry_id
                        elif target["channel_id"] == LIVE_CHANNEL_ID:
                            last_live = entry_id
                        else:
                            last_post = entry_id

        except Exception as e:
            print(f"YouTube 檢查錯誤: {e}")

        # X 推文
        try:
            x_feed = feedparser.parse(X_RSS_URL)
            if x_feed.entries and x_feed.entries[0].id != last_tweet:
                tweet = x_feed.entries[0]
                ch = bot.get_channel(X_CHANNEL_ID)
                if ch:
                    desc = tweet.title[:400] + "..." if len(tweet.title) > 400 else tweet.title
                    embed = discord.Embed(title="📝 新推文", description=desc, url=tweet.link, color=0x1DA1F2)
                    await ch.send("🐦 **X 新推文！**", embed=embed)
                    last_tweet = tweet.id
        except Exception as e:
            print(f"X 錯誤: {e}")

        await asyncio.sleep(60)

bot.run(TOKEN)
