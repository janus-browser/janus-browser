import streamlit as st

from app.utils import constants



#region Config
st.set_page_config(
    page_title=f"About | {constants.APP_NAME}",
    initial_sidebar_state="collapsed",
)

#endregion

st.html(f"""
<h1 align="center" style="font-size: 48px;">
    About
    <img src="{constants.ASSET_LOGO_DATAURI}" alt="" width="64" height="64"/>
    {constants.APP_NAME}!
</h1>
""")
st.caption("A Consolidated Database of Human Transcription Factors Information", text_alignment="center")

st.divider()

#region Details
st.header(f":material/info: What is {constants.APP_NAME}?", anchor=False)
st.markdown(f"""
    {constants.APP_NAME} is a comprehensive database and visualization tool for human
    transcription factors (TFs). It integrates data from multiple sources,
    including [UniProt](https://www.uniprot.org),
    [DisProt](https://disprot.org), and the [ELM Resource](http://elm.eu.org),
    to provide detailed information on selected TFs. Disorder and some relevent
    scores are precalculated from AIUPred, flDPnn, and Metapredict v3 and known
    patterns are retreived and stored from the above mentioned sources.

    Use the <a href="/tf_browser" target="_self" rel="noreferrer">Browser</a> page
    to explore the available TFs and their characteristics, or jump straight
    into the viewer for an in-depth look at a specific TF.

    More details can be found in the <a href="/about" target="_self"
    rel="noreferrer">About</a> page.
""", unsafe_allow_html=True)
#endregion

st.divider()

#region Contact
st.header(":material/contact_mail: Contact", anchor=False)
st.markdown("""
    For inquiries, feedback, or contributions, please reach out to us at
    [f20220019@dubai.bits-pilani.ac.in](mailto:f20220019@dubai.bits-pilani.ac.in). We welcome your input and
    look forward to hearing from you!
""")

#endregion
