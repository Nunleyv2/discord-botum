import discord
from discord.ext import commands
import asyncio
import random
import os
import yt_dlp
import anthropic

# ─────────────────────────────────────────
#  Yapılandırma
# ─────────────────────────────────────────
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN", "ODgxODk3MDc5NjY3MDQ0Mzky.GV9J6i.6NeMgCdeQbjnwfY315RoetufbCcvUZ_MkWVC7I")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "ANTHROPIC_KEY_BURAYA")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents)
claude_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# ─────────────────────────────────────────
#  Müzik — kuyruk sistemi
# ─────────────────────────────────────────
music_queues: dict[int, list] = {}   # guild_id -> [url, ...]
voice_clients: dict[int, discord.VoiceClient] = {}

YDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "default_search": "ytsearch",
}
FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


async def play_next(ctx: commands.Context):
    guild_id = ctx.guild.id
    queue = music_queues.get(guild_id, [])
    if not queue:
        await ctx.send("🎵 Kuyruk bitti, iyi dinlemeler!")
        return
    url = queue.pop(0)
    with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
        info = ydl.extract_info(url, download=False)
        if "entries" in info:
            info = info["entries"][0]
        stream_url = info["url"]
        title = info.get("title", "Bilinmeyen")
    vc = voice_clients[guild_id]
    source = discord.FFmpegPCMAudio(stream_url, **FFMPEG_OPTIONS)
    vc.play(source, after=lambda _: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop))
    await ctx.send(f"▶️ Şimdi çalıyor: **{title}**")


@bot.command(name="çal", aliases=["play", "p"])
async def play(ctx: commands.Context, *, query: str):
    """Müzik çal (YouTube arama veya URL)."""
    if not ctx.author.voice:
        return await ctx.send("❌ Önce bir ses kanalına gir!")
    guild_id = ctx.guild.id

    # Kanala bağlan
    if guild_id not in voice_clients or not voice_clients[guild_id].is_connected():
        vc = await ctx.author.voice.channel.connect()
        voice_clients[guild_id] = vc
    else:
        vc = voice_clients[guild_id]

    music_queues.setdefault(guild_id, [])
    music_queues[guild_id].append(query)
    await ctx.send(f"🎶 Kuyruğa eklendi: **{query}**")

    if not vc.is_playing():
        await play_next(ctx)


@bot.command(name="dur", aliases=["stop"])
async def stop(ctx: commands.Context):
    """Çalmayı durdur ve kanaldan çık."""
    guild_id = ctx.guild.id
    music_queues[guild_id] = []
    if guild_id in voice_clients and voice_clients[guild_id].is_connected():
        await voice_clients[guild_id].disconnect()
        del voice_clients[guild_id]
    await ctx.send("⏹️ Müzik durduruldu.")


@bot.command(name="atla", aliases=["skip"])
async def skip(ctx: commands.Context):
    """Mevcut şarkıyı atla."""
    guild_id = ctx.guild.id
    vc = voice_clients.get(guild_id)
    if vc and vc.is_playing():
        vc.stop()
        await ctx.send("⏭️ Atlandı!")
    else:
        await ctx.send("❌ Şu an çalan bir şarkı yok.")


@bot.command(name="kuyruk", aliases=["queue", "q"])
async def queue(ctx: commands.Context):
    """Müzik kuyruğunu göster."""
    q = music_queues.get(ctx.guild.id, [])
    if not q:
        return await ctx.send("📭 Kuyruk boş.")
    lines = "\n".join(f"{i+1}. {item}" for i, item in enumerate(q))
    await ctx.send(f"📋 **Kuyruk:**\n{lines}")


# ─────────────────────────────────────────
#  Moderasyon
# ─────────────────────────────────────────

@bot.command(name="ban")
@commands.has_permissions(ban_members=True)
async def ban(ctx: commands.Context, member: discord.Member, *, reason: str = "Sebep belirtilmedi"):
    """Bir üyeyi sunucudan yasakla."""
    await member.ban(reason=reason)
    await ctx.send(f"🔨 **{member.display_name}** yasaklandı. Sebep: {reason}")


@bot.command(name="kick")
@commands.has_permissions(kick_members=True)
async def kick(ctx: commands.Context, member: discord.Member, *, reason: str = "Sebep belirtilmedi"):
    """Bir üyeyi sunucudan at."""
    await member.kick(reason=reason)
    await ctx.send(f"👢 **{member.display_name}** atıldı. Sebep: {reason}")


@bot.command(name="mute")
@commands.has_permissions(manage_roles=True)
async def mute(ctx: commands.Context, member: discord.Member, dakika: int = 10):
    """Bir üyeyi sessize al (dakika)."""
    muted_role = discord.utils.get(ctx.guild.roles, name="Muted")
    if not muted_role:
        muted_role = await ctx.guild.create_role(name="Muted")
        for channel in ctx.guild.channels:
            await channel.set_permissions(muted_role, send_messages=False, speak=False)
    await member.add_roles(muted_role)
    await ctx.send(f"🔇 **{member.display_name}** {dakika} dakika susturuldu.")
    await asyncio.sleep(dakika * 60)
    await member.remove_roles(muted_role)
    await ctx.send(f"🔊 **{member.display_name}** susturması kaldırıldı.")


@bot.command(name="temizle", aliases=["clear", "purge"])
@commands.has_permissions(manage_messages=True)
async def clear(ctx: commands.Context, miktar: int = 10):
    """Belirtilen sayıda mesajı sil."""
    deleted = await ctx.channel.purge(limit=miktar + 1)
    msg = await ctx.send(f"🗑️ {len(deleted) - 1} mesaj silindi.")
    await asyncio.sleep(3)
    await msg.delete()


@bot.command(name="uyar", aliases=["warn"])
@commands.has_permissions(manage_messages=True)
async def warn(ctx: commands.Context, member: discord.Member, *, sebep: str = "Sebep yok"):
    """Bir üyeyi uyar."""
    try:
        await member.send(f"⚠️ **{ctx.guild.name}** sunucusunda uyarıldınız!\nSebep: {sebep}")
    except discord.Forbidden:
        pass
    await ctx.send(f"⚠️ **{member.display_name}** uyarıldı: {sebep}")


# ─────────────────────────────────────────
#  AI Sohbet (Claude)
# ─────────────────────────────────────────
conversation_histories: dict[int, list] = {}   # user_id -> message list


@bot.command(name="sor", aliases=["ask", "ai"])
async def ask(ctx: commands.Context, *, soru: str):
    """Claude ile sohbet et."""
    user_id = ctx.author.id
    history = conversation_histories.setdefault(user_id, [])
    history.append({"role": "user", "content": soru})

    async with ctx.typing():
        response = claude_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            system=(
                "Sen Türkçe konuşan, yardımsever ve eğlenceli bir Discord botusun. "
                "Kısa, net ve samimi yanıtlar ver. Emoji kullanabilirsin."
            ),
            messages=history[-20:],   # son 20 mesajı gönder (context penceresi)
        )
    yanit = response.content[0].text
    history.append({"role": "assistant", "content": yanit})

    # Uzun yanıtları böl
    for i in range(0, len(yanit), 1900):
        await ctx.send(yanit[i:i+1900])


@bot.command(name="sıfırla", aliases=["reset"])
async def reset(ctx: commands.Context):
    """Sohbet geçmişini temizle."""
    conversation_histories.pop(ctx.author.id, None)
    await ctx.send("🔄 Sohbet geçmişin temizlendi, yeni başlangıç!")


# ─────────────────────────────────────────
#  Eğlence & Oyunlar
# ─────────────────────────────────────────

@bot.command(name="zar", aliases=["roll", "dice"])
async def zar(ctx: commands.Context, yüz: int = 6):
    """Zar at. Varsayılan 6 yüzlü."""
    sonuç = random.randint(1, yüz)
    await ctx.send(f"🎲 {yüz} yüzlü zar: **{sonuç}**")


@bot.command(name="yazıtura", aliases=["flip"])
async def yazıtura(ctx: commands.Context):
    """Yazı mı tura mı?"""
    sonuç = random.choice(["Yazı 📜", "Tura 🪙"])
    await ctx.send(f"🪙 {sonuç}!")


@bot.command(name="seç", aliases=["choose"])
async def seç(ctx: commands.Context, *seçenekler: str):
    """Seçenekler arasından rastgele seç."""
    if len(seçenekler) < 2:
        return await ctx.send("❌ En az 2 seçenek gir! Örnek: `!seç pizza hamburger döner`")
    await ctx.send(f"🎯 Seçim: **{random.choice(seçenekler)}**")


@bot.command(name="8top", aliases=["8ball"])
async def magic8ball(ctx: commands.Context, *, soru: str):
    """Sihirli 8 top!"""
    yanıtlar = [
        "Kesinlikle evet! ✅", "Evet, tabii ki! 🟢", "Sanırım evet 🤔",
        "Belki... 🤷", "Emin değilim 😬", "Şüpheliyim 🟡",
        "Hayır 🔴", "Kesinlikle hayır! ❌", "Asla! 🚫",
    ]
    await ctx.send(f"🎱 **{random.choice(yanıtlar)}**")


@bot.command(name="sunucu", aliases=["serverinfo"])
async def sunucu(ctx: commands.Context):
    """Sunucu bilgilerini göster."""
    g = ctx.guild
    embed = discord.Embed(title=g.name, color=discord.Color.blurple())
    embed.set_thumbnail(url=g.icon.url if g.icon else None)
    embed.add_field(name="👑 Sahip", value=g.owner.mention)
    embed.add_field(name="👥 Üyeler", value=g.member_count)
    embed.add_field(name="💬 Kanallar", value=len(g.channels))
    embed.add_field(name="🎭 Roller", value=len(g.roles))
    embed.add_field(name="📅 Oluşturulma", value=g.created_at.strftime("%d.%m.%Y"))
    await ctx.send(embed=embed)


@bot.command(name="kullanıcı", aliases=["userinfo", "whois"])
async def kullanıcı(ctx: commands.Context, member: discord.Member = None):
    """Kullanıcı bilgilerini göster."""
    member = member or ctx.author
    embed = discord.Embed(title=member.display_name, color=member.color)
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.add_field(name="🏷️ Tag", value=str(member))
    embed.add_field(name="🆔 ID", value=member.id)
    embed.add_field(name="📅 Katılma", value=member.joined_at.strftime("%d.%m.%Y") if member.joined_at else "?")
    embed.add_field(name="🎭 En yüksek rol", value=member.top_role.mention)
    await ctx.send(embed=embed)


@bot.command(name="yardım2", aliases=["komutlar"])
async def yardım2(ctx: commands.Context):
    """Tüm komutları listele."""
    embed = discord.Embed(title="🤖 Bot Komutları", color=discord.Color.green())
    embed.add_field(name="🎵 Müzik", value=(
        "`!çal <şarkı>` - Şarkı çal\n"
        "`!dur` - Durdur & çık\n"
        "`!atla` - Sonraki şarkı\n"
        "`!kuyruk` - Kuyruğu gör"
    ), inline=False)
    embed.add_field(name="🛡️ Moderasyon", value=(
        "`!ban <@üye> [sebep]` - Yasakla\n"
        "`!kick <@üye> [sebep]` - At\n"
        "`!mute <@üye> [dakika]` - Sustur\n"
        "`!temizle [sayı]` - Mesaj sil\n"
        "`!uyar <@üye> [sebep]` - Uyar"
    ), inline=False)
    embed.add_field(name="🤖 AI Sohbet", value=(
        "`!sor <soru>` - Claude'a sor\n"
        "`!sıfırla` - Geçmişi temizle"
    ), inline=False)
    embed.add_field(name="🎮 Eğlence", value=(
        "`!zar [yüz]` - Zar at\n"
        "`!yazıtura` - Yazı/tura\n"
        "`!seç <a> <b> ...` - Rastgele seç\n"
        "`!8top <soru>` - Sihirli top\n"
        "`!sunucu` - Sunucu bilgisi\n"
        "`!kullanıcı [@üye]` - Kullanıcı bilgisi"
    ), inline=False)
    await ctx.send(embed=embed)


# ─────────────────────────────────────────
#  Etkinlikler
# ─────────────────────────────────────────

@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening,
        name="!yardım2 | Claude destekli 🤖"
    ))
    print(f"✅ {bot.user} olarak giriş yapıldı!")


@bot.event
async def on_member_join(member: discord.Member):
    channel = discord.utils.get(member.guild.text_channels, name="genel")
    if channel:
        await channel.send(
            f"👋 **{member.mention}** sunucuya hoş geldi! "
            f"Toplam üye sayısı: **{member.guild.member_count}**"
        )


@bot.event
async def on_command_error(ctx: commands.Context, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Bu komutu kullanmak için yetkin yok!")
    elif isinstance(error, commands.MemberNotFound):
        await ctx.send("❌ Üye bulunamadı.")
    elif isinstance(error, commands.CommandNotFound):
        pass   # Bilinmeyen komutları sessizce geç
    else:
        await ctx.send(f"⚠️ Hata: {error}")
        raise error


# ─────────────────────────────────────────
#  Başlat
# ─────────────────────────────────────────
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
