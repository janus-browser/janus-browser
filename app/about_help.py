import streamlit as st

from app.utils import constants
from app.utils import helper



#region Config
st.set_page_config(
    page_title=f"Help | {constants.APP_NAME}",
    initial_sidebar_state="expanded",
    # layout="centered",
)

st.html(f"""
<h1 align="center" style="font-size: 48px;">
    Help |
    <img src="{constants.ASSET_LOGO_DATAURI}" alt="" width="64" height="64"/>
    {constants.APP_NAME}
</h1>
""")
st.caption("A Consolidated Database of Transcription Factors Information", text_alignment="center")

#endregion

st.divider()

st.sidebar.write(f"""
## Pages:
\n:material/home: [Home Page](#home_page)
\n:material/view_list: [TF Browser](#tf_browser)
\n:material/visibility: [TF Viewer](#tf_viewer)
\n:material/regular_expression: [Pattern Explorer](#pattern_explorer)
""")



#region Help
# st.header(":primary[:material/help:]**Help**", anchor="help")
st.markdown(f"""
{constants.APP_NAME} is organized into a few pages, and you can perform the
following workflow:
1. Browse and discover available TFs
2. Analyze a particular TF in detail
3. Explore patterns/motifs across a selection of TFs or the entire dataset

Below is an overview of each page and its functionality:
""")

st.subheader(":material/home: Home Page", anchor="home_page")
helper.container_indent().markdown(
f"""
You can start search for a TF in the searchbox using [UniProt
accession](https://www.uniprot.org/help/accession_numbers), Genus number, or
Genus name (derived from the [TFClass
Resource](http://tfclass.bioinf.med.uni-goettingen.de/index.jsf)), and use the
:primary[:material/search: Go To Viewer] button to explore the details in the
:primary[:material/visibility: TF Viewer].

Or click on one of the :primary[example TFs] also mentioned to explore how
{constants.APP_NAME} works.

Or go to :primary[:material/view_list: TF Browser] to see all available TFs.
""")

st.subheader(":material/view_list: TF Browser", anchor="tf_browser")
helper.container_indent().markdown(constants.CONTENT_HELP_TF_BROWSER)

st.subheader(":material/visibility: TF Viewer", anchor="tf_viewer")
helper.container_indent().markdown(
"""
Detailed view of a single TF: its sequence (with optional DBD and disorder
overlays), disorder score plots from AIUPred, flDPnn, and Metapredict, DisProt
regions, and every ELM pattern match found in its sequence. Sequence and data
can be downloaded from this page.
""")

st.subheader(":material/regular_expression: Pattern Explorer", anchor="pattern_explorer")
helper.container_indent().markdown(constants.CONTENT_HELP_PATTERN_EXPLORER)

#endregion

st.divider()

#region Contact
st.header(":primary[:material/contact_mail:] **Contact**", anchor="contact")
st.markdown("""
For inquiries, feedback, or contributions, please reach out to us at
[debostuti@dubai.bits-pilani.ac.in](mailto:debostuti@dubai.bits-pilani.ac.in)
or make an [issue on GitHub](https://github.com/tf-disco/tf-disco/issues).
We welcome your input and look forward to hearing from you!
""")

#endregion
