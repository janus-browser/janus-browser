import streamlit as st

from app.utils import constants

#region Config
st.set_page_config(
    page_title="Janus",
    # page_title="...",
    page_icon=constants.PATH_ASSET_LOGO,
    initial_sidebar_state="expanded",
    menu_items={
        "Report a bug": "https://github.com/janus-browser/janus-browser/issues",
    },
    layout="wide",
)
st.logo(constants.PATH_ASSET_LOGO, size="large")

#endregion


pages = [
    st.Page(constants.PATH_PAGE_HOME, icon=":material/home:", title="Home"),
    st.Page(constants.PATH_PAGE_TF_BROWSER, icon=":material/view_list:", title="TF Browser"),
    st.Page(constants.PATH_PAGE_TF_VIEW, icon=":material/visibility:", visibility="hidden", title="TF Viewer"),
    st.Page(constants.PATH_PAGE_TF_COMPARE, icon=":material/visibility:", visibility="hidden", title="TF Compare"),
    st.Page(constants.PATH_PAGE_PATTERN_EXPLORER, icon=":material/regular_expression:", title="Pattern Explorer"),
    st.Page(constants.PATH_PAGE_ABOUT, icon=":material/info:", title="About"),
]
pages = st.navigation(pages, position="top")
pages.run()

# TODO: Comparison page for comparing multiple TFs
# TODO: Filtering Algo for Patterns
