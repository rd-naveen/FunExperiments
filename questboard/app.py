import streamlit as st
import sqlite3
import pandas as pd
import math



# Initialize DB
DB_FILE = "quest_board.db"
conn = sqlite3.connect(DB_FILE)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS quests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        question TEXT NOT NULL,
        tags TEXT,
        completed BOOLEAN DEFAULT 0
    )
''')

conn.commit()

# Count status
c.execute("SELECT COUNT(*) FROM quests WHERE completed = 1")
completed_count = c.fetchone()[0]

c.execute("SELECT COUNT(*) FROM quests WHERE completed = 0")
incomplete_count = c.fetchone()[0]

# Load CSS
with open("styles.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("🧭 Quest Board")
st.markdown(f"""
<small><strong>✅ Completed:</strong> {completed_count} &nbsp;&nbsp;|&nbsp;&nbsp; ❌ Incomplete:</strong> {incomplete_count}</small>
""", unsafe_allow_html=True)

st.markdown("Welcome, Explorer! Post your quests, mark them complete, and navigate your journeys.")

# Add new quest
with st.expander("📜 Add a New Quest"):
    question = st.text_area("Enter your quest")
    tags = st.text_input("Tags (comma-separated)")
    if st.button("Add Quest"):
        if question.strip():
            c.execute("INSERT INTO quests (question, tags) VALUES (?, ?)", (question, tags))
            conn.commit()
            st.success("Quest added to the board!")

with st.expander("📂 Upload Quests via CSV"):
    uploaded_file = st.file_uploader("Upload a CSV file", type=["csv"])
    if uploaded_file:
        df = pd.read_csv(uploaded_file)
        if "question" not in df.columns:
            st.error("CSV must have a 'question' column.")
        else:
            df["tags"] = df.get("tags", "")
            added_count = 0
            for _, row in df.iterrows():
                q_text = str(row["question"]).strip()
                q_tags = str(row["tags"]).strip()
                if q_text:
                    c.execute("INSERT INTO quests (question, tags) VALUES (?, ?)", (q_text, q_tags))
                    added_count += 1
            conn.commit()
            st.success(f"{added_count} quests added to the board!")


# Search and Filter
st.sidebar.header("🔍 Search & Filter")
search_term = st.sidebar.text_input("Search by text")
status_filter = st.sidebar.selectbox("Filter by status", ["All", "Completed", "Incomplete"])
tag_filter = st.sidebar.text_input("Filter by tag")

# Query builder
query = "SELECT * FROM quests WHERE 1=1"
params = []

if search_term:
    query += " AND question LIKE ?"
    params.append(f"%{search_term}%")

if status_filter == "Completed":
    query += " AND completed = 1"
elif status_filter == "Incomplete":
    query += " AND completed = 0"

if tag_filter:
    query += " AND tags LIKE ?"
    params.append(f"%{tag_filter}%")

c.execute(query, params)
quests = c.fetchall()

# Display quests

st.markdown("## 📌 Posted Quests")

# Split quests into chunks of 2 per row
chunk_size = 2
chunks = [quests[i:i + chunk_size] for i in range(0, len(quests), chunk_size)]

for chunk in chunks:
    cols = st.columns(len(chunk))
    for idx, q in enumerate(chunk):
        with cols[idx]:
            box_style = f"quest-box length-{min(len(q[1]) // 50 + 1, 5)}"
            st.markdown(f"""
                <div class='{box_style}'>
                    <strong>📝 Quest #{q[0]}</strong><br>
                    {q[1]}<br>
                    <em>🏷️ Tags:</em> {q[2] if q[2] else 'None'}<br><br>
            """, unsafe_allow_html=True)

            completed = st.checkbox("✔ Completed", value=bool(q[3]), key=f"chk_{q[0]}")
            if completed != bool(q[3]):
                c.execute("UPDATE quests SET completed = ? WHERE id = ?", (int(completed), q[0]))
                conn.commit()
                st.rerun()

            st.markdown("</div>", unsafe_allow_html=True)

conn.close()