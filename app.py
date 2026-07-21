import streamlit as st
from anthropic import Anthropic
import os 
import pandas as pd
from dotenv import load_dotenv


from query_engine import(
    get_sql_from_claude, load_data_dictionary, load_semantic_model,
    build_system_prompt, build_repair_prompt, ask, run_with_repair
)

load_dotenv()
st.set_page_config(
    page_title = "Convelo Submissions Query Engine",
    page_icon = "C:\\Users\\AMezi\\Pictures\\convelo - full color.svg",
    layout = "wide")

st.title("Convelo Submissions Query Engine")
st.logo("C:\\Users\\AMezi\\Pictures\\signerslogo.png")

#tells  Streamlit to only run this function once and cache the result for future calls.
#without it you'd reconnect to the Anthropic API every time you run the app, which would be inefficient; rate limiting.
@st.cache_resource 
def get_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    return Anthropic(api_key=api_key)

@st.cache_resource
def get_prompts():
    dd = load_data_dictionary()
    sm = load_semantic_model()
    system_prompt = build_system_prompt(dd, sm)
    repair_prompt = build_repair_prompt(sm)
    return system_prompt, repair_prompt

client = get_client()
system_prompt, repair_prompt = get_prompts()

question = st.text_input("Enter your question:")
if "history" not in st.session_state:
    st.session_state.history = []
if "messages" not in st.session_state:
    st.session_state.messages = []
    
if st.button("Run"):
    sql, cols, rows = ask(question, system_prompt, repair_prompt, client, st.session_state.history)
    
    is_error = bool(rows) and rows[0][0] == "ERROR"

    if not cols and not rows:
        st.write(f"Cannot answer: {sql}")
    elif is_error:
        st.code(sql, language='sql')
        st.error(f"SQL error: {rows[0][1]}")
    else:
        print(repr(sql))
        st.code(sql, language='sql')
        df = pd.DataFrame(rows, columns = cols)
        st.dataframe(df)

if st.button("Reset conversation"):
    st.session_state.history = []
    st.session_state.messages = []
    st.rerun()

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if question: 
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)
    
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            sql = get_sql_from_claude(question, system_prompt, client, st.session_state.history)
            final_sql, cols, rows = run_with_repair(sql, question, repair_prompt, client)
        st.code(final_sql, language='sql')
        if rows and rows [0][0] == "ERROR":
            st.error(f"SQL error: {rows[0][1]}")
        else:
            st.dataframe([dict(zip(cols, row)) for row in rows])

    
    st.session_state.messages.append({"role": "assistant", "content": final_sql})


# ─────────────────────────────────────────────────────────────────
# Pipeline Demo — Self-Healing SQL
#
# Fixed, known-bad questions that reliably trigger a real repair,
# each mapped to a documented drift between data_dictionary.json and
# prototypeSchema.sql (see semantic_model.json common_failure_modes).
# ─────────────────────────────────────────────────────────────────
DEMO_QUESTIONS = {
    "Submissions with their status": "Show me all submissions along with their status.",
    "Lines of business with their ID": "Show me the lob_id and name for every line of business we offer.",
}

if "demo_events" not in st.session_state:
    st.session_state.demo_events = []

with st.expander("Pipeline Demo — Self-Healing SQL", expanded=False):
    st.caption(
        "These questions are known to trigger a real SQL error on the first attempt, "
        "then walk through the self-healing repair loop live."
    )
    demo_label = st.selectbox("Known-bad demo question", list(DEMO_QUESTIONS.keys()))
    demo_question = DEMO_QUESTIONS[demo_label]
    st.code(demo_question, language=None)

    if st.button("Run demo"):
        st.session_state.demo_events = []
        pipeline = st.container()
        boxes = {}

        def on_demo_event(event):
            st.session_state.demo_events.append(event)
            stage = event["stage"]

            if stage == "execute":
                gen_box = pipeline.status("Generate SQL", state="complete")
                gen_box.code(event["sql"], language="sql")
                boxes["execute_0"] = pipeline.status("Execute attempt 0", state="running")

            elif stage == "execute_result":
                attempt = event["attempt"]
                box = boxes.setdefault(
                    f"execute_{attempt}", pipeline.status(f"Execute attempt {attempt}", state="running")
                )
                if event["success"]:
                    box.update(label=f"Execute attempt {attempt} — success", state="complete")
                    with box:
                        st.code(event["sql"], language="sql")
                        st.dataframe(pd.DataFrame(event["rows"], columns=event["cols"]))
                else:
                    box.update(label=f"Execute attempt {attempt} — failed", state="error")
                    with box:
                        st.code(event["sql"], language="sql")
                        st.error(event["error"])

            elif stage == "repair_start":
                attempt = event["attempt"]
                box = pipeline.status(f"Diagnose & Repair (after attempt {attempt})", state="running")
                boxes[f"repair_{attempt}"] = box
                with box:
                    st.caption("Fresh, independent diagnosis of the current error — not a patch on the failed SQL.")
                    st.error(f"Triggering error: {event['prior_error']}")

            elif stage == "repair_result":
                attempt = event["attempt"]
                box = boxes.get(f"repair_{attempt}")
                if box is not None:
                    box.update(label=f"Diagnose & Repair (after attempt {attempt}) — done", state="complete")
                    with box:
                        st.code(event["new_sql"], language="sql")
                boxes[f"execute_{attempt + 1}"] = pipeline.status(f"Execute attempt {attempt + 1}", state="running")

            elif stage == "early_stop":
                box = pipeline.status("Stopped — identical error repeated", state="error")
                with box:
                    st.error(event["error"])

            elif stage == "exhausted":
                pipeline.status("Repair attempts exhausted", state="error")

            elif stage == "success":
                pipeline.success(f"Resolved on attempt {event['attempt']}.")

        with st.spinner("Generating SQL..."):
            ask(demo_question, system_prompt, repair_prompt, client, [], on_event=on_demo_event)