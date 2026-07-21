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
DICT_PATH            = "data_dictionary.json"
SEMANTIC_PATH        = "semantic_model.json"
MODEL                = "claude-sonnet-4-6"
CONVERSATION_HISTORY = []


def load_data_dictionary() -> dict:
    with open(DICT_PATH) as f:
        return json.load(f)


def load_semantic_model() -> dict:
    with open(SEMANTIC_PATH) as f:
        return json.load(f)


def build_system_prompt(dd: dict) -> str:
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
- For hit ratio: use quotes table, quote_status = 'Bound', 'Bound-Issued'
- To detect a bound quote: always use quote_status = 'Bound', 'Bound-Issued' on the quotes table —
                           NEVER join to policies and check policy_id IS NOT NULL
- For loss ratio: join losses to policies via policy_id,
                  join policies to submissions via control_number
- For carrier appetite: query quotes grouped by carrier_id,
                        calculate decline_rate from quote_status = 'Declined'
- When ranking by decline behavior: order by decline_rate_pct (percentage) by default —
                                    only order by absolute declined count if the user
                                    explicitly asks for it
- NEVER use YEAR() — use strftime('%Y', column) instead
- NEVER use GETDATE() — use date('now') instead
- Return clean readable SQL with aliases
- Write generated SQL as multi-line using real line breaks, never output literal backslash-n as text
- Limit to 20 rows unless user specifies otherwise
- If the question cannot be answered, say: -- CANNOT_ANSWER: [reason]
- 
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


MAX_REPAIR_ATTEMPTS = 2


def build_repair_prompt(sm: dict) -> str:
    """
    Builds a separate system prompt for the repair agent, distinct from
    build_system_prompt(). Injects the common_failure_modes and
    the join_registry from semantic_model.json so the agent can pattern-match
    the error and verify join paths before reasoning from the schema directly.
    """
    modes = sm.get("common_failure_modes", {}).get("patterns", [])
    modes_text = "\n".join(
        f"- If error contains \"{m['error_message']}\": likely cause is "
        f"{m['likely_cause']}. Fix: {m['solution']}"
        for m in modes
    )

    joins = sm.get("join_registry", [])
    joins_text = "\n".join(
        f"- {j['from_table']}.{j['from_col']} {j['join_type']} JOIN "
        f"{j['to_table']}.{j['to_col']}"
        + (f"  ({j['notes']})" if j.get("notes") else "")
        for j in joins
    )

    return f"""You are repairing a failed SQLite SQL query.

You will be given:
1. The original question
2. The SQL that failed
3. The exact error message

KNOWN FAILURE PATTERNS:
{modes_text}

KNOWN JOIN PATHS:
{joins_text}

Only use the join paths listed above. Do not invent a join between two
tables that isn't listed — if no direct edge exists, connect them through
an intermediate table that does have edges to both.

Match the error message against the known failure patterns first. If none
match, reason from the schema directly. Return ONLY the corrected SQL —
no explanation, no markdown, no backticks.
"""


def repair_sql(question: str, failed_sql: str, error: str,
                repair_prompt: str, client: Anthropic) -> str:
    """
    Generates a single repaired SQL query from a fresh diagnosis of the
    current error only. Does NOT receive prior attempts or prior SQL —
    each call is independent so a query is never excluded just because
    it was tried before.
    """
    user_message = f"""Original question: {question}

Failed SQL:
{failed_sql}

Error:
{error}

Return corrected SQL only."""

    response = client.messages.create(
        model=MODEL,
        max_tokens=1000,
        system=repair_prompt,
        messages=[{"role": "user", "content": user_message}],
    )
    return response.content[0].text.strip()


def run_with_repair(sql: str, question: str, repair_prompt: str,
                     client: Anthropic) -> tuple[str, list, list]:
    """
    Executes sql, and on failure attempts up to MAX_REPAIR_ATTEMPTS fresh
    repairs. Stops early if the error string repeats exactly between two
    consecutive attempts, since that means the repair made no progress
    and further attempts are unlikely to help.

    Returns (final_sql, cols, rows). On unrecoverable failure, rows will
    still contain the ["ERROR", message] sentinel from run_sql.
    """
    previous_error = None

    for attempt in range(MAX_REPAIR_ATTEMPTS + 1):
        lines = sql.splitlines()
        new_list = [line for line in lines if not line.startswith("--")]
        executable_sql = "\n".join(new_list) 
        cols, rows = run_sql(executable_sql)

        is_error = bool(rows) and rows[0][0] == "ERROR"
        if not is_error:
            return sql, cols, rows

        current_error = rows[0][1]

        if current_error == previous_error:
            # Identical error twice in a row — repair isn't progressing.
            break

        if attempt == MAX_REPAIR_ATTEMPTS:
            # Out of attempts; return the last failure as-is.
            break

        previous_error = current_error
        sql = repair_sql(question, sql, current_error, repair_prompt, client)

    return sql, cols, rows


def ask(question: str, system_prompt: str, repair_prompt: str, client: Anthropic) -> tuple[str, list, list]:
    sql = get_sql_from_claude(question, system_prompt, client)

    if "CANNOT_ANSWER" in sql:
        reason = sql.split("CANNOT_ANSWER:")[-1].strip().lstrip("- ")
        return reason,[],[]


    final_sql, cols, rows = run_with_repair(sql, question, repair_prompt, client)

    is_error = bool(rows) and rows[0][0] == "ERROR" 
    return final_sql, cols, rows

def interactive_mode(system_prompt: str, repair_prompt: str, client: Anthropic) -> None:
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

        sql, cols, rows = ask(question, system_prompt, repair_prompt, client)

    if not cols and not rows:
        print(f"\n Cannot answer: {sql}")
    else:
        print(f"\n Question: {question}")
        print(f"\n Generated SQL:\n{sql}")
        print(format_results(cols, rows))



def demo_mode(system_prompt: str, repair_prompt: str, client: Anthropic) -> None:
    demo_questions = [
        "What is our overall hit ratio?",
        "Which carriers have the highest decline rates?",
        "What is our total bound premium by line of business?",
        "Which accounts have the worst loss ratios?",
        "What submissions are currently open?",
    ]
    for q in demo_questions:
       sql, cols, rows = ask(q, system_prompt, repair_prompt, client)

    if not cols and not rows: 
        print(f"\n Cannot answer: {sql}")
    else:
        print(f"\n Question: {q}")
        print(f" Generated SQL:\n{sql}")
        print(format_results(cols, rows))


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
    sm            = load_semantic_model()
    system_prompt = build_system_prompt(dd)
    repair_prompt = build_repair_prompt(sm)

    if args.question:
        ask(args.question, system_prompt, repair_prompt, client)
    elif args.demo:
        demo_mode(system_prompt, repair_prompt, client)
    else:
        interactive_mode(system_prompt, repair_prompt, client)


if __name__ == "__main__":
    main()
