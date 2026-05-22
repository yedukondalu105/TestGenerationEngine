"""Confluence MCP Server — exposes requirement page tools for Claude Code."""

import os
import json
from typing import Optional
from dotenv import load_dotenv
from fastmcp import FastMCP

# Load .env from project root (one level up from mcp_servers/)
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"))

mcp = FastMCP("confluence")


def _get_client():
    from atlassian import Confluence
    return Confluence(
        url=os.getenv("CONFLUENCE_URL", "https://upalyk.atlassian.net/wiki"),
        username=os.getenv("CONFLUENCE_USERNAME"),
        password=os.getenv("CONFLUENCE_API_TOKEN"),
        cloud=True,
    )


def _configured_page_ids() -> list[str]:
    ids = []
    for i in range(1, 7):
        pid = os.getenv(f"CONFLUENCE_PAGE_ID_{i}")
        if pid:
            ids.append(pid)
    return ids


def _page_to_text(page: dict) -> str:
    """Extract plain text from a Confluence page dict."""
    from bs4 import BeautifulSoup
    body = page.get("body", {}).get("storage", {}).get("value", "")
    if body:
        return BeautifulSoup(body, "lxml").get_text(separator="\n", strip=True)
    return ""


@mcp.tool()
def get_page(page_id: str) -> str:
    """Fetch a Confluence page by its ID and return its title and plain-text content.

    Args:
        page_id: Confluence page ID (numeric string).

    Returns:
        Page title and plain-text body content.
    """
    try:
        client = _get_client()
        page = client.get_page_by_id(page_id, expand="body.storage")
        title = page.get("title", "Untitled")
        text = _page_to_text(page)
        return f"# {title}\n\n{text}"
    except Exception as e:
        return f"Error fetching page {page_id}: {e}"


@mcp.tool()
def list_requirement_pages() -> str:
    """List all requirement pages configured in the project (.env CONFLUENCE_PAGE_ID_*).

    Returns:
        JSON list of {page_id, title, url} for each configured page.
    """
    try:
        client = _get_client()
        base_url = os.getenv("CONFLUENCE_URL", "https://upalyk.atlassian.net/wiki")
        page_ids = _configured_page_ids()

        if not page_ids:
            return "No pages configured. Set CONFLUENCE_PAGE_ID_1 through CONFLUENCE_PAGE_ID_6 in .env"

        pages = []
        for pid in page_ids:
            try:
                page = client.get_page_by_id(pid, expand="")
                pages.append({
                    "page_id": pid,
                    "title": page.get("title", "Unknown"),
                    "url": f"{base_url}/pages/{pid}",
                })
            except Exception as e:
                pages.append({"page_id": pid, "title": f"Error: {e}", "url": ""})

        return json.dumps(pages, indent=2)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def search_pages(query: str, limit: int = 10) -> str:
    """Search for Confluence pages in the configured space by keyword.

    Args:
        query: Search query string (e.g. "trade amendment validation").
        limit: Maximum number of results to return (default 10).

    Returns:
        JSON list of {page_id, title, url, excerpt} matching pages.
    """
    try:
        client = _get_client()
        space_key = os.getenv("CONFLUENCE_SPACE_KEY", "")
        base_url = os.getenv("CONFLUENCE_URL", "https://upalyk.atlassian.net/wiki")

        cql = f'text ~ "{query}" AND type = "page"'
        if space_key:
            cql += f' AND space = "{space_key}"'

        results = client.cql(cql, limit=limit)
        pages = []
        for item in results.get("results", []):
            content = item.get("content", {})
            pid = content.get("id", "")
            pages.append({
                "page_id": pid,
                "title": content.get("title", "Unknown"),
                "url": f"{base_url}/pages/{pid}" if pid else "",
                "excerpt": item.get("excerpt", ""),
            })
        if not pages:
            return f"No pages found for query: '{query}'"
        return json.dumps(pages, indent=2)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def get_all_requirements() -> str:
    """Fetch and combine content from all configured requirement pages.

    Useful for getting a full picture of all documented requirements in one call.

    Returns:
        Combined plain-text content of all configured requirement pages, separated by headers.
    """
    try:
        client = _get_client()
        page_ids = _configured_page_ids()

        if not page_ids:
            return "No pages configured. Set CONFLUENCE_PAGE_ID_1 through CONFLUENCE_PAGE_ID_6 in .env"

        sections = []
        for pid in page_ids:
            try:
                page = client.get_page_by_id(pid, expand="body.storage")
                title = page.get("title", f"Page {pid}")
                text = _page_to_text(page)
                sections.append(f"## {title}\n\n{text}")
            except Exception as e:
                sections.append(f"## Page {pid}\n\nError: {e}")

        return "\n\n---\n\n".join(sections)
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def create_test_plan(title: str, content: str, parent_page_id: str = "") -> str:
    """Create a new Confluence page with the given test plan content.

    The page is created in the configured Confluence space. If a parent_page_id
    is provided, the page will be created as a child of that page.

    Args:
        title: Page title for the test plan.
        content: Plain-text or Confluence wiki markup content for the page body.
        parent_page_id: Optional parent page ID. Defaults to space root if empty.

    Returns:
        URL of the newly created page, or an error message.
    """
    try:
        client = _get_client()
        space_key = os.getenv("CONFLUENCE_SPACE_KEY", "")
        base_url = os.getenv("CONFLUENCE_URL", "https://upalyk.atlassian.net/wiki")

        if not space_key:
            return "Error: CONFLUENCE_SPACE_KEY not configured in .env"

        # Wrap plain text in Confluence storage format
        escaped = (
            content
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
        )
        storage_body = f"<p>{escaped.replace(chr(10), '</p><p>')}</p>"

        kwargs = {
            "space": space_key,
            "title": title,
            "body": storage_body,
        }
        if parent_page_id:
            kwargs["parent_id"] = parent_page_id

        page = client.create_page(**kwargs)
        pid = page.get("id", "")
        return f"Created: {base_url}/pages/{pid}\nTitle: {title}\nPage ID: {pid}"
    except Exception as e:
        return f"Error creating page: {e}"


if __name__ == "__main__":
    mcp.run()
