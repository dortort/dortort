#!/usr/bin/env bash
set -euo pipefail

README="README.md"

# ── Current Projects ──────────────────────────────────────────────
# Public repos active in the last 3 months, excluding profile and blog repos

THREE_MONTHS_AGO=$(python3 -c "
from datetime import datetime, timedelta, timezone
print((datetime.now(timezone.utc) - timedelta(days=91)).strftime('%Y-%m-%dT%H:%M:%SZ'))
")

PROJECT_LINES=""
while IFS=$'\t' read -r name url desc; do
  if [ -n "$desc" ]; then
    [[ "$desc" =~ [.!?]$ ]] || desc="$desc."
    PROJECT_LINES+="- [$name]($url) — $desc"$'\n'
  else
    PROJECT_LINES+="- [$name]($url)"$'\n'
  fi
done < <(
  gh api "users/dortort/repos?per_page=100&sort=pushed&direction=desc" \
    --paginate \
    --jq ".[] | select(
      .private == false
      and .pushed_at > \"$THREE_MONTHS_AGO\"
      and .name != \"dortort\"
      and .name != \"dortort.github.io\"
      and .name != \"homebrew-tap\"
    ) | [.name, .html_url, (.description // \"\")] | @tsv"
)

# ── Latest Writing ────────────────────────────────────────────────
# 10 most recent blog posts from the dortort.github.io repo

BLOG_DIR=$(mktemp -d)
trap 'rm -rf "$BLOG_DIR" 2>/dev/null || true' EXIT

git clone --depth 1 https://github.com/dortort/dortort.github.io.git "$BLOG_DIR"

strip_quotes() {
  local v="$1"
  v="${v#\"}" ; v="${v%\"}"
  v="${v#\'}" ; v="${v%\'}"
  printf '%s' "$v"
}

POSTS=()
for dir in "$BLOG_DIR/_posts" "$BLOG_DIR/content/posts" "$BLOG_DIR/content/post" "$BLOG_DIR/src/posts" "$BLOG_DIR/posts"; do
  [ -d "$dir" ] || continue
  while IFS= read -r file; do
    title="" date_val="" in_fm=false
    bn=$(basename "$file")

    while IFS= read -r line; do
      if [[ "$line" == "---" ]]; then
        $in_fm && break
        in_fm=true; continue
      fi
      $in_fm || continue

      if [[ "$line" =~ ^title:\ *(.*) ]]; then
        title=$(strip_quotes "${BASH_REMATCH[1]}")
      fi
      if [[ "$line" =~ ^date:\ *(.*) ]]; then
        date_val=$(strip_quotes "${BASH_REMATCH[1]}")
        [[ "$date_val" =~ ^([0-9]{4}-[0-9]{2}-[0-9]{2}) ]] && date_val="${BASH_REMATCH[1]}" || date_val=""
      fi
    done < "$file"

    # Fallback: extract date from filename
    if [ -z "$date_val" ]; then
      if [[ "$bn" =~ ^([0-9]{4}-[0-9]{2}-[0-9]{2})- ]]; then
        date_val="${BASH_REMATCH[1]}"
      fi
    fi

    [[ -z "$date_val" || -z "$title" ]] && continue

    # Build URL from filename slug
    slug="${bn#[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]-}"
    slug="${slug%.md}" ; slug="${slug%.markdown}" ; slug="${slug%.html}"

    url="https://dortort.com/posts/$slug/"
    POSTS+=("$date_val"$'\t'"$title"$'\t'"$url")
  done < <(find "$dir" -type f \( -name '*.md' -o -name '*.markdown' \))
done

WRITING_LINES=""
if [ ${#POSTS[@]} -gt 0 ]; then
  while IFS=$'\t' read -r d t u; do
    WRITING_LINES+="- $d — [$t]($u)"$'\n'
  done < <(printf '%s\n' "${POSTS[@]}" | sort -t$'\t' -k1 -r | head -10)
fi

# ── Update README ─────────────────────────────────────────────────

PROJECT_LINES=$(printf '%s' "$PROJECT_LINES" | sort -f)
PROJECT_LINES="${PROJECT_LINES%$'\n'}"
WRITING_LINES="${WRITING_LINES%$'\n'}"

awk \
  -v projects="$PROJECT_LINES" \
  -v writing="$WRITING_LINES" \
'
/<!-- CURRENT_PROJECTS_START -->/ { print; if (projects != "") print projects; skip=1; next }
/<!-- CURRENT_PROJECTS_END -->/   { skip=0 }
/<!-- LATEST_WRITING_START -->/   { print; if (writing != "") print writing; skip=1; next }
/<!-- LATEST_WRITING_END -->/     { skip=0 }
!skip { print }
' "$README" > "${README}.tmp"

mv "${README}.tmp" "$README"

echo "README updated successfully."
