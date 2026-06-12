#!/usr/bin/env python3
"""anilist-cli: a small command-line tool for AniList (and MangaDex) data.

Commands
--------
  anilist-cli releases anime [--upcoming] [--hours N] [--limit N]
  anilist-cli releases manga [--source mangadex|anilist] [--limit N] [--lang en]
  anilist-cli list [USERNAME] [--type ANIME|MANGA] [--status CURRENT|PLANNING|...]
  anilist-cli config set-username USERNAME
  anilist-cli config show
"""

import click
from rich.console import Console
from rich.panel import Panel

from . import anilist_api, config, display, mangadex_api

console = Console()


def _resolve_username(username):
    """Return a username to use, falling back to config; prints an error
    and returns None if none is available."""
    username = username or config.get_username()
    if not username:
        console.print(
            "[red]--following requires a username.[/red] Pass "
            "[bold]--username YourName[/bold], or save a default with "
            "[bold]anilist-cli config set-username YourName[/bold]."
        )
        return None
    return username


def _fetch_following(username, media_type):
    """Wrapper around anilist_api.get_following with error handling.

    Returns (ids, titles) or (None, None) on error (after printing it).
    """
    try:
        with console.status(f"[bold blue]Fetching {media_type.lower()} list for {username}..."):
            return anilist_api.get_following(username, media_type=media_type)
    except RuntimeError as exc:
        console.print(f"[red]AniList error:[/red] {exc}")
        return None, None
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Failed to fetch your list:[/red] {exc}")
        return None, None


@click.group()
@click.version_option(version="0.1.0", prog_name="anilist-cli")
def cli():
    """A simple CLI for AniList — check new releases and your lists."""


# ---------------------------------------------------------------------------
# releases
# ---------------------------------------------------------------------------

@cli.group()
def releases():
    """Show new anime or manga releases."""


@releases.command("anime")
@click.option("--hours", default=24, show_default=True, help="Time window in hours.")
@click.option("--limit", default=20, show_default=True, help="Number of results to show.")
@click.option(
    "--upcoming",
    is_flag=True,
    default=False,
    help="Show upcoming episodes instead of recently aired ones.",
)
@click.option(
    "--following",
    is_flag=True,
    default=False,
    help="Only show episodes for anime on your watching/rewatching list.",
)
@click.option(
    "--username",
    default=None,
    help="AniList username for --following (defaults to saved config).",
)
def releases_anime(hours, limit, upcoming, following, username):
    """Recently aired (default) or upcoming anime episodes."""
    following_ids = None

    if following:
        username = _resolve_username(username)
        if username is None:
            return
        following_ids, _ = _fetch_following(username, "ANIME")
        if following_ids is None:
            return
        if not following_ids:
            console.print(
                Panel(
                    f"'{username}' has no anime in CURRENT/REPEATING status.",
                    style="yellow",
                )
            )
            return

    fetch_limit = 50 if following else limit

    try:
        if upcoming:
            with console.status("[bold blue]Fetching upcoming episodes from AniList..."):
                schedules = anilist_api.upcoming_episodes(hours=hours, per_page=fetch_limit)
            if following_ids is not None:
                schedules = [s for s in schedules if s["media"]["id"] in following_ids][:limit]
                if not schedules:
                    console.print(
                        Panel(
                            f"No upcoming episodes in the next {hours}h for anime "
                            f"'{username}' is following.",
                            style="yellow",
                        )
                    )
                    return
            display.show_upcoming_anime(schedules, hours)
        else:
            with console.status("[bold blue]Fetching recently aired episodes from AniList..."):
                schedules = anilist_api.recently_aired(hours=hours, per_page=fetch_limit)
            if following_ids is not None:
                schedules = [s for s in schedules if s["media"]["id"] in following_ids][:limit]
                if not schedules:
                    console.print(
                        Panel(
                            f"No episodes aired in the last {hours}h for anime "
                            f"'{username}' is following.",
                            style="yellow",
                        )
                    )
                    return
            display.show_recent_anime(schedules, hours)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Failed to fetch data:[/red] {exc}")


@releases.command("manga")
@click.option("--limit", default=20, show_default=True, help="Number of results to show.")
@click.option(
    "--lang",
    default="en",
    show_default=True,
    help="Translated language code (used with --source mangadex).",
)
@click.option(
    "--source",
    default="mangadex",
    show_default=True,
    type=click.Choice(["mangadex", "anilist"], case_sensitive=False),
    help="Where to pull manga release data from.",
)
@click.option(
    "--following",
    is_flag=True,
    default=False,
    help="Only show chapters/series for manga on your reading/rereading list.",
)
@click.option(
    "--username",
    default=None,
    help="AniList username for --following (defaults to saved config).",
)
def releases_manga(limit, lang, source, following, username):
    """Recently released manga chapters (MangaDex) or newly added manga (AniList)."""
    following_ids = None
    following_titles = None

    if following:
        username = _resolve_username(username)
        if username is None:
            return
        following_ids, following_titles = _fetch_following(username, "MANGA")
        if following_ids is None:
            return
        if not following_ids:
            console.print(
                Panel(
                    f"'{username}' has no manga in CURRENT/REPEATING status.",
                    style="yellow",
                )
            )
            return

    fetch_limit = 100 if following else limit

    try:
        if source.lower() == "mangadex":
            with console.status("[bold blue]Fetching recent chapters from MangaDex..."):
                chapters = mangadex_api.recent_chapters(limit=fetch_limit, lang=lang)

            if following_ids is not None:
                matched = []
                for c in chapters:
                    al_id = mangadex_api.extract_anilist_id(c)
                    title = mangadex_api.extract_manga_title(c).strip().lower()
                    if (al_id is not None and al_id in following_ids) or (
                        title in following_titles
                    ):
                        matched.append(c)
                chapters = matched[:limit]
                if not chapters:
                    console.print(
                        Panel(
                            f"No recent chapters found for manga '{username}' is reading.",
                            style="yellow",
                        )
                    )
                    return

            display.show_manga_chapters(
                chapters,
                mangadex_api.extract_manga_title,
                mangadex_api.extract_scanlation_group,
            )
        else:
            with console.status("[bold blue]Fetching new manga from AniList..."):
                media = anilist_api.newly_added_manga(per_page=fetch_limit)

            if following_ids is not None:
                media = [m for m in media if m["id"] in following_ids][:limit]
                if not media:
                    console.print(
                        Panel(
                            f"No newly-added/releasing series found for manga "
                            f"'{username}' is reading.",
                            style="yellow",
                        )
                    )
                    return

            display.show_new_manga(media)
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Failed to fetch data:[/red] {exc}")


# ---------------------------------------------------------------------------
# list
# ---------------------------------------------------------------------------

@cli.command("list")
@click.argument("username", required=False)
@click.option(
    "--type",
    "media_type",
    default="ANIME",
    show_default=True,
    type=click.Choice(["ANIME", "MANGA"], case_sensitive=False),
    help="Which list to show.",
)
@click.option(
    "--status",
    default=None,
    type=click.Choice(
        ["CURRENT", "PLANNING", "COMPLETED", "DROPPED", "PAUSED", "REPEATING"],
        case_sensitive=False,
    ),
    help="Only show this status (e.g. CURRENT for watching/reading).",
)
def show_list(username, media_type, status):
    """Show a user's AniList anime or manga list.

    USERNAME is optional if you've set a default with:
    `anilist-cli config set-username <name>`
    """
    username = username or config.get_username()
    if not username:
        console.print(
            "[red]No username given.[/red] Pass one, e.g. "
            "[bold]anilist-cli list YourName[/bold], or save a default with "
            "[bold]anilist-cli config set-username YourName[/bold]."
        )
        return

    try:
        with console.status(f"[bold blue]Fetching {media_type.lower()} list for {username}..."):
            lists = anilist_api.get_user_list(username, media_type=media_type)
    except RuntimeError as exc:
        console.print(f"[red]AniList error:[/red] {exc}")
        return
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]Failed to fetch list:[/red] {exc}")
        return

    if not lists:
        console.print(
            f"[yellow]No {media_type.lower()} list found for '{username}'. "
            "Check the username and that the list is public.[/yellow]"
        )
        return

    display.show_user_list(lists, status_filter=status)


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------

@cli.group(name="config")
def config_group():
    """Manage anilist-cli configuration (e.g. your default username)."""


@config_group.command("set-username")
@click.argument("username")
def set_username(username):
    """Save a default AniList username, used by 'list' when none is given."""
    if not anilist_api.user_exists(username):
        console.print(
            f"[yellow]Warning:[/yellow] could not verify user '{username}' on AniList "
            "(no internet access or the user doesn't exist). Saving anyway."
        )
    config.set_username(username)
    console.print(f"[green]Default username set to '{username}'.[/green]")


@config_group.command("show")
def show_config():
    """Show current configuration values."""
    cfg = config.load_config()
    if not cfg:
        console.print("No configuration set yet.")
        return
    for key, value in cfg.items():
        console.print(f"{key}: {value}")


def main():
    cli()


if __name__ == "__main__":
    main()
