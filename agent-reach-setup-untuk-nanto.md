# Agent Reach — Panduan Setup untuk Nanto

Agent Reach sudah terinstall (v1.5.0). 7 channel langsung aktif:
GitHub, YouTube, V2EX, RSS, Exa Search, Web/Jina, Bilibili.

Berikut langkah manual yang diperlukan untuk mengaktifkan channel lainnya.

---

## 1. OpenCLI Chrome Extension (wajib untuk Reddit, FB, IG, Xiaohongshu)

Satu langkah manual, sisanya otomatis.

Buka link ini di Chrome, klik "Add to Chrome":
```
https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk
```

Setelah terinstall, pastikan Chrome masih terbuka dan kamu sudah login ke platform yang mau dipakai:
- **reddit.com** (untuk Reddit)
- **facebook.com** (untuk Facebook)
- **instagram.com** (untuk Instagram)
- **xiaohongshu.com** (untuk小红书)

Verifikasi:
```bash
opencli doctor
```
Harusnya muncul "Extension: connected".

---

## 2. Twitter/X — Cookie

Cara termudah pakai Cookie-Editor:

1. Install extension: https://chromewebstore.google.com/detail/cookie-editor/hlkenndednhfkekhgcdicdfddnkalmdm
2. Buka x.com, pastikan sudah login
3. Klik ikon Cookie-Editor → Export → Header String
4. Paste hasilnya ke sini:

```bash
agent-reach configure twitter-cookies "paste di sini"
```

---

## 3. LinkedIn — Login Browser

```bash
pip install linkedin-scraper-mcp
linkedin-scraper-mcp --login --no-headless
```
Nanti muncul browser window, login ke LinkedIn. Selesai.

---

## 4. Xiaoyuzhou Podcast (opsional)

Butuh Groq API key (gratis):
1. Buka https://console.groq.com → login → API Keys → Create
2. Copy key (gsk_xxxx), lalu:

```bash
agent-reach configure groq-key gsk_xxxx
```

---

## 5. Gemini API Key (untuk coding & sandbox)

Key sudah diset. Kalau perlu regenerate:
1. Buka https://aistudio.google.com/apikey
2. Login → Create API Key → Copy
3. Kasih ke agent: `export GEMINI_API_KEY="key_kamu"`

---

## Verifikasi Akhir

```bash
agent-reach doctor
```

---

## Catatan

- Agent Reach di `~/.agent-reach/`
- SKILL: `~/.agents/skills/agent-reach/SKILL.md`
- Exa search API key sudah dikonfigurasi
- Gemini API key sudah diset
