import streamlit as st

from app.utils import constants

#region Config
APP_COMMIT_HASH = constants.GET_APP_COMMIT_HASH()
st.set_page_config(
    page_title=constants.APP_NAME,
    # page_title="...",
    page_icon=constants.PATH_ASSET_LOGO,
    initial_sidebar_state="expanded",
    menu_items={
        "Report a bug": "https://github.com/tf-disco/tf-disco/issues",
        "About": "Current version: " + (f"[`{APP_COMMIT_HASH[:7]}`](https://github.com/tf-disco/tf-disco/tree/{APP_COMMIT_HASH})" if APP_COMMIT_HASH else "`unknown`"),
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
