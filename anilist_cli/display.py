"""Rendering helpers built on top of `rich` for a simple, colorful TUI."""

import time

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def media_title(title_obj):
    return title_obj.get("english") or title_obj.get("romaji") or "Unknown"


def _fmt_unix(ts):
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(ts))


def show_recent_anime(schedules, hours):
    if not schedules:
        console.print(
            Panel(f"No anime episodes aired in the last {hours} hour(s).", style="yellow")
        )
        return

    table = Table(title=f"📺  Recently Aired Anime (last {hours}h)")
    table.add_column("Title", style="cyan", overflow="fold")
    table.add_column("Ep", justify="right", style="magenta")
    table.add_column("Aired At", style="green")
    table.add_column("Format", style="dim")

    for s in schedules:
        m = s["media"]
        table.add_row(
            media_title(m["title"]),
            str(s["episode"]),
            _fmt_unix(s["airingAt"]),
            m.get("format") or "-",
        )

    console.print(table)


def show_upcoming_anime(schedules, hours):
    if not schedules:
        console.print(
            Panel(f"No anime episodes airing in the next {hours} hour(s).", style="yellow")
        )
        return

    table = Table(title=f"📺  Upcoming Anime Episodes (next {hours}h)")
    table.add_column("Title", style="cyan", overflow="fold")
    table.add_column("Ep", justify="right", style="magenta")
    table.add_column("Airing At", style="green")
    table.add_column("Format", style="dim")

    for s in schedules:
        m = s["media"]
        table.add_row(
            media_title(m["title"]),
            str(s["episode"]),
            _fmt_unix(s["airingAt"]),
            m.get("format") or "-",
        )

    console.print(table)


def show_new_manga(media_list):
    if not media_list:
        console.print(Panel("No newly added manga found.", style="yellow"))
        return

    table = Table(title="📚  Newly Added / Releasing Manga (AniList)")
    table.add_column("Title", style="cyan", overflow="fold")
    table.add_column("Format", style="dim")
    table.add_column("Status", style="green")
    table.add_column("Start Date")

    for m in media_list:
        sd = m.get("startDate") or {}
        if sd.get("year"):
            date_str = f"{sd.get('year')}-{sd.get('month') or '?'}-{sd.get('day') or '?'}"
        else:
            date_str = "-"
        table.add_row(
            media_title(m["title"]),
            m.get("format") or "-",
            m.get("status") or "-",
            date_str,
        )

    console.print(table)


def show_manga_chapters(chapters, extract_title, extract_group):
    if not chapters:
        console.print(Panel("No recent chapters found on MangaDex.", style="yellow"))
        return

    table = Table(title="📖  Recently Released Manga Chapters (MangaDex)")
    table.add_column("Manga", style="cyan", overflow="fold")
    table.add_column("Ch.", justify="right", style="magenta")
    table.add_column("Chapter Title", overflow="fold")
    table.add_column("Group", style="dim")
    table.add_column("Released At", style="green")

    for c in chapters:
        attrs = c.get("attributes", {})
        chapter_num = attrs.get("chapter") or "-"
        chapter_title = attrs.get("title") or ""
        readable_at = attrs.get("readableAt", "")
        if readable_at:
            readable_at = readable_at.replace("T", " ").split("+")[0]

        table.add_row(
            extract_title(c),
            str(chapter_num),
            chapter_title,
            extract_group(c),
            readable_at,
        )

    console.print(table)


STATUS_EMOJI = {
    "CURRENT": "▶️ ",
    "PLANNING": "📌",
    "COMPLETED": "✅",
    "DROPPED": "🗑️ ",
    "PAUSED": "⏸️ ",
    "REPEATING": "🔁",
}


def show_user_list(lists, status_filter=None):
    found_any = False

    for lst in lists:
        lst_status = (lst.get("status") or "").upper()
        if status_filter and lst_status != status_filter.upper():
            continue
        if not lst["entries"]:
            continue

        found_any = True
        emoji = STATUS_EMOJI.get(lst_status, "")
        title = lst["name"]
        if emoji:
            title = f"{emoji} {title}"

        table = Table(title=title)
        table.add_column("Title", style="cyan", overflow="fold")
        table.add_column("Progress", justify="right", style="magenta")
        table.add_column("Score", justify="right", style="green")
        table.add_column("Format", style="dim")

        for entry in lst["entries"]:
            m = entry["media"]
            total = m.get("episodes") or m.get("chapters")
            total_str = str(total) if total else "?"
            progress = f"{entry.get('progress', 0)}/{total_str}"
            score = entry.get("score")
            score_str = str(score) if score else "-"

            table.add_row(
                media_title(m["title"]),
                progress,
                score_str,
                m.get("format") or "-",
            )

        console.print(table)

    if not found_any:
        msg = "No entries found"
        if status_filter:
            msg += f" for status '{status_filter}'"
        console.print(Panel(msg + ".", style="yellow"))
