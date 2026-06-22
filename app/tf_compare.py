import streamlit as st

from app.utils import constants
from app.utils import data_loading
from app.utils import sidebar
from app.utils import helper
from app.utils import graph

#region Config
st.set_page_config(
    page_title=f"Compare | {constants.APP_NAME}",
    initial_sidebar_state="expanded",
)
#endregion

st.warning("This page is under construction.", icon=":material/construction:")
st.page_link(constants.PATH_PAGE_HOME, label="Go to Home", icon=":material/arrow_back:", icon_position="left")
st.stop()

































#region Data loading
data = data_loading.init()
disprot_df = data.disprot_df
tfclasses_df = data.tfclasses_df
genus_num_name_map = data.genus_num_name_map
load_disorder_scores = data_loading.load_disorder_scores
load_pattern = data_loading.__load_matches

#endregion

@st.dialog(
    title="No TFs selected",
    icon=":material/error:",
    dismissible=False
)
def blank_view():
    st.error("No TFs selected. Please select more than one TFs from the browser.", icon=":material/error:")
    st.page_link(constants.PATH_PAGE_TF_BROWSER, label="Go to TF Browser", icon=":material/arrow_back:", icon_position="left")

if "genus_nums" not in st.query_params:
    blank_view()
    st.stop()

# st.write(st.query_params)

# st.divider()

# =========================================================

selected_rows = None
genus_nums_from_url = st.query_params["genus_nums"].split(",") if "genus_nums" in st.query_params else []

matches = tfclasses_df[tfclasses_df["Genus_Num"].isin(genus_nums_from_url)]
selected_rows = matches.to_dict(orient="records")

# if matches is not None:
with st.container(horizontal=True, width="content"):
    for selected_row in selected_rows:
        with st.container(horizontal=False):
            # selected_row = next((row for row in selected_rows if row["Genus_Num"] == genus_num), None)
            # selected_row = selected_rows[selected_rows["Genus_Num"] == genus_num].iloc[0]
            # if not selected_row:
            #     continue
            selected_genus_num: str = selected_row["Genus_Num"]
            selected_uniprot: str = selected_row["Uniprot_Acc"]
            selected_genus_name: str = selected_row["Genus_Name"]

            selected_disorder_df = load_disorder_scores(selected_genus_num)
            selected_patterns_df = load_pattern(selected_genus_num)
            length = len(selected_disorder_df)

            disprot_regions = disprot_df[disprot_df["Uniprot_Acc"] == selected_uniprot]
            disprot_regions = disprot_regions.sort_values(by="End", ascending=False).sort_values(by="Start")
            disprot_id = disprot_regions.iloc[0]["Region_Id"].split("r")[0] if not disprot_regions.empty else "N/A"

            # Sidebar details
            with st.sidebar:
                st.divider()
                sidebar.render_tf_summary(selected_row, length, disprot_regions) # type: ignore
                st.divider()
                selected_pattern = sidebar.render_pattern_selector(selected_patterns_df, selected_genus_num)

            # TF metrics cards
            st.header(f"{selected_genus_name}", anchor="selected_tf") #: {selected_genus_num} | {selected_genus_name} | [{selected_uniprot}](https://www.uniprot.org/uniprotkb/{selected_uniprot}/entry)")
            col1, col2, col3 = st.columns(3, border=True)
            col1.metric(":material/link: *UniProt Accession*", f"**[{selected_uniprot}](https://www.uniprot.org/uniprotkb/{selected_uniprot}/entry)**")
            col2.metric(":material/error_med: *DisProt ID*", f"**[{disprot_id}](https://disprot.org/{disprot_id})**" if not disprot_regions.empty else "N/A")
            col3.metric(":material/straighten: *Sequence length*", f"**{length} residues**")

            # Sequence section
            with st.expander("Show Sequence", icon=":material/genetics:", expanded=False):
                sequence = selected_disorder_df['Residue'].str.cat(sep='')
                sequence_html = helper.render_sequence(sequence=sequence, pattern=selected_pattern)
                sequence_fasta = f">{selected_genus_num}_{selected_uniprot}_{selected_genus_name}\n{sequence}\n"
                st.write(f"{sequence_html}", unsafe_allow_html=True)
                st.divider()
                with st.container(horizontal=True, vertical_alignment="center", horizontal_alignment="distribute"):
                    st.text("FASTA:")
                    st.download_button(
                        label=":material/download: Download FASTA",
                        data=sequence_fasta,
                        file_name=f"{selected_genus_num}_{selected_uniprot}_{selected_genus_name}.fasta",
                        mime="text/plain"
                    )
                st.code(sequence_fasta, language="plaintext", line_numbers=False, wrap_lines=False)

                # TODO: weblogo
                # sigh

            st.divider()
            st.space(2)

            # Scores section
            score_cols: list[graph.ScoreName] = [
                "Aiupred",
                "AiupredLatest-Disorder",
                "AiupredLatest-Binding",
                "AiupredLatest-Linker",
                "HI",
                "Fldpnn-Disorder",
                "Fldpnn-ProteinBinding",
                "Fldpnn-DnaBinding",
                "Fldpnn-RnaBinding",
                "Fldpnn-Linker",
                "Metapredict-Disorder",
            ]

            default_cols: list[graph.ScoreName] = [
                "AiupredLatest-Disorder",
                "HI",
                "Fldpnn-Disorder",
                "Metapredict-Disorder",
            ]
            # persist selection across navigations
            st.session_state["scoresToDisplay"] = st.session_state.get("scoresToDisplay", default_cols)

            with st.expander("Score Plots", icon=":material/area_chart:", expanded=False):
                st.subheader("Score Plots:")
                display_scores = st.pills(
                    label="Select scores to display:",
                    options=score_cols,
                    default=st.session_state["scoresToDisplay"],
                    selection_mode="multi",
                    key=f"scoresToDisplay-{selected_genus_num}",
                )
                # TODO: also add sequence in x axis
                fig = graph.create_scores_plotly(
                    length=length,
                    scores_list=[
                        graph.make_score_renderable(score_name, selected_disorder_df)
                        for score_name in score_cols
                        if score_name in display_scores
                    ],
                    disprot_regions=disprot_regions,
                )
                st.plotly_chart(fig)

            # Disprot regions section
            if not disprot_regions.empty:
                with st.expander("DisProt Regions for selected TF", icon=":material/error_med:", expanded=True):
                    st.subheader(f"DisProt Regions for [{disprot_id}](https://disprot.org/{disprot_id}):")
                    st.dataframe(
                        disprot_regions[["Region_Id", "Start", "End"]],
                        key=f"disprot_regions-{selected_uniprot}", # uncomment if you make the rows selectable later on
                        hide_index=True,
                    )

            # Patterns section
            # TODO: remove patterns with only 1 occurance

            patterns_reqd = load_pattern(selected_genus_num)
            patterns_reqd = patterns_reqd[patterns_reqd.groupby("Regex")["Instance_accession"].transform("count") > 1]
            patterns_reqd = (
                patterns_reqd
                    .groupby(['Instance_accession', 'Regex', "motif_start_in_query", "motif_end_in_query"], as_index=False)
                    .first()
            )

            if not patterns_reqd.empty:
                with st.expander("ELM Patterns for selected TF", icon=":material/view_timeline:"):
                    st.dataframe(
                        patterns_reqd[["Instance_accession", "Regex", "Instances (Matched Sequence)" ,"motif_start_in_query", "motif_end_in_query"]],
                        # patterns_reqd[["Instance_accession", "Regex", "Matched_sequence" ,"motif_start_in_query", "motif_end_in_query"]],
                        key=f"patterns-{selected_genus_num}", # uncomment if you make the rows selectable later on
                        hide_index=False,
                    )
