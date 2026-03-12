#!/usr/bin/env python3
"""Fetch GitHub repos and blog posts to update the profile README."""

import json
import re
import subprocess
import tempfile
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

README = Path("README.md")
EXCLUDED_REPOS = {"dortort", "dortort.github.io", "homebrew-tap"}
POST_DIRS = ("_posts", "content/posts", "content/post", "src/posts", "posts")
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})")
SLUG_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}-")


def fetch_projects() -> str:
    cutoff = (datetime.now(timezone.utc) - timedelta(days=91)).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )
    result = subprocess.run(
        [
            "gh", "api",
            "users/dortort/repos?per_page=100&sort=pushed&direction=desc",
            "--paginate",
            "--jq",
            f'.[] | select('
            f'.private == false'
            f' and .pushed_at > "{cutoff}"'
            f' and .name != "dortort"'
            f' and .name != "dortort.github.io"'
            f' and .name != "homebrew-tap"'
            f') | [.name, .html_url, (.description // "")] | @tsv',
        ],
        capture_output=True, text=True, check=True,
    )

    lines = []
    for row in result.stdout.strip().splitlines():
        parts = row.split("\t")
        name, url = parts[0], parts[1]
        desc = parts[2] if len(parts) > 2 else ""
        if desc and not re.search(r"[.!?]$", desc):
            desc += "."
        lines.append(f"- [{name}]({url}) — {desc}" if desc else f"- [{name}]({url})")

    lines.sort(key=lambda l: l.lower())
    return "\n".join(lines)


def strip_quotes(s: str) -> str:
    for q in ('"', "'"):
        if s.startswith(q):
            s = s[1:]
        if s.endswith(q):
            s = s[:-1]
    return s


def parse_frontmatter(path: Path) -> tuple[str | None, str | None]:
    title = date_val = None
    in_fm = False
    for line in path.read_text(errors="replace").splitlines():
        if line.strip() == "---":
            if in_fm:
                break
            in_fm = True
            continue
        if not in_fm:
            continue
        if m := re.match(r"^title:\s*(.*)", line):
            title = strip_quotes(m.group(1).strip())
        if m := re.match(r"^date:\s*(.*)", line):
            raw = strip_quotes(m.group(1).strip())
            if dm := DATE_RE.match(raw):
                date_val = dm.group(1)
    return title, date_val


def fetch_posts() -> str:
    blog_dir = Path(tempfile.mkdtemp())
    try:
        subprocess.run(
            ["git", "clone", "--depth", "1",
             "https://github.com/dortort/dortort.github.io.git", str(blog_dir)],
            check=True, capture_output=True,
        )

        posts: list[tuple[str, str, str]] = []
        for sub in POST_DIRS:
            d = blog_dir / sub
            if not d.is_dir():
                continue
            for f in d.iterdir():
                if f.suffix not in (".md", ".markdown"):
                    continue
                title, date_val = parse_frontmatter(f)

                # Fallback: extract date from filename
                if not date_val:
                    if dm := DATE_RE.match(f.name):
                        date_val = dm.group(1)

                if not date_val or not title:
                    continue

                slug = SLUG_DATE_RE.sub("", f.stem)
                if slug.endswith(".markdown"):
                    slug = slug.removesuffix(".markdown")
                url = f"https://dortort.com/posts/{slug}/"
                posts.append((date_val, title, url))

        posts.sort(key=lambda p: p[0], reverse=True)
        lines = [f"- {d} — [{t}]({u})" for d, t, u in posts[:15]]
        return "\n".join(lines)
    finally:
        shutil.rmtree(blog_dir, ignore_errors=True)


def update_readme(projects: str, writing: str) -> None:
    text = README.read_text()
    sections = {
        ("<!-- CURRENT_PROJECTS_START -->", "<!-- CURRENT_PROJECTS_END -->"): projects,
        ("<!-- LATEST_WRITING_START -->", "<!-- LATEST_WRITING_END -->"): writing,
    }
    for (start_tag, end_tag), content in sections.items():
        pattern = re.compile(
            rf"({re.escape(start_tag)}\n).*?(\n{re.escape(end_tag)})",
            re.DOTALL,
        )
        replacement = rf"\g<1>{content}\g<2>" if content else rf"\g<1>\g<2>"
        text = pattern.sub(replacement, text)

    README.write_text(text)


def main() -> None:
    projects = fetch_projects()
    writing = fetch_posts()
    update_readme(projects, writing)
    print("README updated successfully.")


if __name__ == "__main__":
    main()
