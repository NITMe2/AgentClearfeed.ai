"""Phase 3: Dynamic content — live Bitcoin price endpoints (HTML bloat vs ACF)."""

from datetime import datetime, timezone

import httpx
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/phase3", tags=["phase3"])

COINGECKO_URL = "https://api.coingecko.com/api/v3/simple/price"


def fetch_bitcoin_data() -> dict:
    resp = httpx.get(
        COINGECKO_URL,
        params={
            "ids": "bitcoin",
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_market_cap": "true",
            "include_last_updated_at": "true",
        },
        timeout=10.0,
    )
    resp.raise_for_status()
    btc = resp.json()["bitcoin"]
    return {
        "price_usd": btc["usd"],
        "change_24h": round(btc.get("usd_24h_change", 0), 2),
        "market_cap": btc.get("usd_market_cap", 0),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def build_bloated_html(data: dict) -> str:
    price = f"{data['price_usd']:,.2f}"
    change = f"{data['change_24h']:+.2f}"
    market_cap = f"{data['market_cap']:,.0f}"
    fetched = data["fetched_at"]
    change_color = "#16c784" if data["change_24h"] >= 0 else "#ea3943"
    arrow = "▲" if data["change_24h"] >= 0 else "▼"

    return f"""<!DOCTYPE html>
<html lang="en" dir="ltr" class="no-js client-nojs">
<head>
<meta charset="UTF-8">
<title>Bitcoin (BTC) Price, Charts, Market Cap | CryptoTracker</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=5.0">
<meta name="description" content="Get the latest Bitcoin (BTC) price, market cap, trading pairs, charts and data today from the world's number one cryptocurrency price-tracking website.">
<meta name="keywords" content="bitcoin, btc, bitcoin price, bitcoin market cap, crypto, cryptocurrency, bitcoin chart, bitcoin exchange rate, bitcoin trading">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1, max-video-preview:-1">
<meta name="author" content="CryptoTracker">
<meta name="theme-color" content="#1a1a2e">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="CryptoTracker">
<meta name="application-name" content="CryptoTracker">
<meta name="msapplication-TileColor" content="#1a1a2e">
<meta name="msapplication-config" content="/browserconfig.xml">
<meta property="og:title" content="Bitcoin (BTC) Price Today, Chart &amp; Market Cap | CryptoTracker">
<meta property="og:description" content="Get the latest Bitcoin price, BTC market cap, trading pairs, charts and data today from the world's number one cryptocurrency price-tracking website">
<meta property="og:type" content="website">
<meta property="og:site_name" content="CryptoTracker">
<meta property="og:image" content="https://cryptotracker.example.com/images/og-bitcoin.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="Bitcoin BTC price chart and market data">
<meta property="og:url" content="https://cryptotracker.example.com/currencies/bitcoin/">
<meta property="og:locale" content="en_US">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:site" content="@CryptoTracker">
<meta name="twitter:creator" content="@CryptoTracker">
<meta name="twitter:title" content="Bitcoin Price Today | BTC Live Market Cap &amp; Chart">
<meta name="twitter:description" content="Track Bitcoin (BTC) price, market cap, supply, and trading volume in real time.">
<meta name="twitter:image" content="https://cryptotracker.example.com/images/twitter-bitcoin.png">
<link rel="canonical" href="https://cryptotracker.example.com/currencies/bitcoin/">
<link rel="alternate" hreflang="en" href="https://cryptotracker.example.com/currencies/bitcoin/">
<link rel="alternate" hreflang="de" href="https://cryptotracker.example.com/de/currencies/bitcoin/">
<link rel="alternate" hreflang="es" href="https://cryptotracker.example.com/es/currencies/bitcoin/">
<link rel="alternate" hreflang="fr" href="https://cryptotracker.example.com/fr/currencies/bitcoin/">
<link rel="alternate" hreflang="ja" href="https://cryptotracker.example.com/ja/currencies/bitcoin/">
<link rel="alternate" hreflang="ko" href="https://cryptotracker.example.com/ko/currencies/bitcoin/">
<link rel="alternate" hreflang="pt-br" href="https://cryptotracker.example.com/pt-br/currencies/bitcoin/">
<link rel="alternate" hreflang="ru" href="https://cryptotracker.example.com/ru/currencies/bitcoin/">
<link rel="alternate" hreflang="zh" href="https://cryptotracker.example.com/zh/currencies/bitcoin/">
<link rel="alternate" hreflang="ar" href="https://cryptotracker.example.com/ar/currencies/bitcoin/">
<link rel="alternate" hreflang="tr" href="https://cryptotracker.example.com/tr/currencies/bitcoin/">
<link rel="alternate" hreflang="vi" href="https://cryptotracker.example.com/vi/currencies/bitcoin/">
<link rel="alternate" hreflang="x-default" href="https://cryptotracker.example.com/currencies/bitcoin/">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="preconnect" href="https://fonts.googleapis.com" crossorigin>
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preconnect" href="https://www.googletagmanager.com">
<link rel="preconnect" href="https://www.google-analytics.com">
<link rel="dns-prefetch" href="https://cdn.cryptotracker.example.com">
<link rel="dns-prefetch" href="https://api.cryptotracker.example.com">
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap">
<link rel="stylesheet" href="/static/css/main.a4f8e2b1c3d9.min.css">
<link rel="stylesheet" href="/static/css/vendor.7b2e1f4a.min.css">
<link rel="stylesheet" href="/static/css/chart.2c8f1e3d.min.css">
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "WebPage",
  "name": "Bitcoin (BTC) Price, Charts, Market Cap",
  "description": "Live Bitcoin price, market cap, trading volume and cryptocurrency data.",
  "url": "https://cryptotracker.example.com/currencies/bitcoin/",
  "publisher": {{
    "@type": "Organization",
    "name": "CryptoTracker",
    "logo": {{
      "@type": "ImageObject",
      "url": "https://cryptotracker.example.com/images/logo.png"
    }}
  }},
  "mainEntity": {{
    "@type": "ExchangeRateSpecification",
    "currency": "BTC",
    "currentExchangeRate": {{
      "@type": "UnitPriceSpecification",
      "price": "{data['price_usd']}",
      "priceCurrency": "USD"
    }}
  }}
}}
</script>
<script type="application/ld+json">
{{
  "@context": "https://schema.org",
  "@type": "BreadcrumbList",
  "itemListElement": [
    {{"@type": "ListItem", "position": 1, "name": "Cryptocurrencies", "item": "https://cryptotracker.example.com/"}},
    {{"@type": "ListItem", "position": 2, "name": "Coins", "item": "https://cryptotracker.example.com/coins/"}},
    {{"@type": "ListItem", "position": 3, "name": "Bitcoin", "item": "https://cryptotracker.example.com/currencies/bitcoin/"}}
  ]
}}
</script>
<!-- Google Tag Manager -->
<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{'gtm.start':new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src='https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);}})(window,document,'script','dataLayer','GTM-XXXXXX');</script>
<!-- End Google Tag Manager -->
<!-- Google Analytics 4 -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XXXXXXXXXX"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-XXXXXXXXXX',{{'page_title':'Bitcoin Price','page_location':'https://cryptotracker.example.com/currencies/bitcoin/','custom_map':{{'dimension1':'crypto_name','dimension2':'price_view_type'}}}});gtag('event','page_view',{{'crypto_name':'bitcoin','price_view_type':'detail'}});</script>
<!-- Facebook Pixel -->
<script>!function(f,b,e,v,n,t,s){{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?n.callMethod.apply(n,arguments):n.queue.push(arguments)}};if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';n.queue=[];t=b.createElement(e);t.async=!0;t.src=v;s=b.getElementsByTagName(e)[0];s.parentNode.insertBefore(t,s)}}(window,document,'script','https://connect.facebook.net/en_US/fbevents.js');fbq('init','123456789012345');fbq('track','PageView');fbq('track','ViewContent',{{'content_name':'Bitcoin','content_category':'Cryptocurrency','content_type':'coin_detail','value':{data['price_usd']},'currency':'USD'}});</script>
<noscript><img height="1" width="1" style="display:none" src="https://www.facebook.com/tr?id=123456789012345&ev=PageView&noscript=1"/></noscript>
<!-- Twitter Universal Website Tag -->
<script>!function(e,t,n,s,u,a){{e.twq||(s=e.twq=function(){{s.exe?s.exe.apply(s,arguments):s.queue.push(arguments);}},s.version='1.1',s.queue=[],u=t.createElement(n),u.async=!0,u.src='https://static.ads-twitter.com/uwt.js',a=t.getElementsByTagName(n)[0],a.parentNode.insertBefore(u,a))}}(window,document,'script');twq('config','xxxxx');</script>
<!-- Hotjar Tracking -->
<script>(function(h,o,t,j,a,r){{h.hj=h.hj||function(){{(h.hj.q=h.hj.q||[]).push(arguments)}};h._hjSettings={{hjid:1234567,hjsv:6}};a=o.getElementsByTagName('head')[0];r=o.createElement('script');r.async=1;r.src=t+h._hjSettings.hjid+j+h._hjSettings.hjsv;a.appendChild(r);}})(window,document,'https://static.hotjar.com/c/hotjar-','.js?sv=');</script>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
html{{scroll-behavior:smooth;-webkit-text-size-adjust:100%;font-size:16px}}
body{{font-family:'Inter',system-ui,-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Oxygen,Ubuntu,sans-serif;background-color:#0d1117;color:#c9d1d9;line-height:1.6;min-height:100vh;overflow-x:hidden;-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}}
a{{color:#58a6ff;text-decoration:none;transition:color .2s ease}}
a:hover{{color:#79c0ff;text-decoration:underline}}
.container{{max-width:1400px;margin:0 auto;padding:0 24px}}
.header{{background:linear-gradient(180deg,#161b22 0%,#0d1117 100%);border-bottom:1px solid #21262d;position:sticky;top:0;z-index:1000;backdrop-filter:blur(12px)}}
.header-top{{display:flex;align-items:center;justify-content:space-between;padding:8px 0;font-size:12px;color:#8b949e;border-bottom:1px solid #21262d}}
.header-main{{display:flex;align-items:center;justify-content:space-between;padding:12px 0}}
.logo{{font-size:24px;font-weight:800;background:linear-gradient(135deg,#58a6ff,#bc8cff);-webkit-background-clip:text;-webkit-text-fill-color:transparent}}
.nav-links{{display:flex;gap:24px;list-style:none}}
.nav-links a{{color:#c9d1d9;font-weight:500;font-size:14px;padding:8px 0}}
.nav-links a:hover{{color:#58a6ff;text-decoration:none}}
.search-bar{{background:#21262d;border:1px solid #30363d;border-radius:8px;padding:8px 16px;color:#c9d1d9;width:300px;font-size:14px}}
.cookie-banner{{position:fixed;bottom:0;left:0;right:0;background:#161b22;border-top:2px solid #58a6ff;padding:20px;z-index:10000;display:flex;align-items:center;justify-content:space-between;gap:20px;font-size:13px;box-shadow:0 -4px 20px rgba(0,0,0,.5)}}
.cookie-banner .btn-accept{{background:#58a6ff;color:#fff;border:none;padding:10px 24px;border-radius:6px;font-weight:600;cursor:pointer}}
.cookie-banner .btn-settings{{background:transparent;color:#58a6ff;border:1px solid #58a6ff;padding:10px 24px;border-radius:6px;cursor:pointer}}
.ad-banner{{background:linear-gradient(90deg,#1a1f35,#2a1f4e);border:1px solid #30363d;border-radius:12px;padding:16px 24px;margin:16px 0;text-align:center;position:relative;overflow:hidden}}
.ad-banner::before{{content:"AD";position:absolute;top:4px;right:8px;font-size:10px;color:#8b949e;background:#21262d;padding:2px 6px;border-radius:3px}}
.breadcrumb{{padding:16px 0;font-size:13px;color:#8b949e}}
.breadcrumb a{{color:#8b949e}}
.breadcrumb span{{margin:0 8px}}
.price-header{{display:flex;align-items:flex-start;gap:16px;padding:24px 0}}
.coin-logo{{width:48px;height:48px;border-radius:50%;background:#f7931a}}
.coin-name{{font-size:28px;font-weight:700;color:#f0f6fc}}
.coin-symbol{{font-size:14px;color:#8b949e;background:#21262d;padding:4px 8px;border-radius:4px;margin-left:8px}}
.coin-rank{{font-size:12px;color:#f0f6fc;background:#30363d;padding:2px 8px;border-radius:4px}}
.price-main{{font-size:36px;font-weight:800;color:#f0f6fc;margin:16px 0 8px}}
.price-change{{font-size:16px;font-weight:600;padding:4px 8px;border-radius:4px}}
.price-change.positive{{color:#16c784;background:rgba(22,199,132,.1)}}
.price-change.negative{{color:#ea3943;background:rgba(234,57,67,.1)}}
.stats-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin:24px 0;padding:24px 0;border-top:1px solid #21262d;border-bottom:1px solid #21262d}}
.stat-item{{padding:12px}}
.stat-label{{font-size:12px;color:#8b949e;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px}}
.stat-value{{font-size:18px;font-weight:600;color:#f0f6fc}}
.main-content{{display:grid;grid-template-columns:1fr 340px;gap:32px;padding:32px 0}}
.chart-section{{background:#161b22;border:1px solid #21262d;border-radius:12px;padding:24px}}
.chart-tabs{{display:flex;gap:8px;margin-bottom:16px}}
.chart-tab{{padding:6px 16px;border-radius:6px;font-size:13px;cursor:pointer;background:#21262d;color:#8b949e;border:none}}
.chart-tab.active{{background:#58a6ff;color:#fff}}
.chart-placeholder{{height:400px;background:#0d1117;border-radius:8px;display:flex;align-items:center;justify-content:center;color:#30363d;font-size:14px}}
.sidebar{{display:flex;flex-direction:column;gap:24px}}
.sidebar-card{{background:#161b22;border:1px solid #21262d;border-radius:12px;padding:20px}}
.sidebar-title{{font-size:16px;font-weight:700;color:#f0f6fc;margin-bottom:16px;padding-bottom:12px;border-bottom:1px solid #21262d}}
.trending-item{{display:flex;align-items:center;justify-content:space-between;padding:10px 0;border-bottom:1px solid #21262d}}
.trending-item:last-child{{border-bottom:none}}
.newsletter-popup{{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:#161b22;border:2px solid #58a6ff;border-radius:16px;padding:40px;z-index:9999;width:480px;text-align:center;display:none;box-shadow:0 20px 60px rgba(0,0,0,.8)}}
.newsletter-popup h3{{font-size:22px;margin-bottom:8px;color:#f0f6fc}}
.newsletter-popup .email-input{{width:100%;padding:12px 16px;border-radius:8px;border:1px solid #30363d;background:#21262d;color:#c9d1d9;margin:16px 0;font-size:14px}}
.newsletter-popup .subscribe-btn{{width:100%;padding:12px;background:linear-gradient(135deg,#58a6ff,#bc8cff);color:#fff;border:none;border-radius:8px;font-weight:700;font-size:16px;cursor:pointer}}
.overlay{{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.7);z-index:9998;display:none}}
.converter-widget{{background:#161b22;border:1px solid #21262d;border-radius:12px;padding:20px;margin:24px 0}}
.converter-input{{display:flex;gap:12px;align-items:center}}
.converter-input input{{flex:1;padding:10px;background:#21262d;border:1px solid #30363d;border-radius:6px;color:#c9d1d9}}
.markets-table{{width:100%;border-collapse:collapse;margin:24px 0}}
.markets-table th{{text-align:left;padding:12px 16px;font-size:12px;color:#8b949e;text-transform:uppercase;background:#161b22;border-bottom:2px solid #21262d}}
.markets-table td{{padding:12px 16px;border-bottom:1px solid #21262d;font-size:14px}}
.info-section{{background:#161b22;border:1px solid #21262d;border-radius:12px;padding:32px;margin:32px 0}}
.info-section h2{{font-size:22px;font-weight:700;margin-bottom:16px;color:#f0f6fc}}
.info-section p{{color:#8b949e;line-height:1.8;margin-bottom:16px}}
.faq-section{{margin:32px 0}}
.faq-item{{border:1px solid #21262d;border-radius:8px;margin-bottom:8px;overflow:hidden}}
.faq-question{{padding:16px 20px;background:#161b22;cursor:pointer;font-weight:600;display:flex;justify-content:space-between;align-items:center}}
.faq-answer{{padding:0 20px 16px;color:#8b949e;display:none}}
.footer{{background:#0d1117;border-top:1px solid #21262d;padding:48px 0 24px;margin-top:64px}}
.footer-grid{{display:grid;grid-template-columns:repeat(5,1fr);gap:32px;margin-bottom:40px}}
.footer-col h4{{color:#f0f6fc;font-size:14px;margin-bottom:16px;text-transform:uppercase;letter-spacing:1px}}
.footer-col a{{display:block;color:#8b949e;font-size:13px;padding:4px 0}}
.footer-bottom{{display:flex;justify-content:space-between;align-items:center;padding-top:24px;border-top:1px solid #21262d;font-size:12px;color:#484f58}}
.social-links{{display:flex;gap:16px}}
.social-links a{{color:#8b949e;font-size:18px}}
@media(max-width:1024px){{.main-content{{grid-template-columns:1fr}}.stats-grid{{grid-template-columns:repeat(2,1fr)}}.footer-grid{{grid-template-columns:repeat(3,1fr)}}.newsletter-popup{{width:90%;max-width:400px}}}}
@media(max-width:640px){{.header-top{{display:none}}.nav-links{{display:none}}.search-bar{{width:100%}}.price-main{{font-size:28px}}.stats-grid{{grid-template-columns:1fr}}.footer-grid{{grid-template-columns:repeat(2,1fr)}}.cookie-banner{{flex-direction:column;text-align:center}}}}
</style>
</head>
<body>
<!-- Google Tag Manager (noscript) -->
<noscript><iframe src="https://www.googletagmanager.com/ns.html?id=GTM-XXXXXX" height="0" width="0" style="display:none;visibility:hidden"></iframe></noscript>

<!-- Cookie Consent Banner -->
<div class="cookie-banner" id="cookieConsent">
    <div>
        <strong>We value your privacy</strong>
        <p>We use cookies and similar technologies to enhance your browsing experience, serve personalized ads or content, and analyze our traffic. By clicking "Accept All", you consent to our use of cookies. Read our <a href="/privacy-policy">Privacy Policy</a> and <a href="/cookie-policy">Cookie Policy</a> for more information.</p>
    </div>
    <div style="display:flex;gap:12px;flex-shrink:0">
        <button class="btn-settings" onclick="showCookieSettings()">Cookie Settings</button>
        <button class="btn-accept" onclick="acceptCookies()">Accept All</button>
    </div>
</div>

<!-- Header -->
<header class="header">
    <div class="container">
        <div class="header-top">
            <div style="display:flex;gap:24px;align-items:center">
                <span>Coins: <strong>14,832</strong></span>
                <span>Exchanges: <strong>742</strong></span>
                <span>Market Cap: <strong>$3.45T</strong></span>
                <span>24h Vol: <strong>$142.8B</strong></span>
                <span>Dominance: <strong>BTC 54.2% ETH 17.8%</strong></span>
                <span>Gas: <strong>12 Gwei</strong></span>
            </div>
            <div style="display:flex;gap:16px;align-items:center">
                <a href="/portfolio">Portfolio</a>
                <a href="/watchlist">Watchlist</a>
                <a href="/login">Log In</a>
                <a href="/register" style="background:#58a6ff;color:#fff;padding:4px 12px;border-radius:4px">Sign Up</a>
            </div>
        </div>
        <div class="header-main">
            <div style="display:flex;align-items:center;gap:32px">
                <a href="/" class="logo">CryptoTracker</a>
                <nav>
                    <ul class="nav-links">
                        <li><a href="/cryptocurrencies">Cryptocurrencies</a></li>
                        <li><a href="/exchanges">Exchanges</a></li>
                        <li><a href="/nft">NFT</a></li>
                        <li><a href="/defi">DeFi</a></li>
                        <li><a href="/portfolio">Portfolio</a></li>
                        <li><a href="/watchlist">Watchlist</a></li>
                        <li><a href="/learn">Learn</a></li>
                        <li><a href="/news">News</a></li>
                        <li><a href="/products">Products</a></li>
                    </ul>
                </nav>
            </div>
            <div style="display:flex;gap:12px;align-items:center">
                <input type="text" class="search-bar" placeholder="Search coins, exchanges, NFTs...">
                <button style="background:#21262d;border:1px solid #30363d;border-radius:8px;padding:8px 12px;color:#8b949e;cursor:pointer">EN</button>
                <button style="background:#21262d;border:1px solid #30363d;border-radius:8px;padding:8px 12px;color:#8b949e;cursor:pointer">USD</button>
            </div>
        </div>
    </div>
</header>

<!-- Top Ad Banner -->
<div class="container">
    <div class="ad-banner">
        <div style="display:flex;align-items:center;justify-content:center;gap:24px">
            <img src="/static/images/ads/exchange-promo.png" alt="Trade Bitcoin" width="728" height="90" loading="lazy" style="border-radius:8px">
            <div>
                <p style="font-size:18px;font-weight:700;color:#f0f6fc">Trade Bitcoin with 0% fees!</p>
                <p style="color:#8b949e;font-size:13px">New users get $100 in free trading credits. Terms apply.</p>
                <a href="https://exchange.example.com/promo" style="display:inline-block;margin-top:8px;background:#16c784;color:#fff;padding:8px 20px;border-radius:6px;font-weight:600;font-size:13px">Start Trading &rarr;</a>
            </div>
        </div>
    </div>
</div>

<main class="container">
    <!-- Breadcrumb -->
    <div class="breadcrumb">
        <a href="/">Cryptocurrencies</a> <span>&rsaquo;</span>
        <a href="/coins">Coins</a> <span>&rsaquo;</span>
        <span style="color:#c9d1d9">Bitcoin</span>
    </div>

    <!-- Price Header -->
    <div class="price-header">
        <div class="coin-logo"></div>
        <div>
            <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
                <span class="coin-name">Bitcoin</span>
                <span class="coin-symbol">BTC</span>
                <span class="coin-rank">Rank #1</span>
                <span style="font-size:12px;color:#8b949e;background:#21262d;padding:2px 8px;border-radius:4px">Coin</span>
                <span style="font-size:12px;color:#8b949e">On 3,142,857 watchlists</span>
            </div>
            <div class="price-main" data-price="{data['price_usd']}" data-fetched="{fetched}">${price}</div>
            <div style="display:flex;align-items:center;gap:12px">
                <span class="price-change {'positive' if data['change_24h'] >= 0 else 'negative'}">{arrow} {change}% <span style="font-size:12px;color:#8b949e">(24h)</span></span>
                <span style="font-size:13px;color:#8b949e">Updated {fetched}</span>
            </div>
        </div>
    </div>

    <!-- Stats Grid -->
    <div class="stats-grid">
        <div class="stat-item">
            <div class="stat-label">Market Cap</div>
            <div class="stat-value">${market_cap}</div>
            <div style="font-size:12px;color:{'#16c784' if data['change_24h'] >= 0 else '#ea3943'}">{arrow} {change}%</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">24 Hour Trading Vol</div>
            <div class="stat-value">$48,234,567,890</div>
            <div style="font-size:12px;color:#16c784">&9650; 12.4%</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Fully Diluted Valuation</div>
            <div class="stat-value">$2,172,589,000,000</div>
        </div>
        <div class="stat-item">
            <div class="stat-label">Circulating Supply</div>
            <div class="stat-value">19,934,271 BTC</div>
            <div style="font-size:12px;color:#8b949e">Max Supply: 21,000,000</div>
        </div>
    </div>

    <!-- Main Content + Sidebar -->
    <div class="main-content">
        <div>
            <!-- Chart Section -->
            <div class="chart-section">
                <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
                    <h2 style="font-size:18px;font-weight:700;color:#f0f6fc">Bitcoin Price Chart (BTC/USD)</h2>
                    <div class="chart-tabs">
                        <button class="chart-tab">1H</button>
                        <button class="chart-tab active">24H</button>
                        <button class="chart-tab">7D</button>
                        <button class="chart-tab">1M</button>
                        <button class="chart-tab">3M</button>
                        <button class="chart-tab">1Y</button>
                        <button class="chart-tab">ALL</button>
                    </div>
                </div>
                <div class="chart-placeholder">[Interactive TradingView Chart — BTC/USD — Powered by CryptoTracker]</div>
            </div>

            <!-- Converter Widget -->
            <div class="converter-widget">
                <h3 style="font-size:16px;font-weight:600;margin-bottom:12px;color:#f0f6fc">BTC to USD Converter</h3>
                <div class="converter-input">
                    <input type="number" value="1" placeholder="BTC">
                    <span style="color:#8b949e">=</span>
                    <input type="text" value="${price}" readonly>
                </div>
            </div>

            <!-- Markets Table -->
            <div style="margin:32px 0">
                <h2 style="font-size:20px;font-weight:700;margin-bottom:16px;color:#f0f6fc">Bitcoin Markets</h2>
                <table class="markets-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Exchange</th>
                            <th>Pair</th>
                            <th>Price</th>
                            <th>Volume (24h)</th>
                            <th>Spread</th>
                            <th>Trust Score</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr><td>1</td><td>Binance</td><td>BTC/USDT</td><td>${price}</td><td>$8,234,567,890</td><td>0.01%</td><td style="color:#16c784">&#9679;</td></tr>
                        <tr><td>2</td><td>Coinbase</td><td>BTC/USD</td><td>${price}</td><td>$3,456,789,012</td><td>0.02%</td><td style="color:#16c784">&#9679;</td></tr>
                        <tr><td>3</td><td>Kraken</td><td>BTC/USD</td><td>${price}</td><td>$2,345,678,901</td><td>0.01%</td><td style="color:#16c784">&#9679;</td></tr>
                        <tr><td>4</td><td>OKX</td><td>BTC/USDT</td><td>${price}</td><td>$4,567,890,123</td><td>0.02%</td><td style="color:#16c784">&#9679;</td></tr>
                        <tr><td>5</td><td>Bybit</td><td>BTC/USDT</td><td>${price}</td><td>$3,210,987,654</td><td>0.01%</td><td style="color:#16c784">&#9679;</td></tr>
                        <tr><td>6</td><td>Bitfinex</td><td>BTC/USD</td><td>${price}</td><td>$1,234,567,890</td><td>0.03%</td><td style="color:#f5a623">&#9679;</td></tr>
                        <tr><td>7</td><td>KuCoin</td><td>BTC/USDT</td><td>${price}</td><td>$987,654,321</td><td>0.02%</td><td style="color:#16c784">&#9679;</td></tr>
                        <tr><td>8</td><td>Gate.io</td><td>BTC/USDT</td><td>${price}</td><td>$876,543,210</td><td>0.03%</td><td style="color:#f5a623">&#9679;</td></tr>
                        <tr><td>9</td><td>Bitstamp</td><td>BTC/USD</td><td>${price}</td><td>$654,321,098</td><td>0.02%</td><td style="color:#16c784">&#9679;</td></tr>
                        <tr><td>10</td><td>Gemini</td><td>BTC/USD</td><td>${price}</td><td>$543,210,987</td><td>0.04%</td><td style="color:#16c784">&#9679;</td></tr>
                    </tbody>
                </table>
            </div>

            <!-- About Section -->
            <div class="info-section">
                <h2>What is Bitcoin (BTC)?</h2>
                <p>Bitcoin is the first and most well-known cryptocurrency, created in 2009 by an anonymous person or group using the pseudonym Satoshi Nakamoto. It operates on a decentralized peer-to-peer network using blockchain technology to enable direct transactions without intermediaries like banks or governments.</p>
                <p>Bitcoin uses a proof-of-work consensus mechanism where miners compete to validate transactions and add new blocks to the blockchain. The total supply of Bitcoin is capped at 21 million coins, with approximately 19.9 million already mined. New bitcoins are created through mining rewards, which halve approximately every four years in an event known as the "halving."</p>
                <p>Bitcoin is widely regarded as a store of value and is often compared to digital gold. It can be divided into smaller units called satoshis (1 BTC = 100,000,000 satoshis), making it suitable for both large and small transactions. Major companies and institutional investors have increasingly adopted Bitcoin as part of their investment portfolios.</p>
                <h3 style="margin:24px 0 12px;color:#f0f6fc">Key Features</h3>
                <ul style="color:#8b949e;padding-left:20px;line-height:2">
                    <li>Decentralized: No single entity controls the Bitcoin network</li>
                    <li>Limited Supply: Maximum of 21 million BTC will ever exist</li>
                    <li>Pseudonymous: Transactions are recorded on a public ledger but don't require personal identification</li>
                    <li>Immutable: Once confirmed, transactions cannot be reversed or altered</li>
                    <li>Global: Can be sent anywhere in the world without intermediaries</li>
                    <li>Divisible: Each bitcoin can be divided into 100 million satoshis</li>
                </ul>
            </div>

            <!-- Historical Data Section -->
            <div class="info-section">
                <h2>Bitcoin Historical Price Data</h2>
                <table class="markets-table">
                    <thead>
                        <tr><th>Date</th><th>Open</th><th>High</th><th>Low</th><th>Close</th><th>Volume</th></tr>
                    </thead>
                    <tbody>
                        <tr><td>May 09, 2026</td><td>$102,456</td><td>$104,890</td><td>$101,234</td><td>$103,567</td><td>$45.2B</td></tr>
                        <tr><td>May 08, 2026</td><td>$101,234</td><td>$103,456</td><td>$100,123</td><td>$102,456</td><td>$42.8B</td></tr>
                        <tr><td>May 07, 2026</td><td>$99,876</td><td>$102,345</td><td>$98,765</td><td>$101,234</td><td>$38.9B</td></tr>
                        <tr><td>May 06, 2026</td><td>$98,456</td><td>$100,789</td><td>$97,654</td><td>$99,876</td><td>$36.4B</td></tr>
                        <tr><td>May 05, 2026</td><td>$97,123</td><td>$99,456</td><td>$96,543</td><td>$98,456</td><td>$34.1B</td></tr>
                        <tr><td>May 04, 2026</td><td>$96,789</td><td>$98,234</td><td>$95,678</td><td>$97,123</td><td>$31.7B</td></tr>
                        <tr><td>May 03, 2026</td><td>$95,432</td><td>$97,890</td><td>$94,567</td><td>$96,789</td><td>$29.3B</td></tr>
                    </tbody>
                </table>
            </div>

            <!-- FAQ Section -->
            <div class="faq-section">
                <h2 style="font-size:22px;font-weight:700;margin-bottom:16px;color:#f0f6fc">Frequently Asked Questions</h2>
                <div class="faq-item">
                    <div class="faq-question">What is the current price of Bitcoin? <span>+</span></div>
                    <div class="faq-answer">The current price of Bitcoin (BTC) is ${price} USD with a 24-hour trading volume of over $48 billion. Bitcoin price has changed {change}% in the last 24 hours.</div>
                </div>
                <div class="faq-item">
                    <div class="faq-question">How is the price of Bitcoin determined? <span>+</span></div>
                    <div class="faq-answer">Bitcoin's price is determined by supply and demand on cryptocurrency exchanges worldwide. Unlike traditional currencies, it is not controlled by any central bank or government. Factors that influence Bitcoin's price include market sentiment, regulatory news, adoption rates, mining difficulty, and macroeconomic factors.</div>
                </div>
                <div class="faq-item">
                    <div class="faq-question">Is Bitcoin a good investment? <span>+</span></div>
                    <div class="faq-answer">Bitcoin is a highly volatile asset. While it has historically shown significant long-term appreciation, past performance does not guarantee future results. Always do your own research and consider your risk tolerance before investing. This is not financial advice.</div>
                </div>
                <div class="faq-item">
                    <div class="faq-question">How can I buy Bitcoin? <span>+</span></div>
                    <div class="faq-answer">You can buy Bitcoin on cryptocurrency exchanges like Coinbase, Binance, Kraken, and many others. You'll need to create an account, complete identity verification, and fund your account with fiat currency or other cryptocurrencies.</div>
                </div>
                <div class="faq-item">
                    <div class="faq-question">What is Bitcoin halving? <span>+</span></div>
                    <div class="faq-answer">Bitcoin halving is an event that occurs approximately every four years (every 210,000 blocks) where the reward for mining new blocks is cut in half. This mechanism ensures that Bitcoin's total supply never exceeds 21 million coins. The most recent halving occurred in April 2024, reducing the block reward from 6.25 to 3.125 BTC.</div>
                </div>
                <div class="faq-item">
                    <div class="faq-question">What is Bitcoin mining? <span>+</span></div>
                    <div class="faq-answer">Bitcoin mining is the process of using specialized computer hardware to validate transactions and add new blocks to the Bitcoin blockchain. Miners compete to solve complex mathematical puzzles, and the first to find a valid solution earns the block reward plus transaction fees.</div>
                </div>
            </div>

            <!-- Related News -->
            <div class="info-section">
                <h2>Latest Bitcoin News</h2>
                <div style="display:flex;flex-direction:column;gap:20px">
                    <div style="display:flex;gap:16px;padding-bottom:20px;border-bottom:1px solid #21262d">
                        <div style="width:120px;height:80px;background:#21262d;border-radius:8px;flex-shrink:0"></div>
                        <div>
                            <h3 style="font-size:15px;color:#f0f6fc;margin-bottom:4px">Bitcoin ETF Inflows Surge Past $500M as Institutional Demand Grows</h3>
                            <p style="font-size:13px;color:#8b949e">BlackRock's iShares Bitcoin Trust leads the pack with record single-day inflows...</p>
                            <span style="font-size:11px;color:#484f58">CryptoNews &bull; 2 hours ago</span>
                        </div>
                    </div>
                    <div style="display:flex;gap:16px;padding-bottom:20px;border-bottom:1px solid #21262d">
                        <div style="width:120px;height:80px;background:#21262d;border-radius:8px;flex-shrink:0"></div>
                        <div>
                            <h3 style="font-size:15px;color:#f0f6fc;margin-bottom:4px">Federal Reserve Holds Rates Steady, Bitcoin Responds with Rally</h3>
                            <p style="font-size:13px;color:#8b949e">The Fed's decision to maintain current interest rates has been seen as bullish for risk assets...</p>
                            <span style="font-size:11px;color:#484f58">Bloomberg Crypto &bull; 5 hours ago</span>
                        </div>
                    </div>
                    <div style="display:flex;gap:16px;padding-bottom:20px;border-bottom:1px solid #21262d">
                        <div style="width:120px;height:80px;background:#21262d;border-radius:8px;flex-shrink:0"></div>
                        <div>
                            <h3 style="font-size:15px;color:#f0f6fc;margin-bottom:4px">El Salvador's Bitcoin Strategy: Two Years Later, What We've Learned</h3>
                            <p style="font-size:13px;color:#8b949e">A comprehensive look at the Central American nation's experiment with Bitcoin as legal tender...</p>
                            <span style="font-size:11px;color:#484f58">The Block &bull; 8 hours ago</span>
                        </div>
                    </div>
                    <div style="display:flex;gap:16px">
                        <div style="width:120px;height:80px;background:#21262d;border-radius:8px;flex-shrink:0"></div>
                        <div>
                            <h3 style="font-size:15px;color:#f0f6fc;margin-bottom:4px">MicroStrategy Adds Another 12,000 BTC to Holdings, Total Exceeds 250,000</h3>
                            <p style="font-size:13px;color:#8b949e">Michael Saylor's company continues its aggressive Bitcoin accumulation strategy...</p>
                            <span style="font-size:11px;color:#484f58">CoinDesk &bull; 12 hours ago</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Sidebar -->
        <div class="sidebar">
            <!-- Ad Card -->
            <div class="ad-banner" style="margin:0">
                <p style="font-size:16px;font-weight:700;color:#f0f6fc;margin-bottom:8px">Earn up to 8% APY</p>
                <p style="font-size:13px;color:#8b949e;margin-bottom:12px">Stake your BTC and earn passive income</p>
                <a href="#" style="display:block;background:#58a6ff;color:#fff;padding:10px;border-radius:6px;text-align:center;font-weight:600">Start Earning</a>
            </div>

            <!-- BTC Info Card -->
            <div class="sidebar-card">
                <div class="sidebar-title">Bitcoin Info</div>
                <div style="display:flex;flex-direction:column;gap:12px;font-size:13px">
                    <div style="display:flex;justify-content:space-between"><span style="color:#8b949e">Website</span><a href="https://bitcoin.org">bitcoin.org</a></div>
                    <div style="display:flex;justify-content:space-between"><span style="color:#8b949e">Whitepaper</span><a href="#">bitcoin.pdf</a></div>
                    <div style="display:flex;justify-content:space-between"><span style="color:#8b949e">GitHub</span><a href="#">bitcoin/bitcoin</a></div>
                    <div style="display:flex;justify-content:space-between"><span style="color:#8b949e">Block Explorer</span><a href="#">blockchain.com</a></div>
                    <div style="display:flex;justify-content:space-between"><span style="color:#8b949e">Community</span><a href="#">r/Bitcoin</a></div>
                    <div style="display:flex;justify-content:space-between"><span style="color:#8b949e">Category</span><span style="color:#c9d1d9">Cryptocurrency</span></div>
                    <div style="display:flex;justify-content:space-between"><span style="color:#8b949e">Algorithm</span><span style="color:#c9d1d9">SHA-256</span></div>
                    <div style="display:flex;justify-content:space-between"><span style="color:#8b949e">Consensus</span><span style="color:#c9d1d9">Proof of Work</span></div>
                </div>
            </div>

            <!-- Trending Coins -->
            <div class="sidebar-card">
                <div class="sidebar-title">Trending Coins</div>
                <div class="trending-item"><span>1. Ethereum (ETH)</span><span style="color:#16c784">+3.2%</span></div>
                <div class="trending-item"><span>2. Solana (SOL)</span><span style="color:#16c784">+5.7%</span></div>
                <div class="trending-item"><span>3. Dogecoin (DOGE)</span><span style="color:#ea3943">-1.4%</span></div>
                <div class="trending-item"><span>4. Cardano (ADA)</span><span style="color:#16c784">+2.1%</span></div>
                <div class="trending-item"><span>5. XRP (XRP)</span><span style="color:#16c784">+1.8%</span></div>
                <div class="trending-item"><span>6. Polkadot (DOT)</span><span style="color:#ea3943">-0.9%</span></div>
                <div class="trending-item"><span>7. Chainlink (LINK)</span><span style="color:#16c784">+4.3%</span></div>
                <div class="trending-item"><span>8. Avalanche (AVAX)</span><span style="color:#16c784">+6.2%</span></div>
            </div>

            <!-- Another Ad -->
            <div class="ad-banner" style="margin:0">
                <p style="font-size:16px;font-weight:700;color:#f0f6fc;margin-bottom:8px">Free Crypto Course</p>
                <p style="font-size:13px;color:#8b949e;margin-bottom:12px">Learn blockchain fundamentals and start your crypto journey today</p>
                <a href="#" style="display:block;background:linear-gradient(135deg,#f7931a,#f5a623);color:#fff;padding:10px;border-radius:6px;text-align:center;font-weight:600">Enroll Now &mdash; It's Free</a>
            </div>

            <!-- Supply Info -->
            <div class="sidebar-card">
                <div class="sidebar-title">Supply Information</div>
                <div style="margin-bottom:12px">
                    <div style="display:flex;justify-content:space-between;font-size:13px;margin-bottom:4px"><span style="color:#8b949e">Circulating</span><span style="color:#c9d1d9">19,934,271 BTC</span></div>
                    <div style="background:#21262d;border-radius:4px;height:8px;overflow:hidden"><div style="background:#58a6ff;height:100%;width:94.9%;border-radius:4px"></div></div>
                </div>
                <div style="display:flex;flex-direction:column;gap:8px;font-size:13px">
                    <div style="display:flex;justify-content:space-between"><span style="color:#8b949e">Max Supply</span><span style="color:#c9d1d9">21,000,000 BTC</span></div>
                    <div style="display:flex;justify-content:space-between"><span style="color:#8b949e">Total Supply</span><span style="color:#c9d1d9">19,934,271 BTC</span></div>
                    <div style="display:flex;justify-content:space-between"><span style="color:#8b949e">% Mined</span><span style="color:#c9d1d9">94.9%</span></div>
                </div>
            </div>

            <!-- Social Links -->
            <div class="sidebar-card">
                <div class="sidebar-title">Community</div>
                <div style="display:flex;flex-direction:column;gap:8px;font-size:13px">
                    <a href="#" style="display:flex;justify-content:space-between;align-items:center;padding:8px 0"><span>Twitter/X</span><span style="color:#8b949e">@bitcoin &bull; 6.2M followers</span></a>
                    <a href="#" style="display:flex;justify-content:space-between;align-items:center;padding:8px 0"><span>Reddit</span><span style="color:#8b949e">r/Bitcoin &bull; 5.8M members</span></a>
                    <a href="#" style="display:flex;justify-content:space-between;align-items:center;padding:8px 0"><span>Telegram</span><span style="color:#8b949e">128K members</span></a>
                    <a href="#" style="display:flex;justify-content:space-between;align-items:center;padding:8px 0"><span>Discord</span><span style="color:#8b949e">95K members</span></a>
                </div>
            </div>
        </div>
    </div>
</main>

<!-- Newsletter Popup -->
<div class="overlay" id="newsletterOverlay"></div>
<div class="newsletter-popup" id="newsletterPopup">
    <button onclick="closeNewsletter()" style="position:absolute;top:16px;right:16px;background:none;border:none;color:#8b949e;font-size:24px;cursor:pointer">&times;</button>
    <h3>Stay Ahead of the Market</h3>
    <p style="color:#8b949e;font-size:14px">Get daily crypto market updates, price alerts, and exclusive analysis delivered to your inbox.</p>
    <input type="email" class="email-input" placeholder="Enter your email address">
    <button class="subscribe-btn">Subscribe Free</button>
    <p style="font-size:11px;color:#484f58;margin-top:12px">By subscribing, you agree to our Terms of Service and Privacy Policy. Unsubscribe at any time.</p>
</div>

<!-- Footer -->
<footer class="footer">
    <div class="container">
        <div class="footer-grid">
            <div class="footer-col">
                <h4>Products</h4>
                <a href="/app">Mobile App</a>
                <a href="/api">API</a>
                <a href="/widgets">Widgets</a>
                <a href="/portfolio-tracker">Portfolio Tracker</a>
                <a href="/price-alerts">Price Alerts</a>
                <a href="/tax-reporting">Tax Reporting</a>
                <a href="/earn">Crypto Earn</a>
                <a href="/card">Crypto Card</a>
            </div>
            <div class="footer-col">
                <h4>Company</h4>
                <a href="/about">About Us</a>
                <a href="/careers">Careers</a>
                <a href="/press">Press</a>
                <a href="/blog">Blog</a>
                <a href="/contact">Contact Us</a>
                <a href="/investors">Investors</a>
                <a href="/legal">Legal</a>
                <a href="/compliance">Compliance</a>
            </div>
            <div class="footer-col">
                <h4>Support</h4>
                <a href="/help">Help Center</a>
                <a href="/faq">FAQ</a>
                <a href="/glossary">Glossary</a>
                <a href="/guides">Guides</a>
                <a href="/status">System Status</a>
                <a href="/security">Security</a>
                <a href="/bug-bounty">Bug Bounty</a>
                <a href="/feedback">Feedback</a>
            </div>
            <div class="footer-col">
                <h4>Resources</h4>
                <a href="/learn">Learn Crypto</a>
                <a href="/research">Research</a>
                <a href="/reports">Reports</a>
                <a href="/podcast">Podcast</a>
                <a href="/newsletter">Newsletter</a>
                <a href="/events">Events</a>
                <a href="/community">Community</a>
                <a href="/partners">Partners</a>
            </div>
            <div class="footer-col">
                <h4>Legal</h4>
                <a href="/terms">Terms of Service</a>
                <a href="/privacy">Privacy Policy</a>
                <a href="/cookie-policy">Cookie Policy</a>
                <a href="/disclaimer">Disclaimer</a>
                <a href="/aml-policy">AML Policy</a>
                <a href="/risk-disclosure">Risk Disclosure</a>
                <a href="/gdpr">GDPR</a>
                <a href="/licenses">Licenses</a>
            </div>
        </div>
        <div class="footer-bottom">
            <div>
                <p>&copy; 2026 CryptoTracker. All rights reserved.</p>
                <p style="margin-top:4px">Cryptocurrency prices are provided for informational purposes only and should not be construed as financial advice. Trading cryptocurrencies involves substantial risk of loss and is not suitable for every investor.</p>
            </div>
            <div class="social-links">
                <a href="#" aria-label="Twitter">&#120143;</a>
                <a href="#" aria-label="Facebook">f</a>
                <a href="#" aria-label="Instagram">&#9737;</a>
                <a href="#" aria-label="LinkedIn">in</a>
                <a href="#" aria-label="YouTube">&#9654;</a>
                <a href="#" aria-label="Telegram">&#9992;</a>
                <a href="#" aria-label="Discord">&#9741;</a>
            </div>
        </div>
    </div>
</footer>

<!-- Intercom Chat Widget -->
<script>window.intercomSettings={{api_base:"https://api-iam.intercom.io",app_id:"abc123de",custom_launcher_selector:".intercom-launcher"}};</script>
<script>(function(){{var w=window;var ic=w.Intercom;if(typeof ic==="function"){{ic('reattach_activator');ic('update',w.intercomSettings);}}else{{var d=document;var i=function(){{i.c(arguments);}};i.q=[];i.c=function(args){{i.q.push(args);}};w.Intercom=i;var l=function(){{var s=d.createElement('script');s.type='text/javascript';s.async=true;s.src='https://widget.intercom.io/widget/abc123de';var x=d.getElementsByTagName('script')[0];x.parentNode.insertBefore(s,x);}};if(document.readyState==='complete'){{l();}}else if(w.attachEvent){{w.attachEvent('onload',l);}}else{{w.addEventListener('load',l,false);}}}}}})()</script>
<!-- Segment Analytics -->
<script>!function(){{var analytics=window.analytics=window.analytics||[];if(!analytics.initialize)if(analytics.invoked)window.console&&console.error&&console.error("Segment snippet included twice.");else{{analytics.invoked=!0;analytics.methods=["trackSubmit","trackClick","trackLink","trackForm","pageview","identify","reset","group","track","ready","alias","debug","page","once","off","on","addSourceMiddleware","addIntegrationMiddleware","setAnonymousId","addDestinationMiddleware"];analytics.factory=function(e){{return function(){{var t=Array.prototype.slice.call(arguments);t.unshift(e);analytics.push(t);return analytics}}}};for(var e=0;e<analytics.methods.length;e++){{var key=analytics.methods[e];analytics[key]=analytics.factory(key)}}analytics.load=function(key,e){{var t=document.createElement("script");t.type="text/javascript";t.async=!0;t.src="https://cdn.segment.com/analytics.js/v1/"+key+"/analytics.min.js";var n=document.getElementsByTagName("script")[0];n.parentNode.insertBefore(t,n);analytics._loadOptions=e}};analytics._writeKey="XXXXXXXXXXXXXXXXXXXX";analytics.SNIPPET_VERSION="4.15.3";analytics.load("XXXXXXXXXXXXXXXXXXXX");analytics.page();}}}})()</script>
<!-- Cookie consent & newsletter popup scripts -->
<script>
function acceptCookies(){{document.getElementById('cookieConsent').style.display='none';document.cookie='cookie_consent=accepted;path=/;max-age=31536000';gtag('consent','update',{{'analytics_storage':'granted','ad_storage':'granted'}})}}
function showCookieSettings(){{window.location.href='/cookie-settings'}}
function closeNewsletter(){{document.getElementById('newsletterPopup').style.display='none';document.getElementById('newsletterOverlay').style.display='none';sessionStorage.setItem('newsletter_dismissed','1')}}
setTimeout(function(){{if(!sessionStorage.getItem('newsletter_dismissed')){{document.getElementById('newsletterPopup').style.display='block';document.getElementById('newsletterOverlay').style.display='block'}}}},5000);
document.querySelectorAll('.faq-question').forEach(function(q){{q.addEventListener('click',function(){{var a=this.nextElementSibling;a.style.display=a.style.display==='block'?'none':'block';this.querySelector('span').textContent=a.style.display==='block'?'-':'+'}});}});
</script>
<script>
window.dataLayer=window.dataLayer||[];
window.dataLayer.push({{'event':'product_view','ecommerce':{{'detail':{{'products':[{{'name':'Bitcoin','id':'bitcoin','price':'{data['price_usd']}','category':'Cryptocurrency','variant':'BTC'}}]}}}}}});
</script>
</body>
</html>"""


def build_acf_response(data: dict) -> str:
    price = f"{data['price_usd']:.2f}"
    change = f"{data['change_24h']:+.2f}"
    market_cap = f"{data['market_cap']:,.0f}"
    fetched = data["fetched_at"]

    return f"""ACF/0.1
id:           acf-action-bitcoin-price
type:         action
title:        Bitcoin Live Price
source:       CoinGecko API
author:       AgentClearfeed
published:    {fetched[:10]}
confidence:   verified
domain:       Cryptocurrency
tags:         bitcoin, price, live, coingecko
conflicts:    none
license:      none
---
ACTION
name:         get_bitcoin_price
source:       CoinGecko
timestamp:    {fetched}
price_usd:    {price}
change_24h:   {change}%
market_cap:   ${market_cap}
confidence:   verified"""


@router.get("/html/bitcoin-price")
def html_bitcoin_price():
    data = fetch_bitcoin_data()
    html = build_bloated_html(data)
    return JSONResponse({"content": html, "data": data})


@router.get("/acf/bitcoin-price")
def acf_bitcoin_price():
    data = fetch_bitcoin_data()
    acf = build_acf_response(data)
    return JSONResponse({"content": acf, "data": data})
