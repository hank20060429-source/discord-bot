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
last_video = last_live = last_post = last_tweet = None
# ===================================================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# ==================== 關鍵字分類設定 ====================
# 你可以在這裡自由新增或修改關鍵字（不分大小寫）
CLASSIFICATION_RULES = {
    "影片上傳": {
        "keywords": ["【Hololive中文翻譯】", "【MD精華剪輯】", "【VTuber中文翻譯】", "【VTuber直播精華】"],
        "channel_id": VIDEO_CHANNEL_ID,
        "emoji": "🎥",
        "prefix": "@everyone新影片上傳了！"
    },
    "直播": {
        "keywords": ["直播", "live", "正在直播", "開播", "實況", "stream"],
        "channel_id": LIVE_CHANNEL_ID,
        "emoji": "🔴",
        "prefix": "@everyone直播開始了！"
    },
    "Shorts": {
        "keywords": ["shorts", "短片", "short"],
        "channel_id": VIDEO_CHANNEL_ID,   # 你可以改成另外一個 Shorts 頻道
        "emoji": "📱",
        "prefix": "@everyone新 Shorts！"
    }
}
# ===================================================

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

                # 預設是一般影片
                target = {
                    "channel_id": VIDEO_CHANNEL_ID,
                    "emoji": "🎥",
                    "prefix": "新影片上傳！"
                }

                # 檢查是否符合任一分類規則
                for rule_name, rule in CLASSIFICATION_RULES.items():
                    if any(kw.lower() in title_lower for kw in rule["keywords"]):
                        target = rule
                        print(f"[{rule_name}] 偵測到：{title}")
                        break

                # 避免重複發送
                if (target["channel_id"] == LIVE_CHANNEL_ID and entry_id == last_live) or \
                   (target["channel_id"] == POST_CHANNEL_ID and entry_id == last_post) or \
                   (target["channel_id"] == VIDEO_CHANNEL_ID and entry_id == last_video):
                    pass
                else:
                    ch = bot.get_channel(target["channel_id"])
                    if ch:
                        embed = discord.Embed(title=title, url=link, color=0xFF0000)
                        await ch.send(f"{target['emoji']} **{target['prefix']}** @everyone", embed=embed)
                        
                        # 更新最後發送紀錄
                        if target["channel_id"] == LIVE_CHANNEL_ID:
                            last_live = entry_id
                        elif target["channel_id"] == POST_CHANNEL_ID:
                            last_post = entry_id
                        else:
                            last_video = entry_id

        except Exception as e:
            print(f"YouTube 檢查錯誤: {e}")

        # X 推文部分保持不變...
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
# ====================== Pixiv 斜線指令 ======================
from pixivpy import AppPixivAPI
import random
import os
import discord
from discord import app_commands
# 初始化 Pixiv API
pixiv_api = None
@bot.event
async def on_ready():
    global pixiv_api
    print(f'✅ {bot.user} 已上線')
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
        print("✅ 斜線指令已同步")
    except Exception as e:
        print(f"斜線指令同步失敗: {e}")
# ====================== Pixiv 多標籤斜線指令 ======================
from pixivpy import AppPixivAPI
import random
import os
pixiv_api = None
@bot.event
async def on_ready():
    global pixiv_api
    print(f'✅ {bot.user} 已上線')
    try:
        pixiv_api = AppPixivAPI()
        sessid = os.environ.get("PIXIV_PHPSESSID")
        if sessid:
            pixiv_api.requests.headers.update({'Cookie': f'PHPSESSID={sessid}'})
            print("✅ Pixiv API 初始化成功")
    except Exception as e:
        print(f"Pixiv 初始化失敗: {e}")
    try:
        await bot.tree.sync()
    except:
        pass
@bot.tree.command(name="pixiv", description="從 Pixiv 隨機抽一張按讚100以上的圖片（支援多標籤）")
@app_commands.describe(tags="搜尋標籤，可輸入多個 #tag（例如 #原神 #女の子）")
async def pixiv(interaction: discord.Interaction, tags: str = None):
    
    # 頻道限制
    ALLOWED_CHANNELS = [1501131000368074873]   # ← 改成你允許的頻道ID
    if interaction.channel_id not in ALLOWED_CHANNELS:
        await interaction.response.send_message("❌ 此指令只能在指定頻道使用！", ephemeral=True)
        return

    await interaction.response.defer()

    try:
        # 解析多個 #tag
        search_tags = []
        if tags:
            search_tags = [t.strip('# ') for t in tags.split() if t.startswith('#')]

        if search_tags:
            # 多標籤搜尋（Pixiv 會自動 AND 處理）
            keyword = " ".join(search_tags)
            result = pixiv_api.search_illust(keyword, search_target='partial_match_for_tags')
        else:
            result = pixiv_api.illust_ranking(mode='day')  # 無標籤 = 每日排行

        # 篩選按讚 ≥ 100
        candidates = [illust for illust in result.get('illusts', []) if illust.get('total_bookmarks', 0) >= 100]

        if not candidates:
            await interaction.followup.send("❌ 找不到符合條件的圖片，請換個標籤試試！")
            return

        illust = random.choice(candidates)
        image_url = illust['image_urls'].get('large') or illust['image_urls']['medium']
        page_url = f"https://www.pixiv.net/artworks/{illust['id']}"

        embed = discord.Embed(
            title=illust['title'],
            url=page_url,
            description=f"❤️ 按讚數：**{illust.get('total_bookmarks', 0)}**　👤 {illust['user']['name']}",
            color=0xFF69B4
        )
        embed.set_image(url=image_url)
        
        tag_text = " ".join([f"#{t}" for t in search_tags]) if search_tags else "隨機熱門"
        embed.set_footer(text=f"搜尋標籤：{tag_text}")

        await interaction.followup.send(embed=embed)

    except Exception as e:
        await interaction.followup.send("❌ Pixiv 連線失敗，請稍後再試！")
        print(f"Pixiv 錯誤: {e}")
@bot.command()
async def hello(ctx):
    await ctx.send(f'哈囉！{ctx.author.mention} 👋')
bot.run(TOKEN)
