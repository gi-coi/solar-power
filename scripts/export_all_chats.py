"""Export every session in the current project as one JSON *per session*.

Sketch (v1): runs from the current session, discovers every session in the
same OpenCode project (sub-agent sessions included) and records *all* messages
— no type filter and no "stop at the last user message" cutoff. Assistant
thinking is captured in a `thinking` field.

Output: one file per session under an output directory (default `agent-chats/`).
Filenames are meaningful and stable, so re-running overwrites the same file:

    <session-date>-<slugified-title>-<short-id>[-subagent].json

Design decisions (recorded here so they can be revised):
  * Project scope = the `project_id` of the current session. Fallback: the
    current working directory matched against `session_v2.directory`.
  * Sub-agents are included and flagged with a `-subagent` filename suffix;
    `parent_id` / `children` preserve the tree.
  * Every `session_message` row is kept, of types: user, assistant, system,
    idle, synthetic (the sub-agent result notifications in the parent).
  * Filenames use the session *title* (slugified) plus a short id suffix, not
    the random `slug` column. The date is the session's own creation date so a
    re-run targets the same file. Only if a title is edited between runs would
    the filename drift (a new file is then written alongside the old one).
  * Existing files are overwritten in place (the file is keyed to the session).
  * Tool calls are reduced to names by default. Pass `--full-tools` to embed
    each tool call's input/output (can be very large).
  * NOTE: because we keep everything, running this from a session will include
    the export command itself (and the assistant's export turns) in that
    session's transcript. That is the honest "all messages recorded" record.

Usage:
    uv run python scripts/export_all_chats.py [output_dir] [--full-tools]

Defaults: session from $OPENCODE_SESSION_ID; output dir `agent-chats/`.
"""

import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

DB = os.path.expanduser("~/.local/share/opencode/opencode.db")


def iso(ms: int) -> str:
    """Convert an epoch-millisecond timestamp to an ISO-8601 UTC string."""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).isoformat()


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-") or "untitled"


def short_id(session_id: str) -> str:
    return session_id.split("_", 1)[-1][:8]


def find_project(con: sqlite3.Connection, session_id: str, cwd: str) -> dict:
    """Locate the project to export: prefer the session's own project_id."""
    if session_id:
        row = con.execute(
            "SELECT s.project_id, s.directory, p.name, p.vcs "
            "FROM session_v2 s LEFT JOIN project p ON p.id = s.project_id "
            "WHERE s.id = ?",
            (session_id,),
        ).fetchone()
        if row:
            return {
                "project_id": row["project_id"],
                "directory": row["directory"],
                "name": row["name"],
                "vcs": row["vcs"],
            }

    row = con.execute(
        "SELECT s.project_id, s.directory, p.name, p.vcs "
        "FROM session_v2 s LEFT JOIN project p ON p.id = s.project_id "
        "WHERE s.directory = ? LIMIT 1",
        (cwd,),
    ).fetchone()
    if not row:
        raise SystemExit("No project found for the current session or directory.")
    return {
        "project_id": row["project_id"],
        "directory": row["directory"],
        "name": row["name"],
        "vcs": row["vcs"],
    }


def map_assistant(con: sqlite3.Connection, message_id: str, full_tools: bool) -> dict:
    """Reconstruct an assistant message from its parts (text/thinking/tools)."""
    parts = con.execute(
        "SELECT type, data FROM session_part WHERE message_id = ? ORDER BY ordinal",
        (message_id,),
    ).fetchall()

    text_parts, thinking_parts, tool_calls = [], [], []
    for p in parts:
        pd = json.loads(p["data"])
        if p["type"] == "text":
            text_parts.append(pd.get("text", ""))
        elif p["type"] == "reasoning":
            thinking_parts.append(pd.get("text", ""))
        elif p["type"] == "tool":
            call = {"name": pd.get("name", "")}
            if full_tools:
                state = pd.get("state", {})
                call["input"] = state.get("input")
                call["output"] = state.get("output")
            tool_calls.append(call)

    out = {}
    if text_parts:
        out["content"] = "\n".join(text_parts)
    if thinking_parts:
        out["thinking"] = "\n".join(thinking_parts)
    if tool_calls:
        out["tool_calls"] = tool_calls
    return out


def map_message(con: sqlite3.Connection, m: sqlite3.Row, full_tools: bool) -> dict:
    """Map one session_message row to a plain dict, keeping every message type."""
    data = json.loads(m["data"])
    t = m["type"]
    out = {"seq": m["seq"], "role": t, "created_at": iso(m["time_created"])}

    if t == "user":
        out["content"] = data.get("text", "")
    elif t == "system":
        out["content"] = data.get("text", "")
        out["notice"] = (data.get("metadata") or {}).get("notice")
    elif t == "idle":
        out["outcome"] = data.get("outcome")
    elif t == "synthetic":
        md = data.get("metadata") or {}
        out["content"] = data.get("text", "")
        out["source"] = md.get("source")
        out["child_id"] = md.get("childID")
        out["agent"] = md.get("agent")
        out["state"] = md.get("state")
    elif t == "assistant":
        out.update(map_assistant(con, m["id"], full_tools))

    return out


def load_session(con: sqlite3.Connection, s: sqlite3.Row, full_tools: bool) -> dict:
    """Load one session and all of its messages, in order."""
    msgs = con.execute(
        "SELECT id, seq, type, data, time_created FROM session_message "
        "WHERE session_id = ? ORDER BY seq",
        (s["id"],),
    ).fetchall()

    return {
        "session_id": s["id"],
        "parent_id": s["parent_id"],
        "is_subagent": bool(s["parent_id"]),
        "title": s["title"],
        "model": s["model"],
        "agent": s["agent"],
        "directory": s["directory"],
        "created_at": iso(s["time_created"]),
        "updated_at": iso(s["time_updated"]),
        "messages": [map_message(con, m, full_tools) for m in msgs],
    }


def filename_for(rec: dict, out_dir: str) -> str:
    """Deterministic, meaningful filename for a session's transcript."""
    date = rec["created_at"][:10]  # session creation date, stable across runs
    base = f"{date}-{slugify(rec['title'])}-{short_id(rec['session_id'])}"
    if rec["is_subagent"]:
        base += "-subagent"
    return os.path.join(out_dir, f"{base}.json")


def load_all(session_id: str, cwd: str, full_tools: bool) -> dict:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row

    project = find_project(con, session_id, cwd)

    sessions = con.execute(
        "SELECT * FROM session_v2 WHERE project_id = ? ORDER BY time_created",
        (project["project_id"],),
    ).fetchall()

    children = {}
    for s in sessions:
        children.setdefault(s["parent_id"], []).append(s["id"])

    records = []
    for s in sessions:
        rec = load_session(con, s, full_tools)
        rec["children"] = children.get(s["id"], [])
        records.append(rec)

    con.close()

    return {
        "project": project,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "note": (
            "Full transcript of every session in this project (sub-agents included), "
            "recording all message types. Assistant 'thinking' holds internal reasoning."
        ),
        "session_count": len(records),
        "sessions": records,
    }


def main() -> int:
    full_tools = "--full-tools" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]

    session_id = os.environ.get("OPENCODE_SESSION_ID")
    cwd = os.getcwd()
    doc = load_all(session_id, cwd, full_tools)

    out_dir = args[0] if args else "agent-chats"
    os.makedirs(out_dir, exist_ok=True)

    project = doc["project"]
    exported_at = doc["exported_at"]

    created, overwritten = 0, 0
    for rec in doc["sessions"]:
        path = filename_for(rec, out_dir)
        single = {
            "project_id": project["project_id"],
            "project_directory": project["directory"],
            "exported_at": exported_at,
            **rec,
        }
        existed = os.path.exists(path)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(single, f, ensure_ascii=False, indent=2)
            f.write("\n")
        if existed:
            overwritten += 1
        else:
            created += 1
        print(f"{'overwrote' if existed else 'wrote':9s} {path}")

    print(f"\n{created} created, {overwritten} overwritten "
          f"({doc['session_count']} sessions, project {project['project_id']})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
