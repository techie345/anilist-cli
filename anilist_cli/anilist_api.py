"""Thin client around the AniList GraphQL API.

Docs: https://docs.anilist.co/
Endpoint: https://graphql.anilist.co
"""

import time

import requests

API_URL = "https://graphql.anilist.co"


def _post(query, variables=None):
    resp = requests.post(
        API_URL,
        json={"query": query, "variables": variables or {}},
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        timeout=15,
    )
    resp.raise_for_status()
    payload = resp.json()
    if "errors" in payload and payload["errors"]:
        raise RuntimeError(
            "; ".join(e.get("message", "Unknown error") for e in payload["errors"])
        )
    return payload["data"]


# ---------------------------------------------------------------------------
# Anime release schedule
# ---------------------------------------------------------------------------

AIRING_SCHEDULE_QUERY = """
query ($page: Int, $perPage: Int, $greater: Int, $lesser: Int) {
  Page(page: $page, perPage: $perPage) {
    airingSchedules(
      airingAt_greater: $greater
      airingAt_lesser: $lesser
      sort: TIME_DESC
    ) {
      airingAt
      episode
      media {
        id
        title {
          romaji
          english
        }
        format
        siteUrl
      }
    }
  }
}
"""

UPCOMING_SCHEDULE_QUERY = """
query ($page: Int, $perPage: Int, $greater: Int, $lesser: Int) {
  Page(page: $page, perPage: $perPage) {
    airingSchedules(
      airingAt_greater: $greater
      airingAt_lesser: $lesser
      sort: TIME_ASC
    ) {
      airingAt
      episode
      media {
        id
        title {
          romaji
          english
        }
        format
        siteUrl
      }
    }
  }
}
"""


def recently_aired(hours=24, per_page=20, page=1):
    """Episodes that aired in the last `hours` hours, newest first."""
    now = int(time.time())
    greater = now - hours * 3600
    data = _post(
        AIRING_SCHEDULE_QUERY,
        {"page": page, "perPage": per_page, "greater": greater, "lesser": now},
    )
    return data["Page"]["airingSchedules"]


def upcoming_episodes(hours=24, per_page=20, page=1):
    """Episodes airing in the next `hours` hours, soonest first."""
    now = int(time.time())
    lesser = now + hours * 3600
    data = _post(
        UPCOMING_SCHEDULE_QUERY,
        {"page": page, "perPage": per_page, "greater": now, "lesser": lesser},
    )
    return data["Page"]["airingSchedules"]


# ---------------------------------------------------------------------------
# Newly added / currently releasing manga (AniList side, used as a fallback
# / alternative source to MangaDex)
# ---------------------------------------------------------------------------

NEW_MANGA_QUERY = """
query ($page: Int, $perPage: Int) {
  Page(page: $page, perPage: $perPage) {
    media(
      type: MANGA
      sort: START_DATE_DESC
      status_in: [RELEASING, NOT_YET_RELEASED]
    ) {
      id
      title {
        romaji
        english
      }
      format
      status
      startDate {
        year
        month
        day
      }
      siteUrl
    }
  }
}
"""


def newly_added_manga(per_page=20, page=1):
    data = _post(NEW_MANGA_QUERY, {"page": page, "perPage": per_page})
    return data["Page"]["media"]


# ---------------------------------------------------------------------------
# User lists
# ---------------------------------------------------------------------------

MEDIA_LIST_QUERY = """
query ($userName: String, $type: MediaType) {
  MediaListCollection(userName: $userName, type: $type) {
    lists {
      name
      isCustomList
      status
      entries {
        progress
        progressVolumes
        score
        status
        media {
          id
          title {
            romaji
            english
          }
          format
          episodes
          chapters
          status
        }
      }
    }
  }
}
"""


def get_user_list(username, media_type="ANIME"):
    data = _post(MEDIA_LIST_QUERY, {"userName": username, "type": media_type.upper()})
    collection = data.get("MediaListCollection")
    if not collection:
        return []
    return collection["lists"]


# Statuses that count as "actively following" for the --following flag.
FOLLOWING_STATUSES = {"CURRENT", "REPEATING"}


def get_following(username, media_type="ANIME"):
    """Return (media_ids, normalized_titles) for everything the user has in
    CURRENT (watching/reading) or REPEATING (rewatching/rereading) status.
    """
    lists = get_user_list(username, media_type=media_type)
    ids = set()
    titles = set()
    for lst in lists:
        for entry in lst.get("entries", []):
            if (entry.get("status") or "").upper() not in FOLLOWING_STATUSES:
                continue
            media = entry["media"]
            ids.add(media["id"])
            for t in (media["title"].get("romaji"), media["title"].get("english")):
                if t:
                    titles.add(t.strip().lower())
    return ids, titles


USER_EXISTS_QUERY = """
query ($name: String) {
  User(name: $name) {
    id
    name
  }
}
"""


def user_exists(username):
    try:
        data = _post(USER_EXISTS_QUERY, {"name": username})
        return data.get("User") is not None
    except Exception:
        return False
