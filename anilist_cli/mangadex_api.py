"""Thin client around the MangaDex API for recent chapter releases.

Docs: https://api.mangadex.org/docs/
Endpoint: https://api.mangadex.org
"""

import requests

API_URL = "https://api.mangadex.org"


def recent_chapters(limit=20, lang="en"):
    """Return the most recently published chapters, newest first.

    Each item includes a 'manga' and 'scanlation_group' relationship
    (with attributes expanded) thanks to the `includes[]` parameter.
    """
    params = {
        "limit": limit,
        "translatedLanguage[]": [lang],
        "order[readableAt]": "desc",
        "includes[]": ["manga", "scanlation_group"],
        "contentRating[]": ["safe", "suggestive", "erotica"],
    }
    resp = requests.get(f"{API_URL}/chapter", params=params, timeout=15)
    resp.raise_for_status()
    return resp.json().get("data", [])


def extract_manga_title(chapter):
    """Pull a human-readable manga title out of a chapter's relationships."""
    for rel in chapter.get("relationships", []):
        if rel.get("type") == "manga":
            attrs = rel.get("attributes") or {}
            titles = attrs.get("title") or {}
            if titles:
                return titles.get("en") or next(iter(titles.values()))
            for alt in attrs.get("altTitles") or []:
                if "en" in alt:
                    return alt["en"]
    return "Unknown manga"


def extract_scanlation_group(chapter):
    for rel in chapter.get("relationships", []):
        if rel.get("type") == "scanlation_group":
            attrs = rel.get("attributes") or {}
            return attrs.get("name", "Unknown")
    return "-"


def extract_anilist_id(chapter):
    """Return the AniList media ID linked from this chapter's manga, if any.

    MangaDex manga records can include a `links` map with cross-site IDs,
    e.g. {"al": "30013", "mu": "...", ...}. Returns an int or None.
    """
    for rel in chapter.get("relationships", []):
        if rel.get("type") == "manga":
            attrs = rel.get("attributes") or {}
            links = attrs.get("links") or {}
            al = links.get("al")
            if al is None:
                return None
            try:
                return int(al)
            except (TypeError, ValueError):
                return None
    return None
