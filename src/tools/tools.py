import os
import re

import requests
import trafilatura
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from langchain.tools import tool
from readability import Document
from tavily import TavilyClient

load_dotenv()

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


@tool
def web_search(query: str) -> str:
    """Search the web for recent and reliable information on a topic. Return titles, URLs and snippets."""
    results = tavily_client.search(query=query, max_results=4)

    output = []
    for r in results["results"]:
        output.append(
            f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['content'][:200]}\n"
        )
    # NOTE: this used to be indented inside the loop, so it returned after
    # the first result only. Joining now happens after the loop finishes.
    return "\n----\n".join(output)


@tool
def scrape_url(url: str) -> str:
    """
    Scrape and extract clean readable content from a URL.
    Use multiple extraction strategies for better reliability.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
        # NOTE: without this, sites sending Content-Encoding: br return
        # Brotli-compressed bytes that requests can't decode (it only
        # auto-decodes gzip/deflate), and response.text silently returns
        # garbage instead of raising an error. Restricting to gzip/deflate
        # forces servers to send something requests can actually read.
        "Accept-Encoding": "gzip, deflate",
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        html = response.text

        # Strategy 1: trafilatura
        extracted = trafilatura.extract(html, include_comments=False, include_tables=False)
        if extracted and len(extracted.strip()) > 200:
            return re.sub(r"\s+", " ", extracted).strip()[:5000]

        # Strategy 2: readability
        doc = Document(html)
        readable_html = doc.summary()
        soup = BeautifulSoup(readable_html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()
        text = soup.get_text(separator=" ", strip=True)
        if text and len(text.strip()) > 200:
            return re.sub(r"\s+", " ", text).strip()[:5000]

        # Strategy 3: fallback full-page extraction
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()
        cleaned = re.sub(r"\s+", " ", soup.get_text(separator=" ", strip=True)).strip()
        if cleaned:
            return cleaned[:5000]

        return "Could not extract meaningful content from the page."

    except requests.exceptions.Timeout:
        return "Request timed out while scraping the URL."
    except requests.exceptions.HTTPError as e:
        return f"HTTP error occurred: {str(e)}"
    except Exception as e:
        return f"Could not scrape URL: {str(e)}"