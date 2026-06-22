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
    <img src="{constants.ASSET_LOGO_DATAURI}" alt="" width="64" height="64"/>
    Pattern Explorer | {constants.APP_NAME}
</h1>
""")
st.caption("Explore and analyze transcription factor patterns", text_alignment="center")

with st.sidebar:
    st.empty()

columns = ["Genus_Num", "Uniprot_Acc", "Genus_Name", "ELM_Acc", "ELM_Id", "Regex"]

#endregion

#region Data loading
data = data_loading.init()
# disprot_df = data.disprot_df
tfclasses_df = data.tfclasses_df
# genus_num_name_map = data.genus_num_name_map
matches_df = data.matches_df
sequence_dict = data.sequence_dict

#endregion



st.session_state["cart"] = st.session_state.get("cart", set())
cart: set[str] = st.session_state["cart"]



with st.expander(f"Select Patterns", expanded=True):
    #region Filter controls
    is_cart_empty = (len(cart) < 1)
    with st.container(horizontal=True, horizontal_alignment="distribute"):
        with st.container(horizontal=False, horizontal_alignment="left", width="content"):
            patterns_filt_to_cart = st.toggle("Filter to Cart items only", value=(not is_cart_empty), help="Only show patterns that occur in the TFs currently in the cart.", disabled=is_cart_empty)
            strictly_in_all_tfs = st.toggle(f"Show patterns that occur in **strictly all** the TFs" + (" in cart" if patterns_filt_to_cart else ""), value=False)

        max_penalty_at_20 = helper.render_vagueness_penalty_slider()
    vagueness_penalty_func = patterns.make_vagueness_penalty_func(max_penalty_at_20)

    #endregion

    #region Patterns list
    matches_filtered = matches_df
    if patterns_filt_to_cart and cart:
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

    if patterns_filt_to_cart or strictly_in_all_tfs:
        st.write(f"Displaying `{len(patterns_df)}` out of `{patterns_count_total}` patterns:")
    else:
        st.write(f"Displaying `{patterns_count_total}` patterns:")

    display_columns = {
        "ELM_Acc": "ELM Accession",
        "ELM_Id": "ELM ID",
        "Regex": "Regex",
        "Vagueness": "Vagueness",
        "Expected": "Expected matches",
        "Observed": "Observed matches",
        "ZScore": "Z-Score",
        "Log2FC": "log₂ Fold Change",
    }

    if len(patterns_df) == 0:
        st.warning("No patterns found. Try adding more TFs to the cart, or adjusting the settings above.")
        patterns__sel_row, patterns__sel_elm_acc = None, None
    else:
        patterns__state = st.dataframe(
            data=patterns_df[list(display_columns)],
            column_config={
                **display_columns,
                "Log2FC": st.column_config.ProgressColumn(display_columns["Log2FC"], min_value=score_min, max_value=score_max, format="%0.2f"),
            },
            height="stretch",
            hide_index=True,
            selection_mode="single-row",
            on_select="rerun",
        )
        patterns__sel_row_nums = helper.get_df_selected_rows(patterns__state)
        patterns__sel_row = patterns_df.iloc[patterns__sel_row_nums[0]] if len(patterns__sel_row_nums) == 1 else None
        patterns__sel_elm_acc = patterns__sel_row["ELM_Acc"] if patterns__sel_row is not None else None

    #endregion

#region Cart
with st.sidebar:
    st.page_link(constants.PATH_PAGE_TF_BROWSER, label=":primary[Go to TF Browser]", icon=":material/arrow_back:", icon_position="left")

    st.html(f"""<style>.st-key-sidebar-cart {{opacity: {1 if patterns_filt_to_cart else 0.4};}}</style>""")

    with st.container(key="sidebar-cart"):
        st.header(":material/shopping_cart: Cart contents")
        if not cart:
            st.info(":material/info: Cart is empty.")

        else:
            st.info(f":material/remove_shopping_cart: Items in cart: {len(cart)}")
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
                height=300 if len(sidebar_cart) > 5 else "content",
            )

    if not patterns_filt_to_cart:
        st.info(":material/info: The patterns list is currently not filtering by cart, and is showing all TFs.")

with st.sidebar:
    if patterns__sel_row is not None:
        sidebar.render_pattern_summary(patterns__sel_row)

#endregion

st.divider()
st.header(":material/regular_expression: Selected pattern", anchor=False)

if patterns__sel_elm_acc is None:
    st.warning("No pattern selected. Please select a pattern from the table above to see details here.")

else:
    #region Selected pattern: Overview
    selected_pattern_matches_df: pd.DataFrame = matches_df[matches_df["ELM_Acc"] == patterns__sel_elm_acc]
    selected_pattern_df = (selected_pattern_matches_df
                                    .groupby(columns)
                                    .size()
                                    .sort_values(ascending=False)
                                    .reset_index(name="Observed"))
    patterns__sel_pattern = selected_pattern_df['Regex'].values[0]

    if len(selected_pattern_df) == 0:
        st.warning("No matches of this pattern found in the selected species. Try selecting a different pattern or adding more species to the cart.")

    col1, col2, col3 = st.columns(3)

    col1.metric("ELM Accession", f"[{selected_pattern_df['ELM_Acc'].values[0]}](http://elm.eu.org/{selected_pattern_df['ELM_Acc'].values[0]})", border=True, help="The ELM (Eukaryotic Linear Motif) pattern accession number, which uniquely identifies the pattern in the ELM database.")
    col2.metric("ELM ID", f"[{selected_pattern_df['ELM_Id'].values[0]}](http://elm.eu.org/elms/{selected_pattern_df['ELM_Id'].values[0]})", border=True, help="The ELM (Eukaryotic Linear Motif) pattern ID, which uniquely identifies the pattern in the ELM database.")
    col3.metric("Total Matches", selected_pattern_df["Observed"].sum(), border=True, help="The total number of matches of the pattern across all species.")

    @st.fragment()
    def render_alignment_logo():
        with st.spinner("Generating logo..."):
            _, aligned_df = align_logo.run_muscle_alignment(
                sequences=selected_pattern_matches_df[["Genus_Num", "Start", "End", "Matched_Sequence"]],
                print_on_error=True,
            )
            size = (50 * len(aligned_df["Aligned_Sequence"].iloc[0]), 300)
            img = align_logo.create_logo(
                aligned_sequences=aligned_df["Aligned_Sequence"].tolist(),
                font_name="serif",
                size=size,
                prob_threshold=0.025,
            )
            size = img.size

        target_height = 150
        with st.container(width=(target_height * img.width) // img.height):
            st.image(img, width="stretch")

    with st.container(width="stretch", horizontal=True, horizontal_alignment="distribute"):
        st.metric(
            "Regex",
            f"`{patterns__sel_pattern}`",
            border=True,
            help="The regular expression that defines the ELM pattern. This regex is used to search for matches of the pattern in protein sequences. The regex syntax follows standard conventions, where specific characters and symbols represent different types of amino acids or sequence features. For more information on the regex syntax used for ELM patterns, please refer to the [ELM documentation](http://elm.eu.org/infos/help.html)."
        )

        render_alignment_logo()

    #endregion

    #region Selected pattern: Matches in sequences
    # if cart and sequence_dict:
    with st.expander("Matches in Sequences", expanded=False):
        genus_nums = set(selected_pattern_df["Genus_Num"].unique())

        # show_only_with_matches = st.toggle("Show only sequences with matches", value=True, help="Only show sequences that have at least one match of the selected pattern.")
        sequences_filt_to_cart = st.toggle("Filter to Cart items only", value=(not is_cart_empty), help="Only show sequences that are currently in the cart.", disabled=is_cart_empty)
        if sequences_filt_to_cart: genus_nums = genus_nums.intersection(cart)

        for genus_num in genus_nums:
            # if not selected_pattern_df["Genus_Num"].isin([genus_num]).any():
            #     continue
            tfinfo = sequence_dict.get(genus_num, data_loading.TFInfo(Uniprot_Acc="", Genus_Name="", Sequence=""))

            st.divider()
            st.subheader(f"Matches for genus `{genus_num}` | `{tfinfo.Uniprot_Acc}` | {tfinfo.Genus_Name}", anchor=False)
            st.markdown(helper.render_sequence(tfinfo.Sequence, patterns__sel_pattern), unsafe_allow_html=True)
            st.space(size="small")

    #endregion

    #region Selected pattern: Matches

    selected_pattern_df = selected_pattern_df.drop(columns=["Regex", "ELM_Acc", "ELM_Id"])

    st.table(
        data=pd.concat({
            "Genus #": (selected_pattern_df["Genus_Num"] + " [:material/article_shortcut:](/tf_view?genus_num=" + selected_pattern_df["Genus_Num"] + ")"),
            "UniProt": selected_pattern_df["Uniprot_Acc"].apply(lambda acc: f"[{acc}](https://uniprot.org/entry/{acc})"),
            "Genus Name": selected_pattern_df["Genus_Name"],
            "Observed Matches": selected_pattern_df["Observed"],
        }, axis=1),
        height=500 if len(selected_pattern_df) > 10 else "content",
    )

    #endregion
