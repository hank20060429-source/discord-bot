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
    raise RuntimeError("缺少 DISCORD_TOKEN 環境變數")

YT_RSS_URL = os.environ.get('YT_RSS_URL', 'https://rss.app/feeds/2VOFkD9cN2lUEILD.xml')
X_RSS_URL = os.environ.get('X_RSS_URL', 'https://rss.app/feeds/LVhaUIOmUJPrRdhI.xml')

VIDEO_CHANNEL_ID = int(os.environ.get('VIDEO_CHANNEL_ID', '1501136787500830731'))
LIVE_CHANNEL_ID  = int(os.environ.get('LIVE_CHANNEL_ID',  '1501138912389894234'))
POST_CHANNEL_ID  = int(os.environ.get('POST_CHANNEL_ID',  '1501138866868981901'))
X_CHANNEL_ID     = int(os.environ.get('X_CHANNEL_ID',     '1501143513843241041'))

last_video = last_live = last_post = last_tweet = None

# ====================== YouTube 關鍵字分類 ======================
CLASSIFICATION_RULES = {
    "影片上傳": {
        "keywords": ["【Hololive中文翻譯】", "【MD精華剪輯】", "【VTuber中文翻譯】", "【VTuber直播精華】"],
        "channel_id": VIDEO_CHANNEL_ID,
        "emoji": "🎥",
        "prefix": "@everyone 新影片上傳了！"
    },
    "直播": {
        "keywords": ["直播", "live", "正在直播", "開播", "實況", "stream"],
        "channel_id": LIVE_CHANNEL_ID,
        "emoji": "🔴",
        "prefix": "@everyone 直播開始了！"
    },
    "Shorts": {
        "keywords": ["shorts", "短片", "short"],
        "channel_id": VIDEO_CHANNEL_ID,
        "emoji": "📱",
        "prefix": "@everyone 新 Shorts！"
    }
}

# ====================== Pixiv 設定 ======================
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
            print("✅ Pixiv API 初始化成功")
    except Exception as e:
        print(f"⚠️ Pixiv 初始化失敗: {e}")

    # 同步斜線指令
    try:
        await bot.tree.sync()
        print("✅ /pixiv 斜線指令已同步")
    except Exception as e:
        print(f"斜線指令同步失敗: {e}")

# ====================== YouTube 背景檢查 ======================
async def background_check():
    global last_video, last_live, last_post, last_tweet
    await bot.wait_until_ready()
    
    while True:
        # YouTube 部分（你的原本程式碼）
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
                        print(f"[{rule_name}] 偵測到：{title}")
                        break

                if (target["channel_id"] == LIVE_CHANNEL_ID and entry_id == last_live) or \
                   (target["channel_id"] == VIDEO_CHANNEL_ID and entry_id == last_video):
                    pass
                else:
                    ch = bot.get_channel(target["channel_id"])
                    if ch:
                        embed = discord.Embed(title=title, url=link, color=0xFF0000)
                        await ch.send(f"{target['emoji']} **{target['prefix']}**", embed=embed)
                        
                        if target["channel_id"] == LIVE_CHANNEL_ID:
                            last_live = entry_id
                        else:
                            last_video = entry_id
        except Exception as e:
            print(f"YouTube 錯誤: {e}")

        # X 推文部分
        try:
            x_feed = feedparser.parse(X_RSS_URL)
            if x_feed.entries and x_feed.entries[0].id != last_tweet:
                tweet = x_feed.entries[0]
                ch = bot.get_channel(X_CHANNEL_ID)
                if ch:
                    desc = tweet.title[:400] + "..." if len(tweet.title) > 400 else tweet.title
                    embed = discord.Embed(title="📝 新推文", description=desc, url=tweet.link, color=0x1DA1F2)
                    await ch.send("🐦 **@everyone X新推文！**", embed=embed)
                    last_tweet = tweet.id
        except:
            pass

        await asyncio.sleep(60)

# ====================== /pixiv 指令 ======================
@bot.tree.command(name="pixiv", description="從 Pixiv 隨機抽圖（支援多標籤）")
@app_commands.describe(tags="標籤，可輸入多個 #tag")
async def pixiv(interaction: discord.Interaction, tags: str = None):
    ALLOWED_CHANNELS = [1501131000368074873]   # ← 修改成你想要的頻道ID

    if interaction.channel_id not in ALLOWED_CHANNELS:
        await interaction.response.send_message("❌ 此指令只能在指定頻道使用！", ephemeral=True)
        return

    await interaction.response.defer()

    try:
        if tags:
            tag_list = [t.strip('# ') for t in tags.split() if t.startswith('#')]
            keyword = " ".join(tag_list)
            result = pixiv_api.search_illust(keyword, search_target='partial_match_for_tags')
        else:
            result = pixiv_api.illust_ranking(mode='day')

        candidates = [i for i in result.get('illusts', []) if i.get('total_bookmarks', 0) >= 100]

        if not candidates:
            await interaction.followup.send("❌ 找不到按讚100以上的圖片，請換個標籤！")
            return

        illust = random.choice(candidates)
        image_url = illust['image_urls'].get('large') or illust['image_urls']['medium']
        page_url = f"https://www.pixiv.net/artworks/{illust['id']}"

        embed = discord.Embed(
            title=illust['title'],
            url=page_url,
            description=f"❤️ 按讚 {illust.get('total_bookmarks', 0)}　👤 {illust['user']['name']}",
            color=0xFF69B4
        )
        embed.set_image(url=image_url)
        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send("❌ Pixiv 連線失敗，請稍後再試")
        print(f"Pixiv 錯誤: {e}")

# ====================== 基本測試指令 ======================
@bot.command()
async def hello(ctx):
    await ctx.send(f'哈囉！{ctx.author.mention} 👋')

# ====================== 啟動 ======================
bot.loop.create_task(background_check())
bot.run(TOKEN)
