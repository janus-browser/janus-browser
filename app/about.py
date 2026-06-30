import streamlit as st

from app.utils import constants



#region Config
st.set_page_config(
    page_title=f"About | {constants.APP_NAME}",
    initial_sidebar_state="expanded",
    # layout="centered",
)

st.html("<style>.stMain h2 {text-decoration: underline 2px;} .stMain h2 span[role='img'] {margin-right: 0.5rem;}</style>")

st.html(f"""
<h1 align="center" style="font-size: 48px;">
    About 
    <img src="{constants.ASSET_LOGO_DATAURI}" alt="" width="64" height="64"/>
    {constants.APP_NAME}!
</h1>
""")
st.caption("A Consolidated Database of Transcription Factors Information", text_alignment="center")

#endregion

st.divider()

#region What is
st.header(f":primary[:material/info:]**What is {constants.APP_NAME}?**", anchor="what_is")
st.markdown(constants.CONTENT_SUMMARY, unsafe_allow_html=True)

#endregion

st.divider()

#region Features
st.header(":primary[:material/star_shine:]**Features**", anchor="features")
st.markdown(f"""
- **:primary[:material/search: Search and filter].** The database can be queried
  for individual TFs or multiple TFs, based on their UniProt accession and TF
  classification (genus number, genus name). Filter results down to a specific
  subset of TFs as per your interest.

- **:primary[:material/shopping_cart: Cart system].** The user can select TFs of
  interest, and add them to a "cart". This selection can be used to perform a
  more narrowed-down analysis on the patterns/motifs occuring in them.

- **:primary[:material/assignment: Per-TF analysis].** For a selected TF, the
  user can view its full sequence, highlight the patterns found in that
  sequence, visualize & plot the per-resisude disorder propensity scores, and
  observe where each pattern falls relative to the DNA-binding domain and
  activation domain.

- **:primary[:material/area_chart: Interactive graphs and tables].** All plots,
  sequences and most tables are interactive, allowing for zooming into regions,
  toggle annotations, and sort rows.

- **:primary[:material/crown: Pattern ranking based on vagueness].** Patterns
  are ranked using a vagueness penalty metric, which penalizes motifs with
  high sequence variability (i.e. regexes that match many different amino
  acids). This promotes patterns that are more specific, and thus more
  biologically meaningful.

<!--
- **:primary[:material/text_compare: Cross-TF comparison].** TFs in the cart can
  be compared for shared patterns, their disorder characteristics, and whether
  their functional mapping (DBD vs. activation domain) is conserved. This
  supports cross-family and cross-class analysis.
-->

- **:primary[:material/regular_expression: Consensus motifs].** For patterns
  that occur in multiple TFs, {constants.APP_NAME} builds a consensus motif
  using Multiple Sequence Alignment ([MUSCLE](https://drive5.com/muscle5)) and
  displays it as a sequence logo. This can be executed on either the entire
  dataset of TFs, or on a custom selection by the user for a more nuanced
  analysis.

- **:primary[:material/download: Downloads].** Datasets, annotations, and
  analysis outputs (sequences, scores, matches, pattern frequencies) can be
  downloaded as CSV/TSV/FASTA for local processing or use in external workflows.

- **:primary[:material/link: Shareable URLs].** Specific TF Viewer and Pattern
  Explorer views can be shared as a direct link, so others can reproduce the
  same analysis. (Please note that cart contents are not currently encoded in
  shared URLs.)
""", unsafe_allow_html=True)

#endregion

st.divider()

#region Help
st.header(":primary[:material/help:]**Help**", anchor="help")
st.markdown(f"""
{constants.APP_NAME} is organized into a few pages, and you can perform the
following workflow:
1. Browse and discover available TFs
2. Analyze a particular TF in detail
3. Explore patterns/motifs across a selection of TFs or the entire dataset

Click here to view the full Help page:
""")

st.page_link(
  constants.PATH_PAGE_HELP,
  label="Go to :primary[:material/help: Help]",
  icon=":material/arrow_forward:",
  icon_position="right",
)

#endregion

st.divider()

#region Contact
st.header(":primary[:material/contact_mail:]**Contact**", anchor="contact")
st.markdown(constants.CONTENT_CONTACT)

#endregion
