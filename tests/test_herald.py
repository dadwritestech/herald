import datetime as dt
import io
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import herald  # noqa: E402

NOW = dt.datetime(2026, 11, 3, 12, 0, tzinfo=dt.timezone.utc)


def ev(i, text="hello", **kw):
    return json.dumps({"id": i, "text": text, **kw})


def test_oauth1_matches_twitter_docs_example():
    # The worked example from X's "Creating a signature" docs.
    h = herald.oauth1_header(
        "POST", "https://api.twitter.com/1.1/statuses/update.json?include_entities=true",
        "xvz1evFS4wEEPTGEFPHBog", "kAcSOqF21Fu85e7zjz7ZN2U4ZRhfV3WpwPAoE3Z7kBw",
        "370773112-GmHxMAgYyLbNEtIKZeRNFsMKPR9EyMZeS9weJAEb",
        "LswwdoUaIvS8ltyTt5jkRh4J50vUPVVHtR2YPi5kE",
        nonce="kYjzVBB8Y0ZFabxSWbWovY3uYSQ2pTgmZeNu2VS4cg", ts=1318622958,
        form={"status": "Hello Ladies + Gentlemen, a signed OAuth request!"})
    assert 'oauth_signature="hCtSmYh%2BiHYCEqBWrE7C7hYmtUk%3D"' in h


def test_mentions_are_defused():
    out = herald.clean_text("thanks @someone and mail me@example.com")
    assert "@​someone" in out
    assert "me@example.com" in out  # emails untouched


def test_parse_rejects_bad_and_dedupes():
    with pytest.raises(herald.BadEvent):
        herald.parse_events(['{"id": "a"}'])
    evs = herald.parse_events([ev("a"), ev("a", "dup"), "", "# comment", ev("b")])
    assert [e["id"] for e in evs] == ["a", "b"]


def test_compose_trims_and_counts_links_as_23_on_x():
    long = "word " * 80
    t = herald.compose({"text": long, "link": "https://example.com/" + "x" * 100}, "x")
    body, link = t.rsplit("\n\n", 1)
    assert len(body) + 2 + 23 <= 280 and body.endswith("…")
    t2 = herald.compose({"text": "short"}, "mastodon")
    assert t2 == "short"


def test_bsky_facets_use_byte_offsets():
    text = "Telugu తెలుగు https://x.io/a"
    f = herald.bsky_facets(text)[0]["index"]
    assert text.encode()[f["byteStart"]:f["byteEnd"]] == b"https://x.io/a"


def test_select_priority_gap_and_already_posted():
    evs = herald.parse_events([ev("a"), ev("b", priority=5), ev("c")])
    st = {"posted": {"c": {}}, "last_post_at": None}
    assert [e["id"] for e in herald.select(evs, st, 2, 6, NOW)] == ["b", "a"]
    st["last_post_at"] = (NOW - dt.timedelta(hours=1)).isoformat()
    assert herald.select(evs, st, 2, 6, NOW) == []


class FakeOK:
    name = "x"
    sent = []

    def __init__(self, env):
        self.ready = True

    def post(self, text):
        FakeOK.sent.append(text)
        return "https://x.com/i/web/status/1"


class FakeFail(FakeOK):
    name = "mastodon"

    def post(self, text):
        raise RuntimeError("boom")


def test_run_dry_run_writes_nothing(tmp_path):
    state = tmp_path / "s.json"
    out = io.StringIO()
    rc = herald.run([ev("a")], repo="r", state_path=str(state), post=False, max_posts=1,
                    min_gap_h=0, env={}, out=out, now=NOW)
    assert rc == 0 and not state.exists() and "--- a -> x" in out.getvalue()


def test_run_post_records_state_and_isolates_failures(tmp_path):
    state = tmp_path / "s.json"
    FakeOK.sent = []
    out = io.StringIO()
    rc = herald.run([ev("a"), ev("b")], repo="r", state_path=str(state), post=True,
                    max_posts=1, min_gap_h=0, env={}, out=out, now=NOW,
                    platforms=(FakeOK, FakeFail))
    st = json.loads(state.read_text())
    assert rc == 1  # a platform failed, so CI shows red
    assert list(st["posted"]) == ["a"] and FakeOK.sent == ["hello"]
    # second run: 'a' is done, 'b' is next
    herald.run([ev("a"), ev("b")], repo="r", state_path=str(state), post=True, max_posts=1,
               min_gap_h=0, env={}, out=out, now=NOW, platforms=(FakeOK,))
    assert FakeOK.sent == ["hello", "hello"]
    assert set(json.loads(state.read_text())["posted"]) == {"a", "b"}


def test_post_without_credentials_posts_nothing(tmp_path):
    out = io.StringIO()
    herald.run([ev("a")], repo="r", state_path=str(tmp_path / "s.json"), post=True,
               max_posts=1, min_gap_h=0, env={}, out=out, now=NOW)
    assert "nothing posted" in out.getvalue()
    assert not (tmp_path / "s.json").exists()


def test_mark_posted_baseline(tmp_path, monkeypatch, capsys):
    state = tmp_path / "s.json"
    monkeypatch.setattr(sys, "stdin", io.StringIO(ev("a") + "\n" + ev("b")))
    herald.main(["--repo", "r", "--state", str(state), "--mark-posted"])
    assert set(json.loads(state.read_text())["posted"]) == {"a", "b"}
