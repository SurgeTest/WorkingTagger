
import streamlit as st
import pandas as pd
from datetime import datetime
import json

st.set_page_config(page_title="NBA Tagger (Streamlit)", layout="wide")

# ---------- Session State Init ----------
if "buttons" not in st.session_state:
    st.session_state.buttons = [
        {"label": "Pick and Roll", "color": "#3f51b5"},
        {"label": "Rebound", "color": "#009688"},
        {"label": "Turnover", "color": "#e53935"},
    ]

if "events" not in st.session_state:
    st.session_state.events = []  # list of dicts: opponent, game_date, timestamp_iso, label

def compute_counts():
    counts = {}
    for ev in st.session_state.events:
        counts[ev["label"]] = counts.get(ev["label"], 0) + 1
    return counts

# ---------- Sidebar: Game Meta & Admin ----------
st.sidebar.header("Game Info")
opponent = st.sidebar.text_input("Opponent", placeholder="e.g., Acadia", key="opponent")
game_date = st.sidebar.date_input("Game Date", key="game_date")
st.sidebar.caption("Opponent & Date are required before you can tag.")

st.sidebar.header("Buttons")
with st.sidebar.form("new_btn_form", clear_on_submit=True):
    new_label = st.text_input("New Button Label", placeholder="e.g., Pick and Roll")
    new_color = st.color_picker("Color", "#3f51b5")
    submitted = st.form_submit_button("Add Button")
    if submitted:
        lbl = (new_label or "").strip()
        if not lbl:
            st.sidebar.error("Label is required.")
        elif any(b["label"].lower() == lbl.lower() for b in st.session_state.buttons):
            st.sidebar.error("That label already exists.")
        else:
            st.session_state.buttons.append({"label": lbl, "color": new_color})
            st.sidebar.success(f"Added: {lbl}")

st.sidebar.subheader("Layout")
# Save config
cfg = {"buttons": st.session_state.buttons}
st.sidebar.download_button(
    "Save Layout (JSON)",
    data=json.dumps(cfg, indent=2),
    file_name="tagger_layout.json",
    mime="application/json",
    use_container_width=True
)

# Load config
uploaded = st.sidebar.file_uploader("Load Layout (JSON)", type=["json"], accept_multiple_files=False)
if uploaded is not None:
    try:
        content = json.load(uploaded)
        btns = content.get("buttons", [])
        cleaned = []
        for b in btns:
            label = str(b.get("label","")).strip()[:32]
            color = str(b.get("color","#3f51b5")).strip()
            if label:
                cleaned.append({"label": label, "color": color})
        if not cleaned:
            st.sidebar.error("No valid buttons found in uploaded layout.")
        else:
            st.session_state.buttons = cleaned
            st.sidebar.success(f"Loaded {len(cleaned)} buttons.")
    except Exception as e:
        st.sidebar.error(f"Failed to load: {e}")

st.sidebar.subheader("Session")
if st.sidebar.button("Undo Last Tag", use_container_width=True):
    if st.session_state.events:
        st.session_state.events.pop()
        st.sidebar.success("Undid last tag.")
    else:
        st.sidebar.info("No events to undo.")

if st.sidebar.button("Reset Counts", use_container_width=True):
    st.session_state.events = []
    st.sidebar.success("Cleared all events.")

# ---------- Main: Tagging UI ----------
st.title("StFx MBB Tagging Application")
st.caption("Click buttons to tag events in real time. Use the sidebar to manage game info and buttons.")

# Buttons grid
cols_per_row = 5
buttons = st.session_state.buttons
if not buttons:
    st.info("No buttons yet. Add tags from the sidebar → New Button Label.")

rows = [buttons[i:i+cols_per_row] for i in range(0, len(buttons), cols_per_row)]
for row in rows:
    cols = st.columns(len(row), gap="small")
    for i, b in enumerate(row):
        label = b["label"]
        color = b.get("color", "#3f51b5")
        style = f"background-color:{color}; color:white; border:none; padding:14px; border-radius:8px; width:100%; font-weight:700;"
        if cols[i].button(label, key=f"btn_{label}"):
            if not opponent or not game_date:
                st.toast("Enter Opponent and Date first.", icon="⚠️")
            else:
                ev = {
                    "opponent": opponent.strip(),
                    "game_date": str(game_date),
                    "timestamp_iso": datetime.now().isoformat(timespec="seconds"),
                    "label": label,
                }
                st.session_state.events.append(ev)
                st.toast(f"Tagged: {label}", icon="✅")

# ---------- Totals ----------
st.subheader("Totals")
counts = compute_counts()
if counts:
    df_counts = pd.DataFrame([{"Tag": k, "Total": v} for k, v in sorted(counts.items())])
    st.dataframe(df_counts, use_container_width=True, hide_index=True)
else:
    st.write("No tags yet.")

# ---------- Recent Events ----------
st.subheader("Recent Events")
if st.session_state.events:
    df_events = pd.DataFrame(st.session_state.events)
    st.dataframe(df_events.sort_values("timestamp_iso", ascending=False), use_container_width=True, hide_index=True)
    csv = df_events.to_csv(index=False).encode("utf-8")
    st.download_button("Export CSV", data=csv, file_name="tag_events.csv", mime="text/csv")
else:
    st.write("No events yet.")

st.markdown("---")
st.caption("Tip: To deploy online, push this folder to a GitHub repo and use Streamlit Community Cloud to run it directly from the repo.")
