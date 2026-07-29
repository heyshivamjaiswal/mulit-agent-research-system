from httpx import Timeout
from langchain.tools import tool
from lxml_html_clean import clean_html
import requests
from dotenv import load_dotenv
import os
from tavily import TavilyClient
import tavily

from bs4 import BeautifulSoup
from readability import Document
import trafilatura
import re


load_dotenv()

tavily = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

@tool
def web_serach(query: str)->str:
    """Search the web for the recent and reliable information on a topic. Return Titles ,URLs and snippets."""
    results = tavily.search(query=query, max_results=4)

    output = []

    for r in results['results']:
        output.append(
            f"Title: {r['title']}\nURL: {r['url']}\nSnippet: {r['content'][:200]}\n"
        )

        return "\n----\n".join(output)

@tool
def scrape_url(url: str)->str:
    """
    Scrape and extract clean readable content from a URL.
    Use multiple extraction stragegies for better reliability.
    """

    headers =  {
        "User-Agent":(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/124.0 Safari/537.36"
        ),
         "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.google.com/",
    }

    try:
        #Fectch page
        response = requests.get(
            url,
            headers=headers,
            timeout = 15
        )

        response.raise_for_status()
        html = response.text

        # Strategy 1 - trafilatura
        extracted = trafilatura.extract(
            html,
            include_comments=False,
            include_tables=False
        )

        if extracted and len(extracted.strip()) > 200:
            cleaned = re.sub(r'\s+', ' ', extracted).strip()
            return cleaned[:5000]


        #Readability
        doc = Document(html)
        clean_html = doc.summary()

        soup = BeautifulSoup(clean_html, "html.parser")

        for tag in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "form"
        ]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)

        if text and len(text.strip()) > 200:
            cleaned = re.sub(r'\s+', ' ', text)
            return cleaned[:5000]    


        #Fallback full page extraction

        soup = BeautifulSoup(html , "html.parser")

        for tag in soup([
            "script",
            "style",
            "nav",
            "footer",
            "header",
            "aside",
            "form"
        ]):
            tag.decompose()

        text = soup.get_text(separator=" ", strip=True)

        cleaned = re.sub(r'\s+', ' ', text)

        if cleaned:
                return cleaned[:5000]

        return "Cloud not extracted meaningful content from the page."

    except requests.exception.Timeout:
        return "Request timed out while scraping the URL."

    except requests.exceptions.HTTPError as e:
        return f"HTTP error occurred: {str(e)}"

    except Exception as e:
        return f"Could not scrape URL: {str(e)}"