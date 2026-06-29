"""
query_engine.py
Plain English → SQL → Results using Claude API + your data dictionary.

Usage:
    python3 query_engine.py
    python3 query_engine.py --question "What is our hit ratio by carrier?"

Setup:
    set ANTHROPIC_API_KEY=your_key_here  (Windows PowerShell)
    python3 query_engine.py
"""

import sqlite3
import json
import os
import sys
import argparse
import textwrap
from anthropic import Anthropic
from dotenv import load_dotenv

# Ensure UTF-8 output on Windows
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

DB_PATH              = "prototype.db"
DICT_PATH            = "dataDict_Editing.json"
#APPETITE_LIVE_PATH   = "carrierAppetite_live.json"
#APPETITE_STATIC_PATH = "carrierAppetite_static.json"
MODEL                = "claude-sonnet-4-6"
CONVERSATION_HISTORY = []


def load_data_dictionary() -> dict:
    with open(DICT_PATH) as f:
        return json.load(f)

def load_semantic_model() -> dict:
    with open(DICT_PATH) as f:
        return json.load(f)
    
""" def load_appetite() -> dict:
    """Load live appetite file if available, fall back to static."""
    for path in (APPETITE_LIVE_PATH, APPETITE_STATIC_PATH):
        if os.path.exists(path):
            with open(path) as f:
                return json.load(f)
    return {}


def build_appetite_context(appetite: dict) -> str:
    """
    Formats carrier appetite data for injection into the system prompt.
    Only includes carriers that have been profiled (non-empty preferred_divisions).
    """
    carriers = appetite.get("carriers", {})
    if not carriers:
        return ""

    lines = []
    for cid, c in carriers.items():
        if not c.get("preferred_divisions") and not c.get("preferred_lobs"):
            continue
        parts = [f"{cid} | {c['carrier_name']}"]
        if c.get("market_type"):
            parts.append(f"market={c['market_type']}")
        if c.get("am_best_rating"):
            parts.append(f"AM Best={c['am_best_rating']}")
        if c.get("preferred_divisions"):
            parts.append(f"divisions={', '.join(c['preferred_divisions'])}")
        if c.get("preferred_lobs"):
            parts.append(f"prefers=[{', '.join(c['preferred_lobs'][:5])}{'...' if len(c['preferred_lobs']) > 5 else ''}]")
        if c.get("prohibited_lobs"):
            parts.append(f"WILL NOT WRITE=[{', '.join(c['prohibited_lobs'])}]")
        if c.get("prohibited_classes"):
            parts.append(f"prohibited classes=[{', '.join(c['prohibited_classes'][:3])}]")
        geo = c.get("geographic_restrictions", {})
        excl = geo.get("excluded_states", [])
        if excl:
            parts.append(f"excluded states={excl}")
        thresholds = c.get("size_thresholds", {})
        if thresholds.get("min_premium"):
            parts.append(f"min premium=${thresholds['min_premium']:,}")
        if thresholds.get("preferred_account_tiers"):
            parts.append(f"tiers={thresholds['preferred_account_tiers']}")
        if c.get("appetite_notes"):
            parts.append(f"notes: {c['appetite_notes']}")
        lines.append(" | ".join(parts))

    if not lines:
        return ""

    last_refreshed = appetite.get("_meta", {}).get("last_refreshed", "unknown")
    return (
        f"\n═══════════════════════════════\n"
        f"CARRIER APPETITE GUIDE (refreshed {last_refreshed})\n"
        f"═══════════════════════════════\n"
        f"Use this to answer questions about which carriers to approach, avoid, or compare.\n"
        f"Preferred divisions and LOBs reflect stated carrier appetite — not historical bind rates.\n\n"
        + "\n".join(lines)
    )
"""

def build_system_prompt(dd: dict, appetite: dict | None = None) -> str:
    """
    Builds the system prompt by injecting:
    1. Business glossary
    2. Table descriptions
    3. Example Q→SQL pairs
    """

    # ── Layer 1: Business glossary ────────────────────────────
    glossary_lines = []
    for term, info in dd["business_glossary"].items():
        line = f"- {term}: {info.get('definition', '')}"
        if "sql_snippet" in info:
            line += f" | SQL: {info['sql_snippet']}"
        if "data_quality_note" in info:
            line += f" | ⚠ Data quality: {info['data_quality_note']}"
        glossary_lines.append(line)
    glossary_text = "\n".join(glossary_lines)

    # ── Layer 2: Table descriptions ───────────────────────────
    tables_text = ""
    for tbl, meta in dd["tables"].items():
        tables_text += f"\nTABLE: {tbl}\n"
        tables_text += f"  Description: {meta.get('description', '')}\n"
        if "primary_key" in meta:
            tables_text += f"  Primary key: {meta['primary_key']}\n"
        if "foreign_keys" in meta:
            for col, ref in meta["foreign_keys"].items():
                tables_text += f"  {col} → {ref}\n"
        if "columns" in meta:
            for col, desc in meta["columns"].items():
                tables_text += f"  - {col}: {desc}\n"

    # ── Layer 3: Example Q→SQL pairs ─────────────────────────
    examples_text = "\n\n".join(
        f"Q: {ex['question']}\nSQL: {ex['sql']}"
        for ex in dd["example_questions_and_sql"]
    )

    # ── Layer 4: Carrier appetite guide ──────────────────────
    appetite_text = build_appetite_context(appetite or {})

    return f"""You are an expert insurance data analyst. You help users query an insurance CRM database using plain English.

Your job:
1. Understand the question using the business glossary
2. Generate a single valid SQLite SQL query to answer it
3. Return ONLY the SQL — no explanation, no markdown, no backticks
4. If the question is ambiguous, write your interpretation as a comment at the top

DATABASE ENGINE: SQLite

═══════════════════════════════
BUSINESS GLOSSARY
═══════════════════════════════
{glossary_text}

═══════════════════════════════
TABLE SCHEMAS
═══════════════════════════════
{tables_text}

═══════════════════════════════
EXAMPLE QUESTIONS → SQL
═══════════════════════════════
{examples_text}

RULES:
- Query directly from tables — there are no views in this database
- For hit ratio: use quotes table, quote_status = 'bound'
- To detect a bound quote: always use quote_status = 'bound' on the quotes table —
                           NEVER join to policies and check policy_id IS NOT NULL
- For loss ratio: join losses to policies via policy_id,
                  join policies to submissions via control_number
- For carrier appetite: query quotes grouped by carrier_id,
                        calculate decline_rate from quote_status = 'declined'
- When ranking by decline behavior: order by decline_rate_pct (percentage) by default —
                                    only order by absolute declined count if the user
                                    explicitly asks for it
- NEVER use YEAR() — use strftime('%Y', column) instead
- NEVER use GETDATE() — use date('now') instead
- Return clean readable SQL with aliases
- Limit to 20 rows unless user specifies otherwise
- If the question cannot be answered, say: -- CANNOT_ANSWER: [reason]
- For carrier appetite questions: use the CARRIER APPETITE GUIDE above to filter or rank carriers
  by stated preference, prohibited classes, or geographic restrictions — then validate against
  the quotes table for historical behavior
{appetite_text}
"""


def run_sql(sql: str) -> tuple[list, list]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.execute(sql)
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description] if cur.description else []
        return cols, [list(r) for r in rows]
    except Exception as e:
        return [], [["ERROR", str(e)]]
    finally:
        conn.close()


def format_results(cols: list, rows: list, max_col_width=28) -> str:
    if not rows:
        return "  (no results)"
    if rows[0][0] == "ERROR":
        return f"  SQL Error: {rows[0][1]}"

    widths = [
        min(max(len(str(c)), max(len(str(r[i])) for r in rows)), max_col_width)
        for i, c in enumerate(cols)
    ]

    def fmt(val, w):
        s = str(val) if val is not None else "NULL"
        return s[:w].rjust(w) if isinstance(val, (int, float)) else s[:w].ljust(w)

    header  = "  " + "  ".join(c[:w].ljust(w) for c, w in zip(cols, widths))
    divider = "  " + "  ".join("─" * w for w in widths)
    body    = "\n".join(
        "  " + "  ".join(fmt(row[i], widths[i]) for i in range(len(cols)))
        for row in rows[:20]
    )
    suffix = f"\n  ... ({len(rows)} total rows)" if len(rows) > 20 else f"\n  ({len(rows)} rows)"
    return f"{header}\n{divider}\n{body}{suffix}"


def get_sql_from_claude(question: str, system_prompt: str, client: Anthropic) -> str:
    CONVERSATION_HISTORY.append({"role": "user", "content": question})
    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=system_prompt,
        messages=CONVERSATION_HISTORY,
    )
    sql = response.content[0].text.strip()
    CONVERSATION_HISTORY.append({"role": "assistant", "content": sql})
    return sql


def ask(question: str, system_prompt: str, client: Anthropic) -> None:
    print(f"\n{'═'*60}")
    print(f"  Q: {question}")
    print(f"{'═'*60}")

    sql = get_sql_from_claude(question, system_prompt, client)

    if "CANNOT_ANSWER" in sql:
        reason = sql.split("CANNOT_ANSWER:")[-1].strip().lstrip("- ")
        print(f"\n  Cannot answer: {reason}\n")
        return

    print(f"\n  Generated SQL:")
    print(textwrap.indent(sql, "    "))

    cols, rows = run_sql(sql)
    print(f"\n  Results:")
    print(format_results(cols, rows))
    print()


def interactive_mode(system_prompt: str, client: Anthropic) -> None:
    print("\n" + "═"*60)
    print("  Insurance CRM Query Engine")
    print("  Ask questions in plain English.")
    print("  Type 'quit' to exit, 'reset' to clear conversation history.")
    print("═"*60)

    while True:
        try:
            question = input("\n  Your question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nExiting.")
            break

        if not question:
            continue
        if question.lower() == "quit":
            break
        if question.lower() == "reset":
            CONVERSATION_HISTORY.clear()
            print("  Conversation history cleared.")
            continue

        ask(question, system_prompt, client)


def demo_mode(system_prompt: str, client: Anthropic) -> None:
    demo_questions = [
        "What is our overall hit ratio?",
        "Which carriers have the highest decline rates?",
        "What is our total bound premium by line of business?",
        "Which accounts have the worst loss ratios?",
        "What submissions are currently open?",
    ]
    for q in demo_questions:
        ask(q, system_prompt, client)


def main():
    parser = argparse.ArgumentParser(description="Insurance CRM plain-English query engine")
    parser.add_argument("--question", "-q", help="Single question to ask")
    parser.add_argument("--demo", help="Run demo questions", action="store_true")
    args = parser.parse_args()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("\nANTHROPIC_API_KEY environment variable not set.")
        print("Set it with: $env:ANTHROPIC_API_KEY='your_key_here'\n")
        return

    client        = Anthropic(api_key=api_key)
    dd            = load_data_dictionary()
    appetite      = load_appetite()
    system_prompt = build_system_prompt(dd, appetite)

    if args.question:
        ask(args.question, system_prompt, client)
    elif args.demo:
        demo_mode(system_prompt, client)
    else:
        interactive_mode(system_prompt, client)


if __name__ == "__main__":
    main()
