from math import ceil

import streamlit as st
import pandas as pd

from app.utils import data_loading
from app.utils import constants
from app.utils import helper
from app.utils import patterns
from app.utils import sidebar
from app.utils import align_logo

#region Config
st.set_page_config(
    page_title=f"Pattern Explorer | {constants.APP_NAME}",
    initial_sidebar_state="expanded",
)

st.html(f"""
<h1 align="center" style="font-size: 48px;">
    Pattern Explorer |
    <img src="{constants.ASSET_LOGO_DATAURI}" alt="" width="64" height="64"/>
    {constants.APP_NAME}
</h1>
""")
st.caption("Explore and analyze patterns occuring in TFs", text_alignment="center")

with st.sidebar:
    st.empty()

COLUMNS = ["Genus_Num", "Uniprot_Acc", "Genus_Name", "ELM_Acc", "ELM_Id", "Regex"]

#endregion

#region Data loading
data = data_loading.init()
# disprot_df = data.disprot_df
tfclasses_df = data.tfclasses_df
# dbd_ranges_df = data.dbd_ranges_df
# genus_num_name_map = data.genus_num_name_map
matches_df = data.matches_df
sequence_dict = data.sequence_dict

#endregion



#region Cart
st.session_state["cart"] = st.session_state.get("cart", set())
cart: set[str] = st.session_state["cart"]
is_cart_empty = (len(cart) < 1)

with st.sidebar:
    st.page_link(constants.PATH_PAGE_TF_BROWSER, label="Go to :primary[:material/view_list: TF Browser]", icon=":material/arrow_back:", icon_position="left")

    st.header(f":material/shopping_cart: Cart contents (:primary[**{len(cart)}**] TF{'s' if len(cart) != 1 else ''})", anchor=False)

    filt_to_cart = st.toggle("Filter to Cart items only", value=(not is_cart_empty), help="Only show patterns that occur in the TFs currently in the cart.", disabled=is_cart_empty)

    if not cart:
        st.info(":material/info: Cart is empty.")

    else:
        sidebar_cart = tfclasses_df[["Genus_Num", "Uniprot_Acc", "Genus_Name"]][tfclasses_df["Genus_Num"].isin(cart)]
        sidebar_cart = pd.concat([
            sidebar_cart["Genus_Num"] + " [:material/article_shortcut:](/tf_view?genus_num=" + sidebar_cart["Genus_Num"] + ")",
            sidebar_cart["Uniprot_Acc"].apply(lambda acc: f"[{acc}](https://uniprot.org/entry/{acc})"),
            sidebar_cart["Genus_Name"],
        ], axis=1).rename({
            "Genus_Num": "Genus #",
            "Uniprot_Acc": "UniProt",
            "Genus_Name": "Genus Name",
        }, axis=1)
        sidebar_cart__state = st.table(
            data=sidebar_cart,
            hide_index=True,
            height=300 if len(sidebar_cart) > 5 else "content",
        )

    if cart and not filt_to_cart:
        st.info(":material/info: The patterns list is currently not filtering by cart, and is showing all TFs.")

#endregion



with st.expander(f"Select Patterns", expanded=True):
    #region Filter controls
    with st.container(horizontal=True, horizontal_alignment="distribute"):
        with st.container(horizontal=False, horizontal_alignment="left", width="content"):
            strictly_in_all_tfs = st.toggle(f"Show patterns that occur in **strictly all** the TFs" + (" in cart" if filt_to_cart else ""), value=False)

        max_penalty_at_20 = helper.render_vagueness_penalty_slider()
    vagueness_penalty_func = patterns.make_vagueness_penalty_func(max_penalty_at_20)

    #endregion

    #region Patterns list
    matches_filtered = matches_df
    if filt_to_cart and cart:
        matches_filtered = matches_filtered[matches_filtered["Genus_Num"].isin(cart)]

    if strictly_in_all_tfs:
        # select patterns which occur in ALL the tfs in matches_filtered
        required_genus_nums = set(matches_filtered["Genus_Num"].unique())
        matches_filtered = matches_filtered.groupby("ELM_Acc").filter(
            lambda pattern_group_df: required_genus_nums.issubset(set(pattern_group_df["Genus_Num"].unique()))
        )

    patterns_count_total = matches_df["ELM_Acc"].nunique()
    patterns_df = patterns.compute_pattern_scores(matches_filtered, sequence_dict, vagueness_penalty_func)
    score_min = patterns_df["Log2FC"].min()
    score_max = patterns_df["Log2FC"].max()

    if filt_to_cart or strictly_in_all_tfs:
        st.write(f"Displaying :primary[**{len(patterns_df)}**] out of :primary[**{patterns_count_total}**] patterns:")
    else:
        st.write(f"Displaying :primary[**{patterns_count_total}**] patterns:")

    display_columns = {
        "ELM_Acc": "ELM Accession",
        "ELM_Id": "ELM ID",
        "Regex": "Regex",
        "Vagueness": None,
        "Expected": None,
        "Observed": "Observed matches" + (" (in cart)" if filt_to_cart else ""),
        "ZScore": None,
        "Log2FC": None,
    }

    if len(patterns_df) == 0:
        st.warning("No patterns found. Try adding more TFs to the cart, or adjusting the settings above.")
        patterns__sel_row, patterns__sel_elm_acc = None, None
    else:
        patterns__dependencies = "-".join(map(str, [
            filt_to_cart,
            strictly_in_all_tfs,
            max_penalty_at_20,
        ]))
        patterns__state = st.dataframe(
            data=patterns_df[list(display_columns)],
            selection_default={"selection": {"rows":
                patterns_df.index[patterns_df["ELM_Acc"] == st.query_params.get("elm_acc", None)].tolist()
            }},
            column_config={
                **display_columns,
                # "Log2FC": st.column_config.ProgressColumn(display_columns["Log2FC"], min_value=score_min, max_value=score_max, format="%0.2f"),
            },
            hide_index=True,
            key=patterns__dependencies,
            selection_mode="single-row",
            on_select="rerun",
        )
        patterns__sel_row_nums = helper.get_df_selected_rows(patterns__state)
        patterns__sel_row = patterns_df.iloc[patterns__sel_row_nums[0]] if len(patterns__sel_row_nums) == 1 else None
        patterns__sel_elm_acc = patterns__sel_row["ELM_Acc"] if patterns__sel_row is not None else None

    if patterns__sel_elm_acc:
        st.query_params["elm_acc"] = patterns__sel_elm_acc
    else:
        if "elm_acc" in st.query_params: del st.query_params["elm_acc"]

    #endregion

st.divider()

if patterns__sel_row is None:
    st.warning("No pattern selected. Please select a pattern from the table above to see details here.")

    st.divider()
    st.header(":material/help: Help", anchor=False)
    st.markdown(constants.CONTENT_HELP_PATTERN_EXPLORER)

else:
    st.header(":material/regular_expression: Selected pattern", anchor=False)

    #region Selected pattern: Overview
    selected_pattern_matches_df: pd.DataFrame = matches_df[matches_df["ELM_Acc"] == patterns__sel_elm_acc]
    selected_pattern_df = (selected_pattern_matches_df
                                    .groupby(COLUMNS)
                                    .size()
                                    .sort_values(ascending=False)
                                    .reset_index(name="Observed"))
    patterns__sel_pattern = selected_pattern_df["Regex"].values[0]
    total_observed_counts = selected_pattern_df["Observed"].sum()
    if filt_to_cart:
        selected_pattern_matches_df = selected_pattern_matches_df[selected_pattern_matches_df["Genus_Num"].isin(cart)]
        selected_pattern_df = selected_pattern_df[selected_pattern_df["Genus_Num"].isin(cart)]

    with st.sidebar:
        sidebar.render_pattern_summary(patterns__sel_row)

    col1, col2, col3 = st.columns(3)

    col1.metric("ELM Accession", f"[{selected_pattern_df['ELM_Acc'].values[0]}](http://elm.eu.org/{selected_pattern_df['ELM_Acc'].values[0]})", border=True, help="The ELM (Eukaryotic Linear Motif) pattern accession number, which uniquely identifies the pattern in the ELM database.")
    col2.metric("ELM ID", f"[{selected_pattern_df['ELM_Id'].values[0]}](http://elm.eu.org/elms/{selected_pattern_df['ELM_Id'].values[0]})", border=True, help="The ELM (Eukaryotic Linear Motif) pattern ID, which uniquely identifies the pattern in the ELM database.")
    col3.metric("Observed Matches" + (" (in cart)" if filt_to_cart else ""), selected_pattern_df["Observed"].sum(), border=True, help="The number of matches of the pattern across all species.")

    @st.fragment(parallel=True)
    def pattern_logo_fragment(sequences: list[str]):
        with st.spinner("Generating logo..."):
            aligned_sequences = align_logo.run_muscle_alignment(
                sequences=sequences,
            )
            size = (150 * len(aligned_sequences[0]), 400)
            img = align_logo.create_logo(
                aligned_sequences=aligned_sequences,
                font_name="serif",
                size=size,
                prob_threshold=0.025,
            )
            size = img.size

        target_height = 150
        with st.container(width=(target_height * img.width) // img.height):
            st.image(img, width="stretch")

    with st.container(width="stretch", border=True, horizontal=True, horizontal_alignment="distribute"):
        st.metric(
            "Regex",
            f"`{patterns__sel_pattern}`",
            help="The regular expression that defines the ELM pattern. This regex is used to search for matches of the pattern in protein sequences. The regex syntax follows standard conventions, where specific characters and symbols represent different types of amino acids or sequence features. For more information on the regex syntax used for ELM patterns, please refer to the [ELM documentation](http://elm.eu.org/infos/help.html)."
        )
        with st.container(width="content"):
            pattern_logo_fragment(sequences=sorted(selected_pattern_matches_df["Matched_Sequence"].tolist()))

    #endregion


    #region Selected pattern: Matches in sequences
    # if cart and sequence_dict:
    with st.expander("Matches in Sequences", expanded=False):
        with st.container(horizontal=True, vertical_alignment="center", horizontal_alignment="right"):
            st.subheader(f"Matches for pattern `{patterns__sel_pattern}`", anchor=False)
            st.write("Download:")
            st.download_button(
                label=":material/download: HTML",
                data=selected_pattern_matches_df.to_html(index=False, escape=False).encode("utf-8"),
                file_name=f"pattern_{patterns__sel_elm_acc}_matches.html",
                mime="text/html",
            )
            st.download_button(
                label=":material/download: TSV",
                data=selected_pattern_matches_df.to_csv(index=False, sep="\t").encode("utf-8"),
                file_name=f"pattern_{patterns__sel_elm_acc}_matches.tsv",
                mime="text/tab-separated-values",
            )
            st.download_button(
                label=":material/download: CSV",
                data=selected_pattern_matches_df.to_csv(index=False).encode("utf-8"),
                file_name=f"pattern_{patterns__sel_elm_acc}_matches.csv",
                mime="text/csv",
            )

        genus_nums = list(selected_pattern_df["Genus_Num"].unique())
        if filt_to_cart: genus_nums = [g for g in genus_nums if g in cart]
        TFS_PER_PAGE = st.selectbox("TFs per page:", options=[5, 10, 20], filter_mode=None) if len(genus_nums) > 5 else len(genus_nums)
        NUM_PAGES = max(1, ceil(len(genus_nums) / TFS_PER_PAGE))

        page_top = st.pagination(
            num_pages=NUM_PAGES,
            max_visible_pages=20,
            key="pagination_top",
            width="stretch",
            on_change=lambda: st.session_state.update({"pagination_bottom": st.session_state.get("pagination_top", 1)})
        )-1 if NUM_PAGES > 1 else 0

        for genus_num in genus_nums[page_top*TFS_PER_PAGE:(page_top+1)*TFS_PER_PAGE]:
            tfinfo = sequence_dict.get(genus_num, data_loading.TFInfo(Uniprot_Acc="", Genus_Name="", Sequence=""))
            observed_matches_count = selected_pattern_df[selected_pattern_df["Genus_Num"] == genus_num]["Observed"].sum()

            st.divider()
            st.subheader(f"Matches for genus `{genus_num}` | [`{tfinfo.Uniprot_Acc}`](https://uniprot.org/entry/{tfinfo.Uniprot_Acc}) | {tfinfo.Genus_Name}", anchor=False)
            st.write(f"Observed Matches: {observed_matches_count}")
            st.markdown(helper.render_sequence(sequence=tfinfo.Sequence, pattern=patterns__sel_pattern), unsafe_allow_html=True)
            st.space(size="small")

        page_bot = st.pagination(
            num_pages=NUM_PAGES,
            max_visible_pages=20,
            key="pagination_bottom",
            width="stretch",
            on_change=lambda: st.session_state.update({"pagination_top": st.session_state.get("pagination_bottom", 1)})
        )-1 if NUM_PAGES > 1 else 0

    #endregion

    #region Selected pattern: Matches
    selected_pattern_df = selected_pattern_df.drop(columns=["Regex", "ELM_Acc", "ELM_Id"])
    with st.expander("Frequency of Matches per TF", expanded=True):
        with st.container(horizontal=True, vertical_alignment="center", horizontal_alignment="right"):
            st.subheader(f"Frequency of Matches per TF for pattern `{patterns__sel_pattern}`", anchor=False)

            st.write("Download:")
            st.download_button(
                label=":material/download: TSV",
                data=selected_pattern_df.to_csv(index=False, sep="\t").encode("utf-8"),
                file_name=f"pattern_{patterns__sel_elm_acc}_frequency.tsv",
                mime="text/tab-separated-values",
            )
            st.download_button(
                label=":material/download: CSV",
                data=selected_pattern_df.to_csv(index=False).encode("utf-8"),
                file_name=f"pattern_{patterns__sel_elm_acc}_frequency.csv",
                mime="text/csv",
            )

        st.table(
            data=pd.concat({
                "Genus #": (selected_pattern_df["Genus_Num"] + " [:material/article_shortcut:](/tf_view?genus_num=" + selected_pattern_df["Genus_Num"] + ")"),
                "UniProt": selected_pattern_df["Uniprot_Acc"].apply(lambda acc: f"[{acc}](https://uniprot.org/entry/{acc})"),
                "Genus Name": selected_pattern_df["Genus_Name"],
                "Observed Matches": selected_pattern_df["Observed"],
            }, axis=1),
            hide_index=True,
            height=500 if len(selected_pattern_df) > 10 else "content",
        )

    #endregion
