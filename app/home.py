import streamlit as st
from app.utils import data_loading
from app.utils import constants


#region Config
LOGO_IMAGE = "assets/logo.png"
st.set_page_config(
    page_title=constants.APP_NAME,
    initial_sidebar_state="collapsed",
)

st.html(f"""
<h1 align="center" style="font-size: 48px;">
    Welcome to
    <img src="{constants.ASSET_LOGO_DATAURI}" alt="" width="64" height="64"/>
    {constants.APP_NAME}!
</h1>
""")
st.caption("A Consolidated database of Disorder, Patterns and Functional annotations of Transcription Factors", text_alignment="center")
st.divider()

#endregion

#region Data loading
data = data_loading.init()
# disprot_df = data.disprot_df
tfclasses_df = data.tfclasses_df
genus_num_name_map = data.genus_num_name_map
# matches_df = data.matches_df
# sequence_dict = data.sequence_dict

#endregion


#region Search
st.header(":material/search: Search for a TF", anchor=False)
st.write("Search by UniProt accession, Genus number, or Genus name:")
with st.container(width="stretch", horizontal=True, horizontal_alignment="distribute"):
    searched_tf: str|None = st.selectbox(
        label="Search by UniProt accession, Genus number, or Genus name:",
        label_visibility="collapsed",
        options=tfclasses_df["Genus_Num"].dropna().unique(),
        format_func=lambda genus_num: genus_num_name_map.get(genus_num, genus_num), # type: ignore
        placeholder="Start typing...",
        index=None,
        help="You can search by typing in a [UniProt accession](https://www.uniprot.org/help/accession_numbers), [Genus number](http://tfclass.bioinf.med.uni-goettingen.de/about.jsf), or [Genus name](http://tfclass.bioinf.med.uni-goettingen.de/about.jsf) found in the [TFClass Resource](http://tfclass.bioinf.med.uni-goettingen.de/index.jsf).",
    )
    if st.button(
        label="Go to Viewer",
        icon=":material/search:",
        disabled=not searched_tf,
        type="primary",
    ) and searched_tf:
        st.switch_page(
            constants.PATH_PAGE_TF_VIEW,
            query_params={"genus_num": searched_tf}
        )

with st.container(width="stretch", horizontal=False):
    st.write("Or, try out an example:")
    examples = ["1.1.1.2.3", "1.1.7.1.1", "2.1.2.4.3"]
    for genus_num in examples:
        st.page_link(
            constants.PATH_PAGE_TF_VIEW,
            label=f":green[:material/search:] {genus_num_name_map[genus_num]}",
            query_params={"genus_num": genus_num}
        )

st.write("Or, browse all available TFs:")
st.page_link(
    constants.PATH_PAGE_TF_BROWSER,
    label="Go to :primary[:material/view_list: TF Browser]",
    icon=":material/arrow_forward:",
    icon_position="right",
)

#endregion

st.divider()

#region Details
st.header(f":material/info: What is {constants.APP_NAME}?", anchor=False)
st.markdown(f"""
{constants.CONTENT_SUMMARY}

Use the <a href="/tf_browser" target="_self" rel="noreferrer">TF Browser</a>
page to explore the available TFs and their characteristics, or jump
straight into the viewer for an in-depth look at a specific TF.

More details can be found in the <a href="/about" target="_self"
rel="noreferrer">About</a> page.
""", unsafe_allow_html=True)

#endregion

st.divider()

#region Contact
st.header(":material/contact_mail: Contact", anchor=False)
st.markdown(constants.CONTENT_CONTACT)

#endregion
