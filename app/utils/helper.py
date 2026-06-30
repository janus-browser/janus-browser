"""Module for helper functions."""

if __name__ == "__main__":
    print("This module is not intended to be run directly.")
    print("Please import this as a module on the main Streamlit page (app.py).")
    exit()

from random import randint
from typing import Literal
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

def render_sequence(sequence: str, pattern: str|None=None, underline_data: list[tuple[int,int]]|None=None) -> str:
    """
    Get the chunked sequence block in HTML. Also highlights any matches of the
    provided pattern.

    :param sequence: the full sequence to render
    :param pattern: the regex pattern to highlight in the sequence. If None, no highlighting is done.
    :param underline_data: a list of (start, end) tuples indicating regions to underline in the sequence.
    :param color1: the primary color to use for highlighting
    :param color2: the alternate color to use for highlighting
    :return str: the rendered HTML string
    """

    THEME = st.context.theme.type # ! TODO: explore CSS media query instead
    COLOR_BACKGROUND = st.get_option(f"theme.{THEME}.backgroundColor")
    BG1 = st.get_option(f"theme.{THEME}.greenColor")
    FG1 = COLOR_BACKGROUND
    # BG2 = st.get_option(f"theme.{THEME}.violetColor")
    BG2 = f"color-mix(in srgb, {BG1} 50%, transparent)"
    FG2 = "unset"
    GAP = "10px"

    # this array will hold the index of the match for each residue, or 0 if not matched
    # use it for alternating colors
    residues_matched = np.zeros(len(sequence))
    residues_underlined = np.zeros(len(sequence), dtype=bool)

    if pattern:
        try:
            regex = re.compile(pattern)
            for i, match in enumerate(regex.finditer(sequence), start=1):
                for pos in range(match.start(), match.end()):
                    residues_matched[pos] = i
        except:
            pass

    html_chunks: list[str] = []

    for start, end in (underline_data or []):
        for pos in range(start - 1, end): # convert to 0-based index
            residues_underlined[pos] = True

    for chunk_start in range(0, len(sequence), 10):
        chunk_chars = sequence[chunk_start:chunk_start+10]

        # Build HTML for this chunk with highlighting
        html_chunk = ""
        for index_within_chunk, char in enumerate(chunk_chars):
            index = chunk_start + index_within_chunk
            html_chunk_char = ""

            if residues_matched[index] > 0:
                class_name = "c1" if residues_matched[index] % 2 == 1 else "c2"
                last_child = " l" if (index_within_chunk == len(chunk_chars) - 1) else ""
                html_chunk_char = f"""<span class="{class_name}{last_child}">{char}</span>"""
            else:
                html_chunk_char = char

            if residues_underlined[index]:
                html_chunk_char = f"""<span class="u">{html_chunk_char}</span>"""

            html_chunk += html_chunk_char

        html_chunks.append(f"""
<div class="chunk">
    <span class="pos">{chunk_start + len(chunk_chars)}<br/></span>
    <span class="seq">{html_chunk}</span>
</div>
""")

    style = f"""
<style>
    .rendered-sequence-container {{display: flex; flex-wrap: wrap; gap: {GAP}; align-items: flex-start;}}
    .rendered-sequence-container .chunk {{display: flex; flex-direction: column; align-items: flex-end; font-family: monospace;}}
    .rendered-sequence-container .chunk .pos {{font-size: 0.8rem; opacity: 0.6; user-select: none;}}
    .rendered-sequence-container .chunk .seq .c1 {{background-color: {BG1}; color: {FG1}; font-weight: bold; text-decoration-color: {BG1}; position: relative;}}
    .rendered-sequence-container .chunk .seq .c2 {{background-color: {BG2}; color: {FG2}; font-weight: bold; text-decoration-color: {BG2}; position: relative;}}
    .rendered-sequence-container .chunk .seq .c1.l:after {{content: ''; display: block; position: absolute; top: 0; right: -{GAP}; width: {GAP}; height: 100%; background-color: {BG1};}}
    .rendered-sequence-container .chunk .seq .c2.l:after {{content: ''; display: block; position: absolute; top: 0; right: -{GAP}; width: {GAP}; height: 100%; background-color: {BG2};}}
    .rendered-sequence-container .chunk .seq .u {{text-decoration: overline underline 2pt; text-underline-position: under;}}
</style>
"""

    rendered = f"""{style}<div class="rendered-sequence-container">{"\n".join(html_chunks)}</div>"""
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

# ============================================================================ #

def container_indent(*args, **kwargs):
    """Render a st.container with an indent."""

    key = f"{randint(1,100000)}"
    st.html(f"<style>.st-key-{key} {{margin-left: 2em;}}</style>")
    return st.container(*args, key=key, **kwargs)

#endregion
