"""Fetch Wikipedia HTML pages and save as static files for Phase 2 testing."""

import argparse
import re
import time
from pathlib import Path

import httpx
import tiktoken

TOPICS = {
    "photosynthesis": "Photosynthesis",
    "roman_empire": "Roman_Empire",
    "tcp_ip": "Transmission_Control_Protocol",
    "jazz": "Jazz",
    "great_wall_of_china": "Great_Wall_of_China",
    "crispr": "CRISPR",
    "theory_of_relativity": "Theory_of_relativity",
    "impressionism": "Impressionism",
    "volcanic_eruptions": "Types_of_volcanic_eruptions",
    "bitcoin": "Bitcoin",
}

WIKIPEDIA_API = "https://en.wikipedia.org/w/api.php"
OUTPUT_DIR = Path(__file__).parent / "raw_sources"
MAX_TOKENS_PER_PAGE = 9000

WIKI_PAGE_HEADER = """\
<!DOCTYPE html>
<html lang="en" class="client-nojs vector-feature-language-in-header-enabled">
<head>
<meta charset="UTF-8">
<title>{title} - Wikipedia</title>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="{title} — From Wikipedia, the free encyclopedia">
<meta name="generator" content="MediaWiki 1.44.0-wmf.4">
<meta property="og:title" content="{title} - Wikipedia">
<meta property="og:type" content="website">
<meta property="og:image" content="https://upload.wikimedia.org/wikipedia/en/8/80/Wikipedia-logo-v2.svg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<link rel="canonical" href="https://en.wikipedia.org/wiki/{article}">
<link rel="alternate" type="application/x-wiki" title="Edit this page" href="/w/index.php?title={article}&action=edit">
<link rel="alternate" hreflang="x-default" href="https://en.wikipedia.org/wiki/{article}">
<link rel="license" href="https://creativecommons.org/licenses/by-sa/4.0/deed.en">
<link rel="apple-touch-icon" href="/static/apple-touch/wikipedia.png">
<link rel="icon" href="/static/favicon/wikipedia.ico">
<link rel="search" type="application/opensearchdescription+xml" href="/w/opensearch_desc.php" title="Wikipedia (en)">
<link rel="stylesheet" href="/w/load.php?lang=en&modules=ext.cite.styles%7Cext.math.styles%7Cext.uls.interlanguage%7Cext.visualEditor.desktopArticleTarget.noscript%7Cext.wikimediaBadges%7Cext.wikimediamessages.styles%7Cjquery.makeCollapsible.styles%7Cmediawiki.page.gallery.styles%7Cskins.vector.icons%2Cstyles%7Cskins.vector.search.codex.styles%7Cwikibase.client.init&only=styles&skin=vector-2022">
<link rel="stylesheet" href="/w/load.php?lang=en&modules=site.styles&only=styles&skin=vector-2022">
<script async src="https://login.wikimedia.org/wiki/Special:CentralAutoLogin/start?type=1x1"></script>
<script>(RLQ=window.RLQ||[]).push(function(){{mw.loader.implement("user.options@12s5i",function($,jQuery,require,module){{mw.user.tokens.set({{"patrolToken":"+\\\\","watchToken":"+\\\\","csrfToken":"+\\\\"}});}});}});</script>
<script async src="/w/load.php?lang=en&modules=startup&only=scripts&raw=1&skin=vector-2022"></script>
<style>
.mw-parser-output {{ font-family: 'Linux Libertine', 'Georgia', 'Times', serif; font-size: 14px; line-height: 1.6; }}
.mw-parser-output .infobox {{ border: 1px solid #a2a9b1; border-spacing: 3px; background-color: #f8f9fa; color: black; margin: 0.5em 0 0.5em 1em; padding: 0.2em; float: right; clear: right; font-size: 88%; line-height: 1.5em; width: 22em; }}
.mw-parser-output .navbox {{ border: 1px solid #a2a9b1; width: 100%; margin: auto; clear: both; font-size: 88%; text-align: center; padding: 1px; }}
.mw-parser-output .sidebar {{ width: 22em; float: right; clear: right; margin: 0.5em 0 1em 1em; background: #f8f9fa; border: 1px solid #aaa; padding: 0.2em; text-align: center; }}
.mw-parser-output .reflist {{ font-size: 90%; margin-bottom: 0.5em; list-style-type: decimal; }}
.mw-parser-output .catlinks {{ border: 1px solid #a2a9b1; background-color: #f8f9fa; padding: 5px; margin-top: 1em; clear: both; }}
.mw-parser-output .toc {{ border: 1px solid #a2a9b1; background-color: #f8f9fa; padding: 7px; font-size: 95%; }}
.mw-parser-output .mw-headline {{ font-weight: bold; }}
.mw-parser-output .hatnote {{ font-style: italic; padding-left: 1.6em; margin-bottom: 0.5em; }}
.mw-parser-output .ambox {{ border: 1px solid #a2a9b1; background-color: #fbfbfb; margin: 0 10%; }}
</style>
</head>
<body class="skin-vector skin-vector-search-vue mediawiki ltr sitedir-ltr mw-hide-empty-elt ns-0 ns-subject mw-editable page-{article} rootpage-{article} vector-feature-language-in-header-enabled vector-feature-language-in-main-page-header-disabled vector-feature-sticky-header-enabled vector-feature-page-tools-pinned-disabled vector-feature-toc-pinned-clientpref-1 vector-feature-main-menu-pinned-disabled vector-feature-limited-width-clientpref-1 vector-feature-limited-width-content-enabled vector-feature-custom-font-size-clientpref-1 vector-feature-appearance-pinned-clientpref-1 vector-feature-night-mode-disabled skin-theme-clientpref-day vector-toc-available">
<div id="mw-page-base" class="noprint"></div>
<div id="mw-head-base" class="noprint"></div>
<div id="mw-navigation" class="noprint" role="navigation" aria-label="Site">
    <div id="mw-head">
        <nav id="p-personal" class="mw-portlet mw-portlet-personal vector-user-links" aria-label="Personal tools">
            <div class="vector-user-links-main">
                <li id="pt-anonuserpage">Not logged in</li>
                <li id="pt-anontalk"><a href="/wiki/Special:MyTalk">Talk</a></li>
                <li id="pt-anoncontribs"><a href="/wiki/Special:MyContributions">Contributions</a></li>
                <li id="pt-createaccount"><a href="/w/index.php?title=Special:CreateAccount">Create account</a></li>
                <li id="pt-login"><a href="/w/index.php?title=Special:UserLogin">Log in</a></li>
            </div>
        </nav>
        <nav id="p-namespaces" class="mw-portlet" aria-label="Namespaces">
            <ul>
                <li id="ca-nstab-main" class="selected"><a href="/wiki/{article}">Article</a></li>
                <li id="ca-talk"><a href="/wiki/Talk:{article}" rel="discussion">Talk</a></li>
            </ul>
        </nav>
        <nav id="p-views" class="mw-portlet" aria-label="Views">
            <ul>
                <li id="ca-view" class="selected"><a href="/wiki/{article}">Read</a></li>
                <li id="ca-edit"><a href="/w/index.php?title={article}&action=edit">Edit</a></li>
                <li id="ca-history"><a href="/w/index.php?title={article}&action=history">View history</a></li>
            </ul>
        </nav>
    </div>
    <div id="mw-panel" class="vector-sidebar-container-no-toc">
        <nav id="p-logo" role="banner"><a class="mw-wiki-logo" href="/wiki/Main_Page" title="Visit the main page"></a></nav>
        <nav id="p-navigation" class="mw-portlet" role="navigation" aria-label="Navigation">
            <h3>Navigation</h3>
            <div class="body">
                <ul>
                    <li><a href="/wiki/Main_Page">Main page</a></li>
                    <li><a href="/wiki/Wikipedia:Contents">Contents</a></li>
                    <li><a href="/wiki/Portal:Current_events">Current events</a></li>
                    <li><a href="/wiki/Special:Random">Random article</a></li>
                    <li><a href="https://donate.wikimedia.org/">Donate to Wikipedia</a></li>
                    <li><a href="/wiki/Wikipedia:About">About Wikipedia</a></li>
                </ul>
            </div>
        </nav>
        <nav id="p-interaction" class="mw-portlet" aria-label="Contribute">
            <h3>Contribute</h3>
            <div class="body">
                <ul>
                    <li><a href="/wiki/Help:Contents">Help</a></li>
                    <li><a href="/wiki/Wikipedia:Community_portal">Community portal</a></li>
                    <li><a href="/wiki/Special:RecentChanges">Recent changes</a></li>
                    <li><a href="/wiki/Wikipedia:File_Upload_Wizard">Upload file</a></li>
                </ul>
            </div>
        </nav>
        <nav id="p-tb" class="mw-portlet" aria-label="Tools">
            <h3>Tools</h3>
            <div class="body">
                <ul>
                    <li><a href="/wiki/Special:WhatLinksHere/{article}">What links here</a></li>
                    <li><a href="/wiki/Special:RecentChangesLinked/{article}">Related changes</a></li>
                    <li><a href="/wiki/Special:SpecialPages">Special pages</a></li>
                    <li><a href="/w/index.php?title={article}&oldid=1234567890">Permanent link</a></li>
                    <li><a href="/w/index.php?title={article}&action=info">Page information</a></li>
                    <li><a href="https://www.wikidata.org/wiki/Special:EntityPage/Q1234">Wikidata item</a></li>
                    <li><a href="/w/index.php?title=Special:CiteThisPage&page={article}">Cite this page</a></li>
                </ul>
            </div>
        </nav>
        <nav id="p-lang" class="mw-portlet" aria-label="In other languages">
            <h3>In other languages</h3>
            <div class="body">
                <ul>
                    <li class="interlanguage-link interwiki-de"><a href="https://de.wikipedia.org/wiki/{article}" lang="de">Deutsch</a></li>
                    <li class="interlanguage-link interwiki-es"><a href="https://es.wikipedia.org/wiki/{article}" lang="es">Espa&ntilde;ol</a></li>
                    <li class="interlanguage-link interwiki-fr"><a href="https://fr.wikipedia.org/wiki/{article}" lang="fr">Fran&ccedil;ais</a></li>
                    <li class="interlanguage-link interwiki-ja"><a href="https://ja.wikipedia.org/wiki/{article}" lang="ja">&#26085;&#26412;&#35486;</a></li>
                    <li class="interlanguage-link interwiki-zh"><a href="https://zh.wikipedia.org/wiki/{article}" lang="zh">&#20013;&#25991;</a></li>
                    <li class="interlanguage-link interwiki-ru"><a href="https://ru.wikipedia.org/wiki/{article}" lang="ru">&#1056;&#1091;&#1089;&#1089;&#1082;&#1080;&#1081;</a></li>
                    <li class="interlanguage-link interwiki-pt"><a href="https://pt.wikipedia.org/wiki/{article}" lang="pt">Portugu&ecirc;s</a></li>
                    <li class="interlanguage-link interwiki-ar"><a href="https://ar.wikipedia.org/wiki/{article}" lang="ar">&#1575;&#1604;&#1593;&#1585;&#1576;&#1610;&#1577;</a></li>
                    <li class="interlanguage-link interwiki-hi"><a href="https://hi.wikipedia.org/wiki/{article}" lang="hi">&#2361;&#2367;&#2344;&#2381;&#2342;&#2368;</a></li>
                    <li class="interlanguage-link interwiki-ko"><a href="https://ko.wikipedia.org/wiki/{article}" lang="ko">&#54620;&#44397;&#50612;</a></li>
                </ul>
            </div>
        </nav>
    </div>
</div>
<div id="content" class="mw-body" role="main">
    <a id="top"></a>
    <div id="siteNotice" class="mw-body-content">
        <div id="centralNotice" class="cn-notice"></div>
    </div>
    <div class="mw-indicators"></div>
    <h1 id="firstHeading" class="firstHeading mw-first-heading"><span class="mw-page-title-main">{title}</span></h1>
    <div id="bodyContent" class="mw-body-content">
        <div id="siteSub" class="noprint">From Wikipedia, the free encyclopedia</div>
        <div id="contentSub"></div>
        <div id="mw-content-text" class="mw-body-content mw-content-ltr" lang="en" dir="ltr">
            <div class="mw-parser-output">
"""

WIKI_PAGE_FOOTER = """
            </div>
        </div>
        <div id="catlinks" class="catlinks" data-mw="interface">
            <div id="mw-normal-catlinks" class="mw-normal-catlinks">
                <a href="/wiki/Help:Category" title="Help:Category">Categories</a>:
                <ul>
                    <li><a href="/wiki/Category:All_articles">{title}</a></li>
                    <li><a href="/wiki/Category:Articles_with_short_description">Articles with short description</a></li>
                    <li><a href="/wiki/Category:Good_articles">Good articles</a></li>
                    <li><a href="/wiki/Category:Wikipedia_articles_with_GND_identifiers">Wikipedia articles with GND identifiers</a></li>
                </ul>
            </div>
            <div id="mw-hidden-catlinks" class="mw-hidden-catlinks mw-hidden-cats-hidden">
                Hidden categories:
                <ul>
                    <li><a href="/wiki/Category:Articles_with_J9U_identifiers">Articles with J9U identifiers</a></li>
                    <li><a href="/wiki/Category:Articles_with_LCCN_identifiers">Articles with LCCN identifiers</a></li>
                </ul>
            </div>
        </div>
        <div class="printfooter" data-nosnippet="">
            Retrieved from "<a dir="ltr" href="https://en.wikipedia.org/w/index.php?title={article}&oldid=1234567890">https://en.wikipedia.org/w/index.php?title={article}&oldid=1234567890</a>"
        </div>
    </div>
</div>
<div id="mw-footer" role="contentinfo">
    <ul id="footer-info">
        <li id="footer-info-lastmod">This page was last edited on 1 May 2026, at 12:00 (UTC).</li>
        <li id="footer-info-copyright">Text is available under the <a rel="license" href="https://creativecommons.org/licenses/by-sa/4.0/">Creative Commons Attribution-ShareAlike 4.0 License</a>; additional terms may apply.</li>
    </ul>
    <ul id="footer-places">
        <li id="footer-places-privacy"><a href="https://foundation.wikimedia.org/wiki/Special:MyLanguage/Policy:Privacy_policy">Privacy policy</a></li>
        <li id="footer-places-about"><a href="/wiki/Wikipedia:About">About Wikipedia</a></li>
        <li id="footer-places-disclaimers"><a href="/wiki/Wikipedia:General_disclaimer">Disclaimers</a></li>
        <li id="footer-places-contact"><a href="//en.wikipedia.org/wiki/Wikipedia:Contact_us">Contact Wikipedia</a></li>
        <li id="footer-places-wm-codeofconduct"><a href="https://foundation.wikimedia.org/wiki/Special:MyLanguage/Policy:Universal_Code_of_Conduct">Code of Conduct</a></li>
        <li id="footer-places-developers"><a href="https://developer.wikimedia.org">Developers</a></li>
        <li id="footer-places-statslink"><a href="https://stats.wikimedia.org/#/en.wikipedia.org">Statistics</a></li>
        <li id="footer-places-cookiestatement"><a href="https://foundation.wikimedia.org/wiki/Special:MyLanguage/Policy:Cookie_statement">Cookie statement</a></li>
        <li id="footer-places-mobileview"><a href="//en.m.wikipedia.org/w/index.php?title={article}&mobileaction=toggle_view_mobile" class="noprint stopMobileRedirectToggle">Mobile view</a></li>
    </ul>
    <ul id="footer-icons" class="noprint">
        <li id="footer-copyrightico"><a href="https://wikimediafoundation.org/"><img src="/static/images/footer/wikimedia-button.png" width="88" height="31" alt="Wikimedia Foundation" loading="lazy"></a></li>
        <li id="footer-poweredbyico"><a href="https://www.mediawiki.org/"><img src="/static/images/footer/poweredby_mediawiki_88x31.png" alt="Powered by MediaWiki" width="88" height="31" loading="lazy"></a></li>
    </ul>
</div>
<script>(RLQ=window.RLQ||[]).push(function(){{mw.config.set({{"wgPageName":"{article}","wgTitle":"{title}","wgCurRevisionId":1234567890,"wgRevisionId":1234567890,"wgArticleId":12345,"wgIsArticle":true,"wgIsRedirect":false,"wgAction":"view","wgUserName":null,"wgCategories":["{title}"],"wgPageContentLanguage":"en","wgPageContentModel":"wikitext","wgRelevantPageName":"{article}","wgRelevantArticleId":12345,"wgRequestId":"abc123","wgCanonicalNamespace":"","wgCanonicalSpecialPageName":false,"wgNamespaceNumber":0,"wgPageViewLanguage":"en","wgWikibaseItemId":"Q12345","wgCheckUserClientHintsHeadersJsApi":["brands","architecture","bitness","fullVersionList","mobile","model","platform","platformVersion"]}});mw.loader.state({{"ext.globalCssJs.user.styles":"ready","site.styles":"ready","user.styles":"ready","ext.globalCssJs.user":"ready","user":"ready","user.options":"loading","ext.cite.styles":"ready","ext.math.styles":"ready","skins.vector.search.codex.styles":"ready","skins.vector.styles":"ready","skins.vector.icons":"ready","ext.wikimediamessages.styles":"ready","ext.visualEditor.desktopArticleTarget.noscript":"ready","ext.uls.interlanguage":"ready","wikibase.client.init":"ready","ext.wikimediaBadges":"ready"}});mw.loader.load(["ext.cite.ux-enhancements","ext.scribunto.logs","site","mediawiki.page.ready","jquery.makeCollapsible","mediawiki.toc","skins.vector.js","ext.centralNotice.geo498IP","ext.centralNotice.startUp","ext.gadget.ReferenceTooltips","ext.gadget.switcher","ext.urlShortener.toolbar","ext.centralauth.centralautologin","mmv.bootstrap","ext.popups","ext.visualEditor.desktopArticleTarget.init","ext.visualEditor.targetLoader","ext.echo.centralauth","ext.eventLogging","ext.wikimediaEvents","ext.navigationTiming","ext.uls.interface","ext.cx.eventlogging.campaigns","ext.cx.uls.quick.actions","wikibase.client.vector-2022","ext.checkUser.clientHints","ext.growthExperiments.SuggestedEditSession","wikibase.sidebar.tracking"]);}});</script>
</body>
</html>"""


def count_tokens(text: str) -> int:
    enc = tiktoken.get_encoding("cl100k_base")
    return len(enc.encode(text))


def truncate_html_sections(html: str, max_body_tokens: int) -> str:
    sections = re.split(r'(?=<h[23][^>]*>)', html)
    result = sections[0] if sections else ""
    for section in sections[1:]:
        candidate = result + section
        if count_tokens(candidate) > max_body_tokens:
            break
        result = candidate
    if count_tokens(result) > max_body_tokens:
        enc = tiktoken.get_encoding("cl100k_base")
        tokens = enc.encode(result)[:max_body_tokens]
        result = enc.decode(tokens)
    return result


def fetch_wikipedia_html(article_title: str) -> str:
    params = {
        "action": "parse",
        "page": article_title,
        "prop": "text",
        "format": "json",
        "disablelimitreport": "true",
    }
    headers = {
        "User-Agent": "AgentClearfeed/0.1 (https://github.com/NITMe2/AgentClearfeed.ai; niteeshtapre@gmail.com)",
    }
    resp = httpx.get(WIKIPEDIA_API, params=params, headers=headers, timeout=30.0)
    resp.raise_for_status()
    data = resp.json()
    return data["parse"]["text"]["*"], data["parse"]["title"]


def wrap_in_full_page(title: str, article: str, body_html: str) -> str:
    header = WIKI_PAGE_HEADER.format(title=title, article=article)
    footer = WIKI_PAGE_FOOTER.format(title=title, article=article)
    chrome_tokens = count_tokens(header) + count_tokens(footer)
    max_body_tokens = MAX_TOKENS_PER_PAGE - chrome_tokens
    truncated_body = truncate_html_sections(body_html, max_body_tokens)
    return header + truncated_body + footer


def main():
    parser = argparse.ArgumentParser(description="Fetch Wikipedia HTML for Phase 2")
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Delay between requests (be polite to Wikipedia)")
    parser.add_argument("--force", action="store_true",
                        help="Re-fetch even if files exist")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total_tokens = 0
    for filename, article in TOPICS.items():
        output_path = OUTPUT_DIR / f"{filename}.html"
        if output_path.exists() and not args.force:
            html = output_path.read_text(encoding="utf-8")
            tokens = count_tokens(html)
            total_tokens += tokens
            print(f"  Skipping {filename} (exists, {tokens:,} tokens)")
            continue

        print(f"  Fetching {article}...")
        body_html, title = fetch_wikipedia_html(article)
        full_html = wrap_in_full_page(title, article, body_html)
        tokens = count_tokens(full_html)
        total_tokens += tokens

        output_path.write_text(full_html, encoding="utf-8")
        print(f"  Saved {output_path.name} ({len(full_html):,} bytes, {tokens:,} tokens)")
        time.sleep(args.delay)

    print(f"\nTotal tokens across all {len(TOPICS)} pages: {total_tokens:,}")
    if total_tokens > 120_000:
        print(f"  WARNING: Total exceeds 120K tokens. Consider reducing MAX_TOKENS_PER_PAGE.")
    else:
        print(f"  OK: Fits within 128K context window with room for prompt.")


if __name__ == "__main__":
    main()
