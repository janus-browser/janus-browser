import streamlit as st
import pandas as pd

from app.utils import constants
from app.utils import data_loading
from app.utils import sidebar
from app.utils import patterns
from app.utils import helper
from app.utils import graph

#region Config
st.set_page_config(
    page_title=f"Viewer | {constants.APP_NAME}",
    initial_sidebar_state="expanded",
)
#endregion

#region Data loading, query params
data = data_loading.init()
disprot_df = data.disprot_df
tfclasses_df = data.tfclasses_df
# genus_num_name_map = data.genus_num_name_map
matches_df = data.matches_df
sequence_dict = data.sequence_dict



tf_row = None
if "genus_num" in st.query_params:
    tf_genus_num = st.query_params["genus_num"]
    __search = tfclasses_df[tfclasses_df["Genus_Num"] == tf_genus_num]
    if not __search.empty:
        tf_row = __search.iloc[0]

@st.dialog(title="No TF selected", icon=":material/error:", dismissible=False)
def blank_view():
    st.error("No TF selected. Please select a TF from the browser.", icon=":material/error:")
    st.page_link(constants.PATH_PAGE_TF_BROWSER, label="Go to TF Browser", icon=":material/arrow_back:", icon_position="left")

if ("genus_num" not in st.query_params) or (tf_row is None):
    blank_view()
    st.stop()



tf_genus_num: str = tf_row["Genus_Num"]
tf_uniprot: str = tf_row["Uniprot_Acc"]
tf_genus_name: str = tf_row["Genus_Name"]
tf_dbd_range: str = tf_row["Dbd_Range"]
tf_sequence: str = sequence_dict[tf_genus_num].Sequence
st.set_page_config(page_title=f"{tf_genus_name} | {constants.APP_NAME}")

tf_disprot_regions = disprot_df[disprot_df["Uniprot_Acc"] == tf_uniprot]
tf_disprot_id = tf_disprot_regions.iloc[0]["Disprot_Id"] if not tf_disprot_regions.empty else "N/A"

tf_disorder_scores = data_loading.load_disorder_scores(tf_genus_num)

tf_matches = matches_df[matches_df["Genus_Num"] == tf_genus_num]

# Parse the DBD range string into a list of (start, end) tuples (used for pltting in the graph)
tf_dbd_range_list = helper.parse_dbd_ranges(tf_dbd_range)
"""Matches occurring ONLY in this TF."""

#endregion

#region Overview
with st.sidebar:
    sidebar.render_tf_summary(tf_row, len(tf_sequence), tf_disprot_regions)

# TF metrics cards
st.header(f"{tf_genus_name}", anchor="selected_tf") #: {tf_genus_num} | {tf_genus_name} | [{tf_uniprot}](https://www.uniprot.org/uniprotkb/{tf_uniprot}/entry)")
col11, col12 = st.columns(2, border=True)
col21, col22 = st.columns(2, border=True)
col11.metric(":material/link: UniProt Accession", f"**[{tf_uniprot}](https://www.uniprot.org/uniprotkb/{tf_uniprot}/entry)**", help="The unique identifier for this transcription factor in the UniProt database.")
col12.metric(":material/error_med: DisProt ID", f"**[{tf_disprot_id}](https://disprot.org/{tf_disprot_id})**" if not tf_disprot_regions.empty else "N/A", help="The unique identifier for this transcription factor in the DisProt database. Click the link to view more details about the disordered regions in this TF.")
col21.metric(":material/straighten: Sequence length", f"**{len(tf_sequence)} residues**", help="The number of amino acids in this transcription factor's sequence.")
col22.metric(":material/format_list_numbered: DBD Range(s)", f"**{tf_dbd_range}**", help="The range of amino acids that correspond to the DNA-binding domain (DBD) of this transcription factor. This is the region that interacts with DNA to regulate gene expression.")

#endregion

#region Patterns (sidebar)
with st.sidebar:
    st.divider()

    tf_patterns, selected_pattern = sidebar.render_pattern_selector(tf_matches, tf_genus_num)

    #Sort matches by regex, with the same order as that in tf_patterns
    #copilot cooked this line... idk how it works, but it works 🙏
    tf_matches = tf_matches.sort_values(by="Regex", key=lambda col: col.map(
        lambda regex: tf_patterns.index[tf_patterns["Regex"] == regex][0] if regex in tf_patterns["Regex"].values else -1
    ))

#endregion

#region Sequence
with st.expander("Sequence", icon=":material/genetics:", expanded=True):
    sequence_html = helper.render_sequence(tf_sequence, selected_pattern)
    sequence_fasta = f">{tf_genus_num}_{tf_uniprot}_{tf_genus_name}\n{tf_sequence}\n"
    st.write(f"{sequence_html}", unsafe_allow_html=True)
    st.divider()
    with st.container(horizontal=True, vertical_alignment="center", horizontal_alignment="distribute"):
        st.text("FASTA:")
        st.download_button(
            label=":material/download: Download FASTA",
            data=sequence_fasta,
            file_name=f"{tf_genus_num}_{tf_uniprot}_{tf_genus_name}.fasta",
            mime="text/plain"
        )
    st.code(sequence_fasta, language="plaintext", line_numbers=False, wrap_lines=False)

#endregion

st.divider()
st.space(2)

#region Disorder scores
score_cols: list[graph.ScoreName] = [
    "Aiupred-Disorder",
    "Aiupred-Binding",
    "Aiupred-Linker",
    "HI",
    "Fldpnn-Disorder",
    "Fldpnn-ProteinBinding",
    "Fldpnn-DnaBinding",
    "Fldpnn-RnaBinding",
    "Fldpnn-Linker",
    "Metapredict-Disorder",
]

default_cols: list[graph.ScoreName] = [
    "Aiupred-Disorder",
    "HI",
    "Fldpnn-Disorder",
    "Metapredict-Disorder",
]
# persist selection across navigations
st.session_state["scoresToDisplay"] = st.session_state.get("scoresToDisplay", default_cols)

with st.expander("Score Plots", icon=":material/area_chart:", expanded=True):
    st.subheader("Score Plots", anchor=False)
    display_scores = st.pills(
        label="Select scores to display:",
        options=score_cols,
        default=st.session_state["scoresToDisplay"],
        selection_mode="multi",
        key="scoresToDisplay",
    )

    fig = graph.create_scores_plotly(
        sequence=tf_sequence,
        scores_list=[
            graph.make_score_renderable(score_name, tf_disorder_scores)
            for score_name in score_cols
            if score_name in display_scores
        ],
        dbd_ranges=tf_dbd_range_list,
        disprot_regions=tf_disprot_regions,
    )
    st.plotly_chart(fig)

#endregion

#region Disprot regions
with st.expander("DisProt regions for selected TF", icon=":material/error_med:"):
    if tf_disprot_regions.empty:
        st.write("No DisProt regions found for this TF.")

    else:
        st.subheader(f"DisProt regions in [{tf_disprot_id}](https://disprot.org/{tf_disprot_id})", anchor=False)
        st.table(
            data=pd.concat({
                "Region ID": (tf_disprot_regions["Region_Id"].apply(lambda x: f"[{x}](https://disprot.org/{x})")),
                "Start-End": (tf_disprot_regions["Start"].astype(str) + "-" + tf_disprot_regions["End"].astype(str)),
                "Term Namespace": (tf_disprot_regions["Term_Namespace"].astype(str)),
                "Term Name": ("_" + tf_disprot_regions["Term_Name"] + "_: " + (tf_disprot_regions["Term_Id"].apply(lambda x: f"[{x}](https://disprot.org/idpo/{x})" if x.startswith("IDPO") else f"[{x}](https://www.ebi.ac.uk/QuickGO/term/{x})"))),
                "Evidence Details": (tf_disprot_regions["Eco_Term_Id"].astype(str).apply(lambda x: f"[{x}](https://www.ebi.ac.uk/QuickGO/term/{x})" if x.startswith("ECO") else x) + ": " + tf_disprot_regions["Eco_Term_Name"].astype(str)),
                "PubMed ID": (tf_disprot_regions["Pmid"].apply(lambda x: f"[{x}](https://pubmed.ncbi.nlm.nih.gov/{x.split(':')[1]})")),
            }, axis=1),
            hide_index=True,
            height=500 if len(tf_disprot_regions) > 5 else "content",
        )

#endregion

#region Matches

# ? NOTE: We'll NOT remove patterns with only 1 match, since that pattern might
# have more matches in other TFs as well.

with st.expander("Matches in ELM Patterns for selected TF", icon=":material/view_timeline:"):
    st.info("Click on a column name (e.g. “Start”) to sort.", icon=":material/info:")
    st.dataframe(
        tf_matches[["ELM_Acc", "ELM_Id", "Regex", "Matched_Sequence" ,"Start", "End"]],
        column_config={
            "ELM_Acc": "ELM Accession",
            "ELM_Id": "ELM ID",
            "Regex": "Regex",
            "Matched_Sequence": "Matched Sequence",
            "Start": "Start",
            "End": "End",
        },
        height=500 if len(tf_matches) > 5 else "content",
        hide_index=True,
    )

#endregion
