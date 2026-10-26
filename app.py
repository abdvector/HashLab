"""HashLab interface. Run with python -m streamlit run app.py."""

from html import escape
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from experiments import run_experiment
from hashing import Book, DELETED, HashTable, STRATEGIES


def reset_table(size, strategy):
    st.session_state.table = HashTable(size, strategy)
    st.session_state.latest = None
    st.session_state.before = None
    st.session_state.collisions = 0
    st.session_state.trace_position = 1


def execute(operation, key, book=None):
    table = st.session_state.table
    st.session_state.before = table.snapshot()
    result = table.operate(operation, key, book=book)
    st.session_state.latest = result
    st.session_state.collisions += result.collisions
    st.session_state.trace_position = len(result.steps)


def table_html(snapshot, active=None, visited=()):
    cards = []
    for index, value in enumerate(snapshot):
        classes = ["slot"]
        if value is not None and value != []:
            classes.append("filled")
        if index in visited:
            classes.append("visited")
        if index == active:
            classes.append("active")
        if isinstance(value, list):
            content = " &rarr; ".join(map(str, value)) if value else "Empty"
        elif value == DELETED:
            content = "Deleted"
        else:
            content = escape(str(value)) if value is not None else "Empty"
        cards.append(
            f'<div class="{" ".join(classes)}">'
            f'<div class="slot-index">{index:02}</div>'
            f'<div class="slot-value">{content}</div></div>'
        )
    return '<div class="table-grid">' + "".join(cards) + "</div>"


def simulator():
    mode = st.radio("Data", ["Integer keys", "Library books"], horizontal=True)
    library_mode = mode == "Library books"
    settings = st.columns([2, 1])
    strategy = settings[0].selectbox("Collision strategy", STRATEGIES)
    size = settings[1].selectbox("Table size", [7, 11, 13, 17, 23, 31], index=1)
    st.caption("Changing the data mode, strategy or table size clears the table. Data lasts for this session.")
    if "table" not in st.session_state or (
        st.session_state.table.size, st.session_state.table.strategy
    ) != (size, strategy) or st.session_state.get("data_mode") != mode:
        reset_table(size, strategy)
        st.session_state.data_mode = mode

    # Outside the form so selecting an operation immediately updates its fields.
    choices = ["Add book", "Find book", "Remove book"] if library_mode else ["Insert", "Search", "Delete"]
    action = st.selectbox("Operation", choices)
    operation = ["Insert", "Search", "Delete"][choices.index(action)]
    with st.form("operation_form"):
        key = st.number_input(
            "Book ID" if library_mode else "Integer key",
            min_value=1 if library_mode else -1_000_000_000, max_value=1_000_000_000,
            value=12, step=1,
        )
        title, shelf = "", ""
        if library_mode and operation == "Insert":
            title = st.text_input("Book title", max_chars=120)
            shelf = st.text_input("Shelf location", max_chars=40, placeholder="A2")
        submitted = st.form_submit_button(
            "Run operation", type="primary", use_container_width=True,
        )
    if submitted:
        if library_mode and operation == "Insert" and (not title.strip() or not shelf.strip()):
            st.error("Enter a book title and shelf location.")
        else:
            book = Book(title.strip(), shelf.strip()) if library_mode and operation == "Insert" else None
            execute(operation, int(key), book)

    actions = st.columns(2)
    if actions[0].button("Load collision sample", use_container_width=True,
                         help="Replaces the table with five entries that share an initial index."):
        reset_table(size, strategy)
        titles = ["Algorithms", "Python Basics", "Data Structures", "Computer Networks", "Database Systems"]
        for i, title in enumerate(titles):
            sample_key = 12 + size * i
            book = Book(title, f"{chr(65 + i)}{i + 2}") if library_mode else None
            execute("Insert", sample_key, book)
    if actions[1].button("Clear table", use_container_width=True):
        reset_table(size, strategy)

    table = st.session_state.table
    metrics = st.columns(3)
    metrics[0].metric("Stored books" if library_mode else "Stored keys", table.count)
    metrics[1].metric("Load factor", f"{table.count / size:.2f}")
    metrics[2].metric("Collisions", st.session_state.collisions,
                      help="Unequal stored keys encountered during insertion attempts.")

    st.subheader("Hash table")
    formula = f"h(k) = k mod {size}"
    if strategy == STRATEGIES[2]:
        formula += f" | step = 1 + (k mod {size - 1})"
    st.caption(formula)
    result = st.session_state.latest
    display = st.empty()
    display.markdown(table_html(table.snapshot()), unsafe_allow_html=True)
    if result is None:
        st.caption("Add a book or load the sample to get started." if library_mode else "Insert a key or load the sample to get started.")
        return

    st.subheader("Last operation")
    message = f"Book {result.key}: {result.status.lower()}" if library_mode else f"{result.operation} {result.key}: {result.status.lower()}"
    if result.status in ("Table full", "Not found"):
        st.warning(message)
    else:
        st.success(message)
    if library_mode and result.book is not None:
        with st.container(border=True):
            st.text(result.book.title)
            st.caption(f"Book ID: {result.key} | Shelf: {result.book.shelf}")
        if result.status == "Already present":
            st.caption("This ID is already registered. Its book details have been kept.")
    st.caption(
        f"{result.probes} bucket/slot visits | {result.comparisons} key comparisons"
        f" | {result.collisions} insertion collisions"
    )
    position = st.slider("Step", 1, len(result.steps), key="trace_position") if len(result.steps) > 1 else 1
    current = result.steps[position - 1]
    snapshot = table.snapshot() if position == len(result.steps) else st.session_state.before
    display.markdown(
        table_html(snapshot, current.index, [step.index for step in result.steps[:position - 1]]),
        unsafe_allow_html=True,
    )
    st.write(current.message)
    st.caption("Green: current bucket. Amber: previously visited. Deleted slots remain searchable.")


def comparison():
    with st.form("comparison_form"):
        inputs = st.columns(3)
        capacity = inputs[0].selectbox("Capacity", [31, 101, 251, 503], index=1)
        distribution = inputs[1].selectbox("Input distribution", ["Random keys", "Same initial bucket"])
        fill = inputs[2].slider("Fill table to (%)", 20, 100, 90, 5)
        run = st.form_submit_button("Run comparison", type="primary")

    if run:
        with st.spinner("Running comparison..."):
            rows, summaries, keys = run_experiment(capacity, distribution, 42, fill / 100)
            st.session_state.comparison = (rows, summaries, len(keys), capacity, distribution)
    if "comparison" not in st.session_state:
        st.caption("Compare all three strategies using the same keys and table capacity.")
        return

    rows, summaries, count, capacity, distribution = st.session_state.comparison
    st.caption(f"Last run: {distribution} | {count} keys | capacity {capacity} | load factor {count / capacity:.2f}")
    df = pd.DataFrame(rows)
    metric = st.selectbox("Measurement", [
        "Insertion comparisons", "Successful search comparisons", "Unsuccessful search comparisons",
    ])
    chart = alt.Chart(df).mark_line(point=True, strokeWidth=2).encode(
        x=alt.X("Load factor:Q", title="Load factor", scale=alt.Scale(domain=[0, 1])),
        y=alt.Y(f"{metric}:Q", title="Average key comparisons", scale=alt.Scale(zero=True)),
        color=alt.Color("Strategy:N", scale=alt.Scale(
            domain=list(STRATEGIES), range=["#c4f568", "#79b8ff", "#c5a0ff"],
        ), legend=alt.Legend(orient="bottom", title=None)),
        tooltip=["Strategy:N", "Keys:Q", alt.Tooltip("Load factor:Q", format=".2f"),
                 alt.Tooltip(f"{metric}:Q", format=".2f")],
    ).properties(height=320).configure_view(strokeOpacity=0)
    st.altair_chart(chart, use_container_width=True)
    summary = pd.DataFrame(summaries)[["Strategy", metric, "Insertion collisions"]]
    summary[metric] = summary[metric].round(2)
    st.dataframe(summary, hide_index=True, use_container_width=True)
    st.caption("Results at the final load factor. Collisions count unequal keys encountered during insertion.")
    st.download_button("Download results (CSV)", df.to_csv(index=False),
                       "hashlab_results.csv", "text/csv")


st.set_page_config(page_title="HashLab", layout="wide", initial_sidebar_state="collapsed")
st.markdown(f"<style>{Path(__file__).with_name('styles.css').read_text()}</style>", unsafe_allow_html=True)
st.title("HashLab")
st.caption("Hash collision simulator")
simulation_tab, comparison_tab = st.tabs(["Simulator", "Compare strategies"])
with simulation_tab:
    simulator()
with comparison_tab:
    comparison()
