# 🤖 Discord Bot — Kurulum Kılavuzu

## 1. Gereksinimler

- Python 3.10+
- FFmpeg (müzik için)

## 2. Kurulum

```bash
# Bağımlılıkları yükle
pip install -r requirements.txt

# FFmpeg kur (Ubuntu/Debian)
sudo apt install ffmpeg

# FFmpeg kur (macOS)
brew install ffmpeg

# FFmpeg kur (Windows)
# https://ffmpeg.org/download.html adresinden indir, PATH'e ekle
```

## 3. Token Ayarları

`bot.py` dosyasını aç, şu iki satırı düzenle:

```python
DISCORD_TOKEN    = "BOT_TOKEN_BURAYA"      # Discord geliştirici portalından al
ANTHROPIC_API_KEY = "ANTHROPIC_KEY_BURAYA" # console.anthropic.com'dan al
```

**Veya** ortam değişkeni kullan (önerilen):

```bash
export DISCORD_TOKEN="..."
export ANTHROPIC_API_KEY="..."
python bot.py
```

## 4. Discord Bot Oluşturma

1. https://discord.com/developers/applications → **New Application**
2. **Bot** sekmesi → **Add Bot** → Token'ı kopyala
3. **Privileged Gateway Intents** bölümünden şunları aç:
   - ✅ Server Members Intent
   - ✅ Message Content Intent
4. **OAuth2 → URL Generator** ile sunucuya davet et:
   - Scope: `bot`
   - Permissions: `Administrator` (veya gerekli izinler)

## 5. Botu Başlat

```bash
python bot.py
```

---

## Komutlar

| Komut | Açıklama |
|-------|----------|
| `!çal <şarkı/URL>` | YouTube'dan müzik çal |
| `!dur` | Müziği durdur, kanaldan çık |
| `!atla` | Sonraki şarkıya geç |
| `!kuyruk` | Kuyruğu listele |
| `!ban @üye [sebep]` | Üyeyi yasakla |
| `!kick @üye [sebep]` | Üyeyi at |
| `!mute @üye [dakika]` | Üyeyi sustur |
| `!temizle [sayı]` | Mesaj sil |
| `!uyar @üye [sebep]` | Üyeyi uyar |
| `!sor <soru>` | Claude AI ile sohbet |
| `!sıfırla` | AI sohbet geçmişini temizle |
| `!zar [yüz]` | Zar at |
| `!yazıtura` | Yazı / tura |
| `!seç a b c` | Rastgele seç |
| `!8top <soru>` | Sihirli 8 top |
| `!sunucu` | Sunucu bilgisi |
| `!kullanıcı [@üye]` | Kullanıcı bilgisi |
| `!yardım2` | Tüm komutlar |
