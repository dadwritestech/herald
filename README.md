# herald

**Your repo's data changes, posted for you.** A daily CI job reads what changed in your
repo (new measurements, a release tag, a new gallery entry) and posts it to X, Bluesky
and Mastodon, labelled as an automated account. One Python file, standard library only.

```
python .herald/feed.py | python .herald/herald.py --repo my-repo          # dry run: print the posts
python .herald/feed.py | python .herald/herald.py --repo my-repo --post   # post them
```

## How it works
- **Your repo writes the feed.** `.herald/feed.py` prints one JSON event per line:
  `{"id": "...", "text": "...", "link": "...", "priority": 0}`. Only you know what is news
  in your data, so the feed lives in your repo. [`feeds/entries.py`](feeds/entries.py) is a
  ready-made feed for release tags and new files in a folder.
- **herald does the rest:**
  - Each `id` is posted once, ever. The record is `.herald/state.json`, which CI commits back.
  - At most `--max-posts` per run (default 1), and nothing within `--min-gap-hours` of the
    last post.
  - Text is trimmed at a word boundary to each platform's limit; X counts links as 23 characters.
  - `@mentions` are defused with a zero-width space. A bot never pings people.
  - A platform with no credentials is skipped. One failing platform doesn't block the others.
- **First run on an old repo:** `--mark-posted` records everything the feed prints now as
  already posted, so the bot starts with news and not the backlog.

## Credentials (CI secrets)
| Platform | Secrets |
|---|---|
| X | `HERALD_X_API_KEY`, `HERALD_X_API_SECRET`, `HERALD_X_ACCESS_TOKEN`, `HERALD_X_ACCESS_SECRET` (OAuth 1.0a, app with write access) |
| Bluesky | `HERALD_BSKY_HANDLE` (variable), `HERALD_BSKY_APP_PASSWORD` (an app password, not the account password) |
| Mastodon | `HERALD_MASTODON_URL` (variable), `HERALD_MASTODON_TOKEN` (`write:statuses` scope) |

The workflow only runs when the repo variable `HERALD_ENABLED` is `true`.

## Be a good bot
Mark the account as automated: X has an "Automated" label in account settings, Mastodon a
"bot" checkbox, and herald self-labels Bluesky posts as `bot`. Post facts from your data, link
the source, and never reply to or mention people automatically.

## Feeds in the wild
token-tax (weekly language fact, new tokenizers) · fineprint (AI vendor terms and pricing
changes) · rejectall-index (hardest cookie banners to refuse) · nerf-watch (statistically
significant model score changes only) · sitepatch (patches broken and self-healed) ·
world-ears (what TV in several countries all talked about) · reskin, awesome-motion-md,
awesome-voice, one-file-saas, necromancer (new entries) · plus release tags everywhere.

## License
Apache-2.0
