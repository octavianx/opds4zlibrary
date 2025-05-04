from fastapi import FastAPI, Query, Request, Depends, HTTPException, status
from fastapi.responses import Response, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from bs4 import BeautifulSoup
from datetime import datetime
import httpx, os, json, logging, secrets
from dotenv import load_dotenv
from urllib.parse import quote_plus, quote, unquote, urlparse, parse_qs
from html import escape

app = FastAPI()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
BASE_URL = "https://z-lib.fm"
COOKIE_FILE = "zlib_cookies.json"
cookies_jar = httpx.Cookies()

USERNAME = os.getenv("OPDS_USER", "admin")
PASSWORD = os.getenv("OPDS_PASS", "password")
 

# 注意一定要写 auto_error = false才能让你的http header有效
security = HTTPBasic(auto_error=False)

def verify_credentials(credentials: HTTPBasicCredentials = Depends(security)):
    if credentials is None or not credentials.username:
        # 未提供任何凭证
        logger.info(f"🚨 no credential provided")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": 'Basic realm="Login Required"'}
        )
    # 校验用户名和密码（假设正确凭证为 user/pass）
    correct_username = secrets.compare_digest(credentials.username, USERNAME)
    correct_password = secrets.compare_digest(credentials.password, PASSWORD)
    
    if not (correct_username and correct_password):
        # 凭证不匹配
        logger.info(f" 🚨  credential error")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": 'Basic realm="Login Required"'}
        )
    return True  # 验证通过


def load_cookies():
    global cookies_jar
    if os.path.exists(COOKIE_FILE) and os.path.getsize(COOKIE_FILE) > 0:
        with open(COOKIE_FILE, "r") as f:
            cookies_list = json.load(f)
            for c in cookies_list:
                cookies_jar.set(c["name"], c["value"], domain=c.get("domain", "z-lib.fm"), path=c.get("path", "/"))
        logger.info(f"✅ Loaded {len(cookies_list)} cookies from {COOKIE_FILE}")

@app.on_event("startup")
async def startup_event():
    load_cookies()

@app.get("/")
async def homepage():
    return RedirectResponse(url="/opds")

@app.get("/opds")
async def opds_index(request: Request, credentials: HTTPBasicCredentials = Depends(verify_credentials)):
    updated = datetime.utcnow().isoformat() + "Z"
    xml = f"""<?xml version='1.0' encoding='utf-8'?>
<feed xmlns='http://www.w3.org/2005/Atom'
      xmlns:opds='http://opds-spec.org/2010/catalog'>
  <title>Z-Library OPDS Proxy Directory</title>
  <id>urn:zlib:opds:index</id>
  <updated>{updated}</updated>
  <link rel='start' type='application/atom+xml' href='/opds/root.xml'/>
  <link rel='search' type='application/opensearchdescription+xml' href='/opds/opensearch.xml'/>
  <link rel='http://opds-spec.org/search' type='application/atom+xml' href='/opds/search?q={{searchTerms}}'/>
  <entry>
    <title>Root Directory</title>
    <id>urn:zlib:opds:root</id>
    <link rel='subsection' href='/opds/root.xml' type='application/atom+xml'/>
  </entry>
  <entry>
    <title>Example Search: python</title>
    <id>urn:zlib:opds:search:python</id>
    <link rel='subsection' href='/opds/search?q=python' type='application/atom+xml'/>
  </entry>
  <entry>
    <title>NYT Bestsellers</title>
    <id>urn:zlib:opds:nyt-bestsellers</id>
    <link rel='subsection' href='/opds/nyt-bestsellers' type='application/atom+xml'/>
  </entry>
</feed>"""
    return Response(content=xml.strip(), media_type="application/atom+xml")

@app.get("/opds/root.xml")
async def opds_root(credentials: HTTPBasicCredentials = Depends(verify_credentials)):
    updated = datetime.utcnow().isoformat() + "Z"
    xml = f"""<?xml version='1.0' encoding='utf-8'?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opds="http://opds-spec.org/2010/catalog">
  <id>urn:uuid:zlib-root-feed</id>
  <title>Z-Library OPDS Root</title>
  <updated>{updated}</updated>
  <author><name>Z-Lib Proxy</name></author>
  <link rel="self" href="/opds/root.xml" type="application/atom+xml"/>
  <link rel="start" href="/opds" type="application/atom+xml"/>
  <link rel="search" type="application/opensearchdescription+xml" href="/opds/opensearch.xml"/>
  <link rel="http://opds-spec.org/search" type="application/atom+xml" href="/opds/search?q={{searchTerms}}"/>

  <entry>
    <title>Search: Python</title>
    <id>urn:zlib:opds:search:python</id>
    <updated>{updated}</updated>
    <link rel="subsection" href="/opds/search?q=python" type="application/atom+xml"/>
    <content type="text">Search for books about Python</content>
  </entry>
  <entry>
    <title>Search: Deep Learning</title>
    <id>urn:zlib:opds:search:deep-learning</id>
    <updated>{updated}</updated>
    <link rel="subsection" href="/opds/search?q=deep%20learning" type="application/atom+xml"/>
    <content type="text">Search for books about Deep Learning</content>
  </entry>
  <entry>
    <title>Popular Recommendations</title>
    <id>urn:zlib:opds:popular</id>
    <updated>{updated}</updated>
    <link rel="subsection" href="/opds/popular" type="application/atom+xml"/>
    <content type="text">Recommended books from Z-Library</content>
  </entry>  
</feed>"""
    return Response(content=xml.strip(), media_type="application/atom+xml")

@app.get("/opds/opensearch.xml")
async def opensearch_description(request: Request):
    base_url = str(request.base_url).rstrip("/")
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
  <ShortName>Z-Lib Search</ShortName>
  <Description>Search Z-Library via OPDS</Description>
  <InputEncoding>UTF-8</InputEncoding>
  <Url type="application/atom+xml" template="{base_url}/opds/search?q={{searchTerms}}"/>
</OpenSearchDescription>"""
    return Response(content=xml.strip(), media_type="application/opensearchdescription+xml")

@app.get("/opds/search")
async def search_books(q: str = Query(...), page: int = Query(1), credentials: HTTPBasicCredentials = Depends(verify_credentials)):
    keywords = " ".join(q.strip().split())
    encoded_keywords = quote_plus(keywords).replace("+", "%20")
    search_url = f"{BASE_URL}/s/{encoded_keywords}?page={page}"

    async with httpx.AsyncClient(cookies=cookies_jar) as client:
        resp = await client.get(search_url)
        logger.info(f"🔎 Search request to: {search_url} => {resp.status_code}")
        if resp.status_code != 200:
            logger.error(f"Search failed: {resp.status_code}")
        if "form" in resp.text and "password" in resp.text:
            logger.warning("Redirected to login page — cookie likely invalid.")

    soup = BeautifulSoup(resp.text, "html.parser")
    book_items = soup.select("z-bookcard")
    entries = ""
    for item in book_items:
        title = escape(item.select_one("div[slot=title]").text.strip())
        author = escape(item.select_one("div[slot=author]").text.strip())
        publisher = escape(item.get("publisher", ""))
        book_id = item.get("id", "")
        download_path = item.get("download", "")
        token = quote(f"{book_id}:{download_path}", safe="")
        book_url = f"/download?token={token}"
        cover_url = escape(item.select_one("img").get("data-src", ""))
        extension = escape(item.get("extension", ""))
        filesize = escape(item.get("filesize", ""))
        year = escape(item.get("year", ""))

        if year and year.isdigit():
            published_date = f"{year}-01-01T00:00:00Z"
        else:
            published_date = ""

        emoji_map = {
            "pdf": "📕", "epub": "📚", "mobi": "📘", "djvu": "📄",
            "azw3": "📙", "txt": "📝"
        }
        emoji = emoji_map.get(extension.lower(), "📦")
        summary = f"{emoji} {extension.upper()}, {filesize}, {year}"

        entries += f"""
        <entry>
            <title>{title}</title>
            <author><name>{emoji}{author}</name></author>
            <publisher><name>🏛️ {publisher}/{extension},{filesize}</name></publisher>
            <published>{published_date}</published>
            <id>{book_url}</id>
            <link rel='http://opds-spec.org/acquisition' href='{book_url}' type='application/octet-stream'/>
            <updated>{datetime.utcnow().isoformat()}Z</updated>
            <content type='text'>{summary}</content>
            <link rel='http://opds-spec.org/image' href='{cover_url}' type='image/jpeg'/>
            <link rel='http://opds-spec.org/image/thumbnail' href='{cover_url}' type='image/jpeg'/>
        </entry>
        """

    # 修复分页检测：使用 paginator 的 rel 属性检测下一页
    next_link = ""
    next_link_tag = ""
    href_escaped = ""
    temp_href = ""

    # 修复分页部分的代码
    next_link_tag = soup.select_one("div.paginator noscript a")
    if next_link_tag:
        logger.info(f"✅ Found paginator: {next_link_tag.get('href')}")
    else:
        logger.warning("⚠️ No pagination link found.")

    if next_link_tag:
        next_href = next_link_tag.get("href", "")
    # 提取下一页页码
        next_page = parse_qs(urlparse(next_href).query).get("page", [None])[0]

    if next_page:
        temp_href = escape(f"/opds/search?q={quote_plus(keywords)}&page={next_page}")
        next_link = f"<link rel='next' href='{temp_href}' type='application/atom+xml'/>"

    if page > 1:
        temp_href = escape(f"/opds/search?q={quote_plus(keywords)}&page={page - 1}")
        next_link += f"\n    <link rel='previous' href='{temp_href}' type='application/atom+xml'/>"
        temp_href = escape(f"/opds/search?q={quote_plus(keywords)}&page=1")
        next_link += f"\n    <link rel='first' href='{temp_href}' type='application/atom+xml'/>"

    href_escaped = escape(f"/opds/search?q={quote_plus(keywords)}&page={page}")

    feed = f"""<?xml version='1.0' encoding='utf-8'?>
<feed xmlns='http://www.w3.org/2005/Atom'>
  <title>Z-Library Search: {escape(keywords)}</title>
  <id>urn:zlib:opds:search:{escape(keywords.replace(" ", "-"))}</id>
  <updated>{datetime.utcnow().isoformat()}Z</updated>
  <link rel='self' type='application/atom+xml' href='{href_escaped}'/>
  <link rel='start' type='application/atom+xml' href='/opds/root.xml'/>
  {next_link}
  {entries}
</feed>"""
    return Response(content=feed.strip(), media_type="application/atom+xml")

@app.get("/download")
async def download(token: str):
    try:
        book_id, path = token.split(":", 1)
        path = unquote(path)
        url = f"{BASE_URL}{path}"
        logger.info(f"📥 Downloading from {url} with token {token}")

        async with httpx.AsyncClient(cookies=cookies_jar, follow_redirects=True) as client:
            resp = await client.get(url)
            logger.info(f"📦 Download response status: {resp.status_code}, headers: {dict(resp.headers)}")
            if resp.status_code == 200:
                return Response(content=resp.content, media_type=resp.headers.get("content-type", "application/octet-stream"))
            else:
                return Response(f"Download failed with status {resp.status_code}", status_code=resp.status_code)
    except Exception as e:
        logger.exception("Download failed")
        return Response("Internal error", status_code=500)

@app.get("/opds/nyt-bestsellers")
async def nyt_bestsellers(request: Request, credentials: HTTPBasicCredentials = Depends(verify_credentials)):
    api_key = os.getenv("NYT_API_KEY")
    url = f"https://api.nytimes.com/svc/books/v3/lists/current/hardcover-nonfiction.json?api-key={api_key}"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url)
        data = resp.json()

    books = data.get("results", {}).get("books", [])
    updated = datetime.utcnow().isoformat() + "Z"
    entries = ""
    for book in books:
        title = escape(book.get("title", "Untitled").strip())
        author = escape(book.get("author", "Unknown").strip())
        desc = escape(book.get("description", ""))
        img = escape(book.get("book_image", ""))
        search_url = escape(f"/opds/search?q={quote_plus(title)}")

        entries += f"""
        <entry>
            <title>{title}</title>
            <author><name>{author}</name></author>
            <id>{search_url}</id>
            <updated>{updated}</updated>
            <link rel='subsection' href='{search_url}' type='application/atom+xml'/>
            <content type='text'>{desc}</content>
            <link rel='http://opds-spec.org/image' href='{img}' type='image/jpeg'/>
            <link rel='http://opds-spec.org/image/thumbnail' href='{img}' type='image/jpeg'/>
        </entry>
        """

    feed = f"""<?xml version='1.0' encoding='utf-8'?>
<feed xmlns='http://www.w3.org/2005/Atom'>
  <title>NYT Bestsellers: Hardcover Nonfiction</title>
  <id>urn:zlib:opds:nyt-bestsellers</id>
  <updated>{updated}</updated>
  <link rel='self' href='/opds/nyt-bestsellers' type='application/atom+xml'/>
  <link rel='start' href='/opds/root.xml' type='application/atom+xml'/>
  {entries}
</feed>"""
    return Response(content=feed.strip(), media_type="application/atom+xml")
