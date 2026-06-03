import requests
import threading
import queue
import time
import os
import re
import platform
import socket
import socks
from bs4 import BeautifulSoup
from colorama import Fore, Style, init
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum

init(autoreset=True)


class Lang(Enum):
    EN = "EN"
    TR = "TR"


class ProxyType(Enum):
    HTTP    = "http"
    HTTPS   = "https"
    SOCKS4  = "socks4"
    SOCKS5  = "socks5"
    UNKNOWN = "unknown"


@dataclass
class ProxyEntry:
    raw:        str
    ip:         str
    port:       int
    proxy_type: ProxyType     = ProxyType.UNKNOWN
    latency:    Optional[int] = None
    valid:      bool          = False


@dataclass
class ScanConfig:
    mode:         str          = "fastest_10"
    custom_limit: Optional[int] = None
    thread_count: int          = 30
    timeout:      int          = 5
    lang:         Lang         = Lang.EN


# ──────────────────────────────────────────────
# Çok dilli metin tablosu
# ──────────────────────────────────────────────
TEXTS = {
    "lang_prompt":    {"EN": "Choose Language",                            "TR": "Dil Seçin"},
    "lang_set_en":    {"EN": "[+] Language set to English.",               "TR": "[+] Language set to English."},
    "lang_set_tr":    {"EN": "[+] Dil Türkçe olarak ayarlandı.",           "TR": "[+] Dil Türkçe olarak ayarlandı."},
    "mode_title":     {"EN": "Select Scan Mode",                           "TR": "Tarama Modu Seçin"},
    "mode_1":         {"EN": "Fastest 10 Proxies (Recommended: 15 threads)","TR": "En Hızlı 10 Proxy (Önerilen: 15 thread)"},
    "mode_2":         {"EN": "Fastest 20 Proxies (Recommended: 20 threads)","TR": "En Hızlı 20 Proxy (Önerilen: 20 thread)"},
    "mode_3":         {"EN": "Fastest 50 Proxies (Recommended: 25 threads)","TR": "En Hızlı 50 Proxy (Önerilen: 25 thread)"},
    "mode_4":         {"EN": "Custom Limit (Recommended: 100 proxies)",    "TR": "Özel Limit (Önerilen: 100 proxy)"},
    "mode_5":         {"EN": "Unlimited (collect all valid)",              "TR": "Sınırsız (tümünü topla)"},
    "mode_prompt":    {"EN": "Enter mode [1-5]: ",                         "TR": "Mod seçin [1-5]: "},
    "custom_prompt":  {"EN": "Enter proxy limit: ",                        "TR": "Proxy limiti girin: "},
    "thread_prompt":  {"EN": "Thread count [default recommended, max 120]: ", "TR": "Thread sayısı [varsayılan önerilen, maks 120]: "},
    "timeout_prompt": {"EN": "Timeout in seconds [default 5]: ",           "TR": "Zaman aşımı saniye [varsayılan 5]: "},
    "scraping":       {"EN": "[*] Scraping proxies from sources...",       "TR": "[*] Kaynaklardan proxy toplanıyor..."},
    "found":          {"EN": "[+] Found {n} raw proxies.",                 "TR": "[+] {n} ham proxy bulundu."},
    "checking":       {"EN": "[*] Starting {n} threads for validation...", "TR": "[*] Doğrulama için {n} thread başlatılıyor..."},
    "valid":          {"EN": "[+] VALID",                                  "TR": "[+] AKTİF"},
    "invalid":        {"EN": "[-] DEAD",                                   "TR": "[-] ÖLÜM"},
    "limit_reached":  {"EN": "[!] Target limit reached. Stopping.",        "TR": "[!] Hedef limite ulaşıldı. Durduruluyor."},
    "scan_done":      {"EN": "Scan Completed!",                            "TR": "Tarama Tamamlandı!"},
    "total_valid":    {"EN": "Total Valid Proxies: {n}",                   "TR": "Toplam Aktif Proxy: {n}"},
    "saved":          {"EN": "Results saved to valid_proxies.txt",         "TR": "Sonuçlar valid_proxies.txt dosyasına kaydedildi."},
    "invalid_input":  {"EN": "[!] Invalid input, using default.",          "TR": "[!] Geçersiz giriş, varsayılan kullanılıyor."},
}


def t(key: str, cfg: ScanConfig, **kwargs) -> str:
    """Verilen anahtarı aktif dilde döndürür, {placeholder} değerlerini değiştirir."""
    lang = cfg.lang.value
    text = TEXTS.get(key, {}).get(lang, TEXTS.get(key, {}).get("EN", key))
    for k, v in kwargs.items():
        text = text.replace("{" + k + "}", str(v))
    return text


# ──────────────────────────────────────────────
# HTTP / HTTPS kaynak listesi
# Orijinal kaynaklar + yeni eklenenler (# NEW ile işaretli)
# ──────────────────────────────────────────────
SOURCES_HTTP = [
    # ── Tablo tabanlı siteler (BeautifulSoup ile parse edilir) ──
    "https://free-proxy-list.net/",
    "https://www.us-proxy.org/",
    "https://www.sslproxies.org/",

    # ── Düz metin / API uçnoktaları ──
    "https://www.proxy-list.download/HTTP",
    "https://www.proxy-list.download/HTTPS",
    "https://api.proxyscrape.com/v2/?request=get&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all",

    # ── GitHub düz metin listeleri (orijinal) ──
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/https.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/https.txt",
    "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
    "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/proxies.txt",
    "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-https.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/http.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/https.txt",
    "https://raw.githubusercontent.com/zevtyardt/proxy-list/main/http.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/http.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/https.txt",
    "https://www.proxyscan.io/download?type=http",
    "https://www.proxyscan.io/download?type=https",
    "https://proxyspace.pro/http.txt",
    "https://proxyspace.pro/https.txt",

    # ── YENİ: proxifly (tüm protokoller, data.txt) ──          # NEW
    "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all/data.txt",  # NEW

    # ── YENİ: ManishMali ──                                     # NEW
    "https://raw.githubusercontent.com/ManishMali/free-proxy/main/proxies.txt",              # NEW

    # ── YENİ: almroot ──                                        # NEW
    "https://raw.githubusercontent.com/almroot/proxylists/master/list.txt",                  # NEW

    # ── YENİ: ErcanOzdemir HTTP / HTTPS ──                      # NEW
    "https://raw.githubusercontent.com/ErcanOzdemir/Free-Proxy-List/main/Proxies/HTTP.txt",  # NEW
    "https://raw.githubusercontent.com/ErcanOzdemir/Free-Proxy-List/main/Proxies/HTTPS.txt", # NEW

    # ── YENİ: saisuiu güncel listeler ──                        # NEW
    "https://raw.githubusercontent.com/saisuiu/Latest-Proxy/main/http.txt",                  # NEW
    "https://raw.githubusercontent.com/saisuiu/Latest-Proxy/main/https.txt",                 # NEW

    # ── YENİ: GeoNode API (HTTP / HTTPS, 500 kayıt) ──          # NEW
    "https://proxylist.geonode.com/api/proxy-list?protocol=http&limit=500&page=1&format=txt",   # NEW
    "https://proxylist.geonode.com/api/proxy-list?protocol=https&limit=500&page=1&format=txt",  # NEW
]

# ──────────────────────────────────────────────
# SOCKS4 kaynak listesi
# ──────────────────────────────────────────────
SOURCES_SOCKS4 = [
    # ── Tablo tabanlı ──
    "https://www.socks-proxy.net/",

    # ── API / düz metin (orijinal) ──
    "https://www.proxy-list.download/SOCKS4",
    "https://api.proxyscrape.com/v2/?request=get&protocol=socks4&timeout=10000&country=all",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks4.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks4.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks4.txt",
    "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS4_RAW.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks4.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks4.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks4.txt",
    "https://www.proxyscan.io/download?type=socks4",
    "https://proxyspace.pro/socks4.txt",

    # ── YENİ: ErcanOzdemir SOCKS4 ──                            # NEW
    "https://raw.githubusercontent.com/ErcanOzdemir/Free-Proxy-List/main/Proxies/SOCKS4.txt", # NEW

    # ── YENİ: saisuiu SOCKS4 ──                                 # NEW
    "https://raw.githubusercontent.com/saisuiu/Latest-Proxy/main/socks4.txt",                 # NEW

    # ── YENİ: GeoNode API SOCKS4 ──                             # NEW
    "https://proxylist.geonode.com/api/proxy-list?protocol=socks4&limit=500&page=1&format=txt", # NEW
]

# ──────────────────────────────────────────────
# SOCKS5 kaynak listesi
# ──────────────────────────────────────────────
SOURCES_SOCKS5 = [
    # ── API / düz metin (orijinal) ──
    "https://www.proxy-list.download/SOCKS5",
    "https://api.proxyscrape.com/v2/?request=get&protocol=socks5&timeout=10000&country=all",
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/socks5.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/socks5.txt",
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt",
    "https://raw.githubusercontent.com/UptimerBot/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt",
    "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-socks5.txt",
    "https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt",
    "https://raw.githubusercontent.com/rdavydov/proxy-list/main/proxies/socks5.txt",
    "https://raw.githubusercontent.com/Zaeem20/FREE_PROXIES_LIST/master/socks5.txt",
    "https://www.proxyscan.io/download?type=socks5",
    "https://proxyspace.pro/socks5.txt",

    # ── YENİ: ErcanOzdemir SOCKS5 ──                            # NEW
    "https://raw.githubusercontent.com/ErcanOzdemir/Free-Proxy-List/main/Proxies/SOCKS5.txt", # NEW

    # ── YENİ: saisuiu SOCKS5 ──                                 # NEW
    "https://raw.githubusercontent.com/saisuiu/Latest-Proxy/main/socks5.txt",                 # NEW

    # ── YENİ: GeoNode API SOCKS5 ──                             # NEW
    "https://proxylist.geonode.com/api/proxy-list?protocol=socks5&limit=500&page=1&format=txt", # NEW
]

# IP:PORT formatını doğrulamak için regex
PROXY_RE = re.compile(r"^(\d{1,3}\.){3}\d{1,3}:\d{2,5}$")

BANNER = f"""
{Fore.CYAN}    ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗     
    ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║     
    ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║     
    ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║     
    ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
    ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
{Fore.RED}    [#] Advanced Proxy Scraper & Checker  |  HTTP · HTTPS · SOCKS4 · SOCKS5
{Fore.WHITE}    [#] Created by Tc4dy | 2026
"""


def clear():
    """Terminali temizler (Windows ve Unix uyumlu)."""
    os.system("cls" if platform.system().lower() == "windows" else "clear")


def parse_proxy_line(line: str) -> Optional[ProxyEntry]:
    """
    Bir satırı IP:PORT formatında ayrıştırır.
    Geçersiz formatlarda None döndürür.
    """
    line = line.strip()
    parts = line.split(":")
    if len(parts) != 2:
        return None
    ip, port_str = parts[0], parts[1]
    if not PROXY_RE.match(line):
        return None
    try:
        port = int(port_str)
    except ValueError:
        return None
    if not (1 <= port <= 65535):
        return None
    octets = ip.split(".")
    if any(int(o) > 255 for o in octets):
        return None
    return ProxyEntry(raw=line, ip=ip, port=port)


def fetch_raw(url: str, proxy_type: ProxyType) -> list[ProxyEntry]:
    """
    Verilen URL'den proxy listesi çeker.
    HTML tablo tabanlı siteler BeautifulSoup ile,
    düz metin kaynaklar satır satır parse edilir.
    """
    results = []
    try:
        resp = requests.get(url, timeout=12, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()

        # HTML tablo içeren bilinen alan adları
        table_domains = [
            "free-proxy-list.net", "us-proxy.org", "socks-proxy.net", "sslproxies.org"
        ]
        is_table = any(d in url for d in table_domains)

        if is_table:
            # HTML tablosunu parse et
            soup = BeautifulSoup(resp.text, "html.parser")
            table = soup.find("table")
            if table:
                for row in table.find_all("tr")[1:]:
                    tds = row.find_all("td")
                    if len(tds) >= 2:
                        entry = parse_proxy_line(f"{tds[0].text.strip()}:{tds[1].text.strip()}")
                        if entry:
                            entry.proxy_type = proxy_type
                            results.append(entry)
        else:
            # Düz metin: her satırı dene
            for line in resp.text.splitlines():
                entry = parse_proxy_line(line)
                if entry:
                    entry.proxy_type = proxy_type
                    results.append(entry)
    except Exception:
        # Ağ hatası, timeout, HTTP hataları sessizce geçilir
        pass
    return results


def scrape_all() -> list[ProxyEntry]:
    """
    Tüm kaynak listelerini paralel olarak çeker,
    tekrar edenleri filtreler ve birleşik liste döndürür.
    """
    all_entries: list[ProxyEntry] = []
    seen: set[str] = set()

    # Tüm kaynak/tip çiftlerini tek listeye topla
    tasks: list[tuple[str, ProxyType]] = (
        [(u, ProxyType.HTTP)   for u in SOURCES_HTTP]  +
        [(u, ProxyType.SOCKS4) for u in SOURCES_SOCKS4] +
        [(u, ProxyType.SOCKS5) for u in SOURCES_SOCKS5]
    )

    # 20 iş parçacığıyla kaynakları eş zamanlı çek
    with ThreadPoolExecutor(max_workers=20) as ex:
        futures = {ex.submit(fetch_raw, url, ptype): (url, ptype) for url, ptype in tasks}
        for future in as_completed(futures):
            for entry in future.result():
                if entry.raw not in seen:
                    seen.add(entry.raw)
                    all_entries.append(entry)

    return all_entries


def check_http_proxy(entry: ProxyEntry, timeout: int) -> bool:
    """HTTP/HTTPS proxy'yi httpbin.org üzerinden doğrular."""
    try:
        proxies = {
            "http":  f"http://{entry.raw}",
            "https": f"http://{entry.raw}",
        }
        start = time.time()
        r = requests.get("https://httpbin.org/ip", proxies=proxies, timeout=timeout)
        if r.status_code == 200:
            entry.latency = round((time.time() - start) * 1000)
            return True
    except Exception:
        pass
    return False


def check_socks_proxy(entry: ProxyEntry, timeout: int) -> bool:
    """SOCKS4/5 proxy'yi PySocks üzerinden TCP bağlantısıyla doğrular."""
    socks_type = socks.SOCKS4 if entry.proxy_type == ProxyType.SOCKS4 else socks.SOCKS5
    try:
        s = socks.socksocket()
        s.set_proxy(socks_type, entry.ip, entry.port)
        s.settimeout(timeout)
        start = time.time()
        s.connect(("httpbin.org", 80))
        s.sendall(b"GET /ip HTTP/1.1\r\nHost: httpbin.org\r\nConnection: close\r\n\r\n")
        response = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            response += chunk
        s.close()
        if b"200 OK" in response or b'"origin"' in response:
            entry.latency = round((time.time() - start) * 1000)
            return True
    except Exception:
        pass
    return False


def validate_proxy(entry: ProxyEntry, timeout: int) -> bool:
    """Proxy tipine göre doğru kontrol fonksiyonunu çağırır."""
    if entry.proxy_type in (ProxyType.SOCKS4, ProxyType.SOCKS5):
        return check_socks_proxy(entry, timeout)
    return check_http_proxy(entry, timeout)


def select_language() -> Lang:
    """Kullanıcıdan dil seçimi alır."""
    clear()
    print(BANNER)
    print(f"{Fore.YELLOW}  1 — English")
    print(f"{Fore.YELLOW}  2 — Türkçe\n")
    choice = input(f"{Fore.WHITE}  Choose Language / Dil Seçin [1/2]: ").strip()
    if choice == "2":
        print(f"\n{Fore.GREEN}  [+] Dil Türkçe olarak ayarlandı.\n")
        return Lang.TR
    print(f"\n{Fore.GREEN}  [+] Language set to English.\n")
    return Lang.EN


def build_config(lang: Lang) -> ScanConfig:
    """
    Kullanıcıdan tarama modunu, thread sayısını ve timeout'u alır.
    Thread sayısı 1-120 arasında sınırlandırılmıştır.
    """
    cfg = ScanConfig(lang=lang)

    # ── Mod seçim menüsü ──
    print(f"{Fore.CYAN}  {'─'*52}")
    print(f"{Fore.CYAN}  {t('mode_title', cfg)}")
    print(f"{Fore.CYAN}  {'─'*52}")
    print(f"{Fore.WHITE}  1 — {t('mode_1', cfg)}")
    print(f"{Fore.WHITE}  2 — {t('mode_2', cfg)}")
    print(f"{Fore.WHITE}  3 — {t('mode_3', cfg)}")
    print(f"{Fore.WHITE}  4 — {t('mode_4', cfg)}")
    print(f"{Fore.WHITE}  5 — {t('mode_5', cfg)}")
    print(f"{Fore.CYAN}  {'─'*52}\n")

    # mod_key → (mod adı, önerilen thread, -)
    mode_map = {
        "1": ("fastest_10", 15,  None),
        "2": ("fastest_20", 20,  None),
        "3": ("fastest_50", 25,  None),
        "4": ("custom",     30,  None),
        "5": ("unlimited",  30,  None),
    }

    raw_mode = input(f"  {t('mode_prompt', cfg)}").strip()
    if raw_mode not in mode_map:
        print(f"  {Fore.YELLOW}{t('invalid_input', cfg)}")
        raw_mode = "1"

    mode_key, recommended_threads, _ = mode_map[raw_mode]
    cfg.mode = mode_key

    # Özel limit modu
    if mode_key == "custom":
        raw_limit = input(f"  {t('custom_prompt', cfg)}").strip()
        try:
            cfg.custom_limit = max(1, int(raw_limit))
        except ValueError:
            print(f"  {Fore.YELLOW}{t('invalid_input', cfg)}")
            cfg.custom_limit = 100

    # ── Thread sayısı girişi (maks 120) ──
    print(f"\n  {Fore.CYAN}[Recommended threads: {recommended_threads} | Max: 120]")
    raw_threads = input(f"  {t('thread_prompt', cfg)}").strip()
    try:
        entered = int(raw_threads)
        # 1 altı → 1, 120 üstü → 120
        cfg.thread_count = max(1, min(120, entered))
        if entered > 120:
            print(f"  {Fore.YELLOW}[!] Thread count capped at 120.")
    except ValueError:
        cfg.thread_count = recommended_threads

    # ── Timeout girişi ──
    raw_timeout = input(f"  {t('timeout_prompt', cfg)}").strip()
    try:
        cfg.timeout = max(1, min(30, int(raw_timeout)))
    except ValueError:
        cfg.timeout = 5

    return cfg


def resolve_target_limit(cfg: ScanConfig) -> Optional[int]:
    """Seçilen moda göre hedef proxy limitini döndürür. Sınırsız modda None."""
    mapping = {
        "fastest_10": 10,
        "fastest_20": 20,
        "fastest_50": 50,
        "custom":     cfg.custom_limit,
        "unlimited":  None,
    }
    return mapping.get(cfg.mode)


def run_scan(cfg: ScanConfig, proxies: list[ProxyEntry]) -> list[ProxyEntry]:
    """
    Proxy listesini thread havuzuyla paralel doğrular.
    Geçerli proxy bulununca ekrana yazar ve dosyaya kaydeder.
    Limite ulaşıldığında stop_event ile tüm thread'leri durdurur.
    """
    target_limit  = resolve_target_limit(cfg)
    valid_proxies: list[ProxyEntry] = []
    lock          = threading.Lock()
    stop_event    = threading.Event()
    proxy_queue: queue.Queue[ProxyEntry] = queue.Queue()

    for p in proxies:
        proxy_queue.put(p)

    output_file = "valid_proxies.txt"
    if os.path.exists(output_file):
        os.remove(output_file)

    def worker():
        """Her thread bu fonksiyonu çalıştırır; kuyruk boşalınca veya stop_event set edilince durur."""
        while not stop_event.is_set():
            try:
                entry = proxy_queue.get_nowait()
            except queue.Empty:
                break
            try:
                if validate_proxy(entry, cfg.timeout):
                    entry.valid = True
                    with lock:
                        if stop_event.is_set():
                            return
                        valid_proxies.append(entry)
                        # Tip bazlı renk
                        type_color = {
                            ProxyType.HTTP:   Fore.GREEN,
                            ProxyType.HTTPS:  Fore.GREEN,
                            ProxyType.SOCKS4: Fore.MAGENTA,
                            ProxyType.SOCKS5: Fore.CYAN,
                        }.get(entry.proxy_type, Fore.WHITE)
                        print(
                            f"  {Fore.GREEN}{t('valid', cfg)}{Fore.WHITE} "
                            f"{type_color}[{entry.proxy_type.value.upper():6}]{Fore.WHITE} "
                            f"{entry.raw:<22} {Fore.YELLOW}{entry.latency}ms"
                        )
                        # Geçerli proxy'yi dosyaya ekle
                        with open(output_file, "a") as f:
                            f.write(f"{entry.proxy_type.value}://{entry.raw}\n")
                        # Limite ulaşıldıysa tüm thread'leri durdur
                        if target_limit and len(valid_proxies) >= target_limit:
                            print(f"\n  {Fore.YELLOW}{t('limit_reached', cfg)}")
                            stop_event.set()
            finally:
                proxy_queue.task_done()

    print(f"\n  {Fore.BLUE}{t('checking', cfg, n=cfg.thread_count)}\n")

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(cfg.thread_count)]
    for th in threads:
        th.start()
    proxy_queue.join()
    for th in threads:
        th.join()

    # "fastest" modlarında latency'ye göre sırala ve kes
    if "fastest" in cfg.mode:
        valid_proxies.sort(key=lambda p: p.latency or 9999)
        valid_proxies = valid_proxies[:target_limit]

    return valid_proxies


def print_summary(cfg: ScanConfig, valid: list[ProxyEntry]):
    """Tarama sonuçlarını ekrana basar."""
    print(f"\n  {Fore.YELLOW}{'═'*52}")
    print(f"  {Fore.CYAN}[!] {t('scan_done', cfg)}")
    print(f"  {Fore.GREEN}[+] {t('total_valid', cfg, n=len(valid))}")
    if valid:
        avg_latency = round(sum(p.latency or 0 for p in valid) / len(valid))
        best = min(valid, key=lambda p: p.latency or 9999)
        print(f"  {Fore.GREEN}[+] Best:         {best.raw} | {best.latency}ms ({best.proxy_type.value.upper()})")
        print(f"  {Fore.GREEN}[+] Avg latency:  {avg_latency}ms")
        # Tip dağılımı
        type_counts: dict[str, int] = {}
        for p in valid:
            k = p.proxy_type.value.upper()
            type_counts[k] = type_counts.get(k, 0) + 1
        for k, v in sorted(type_counts.items()):
            print(f"  {Fore.WHITE}    {k}: {v}")
    print(f"  {Fore.GREEN}[+] {t('saved', cfg)}")
    print(f"  {Fore.YELLOW}{'═'*52}\n")


def main():
    clear()
    print(BANNER)

    lang = select_language()
    cfg  = build_config(lang)

    clear()
    print(BANNER)
    print(f"\n  {Fore.BLUE}{t('scraping', cfg)}\n")

    proxies = scrape_all()
    print(f"  {Fore.GREEN}{t('found', cfg, n=len(proxies))}")
    time.sleep(0.6)

    valid = run_scan(cfg, proxies)
    print_summary(cfg, valid)


if __name__ == "__main__":
    main()
