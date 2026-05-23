<div align="center">

```
███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗     
██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║     
███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║     
╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║     
███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
```

**Advanced Proxy Scraper & Checker**

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-Free-green?style=flat-square)](https://github.com/tc4dy/SentinelProxyV2)
[![GitHub](https://img.shields.io/badge/GitHub-tc4dy-black?style=flat-square&logo=github)](https://github.com/tc4dy/SentinelProxyV2)
[![Proxies](https://img.shields.io/badge/Sources-55%2B-orange?style=flat-square)]()

*HTTP · HTTPS · SOCKS4 · SOCKS5 — Türkçe / English*

</div>

---

## 📋 İçindekiler / Table of Contents

- [Özellikler / Features](#-özellikler--features)
- [Kurulum / Installation](#-kurulum--installation)
- [Kullanım / Usage](#-kullanım--usage)
- [Modlar / Modes](#-modlar--modes)
- [Proxy Tipleri](#-proxy-tipleri)
- [Kaynaklar / Sources](#-kaynaklar--sources)
- [Gereksinimler / Requirements](#-gereksinimler--requirements)

---

## ✨ Özellikler / Features

| Özellik | Açıklama | Feature | Description |
|--------|----------|---------|-------------|
| 🌐 Çoklu Kaynak | 55+ kaynaktan proxy toplar | Multi-Source | Scrapes from 55+ sources |
| ⚡ Paralel Scraping | 20 thread ile eş zamanlı çeker | Parallel Scraping | 20 threads simultaneously |
| ✅ Gerçek Doğrulama | HTTP ve SOCKS ayrı ayrı test edilir | Real Validation | HTTP & SOCKS tested separately |
| 🎯 5 Farklı Mod | Hedef sayıya göre otomatik durur | 5 Scan Modes | Stops at target count |
| 📊 Hız Sıralaması | En hızlı proxyleri öne çıkarır | Speed Ranking | Ranks by latency |
| 🌍 2 Dil | Türkçe ve İngilizce arayüz | Bilingual UI | Turkish & English |
| 🔧 Özelleştirilebilir | Thread, timeout, limit ayarlanabilir | Customizable | Thread, timeout, limit |
| 💾 Otomatik Kayıt | Geçerli proxyler dosyaya yazılır | Auto-Save | Valid proxies saved instantly |

---

## 📦 Kurulum / Installation

```bash
# Repoyu klonla / Clone the repo
git clone https://github.com/tc4dy/SentinelProxyV2.git
cd SentinelProxyV2

# Bağımlılıkları yükle / Install dependencies
pip install -r requirements.txt
```

### requirements.txt

```
requests
beautifulsoup4
colorama
PySocks
```

---

## 🚀 Kullanım / Usage

```bash
python sentinel_proxy.py
```

Başlatınca sırasıyla / On launch, in order:

```
1. Dil seçimi          →  TR / EN
2. Mod seçimi          →  1-5
3. Thread sayısı       →  (önerilen gösterilir)
4. Timeout süresi      →  saniye cinsinden
5. Scraping başlar     →  otomatik
6. Doğrulama başlar    →  canlı çıktı
7. Özet & kayıt        →  valid_proxies.txt
```

---

## 🎯 Modlar / Modes

| # | Mod | Açıklama | Önerilen Thread |
|---|-----|----------|:--------------:|
| 1 | **En Hızlı 10** / Fastest 10 | Sadece 10 proxy toplar, hıza göre sıralar | `15` |
| 2 | **En Hızlı 20** / Fastest 20 | Sadece 20 proxy toplar, hıza göre sıralar | `20` |
| 3 | **En Hızlı 50** / Fastest 50 | Sadece 50 proxy toplar, hıza göre sıralar | `25` |
| 4 | **Özel Limit** / Custom Limit | Kullanıcının girdiği sayıya ulaşınca durur | `30` *(öneri: 100)* |
| 5 | **Sınırsız** / Unlimited | Tüm geçerli proxyleri toplar | `30` |

---

## 🔌 Proxy Tipleri

| Tip | Doğrulama Yöntemi | Renk |
|-----|------------------|------|
| `HTTP` | `httpbin.org/ip` üzerinden HTTP isteği | 🟢 Yeşil |
| `HTTPS` | `httpbin.org/ip` üzerinden HTTPS isteği | 🟢 Yeşil |
| `SOCKS4` | PySocks ile gerçek socket bağlantısı | 🟣 Mor |
| `SOCKS5` | PySocks ile gerçek socket bağlantısı | 🔵 Mavi |

> **Not:** SOCKS proxy'leri artık HTTP gibi yanlış test edilmiyor — doğrudan TCP socket üzerinden doğrulanıyor.

---

## 📡 Kaynaklar / Sources

| Kaynak Tipi | Sayı |
|-------------|:----:|
| HTTP / HTTPS kaynakları | 27 |
| SOCKS4 kaynakları | 14 |
| SOCKS5 kaynakları | 14 |
| **Toplam** | **55+** |

Kaynaklar arasında / Sources include:

- `free-proxy-list.net`, `sslproxies.org`, `socks-proxy.net`
- `proxyscrape.com`, `proxyscan.io`, `proxyspace.pro`
- `proxy-list.download`
- GitHub: `TheSpeedX`, `ShiftyTR`, `monosans`, `jetkai`, `Zaeem20`, `rdavydov` ve daha fazlası

---

## 💾 Çıktı / Output

Geçerli proxyler `valid_proxies.txt` dosyasına protokol bilgisiyle kaydedilir:

```
http://1.2.3.4:8080
https://5.6.7.8:3128
socks4://9.10.11.12:4145
socks5://13.14.15.16:1080
```

---

## ⚙️ Gereksinimler / Requirements

| Paket | Kullanım |
|-------|---------|
| `requests` | HTTP istekleri ve proxy testi |
| `beautifulsoup4` | HTML tablo kaynaklarını parse etmek |
| `colorama` | Renkli terminal çıktısı |
| `PySocks` | SOCKS4/SOCKS5 doğrulaması |

**Python 3.8+** gereklidir.

---

## ⚠️ Yasal Uyarı / Legal Notice

Bu araç yalnızca **eğitim, araştırma ve kişisel kullanım** amaçlıdır.  
This tool is intended for **educational, research and personal use** only.

---

<div align="center">

**[⭐ GitHub](https://github.com/tc4dy/SentinelProxyV2)**

*Created by [@tc4dy](https://github.com/tc4dy) · 2026 · Free to use · Unauthorized selling prohibited*

</div>
