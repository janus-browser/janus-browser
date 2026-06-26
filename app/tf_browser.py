import streamlit as st
import pandas as pd

from app.utils import constants
from app.utils import data_loading
from app.utils import helper

#region Config
st.set_page_config(
    page_title=f"TF Browser | {constants.APP_NAME}",
    initial_sidebar_state="expanded",
)

with st.sidebar:
    st.empty()

st.html(f"""
<h1 align="center" style="font-size: 48px;">
    <img src="{constants.ASSET_LOGO_DATAURI}" alt="" width="64" height="64"/>
    TF Browser | {constants.APP_NAME}
</h1>
""")
st.caption("Browse and filter human transcription factors", text_alignment="center")

#endregion

#region Data loading
data = data_loading.init()
# disprot_df = data.disprot_df
tfclasses_df = data.tfclasses_df
# genus_num_name_map = data.genus_num_name_map
# matches_df = data.matches_df
# sequence_dict = data.sequence_dict

#endregion

#region Filter controls
catalog_filt = tfclasses_df
option, filter_by, filter_disprot = helper.render_filter_controls(catalog_filt)

if filter_disprot:
    # catalog_filt = catalog_filt[catalog_filt["Disprot_Available"] == "✅"] # 😭😭😭 goofy ahh logic
    catalog_filt = catalog_filt[catalog_filt["Disprot_Perc"] > 0]

if option and filter_by:
    st.write(f"Filtering by {filter_by}: `{'`, `'.join(option)}`")
    catalog_filt = catalog_filt[catalog_filt[filter_by].isin(option)]

# Since we're passing tfclasses_df_filtered to st.dataframe, and st.dataframe
# only accepts and returns *ROW NUMBERS*, we reset the index to count from 0.
catalog_filt = catalog_filt.reset_index(drop=True)

catalog_filt__before: pd.DataFrame = st.session_state.get("catalog_filt__before", catalog_filt)
catalog_filt__is_refiltered = len(catalog_filt__before) != len(catalog_filt) or (catalog_filt__before["Genus_Num"] != catalog_filt["Genus_Num"]).any()
st.session_state["catalog_filt__before"] = catalog_filt

#endregion

# Retrieve / Initialize cart
st.session_state["cart"] = st.session_state.get("cart", set())
cart: set[str] = st.session_state["cart"]

#region Catalog render
if (option and filter_by) or filter_disprot:
    st.write(f"Displaying `{len(catalog_filt)}` out of `{len(tfclasses_df)}` TFs (after filtering):")
else:
    st.write(f"Displaying `{len(tfclasses_df)}` TFs:")

# Add all variables to this list, such that when they change, it should trigger a re-render of the df:
catalog_filt__dependencies: str = "-".join(map(str, [
    filter_by,
    option,
    filter_disprot,
    st.session_state.get("sidebar_cart__trigger", 0),
]))
catalog_filt__state = st.dataframe(
    data=catalog_filt[["Genus_Num", "Uniprot_Acc", "Genus_Name", "Dbd_Range", "Disprot_Perc"]],
    selection_default={"selection": {"rows":
        catalog_filt.index[catalog_filt["Genus_Num"].isin(cart)].tolist()
    }},
    column_config={
        "Genus_Num": "Genus Number",
        "Uniprot_Acc": "UniProt Accession",
        "Genus_Name": "Genus Name",
        "Dbd_Range": "DBD Range",
        # "Disprot_Available": "DisProt data available?",
        "Disprot_Perc": st.column_config.ProgressColumn("Disordered content (as per DisProt)", min_value=0.0, max_value=1.0,),
    },
    height="stretch",
    hide_index=True,
    key=catalog_filt__dependencies,
    selection_mode="multi-row",
    on_select="rerun",
)

# if user re-filtered, then don't modify cart.
# if only selection changed, that means user actively clicked items, hence update the cart.
if not catalog_filt__is_refiltered:
    catalog_filt__sel_row_nums = helper.get_df_selected_rows(catalog_filt__state)
    catalog_filt__genus_num = catalog_filt["Genus_Num"]

    for i, genus_num in enumerate(catalog_filt__genus_num.tolist()):
        is_selected = i in catalog_filt__sel_row_nums

        if (is_selected) and (genus_num not in cart): cart.add(genus_num)
        elif (genus_num in cart) and (not is_selected): cart.remove(genus_num)

#endregion

#region Cart
with st.sidebar:
    st.header(":material/shopping_cart: Cart contents")

    if not cart:
        st.info(":material/info: Cart is empty. Make a selection first.")

    else:
        st.info(f":material/remove_shopping_cart: Items in cart: {len(cart)}")
        # MARK: Cart | df
        sidebar_cart = tfclasses_df[["Genus_Num", "Uniprot_Acc", "Genus_Name"]][tfclasses_df["Genus_Num"].isin(cart)]
        sidebar_cart__state = st.dataframe(
            data=sidebar_cart,
            column_config={
                "Genus_Num": "Genus #",
                "Uniprot_Acc": "UniProt",
                "Genus_Name": "Genus Name",
            },
            hide_index=True,
            key=f"sidebar-cart-{cart}",
            on_select="rerun",
            selection_mode="multi-row",
        )

        sidebar_cart__sel_row_nums = helper.get_df_selected_rows(sidebar_cart__state)
        sidebar_cart__sel_genus_nums: list[str] = sidebar_cart["Genus_Num"].iloc[sidebar_cart__sel_row_nums].tolist() # type: ignore
        sidebar_cart__sel_len = len(sidebar_cart__sel_genus_nums)



        # MARK: Cart | buttons
        with st.container(width="stretch", horizontal=True, horizontal_alignment="right"):
            if sidebar_cart__sel_len == 1:
                if st.button("View selected TF", icon=":material/visibility:", width="stretch"):
                    st.switch_page(constants.PATH_PAGE_TF_VIEW, query_params={"genus_num": sidebar_cart__sel_genus_nums[0]})
            else:
                if st.button(f"Compare `{sidebar_cart__sel_len}` selected TFs", icon=":material/visibility:", width="stretch", help="~~Select atleast 2 items to compare.~~ Work in progress feature.", disabled=True or sidebar_cart__sel_len<2):
                    st.switch_page(constants.PATH_PAGE_TF_COMPARE, query_params={"genus_nums": ",".join(sidebar_cart__sel_genus_nums)})

            if st.button(f":red[:material/delete: Delete `{sidebar_cart__sel_len}` selected TFs]", type="secondary", width="stretch", help="Remove selected TFs from the cart.", disabled=sidebar_cart__sel_len==0):
                for genus_num in sidebar_cart__sel_genus_nums: cart.remove(genus_num)
                st.session_state.update({"sidebar_cart__trigger": st.session_state.get("sidebar_cart__trigger", 0) + 1})
                st.rerun()

        st.divider()
        st.write(f"Click below to explore patterns occurring in the `{len(cart)}` TFs in the cart:")

        if st.button("Explore patterns", icon=":material/regular_expression:", width="stretch", type="primary"):
            st.switch_page(constants.PATH_PAGE_PATTERN_EXPLORER)#, query_params={"genus_nums": ",".join(sidebar_cart__sel_genus_nums)})

#endregion

st.divider()

st.header(":material/info: How to use", anchor=False)
st.markdown(
f"""
You can use this Browser page to discover and search amongst all the `{len(tfclasses_df)}` TFs available on disk, which are :primary[listed above in the table].

To narrow down your search, you may use the :primary[filters]. There are two types:
1. :primary[**Basic search**]: Search for one specific TF, either by its **Genus number** or **UniProt Accession** or **Genus name**
2. :primary[**Advanced search**]: List for all TFs which belong to a superclass/class/family/subfamily

For each TF that you want to add to the Cart, click on the :primary[:material/check_box:] icon.

The Cart is visible on the sidebar.
- Select :primary[**1**] item in the Cart to :primary[**view its details**].
- Select :primary[**2+**] items in the Cart to proceed to :primary[**Compare**] page (work in progress feature).
""")
