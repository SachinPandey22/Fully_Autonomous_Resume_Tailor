import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("scraper")

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)


def _detect_platform(url: str) -> str:
    hostname = urlparse(url).hostname or ""
    if "greenhouse.io" in hostname:
        return "greenhouse"
    if "lever.co" in hostname:
        return "lever"
    if "linkedin.com" in hostname:
        return "linkedin"
    if "myworkdayjobs.com" in hostname or "workday.com" in hostname:
        return "workday"
    if "ashbyhq.com" in hostname:
        return "ashby"
    return "other"


def _extract_text(soup: BeautifulSoup, platform: str) -> str:
    # Remove noise tags
    for tag in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
        tag.decompose()

    selectors = {
        "greenhouse": ["#app_body", "main", ".job-post"],
        "lever": [".posting-page", "main", ".content"],
        "linkedin": [".description", ".show-more-less-html", "main"],
        "workday": ["[data-automation-id='jobPostingDescription']", "main"],
        "ashby": ["main", "article", ".job-description"],
        "other": [],
    }

    for selector in selectors.get(platform, []):
        el = soup.select_one(selector)
        if el:
            return el.get_text(separator="\n", strip=True)

    # Fallback: find the largest text block
    blocks = soup.find_all(["div", "article", "section", "main"])
    if blocks:
        largest = max(blocks, key=lambda b: len(b.get_text()))
        return largest.get_text(separator="\n", strip=True)

    return soup.get_text(separator="\n", strip=True)


def _extract_title(soup: BeautifulSoup) -> str:
    h1 = soup.find("h1")
    if h1:
        return h1.get_text(strip=True)
    title = soup.find("title")
    if title:
        raw = title.get_text(strip=True)
        # Strip common suffixes like " | Company" or " - Company"
        return re.split(r"\s*[\|\-–]\s*", raw)[0].strip()
    return "Unknown Title"


def _extract_company(soup: BeautifulSoup, url: str) -> str:
    title_tag = soup.find("title")
    if title_tag:
        raw = title_tag.get_text(strip=True)
        parts = re.split(r"\s*[\|\-–]\s*", raw)
        if len(parts) >= 2:
            return parts[-1].strip()
    # Fallback: use domain
    hostname = urlparse(url).hostname or ""
    parts = hostname.replace("www.", "").split(".")
    return parts[0].capitalize() if parts else "Unknown Company"


@mcp.tool()
def fetch_job(url: str) -> dict:
    """Fetch a job description from a URL and extract structured data."""
    platform = _detect_platform(url)
    try:
        response = requests.get(
            url,
            headers={"User-Agent": USER_AGENT},
            timeout=15,
        )
        response.raise_for_status()
    except requests.exceptions.Timeout:
        return {
            "error": "Request timed out",
            "message": (
                "The page took too long to load. "
                "Please paste the job description text manually."
            ),
        }
    except requests.exceptions.HTTPError as e:
        return {
            "error": f"HTTP {e.response.status_code}",
            "message": (
                f"The page returned {e.response.status_code}. "
                "It may require a login. "
                "Please paste the job description text manually."
            ),
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": str(e),
            "message": "Fetch failed. Please paste the job description text manually.",
        }

    soup = BeautifulSoup(response.text, "html.parser")
    title = _extract_title(soup)
    company = _extract_company(soup, url)
    description = _extract_text(soup, platform)

    # Truncate
    description = description[:6000]

    return {
        "company": company,
        "title": title,
        "description": description,
        "url": url,
        "word_count": len(description.split()),
        "platform": platform,
    }


if __name__ == "__main__":
    mcp.run()
