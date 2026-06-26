"""Module for rendering the elements in the sidebar of the Streamlit app."""

if __name__ == "__main__":
    print("This module is not intended to be run directly.")
    print("Please import this as a module on the main Streamlit page (app.py).")
    exit()

import streamlit as st
import pandas as pd

from . import helper
from . import patterns
from . import data_loading

# ============================================================================ #

def render_tf_summary(tfclass_row: pd.Series, length: int, disprot_regions: pd.DataFrame):
    """Render the summary of the selected TF.

    :param tfclass_row: Expected columns: `Genus_Num`, `Uniprot_Acc`,
        `Genus_Name`, `Dbd_Range`.
    :param length: Length of the TF sequence.
    :param disprot_regions: DataFrame of DisProt regions for the TF. Expected
        columns: `Region_Id`, `Start`, `End`.
    """

    selected_genus_num: str = tfclass_row["Genus_Num"]
    selected_uniprot: str = tfclass_row["Uniprot_Acc"]
    selected_genus_name: str = tfclass_row["Genus_Name"]
    dbd_ranges: str = tfclass_row["Dbd_Range"]
    disprot_id = disprot_regions.iloc[0]["Region_Id"].split("r")[0] if not disprot_regions.empty else "N/A"
    disprot_regions_unique = len(disprot_regions[["Start", "End"]].drop_duplicates())

    st.header(f":material/select_check_box: Selected TF details")
    st.table({
        ":material/link: UniProt accession": f"[{selected_uniprot}](https://www.uniprot.org/uniprotkb/{selected_uniprot}/entry)",
        ":material/numbers: Genus number": selected_genus_num,
        ":material/immunology: Genus name": selected_genus_name,
        ":material/straighten: Length": f"{length} residues",
        ":material/format_list_numbered: DBD range(s)": dbd_ranges,
        ":material/error_med: DisProt": f"[{disprot_id}](https://disprot.org/{disprot_id}) ({disprot_regions_unique} distinct regions)" if not disprot_regions.empty else "N/A",
    }, border="horizontal", width="content", hide_header=True)

# ============================================================================ #

def render_pattern_summary(pattern_row: pd.Series):
    """Render the summary of the selected pattern.

    :param pattern_row: Expected columns: `pattern_row`: `Regex`, `Expected`,
        `Observed`, `ZScore`, `Log2FC`."""

    st.header(f":material/pattern: Selected pattern details")
    st.table({
        ":material/regular_expression: Regex": f"`{pattern_row["Regex"]}`",
        ":material/numbers: Expected matches": f"{pattern_row["Expected"]:.2f}",
        ":material/numbers: Observed matches": f"{pattern_row['Observed']}",
        ":material/vital_signs: Z-score": f"{pattern_row['ZScore']:.4f}",
        ":material/vital_signs: Log2FC": f"{pattern_row['Log2FC']:.4f}",
    }, border="horizontal", width="content", hide_header=True)

def render_pattern_selector(matches: pd.DataFrame, selected_genus_num: str) -> tuple[pd.DataFrame, str | None]:
    """Render pattern selector. Returns two things:
    1. Patterns sorted with computed scores (Z-score, Log2FC)
    2. The regex pattern selected by the user

    :param pd.DataFrame matches: The matches in the selected TF.
    :param str selected_genus_num: The genus number of the selected TF.
    """

    st.header(":material/view_timeline: ELM patterns")
    st.write("Select a pattern from the table below to highlight its matches in the TF's sequence. Scroll down to see more details about the pattern.")

    max_penalty_at_20 = helper.render_vagueness_penalty_slider()
    vagueness_penalty_func = patterns.make_vagueness_penalty_func(max_penalty_at_20)
    patterns_df = patterns.compute_pattern_scores(matches, data_loading.init().sequence_dict, vagueness_penalty_func)

    patterns__state = st.dataframe(
        patterns_df[["Regex", "Observed", "ZScore", "Log2FC"]],
        hide_index=True,
        key=f"patterns-{selected_genus_num}",
        column_config={
            "Regex": "Regex",
            "Observed": "Observed matches",
            "ZScore": None,
            "Log2FC": None,
        },
        selection_mode="single-row",
        on_select="rerun",
    )

    patterns__sel_row_indices = helper.get_df_selected_rows(patterns__state)
    if len(patterns__sel_row_indices) == 1:
        patterns__sel_row = patterns_df.iloc[patterns__sel_row_indices[0]]
        selected_pattern__str: str = patterns__sel_row["Regex"]

        render_pattern_summary(patterns__sel_row)

        return patterns_df, selected_pattern__str

    return patterns_df, None
