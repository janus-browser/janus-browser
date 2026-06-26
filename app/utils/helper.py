"""Module for helper functions."""

if __name__ == "__main__":
    print("This module is not intended to be run directly.")
    print("Please import this as a module on the main Streamlit page (app.py).")
    exit()

from typing import Literal, overload
from collections import OrderedDict
import re

import streamlit as st
import streamlit.elements.arrow
import numpy as np
import pandas as pd

# ============================================================================ #

#region Non-render
def calculate_disprot_perc(ranges: pd.DataFrame, seq_len: int) -> float:
    """For the given list of DisProt regions, calculate the disordered
    percentage.

    :param ranges: A DataFrame with `Start` and `End` columns.
    :param seq_len: The length of the full sequence.
    """

    if seq_len <= 0: return 0.0

    arr = np.zeros(seq_len, dtype=int)
    for start, end in ranges[["Start", "End"]].astype(int).itertuples(index=False, name=None):
        arr[start:end+1] = 1
    return arr.sum() / seq_len

def get_df_selected_rows(state: streamlit.elements.arrow.DataframeState) -> list[int]:
    """Shorthand for `state["selection"]["rows"]`, but with safety."""

    if "selection" not in state: return []
    if "rows" not in state["selection"]: return []
    return state["selection"]["rows"]

def parse_dbd_ranges(dbd_range_str: str) -> list[tuple[int, int]]:
    """Parse the DBD range string into a list of (start, end) tuples.

    :param dbd_range_str: The DBD range string, e.g. "10-20,30-40"
    :return: A list of (start, end) tuples, e.g. [(10, 20), (30, 40)]
    """

    ranges = []
    for part in dbd_range_str.split(","):
        part = part.strip()
        if not part: continue
        try:
            start, end = map(int, part.split("-"))
            ranges.append((start, end))
        except ValueError:
            continue
    return ranges

#endregion

# ============================================================================ #

#region Render
FilterBy = Literal["Superclass", "Class", "Family", "Subfamily", "Name"]
# dict mapping `option` to its display name
FILTER_OPTIONS: OrderedDict[FilterBy, str] = OrderedDict([
    ("Superclass", "Superclass"),
    ("Class", "Class"),
    ("Family", "Family"),
    ("Subfamily", "Subfamily"),
    ("Name", "Genus number (or) UniProt Accession (or) Genus name"),
])

def render_search_dropdown(classes_df: pd.DataFrame, filter_by: FilterBy, st_key: str) -> list[str]:
    return st.multiselect(
        label=f"Select a {filter_by}:",
        label_visibility="collapsed",
        options=classes_df[filter_by].dropna().unique(),
        placeholder=f"Search for {FILTER_OPTIONS.get(filter_by, filter_by)}",
        key=st_key,
    )

def render_filter_controls(tfclasses_df: pd.DataFrame):
    """Filter the `tfclasses_df` based on user-input `filter_by` and `option`.
    Returns the following:
    1. `selected_option`
    2. `filter_by`
    3. `disprot_filter`
    """

    tab1, tab2 = st.tabs(["Basic search", "Advanced search"], on_change="rerun")

    disprot_filter = st.toggle(label="View only entries with DisProt data available", value=False, key="disprot_filter", help="This will filter the catalog to only show entries that have DisProt data available, which is required for pattern generation. (Currently, only a subset of entries have DisProt data available.)")

    with tab1:
        filter_by1 = "Name"
        selected_option1 = render_search_dropdown(tfclasses_df, filter_by1, "option1")

    with tab2:
        filter_by2: FilterBy = st.segmented_control(
            label="Filter by:",
            options=[k for k in FILTER_OPTIONS if k!="Name"],
            format_func=lambda k: FILTER_OPTIONS.get(k, f"{k}"),
            default="Subfamily",
            required=True,
            selection_mode="single",
        ) # type: ignore because narrowing from str to `FilterBy`
        selected_option2 = render_search_dropdown(tfclasses_df, filter_by2, "option2")

    if tab1.open:
        return (selected_option1, filter_by1, disprot_filter)
    else: # tab2.open:
        return (selected_option2, filter_by2, disprot_filter)
    # else:
    #     return ([], "", disprot_filter)

# ============================================================================ #

def render_sequence(sequence: str, *patterns_and_colors: str|tuple[str, str]|None) -> str:
    """
    Get the chunked sequence block in HTML. Also highlights any matches of the
    provided pattern.

    :param str sequence: the full sequence to render
    :param patterns_and_colors: the regex pattern to highlight in the
        sequence (optional). Pass multiple patterns as separate arguments, or as
        tuples of (pattern, color).
    :return str: the rendered HTML string
    """

    # Find all match positions if pattern is provided
    highlighted_positions: dict[int, str] = {}
    for pattern in patterns_and_colors:
        if pattern is None: continue

        color = "DarkSalmon"
        if isinstance(pattern, tuple):
            pattern, color = pattern

        try:
            regex = re.compile(pattern)
            for match in regex.finditer(sequence):
                for pos in range(match.start(), match.end()):
                    highlighted_positions[pos] = color
        except:
            pass

    html_chunks: list[str] = []

    for i in range(0, len(sequence), 10):
        chunk_chars = sequence[i:i+10]
        index = i + len(chunk_chars)

        # Build HTML for this chunk with highlighting
        html_chunk = ""
        for j, char in enumerate(chunk_chars):
            pos = i + j
            if pos in highlighted_positions:
                html_chunk += f"<span style='background-color: {highlighted_positions[pos]}; font-weight: bold;'>{char}</span>"
            else:
                html_chunk += char

        html_chunks.append(f"""
<div style='display: flex; flex-direction: column; align-items: flex-end;'>
    <span style='font-family: monospace; font-size: 0.8rem; opacity: 0.6; user-select: none;'>{index}</span>
    <span style='font-family: monospace;'>{html_chunk}</span>
</div>
        """)

    rendered = f"""<div style="display: flex; flex-wrap: wrap; gap: 10px; align-items: flex-start;">{"\n".join(html_chunks)}</div>"""
    return rendered

# ============================================================================ #

def render_vagueness_penalty_slider(key: str|None=None):
    """Render a vagueness penalty slider, and return the selected value.

    This is its own function because it's used in multiple places, and so that
    the huge ass help text is consistent."""

    return st.slider(
        "Vagueness Penalty", min_value=1.0, max_value=10.0, value=2.25, step=0.25,
        help="Vagueness is a measure of how specific a pattern is, with lower values indicating more specific patterns. A penalty may be applied to highly vague patterns.\n\nIncreasing this penalty allows you to focus on patterns that are more likely to be biologically meaningful.\n\nSet to 1.0 to not apply any penalty.\n\nNote that this is only used to rank the patterns for convenience purposes, and it doesn't affect the actual pattern matching.",
        key=key,
    )

#endregion
