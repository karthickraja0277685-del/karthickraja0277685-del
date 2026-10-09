
#!/usr/bin/env python3
"""Generate an SVG calendar from public GitHub contribution data."""

from datetime import date, timedelta
from html import escape
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
import json
import os
import sys
import xml.etree.ElementTree as ET

USERNAME = "karthickraja0277685-del"
OUTPUT = "assets/contrib-heatmap.svg"
API_URL = "https://api.github.com/graphql"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
            color
          }
        }
      }
    }
  }
}
"""


def fetch_contributions():
    token = os.environ.get("GH_TOKEN")
    if not token:
        raise RuntimeError(
            "GH_TOKEN is not set. Configure it as a GitHub Actions secret."
        )

    body = json.dumps({
        "query": QUERY,
        "variables": {"login": USERNAME},
    }).encode()

    request = Request(
        API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "User-Agent": "profile-heatmap-generator",
        },
        method="POST",
    )

    with urlopen(request, timeout=20) as response:
        result = json.loads(response.read())

    if result.get("errors"):
        raise RuntimeError("GitHub API returned GraphQL errors.")

    user = result.get("data", {}).get("user")
    if not user:
        raise RuntimeError("GitHub user was not found.")

    calendar = user["contributionsCollection"]["contributionCalendar"]
    return calendar["weeks"], calendar["totalContributions"]


def generate_svg(weeks, total):
    cell = 11
    gap = 3
    left = 38
    top = 35
    width = left + len(weeks) * (cell + gap) + 8
    height = top + 7 * (cell + gap) + 32

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'viewBox="0 0 {width} {height}" role="img">',
        '<rect width="100%" height="100%" rx="8" fill="#0d1117"/>',
        '<style>text{font-family:ui-monospace,monospace}'
        '.title{fill:#e6edf3;font-size:13px;font-weight:600}'
        '.label{fill:#8b949e;font-size:9px}</style>',
        '<text x="12" y="19" class="title">'
        f'{escape(USERNAME)} · {total} contributions</text>',
    ]

    days = ["Mon", "Wed", "Fri"]
    for row, label in [(0, "Mon"), (2, "Wed"), (4, "Fri")]:
        y = top + row * (cell + gap) + 9
        parts.append(
            f'<text x="5" y="{y}" class="label">{label}</text>'
        )

    for col, week in enumerate(weeks):
        for day in week["contributionDays"]:
            day_date = date.fromisoformat(day["date"])
            row = day_date.weekday()
            x = left + col * (cell + gap)
            y = top + row * (cell + gap)
            color = day.get("color", "#161b22")
            count = int(day.get("contributionCount", 0))
            parts.append(
                f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" '
                f'rx="2" fill="{escape(color, quote=True)}">'
                f'<title>{day_date.isoformat()}: {count} contributions'
                f'</title></rect>'
            )

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    try:
        weeks, total = fetch_contributions()
        svg = generate_svg(weeks, total)
        os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
        with open(OUTPUT, "w", encoding="utf-8") as file:
            file.write(svg + "\n")
        print(f"Generated {OUTPUT}: {total} contributions.")
    except (RuntimeError, URLError, HTTPError, TimeoutError, OSError,
            ValueError, KeyError) as error:
        print(f"Heatmap generation failed: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
