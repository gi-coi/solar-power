"""Export an OpenCode session transcript as JSON for `agent-chats/`.

Reads the local OpenCode SQLite database and reconstructs a transcript of
user + assistant messages only. System updates and idle markers are omitted;
tool calls are reduced to their names, and the assistant's internal reasoning
("thinking") is captured in a `thinking` field on each assistant message.

Only messages up to and including the most recent *user* message are captured,
so the export's own tool activity is not included in the transcript.

Usage:
    uv run python scripts/export_chat.py [output.json]

Defaults: session from $OPENCODE_SESSION_ID, output path derived from the date
and a slug of the session title.
"""

import json
import os
import re
import sqlite3
import sys
from datetime import datetime, timezone

DB = os.path.expanduser("~/.local/share/opencode/opencode.db")


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def load(session_id: str) -> dict:
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    cur = con.cursor()

    row = cur.execute("SELECT title FROM session_v2 WHERE id = ?", (session_id,)).fetchone()
    title = row["title"] if row and row["title"] else ""

    # Capture everything up to and including the last user message.
    last_user = cur.execute(
        "SELECT MAX(seq) AS s FROM session_message WHERE session_id = ? AND type = 'user'",
        (session_id,),
    ).fetchone()["s"]

    msgs = cur.execute(
        "SELECT id, seq, type, data FROM session_message "
        "WHERE session_id = ? AND type IN ('user', 'assistant') AND seq <= ? "
        "ORDER BY seq",
        (session_id, last_user),
    ).fetchall()

    messages = []
    for m in msgs:
        data = json.loads(m["data"])
        if m["type"] == "user":
            messages.append({"role": "user", "content": data.get("text", "")})
            continue

        parts = cur.execute(
            "SELECT type, data FROM session_part WHERE message_id = ? ORDER BY ordinal",
            (m["id"],),
        ).fetchall()

        text_parts = []
        thinking_parts = []
        tool_names = []
        for p in parts:
            pd = json.loads(p["data"])
            if p["type"] == "text":
                text_parts.append(pd.get("text", ""))
            elif p["type"] == "reasoning":
                thinking_parts.append(pd.get("text", ""))
            elif p["type"] == "tool":
                tool_names.append(pd.get("name", ""))

        entry = {"role": "assistant"}
        if text_parts:
            entry["content"] = "\n".join(text_parts)
        if thinking_parts:
            entry["thinking"] = "\n".join(thinking_parts)
        if tool_names:
            entry["tool_calls"] = tool_names
        messages.append(entry)

    con.close()
    return {
        "session": session_id,
        "title": title,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "note": "Transcript of user and assistant messages only; system updates and idle markers omitted. Assistant 'thinking' holds internal reasoning.",
        "messages": messages,
    }


def main() -> int:
    session_id = os.environ.get("OPENCODE_SESSION_ID")
    if not session_id:
        print("OPENCODE_SESSION_ID is not set", file=sys.stderr)
        return 1

    doc = load(session_id)

    if len(sys.argv) > 1:
        out = sys.argv[1]
    else:
        date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        out = f"agent-chats/{date}-{slugify(doc['title'])}.json"

    with open(out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print(f"Wrote {out}: {len(doc['messages'])} messages "
          f"(session {session_id}, title '{doc['title']}')")
    return 0


if __name__ == "__main__":
    sys.exit(main())
