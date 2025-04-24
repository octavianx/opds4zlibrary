from fastapi import FastAPI, Request, Query
from fastapi.responses import Response, RedirectResponse, HTMLResponse
import httpx
from bs4 import BeautifulSoup
from datetime import datetime
import logging

# 修复 Z-Library 搜索 URL 的多关键词分隔符为 `%20`
from urllib.parse import quote_plus


app = FastAPI()

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://z-lib.fm"

@app.get("/opds", response_class=HTMLResponse)
async def opds_index(request: Request):
    updated = datetime.utcnow().isoformat() + "Z"
    xml_index = f"""<?xml version='1.0' encoding='utf-8'?>
<feed xmlns='http://www.w3.org/2005/Atom'>
  <title>Z-Library OPDS Proxy Directory</title>
  <id>urn:zlib:opds:index</id>
  <updated>{updated}</updated>
  <link rel='self' type='application/atom+xml' href='/opds'/>
  <link rel='start' type='application/atom+xml' href='/opds/root.xml'/>
  <link rel='search' type='application/opensearchdescription+xml' href='/opds/opensearch.xml'/>
  <entry>
    <title>Root Directory</title>
    <id>urn:zlib:opds:root</id>
    <link rel='subsection' href='/opds/root.xml' type='application/atom+xml'/>
  </entry>
  <entry>
    <title>Search by Title</title>
    <id>urn:zlib:opds:search:title</id>
    <link rel='search' type='application/atom+xml' href='/opds/search?q={{searchTerms}}'/>
  </entry>
  <entry>
    <title>Example Search: python</title>
    <id>urn:zlib:opds:search:example:python</id>
    <link rel='subsection' href='/opds/search?q=python' type='application/atom+xml'/>
  </entry>
</feed>"""

    accept_header = request.headers.get("accept", "")
    if "application/atom+xml" in accept_header:
        return Response(content=xml_index.strip(), media_type="application/atom+xml")

    html = """
    <html>
    <head><title>Z-Lib OPDS Proxy</title></head>
    <body>
        <h1>Z-Library OPDS Proxy</h1>
        <p>This is a proxy service that wraps Z-Library's search results into an OPDS 1.0 compatible feed.</p>
        <h2>Endpoints</h2>
        <ul>
            <li><a href="/opds/root.xml">OPDS Root Directory</a> — for OPDS clients like KOReader, Calibre, etc.</li>
            <li><a href="/opds/search?q=python">Example Search for 'python'</a></li>
        </ul>
        <h2>Try a Custom Search</h2>
        <form action="/opds/search" method="get">
            <input type="text" name="q" placeholder="Enter keyword" required />
            <input type="submit" value="Search" />
        </form>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

@app.get("/opds/root.xml")
async def opds_root():
    updated = datetime.utcnow().isoformat() + "Z"
    feed = f"""<?xml version='1.0' encoding='utf-8'?>
<feed xmlns='http://www.w3.org/2005/Atom'>
  <title>Z-Library OPDS Directory</title>
  <id>urn:zlib:opds:root</id>
  <updated>{updated}</updated>
  <link rel='self' type='application/atom+xml' href='/opds/root.xml'/>
  <link rel='search' type='application/opensearchdescription+xml' href='/opds/opensearch.xml'/>
  <entry>
    <title>Search by Title</title>
    <id>urn:zlib:opds:search:title</id>
    <link rel='search' type='application/atom+xml' href='/opds/search?q={{searchTerms}}'/>
  </entry>
  <entry>
    <title>Example Search: python</title>
    <id>urn:zlib:opds:search:example:python</id>
    <link rel='subsection' href='/opds/search?q=python' type='application/atom+xml'/>
  </entry>
</feed>"""
    return Response(content=feed.strip(), media_type="application/atom+xml")

@app.get("/opds/opensearch.xml")
async def opds_opensearch():
    xml = """<?xml version="1.0" encoding="UTF-8"?>
<OpenSearchDescription xmlns="http://a9.com/-/spec/opensearch/1.1/">
  <ShortName>Z-Lib OPDS Search</ShortName>
  <Description>Search Z-Library books via OPDS feed</Description>
  <InputEncoding>UTF-8</InputEncoding>
  <Url type="application/atom+xml" template="/opds/search?q={searchTerms}"/>
</OpenSearchDescription>"""
    return Response(content=xml.strip(), media_type="application/opensearchdescription+xml")


@app.get("/opds/search")
async def search_books(q: str = Query(..., alias="q"), page: int = Query(1)):
    logger.info(f"Search query received: {q}, page: {page}")

    # Normalize and encode multiple keywords with %20 (Z-Lib prefers %20 over '+')
    keywords = " ".join(q.strip().split())
    encoded_keywords = quote_plus(keywords).replace("+", "%20")
    search_url = f"{BASE_URL}/s/{encoded_keywords}?page={page}"
    logger.info(f"Fetching Z-Lib search page: {search_url}")

    async with httpx.AsyncClient() as client:
        resp = await client.get(search_url)

    logger.info(f"Response status code: {resp.status_code}")

    soup = BeautifulSoup(resp.text, "html.parser")
    book_items = soup.select("z-bookcard")
    logger.info(f"Found {len(book_items)} book entries on page {page}.")

    entries = ""
    for item in book_items:
        title = item.select_one("div[slot=title]").text.strip() if item.select_one("div[slot=title]") else "Unknown Title"
        author = item.select_one("div[slot=author]").text.strip() if item.select_one("div[slot=author]") else "Unknown Author"
        book_id = item.get("id", "")
        download_path = item.get("download", "")
        book_url = f"/download?id={book_id}&path={download_path}" if book_id and download_path else BASE_URL + item.get("href", "")

        cover_url = item.select_one("img").get("data-src") if item.select_one("img") else ""
        extension = item.get("extension", "")
        filesize = item.get("filesize", "")
        year = item.get("year", "")
        summary = f"Format: {extension}, Size: {filesize}, Year: {year}"

        entry = f"""
        <entry>
            <title>{title}</title>
            <author><name>{author}</name></author>
            <id>{book_url}</id>
            <link rel='http://opds-spec.org/acquisition' href='{book_url}' type='application/octet-stream'/>
            <updated>{datetime.utcnow().isoformat()}Z</updated>
            <content type='text'>Format: {extension.upper()}, Size: {filesize}, Year: {year}</content>
            <link rel='http://opds-spec.org/image' href='{cover_url}' type='image/jpeg'/>
            <link rel='http://opds-spec.org/image/thumbnail' href='{cover_url}' type='image/jpeg'/>
        </entry>
        """

        entries += entry

    has_next = bool(soup.select_one("a[title='Next page']"))
    next_link = ""
    if has_next:
        next_url = f"/opds/search?q={quote_plus(keywords)}&page={page + 1}"
        next_link = f"<link rel='next' href='{next_url}' type='application/atom+xml'/>"
        logger.info(f"Next page available: {next_url}")

    feed = f"""<?xml version='1.0' encoding='utf-8'?>
<feed xmlns='http://www.w3.org/2005/Atom'>
  <title>Z-Library OPDS Search: {keywords}</title>
  <id>urn:uuid:zlib-opds-feed:{keywords.replace(" ", "-")}-page-{page}</id>
  <updated>{datetime.utcnow().isoformat()}Z</updated>
  <link rel='self' type='application/atom+xml' href='/opds/search?q={quote_plus(keywords)}&page={page}'/>
  <link rel='start' type='application/atom+xml' href='/opds/root.xml'/>
  {next_link}
  {entries}
</feed>"""
    return Response(content=feed.strip(), media_type="application/atom+xml")

    
@app.get("/download")
async def download_book(id: str, path: str):
    logger.info(f"Redirecting download for book id={id}, path={path}")
    download_url = f"{BASE_URL}{path}"
    return RedirectResponse(download_url)
