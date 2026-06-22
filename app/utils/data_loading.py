"""Module for loading data from disk.

Call the `init()` function to get the required variables."""

if __name__ == "__main__":
    print("This module is not intended to be run directly.")
    print("Please import this as a module on the main Streamlit page (app.py).")
    exit()

from pathlib import Path
from dataclasses import dataclass
from typing import Any, NamedTuple

import streamlit as st
import pandas as pd
import kagglehub
from Bio.SeqIO.FastaIO import FastaIterator

from . import constants
from . import helper



# ============================================================================ #

# DISORDER_COLS_DONT_REPLACE_X = {
#     "Position", "Residue", "DbdFlag",
#     "Disprot", "DisprotRegionIds",
#     "AiupredAgreesWithDisprot", "HICorrelatesWithDisprot",
# }

# ============================================================================ #

#region Internal functions
@st.cache_resource()
def __global_state() -> dict[str, Any]:
    """A dictionary to hold global state. This is used to share data among
    multiple Streamlit sessions/users."""
    return {}

# @st.cache_data(show_spinner="Downloading data from Kaggle...")
def __initialize_dataset():
    """Downloads the dataset from Kaggle, and sets the paths in `constants.PATH_DATA`."""
    if constants.ENV_DATASET_PATH_OVERRIDE and constants.ENV_DATASET_PATH_OVERRIDE.is_dir():
        print(f"Using dataset path from environment variable: {constants.ENV_DATASET_PATH_OVERRIDE}")
        base_dir = constants.ENV_DATASET_PATH_OVERRIDE
    else:
        print("Downloading dataset from Kaggle...")
        base_dir = Path(kagglehub.dataset_download(handle=constants.KAGGLE_HANDLE))
        print("Download complete!")
    constants.PATH_DATA.set_base_dir(base_dir)

# @st.cache_data(show_spinner="Loading DisProt and TFClasses data...")
def __load_disprot_tfclasses_dfs() -> tuple[pd.DataFrame, pd.DataFrame, dict[str, str]]:
    """Loads and returns:
    1. DisProt DataFrame
    2. TFClasses DataFrame
    3. A mapping from Genus number to Genus name (e.g. `"2.1.1.1.1"` -> `"Glucocorticoid receptor (GR) (NR3C1)"`)
    """

    tfclasses_df = pd.read_csv(constants.PATH_DATA.TFCLASSES, sep="\t")
    disprot_df = pd.read_csv(constants.PATH_DATA.DISPROT, sep="\t")

    disprot_df = disprot_df.sort_values(by=["Uniprot_Acc", "Start", "End"], ascending=True).reset_index(drop=True)

    # for each row (tf), `genus_num_parts` is a list of ints.
    # 1. sort on genus number
    tfclasses_df["Genus_Num_Parts"] = tfclasses_df["Genus_Num"].str.split(".").map(lambda parts: [int(part) for part in parts]) # type:ignore
    tfclasses_df = tfclasses_df.sort_values(by="Genus_Num_Parts")

    # 2. create columns superclass, class, family, subfamily, genus:
    tfclasses_df["Superclass"] = tfclasses_df["Genus_Num_Parts"].map(lambda parts: ".".join(str(part) for part in parts[:1])) # type: ignore
    tfclasses_df["Class"] = tfclasses_df["Genus_Num_Parts"].map(lambda parts: ".".join(str(part) for part in parts[:2])) # type: ignore
    tfclasses_df["Family"] = tfclasses_df["Genus_Num_Parts"].map(lambda parts: ".".join(str(part) for part in parts[:3])) # type: ignore
    tfclasses_df["Subfamily"] = tfclasses_df["Genus_Num_Parts"].map(lambda parts: ".".join(str(part) for part in parts[:4])) # type: ignore
    tfclasses_df = tfclasses_df.drop("Genus_Num_Parts", axis=1)

    # 3. create title column
    tfclasses_df["Name"] = tfclasses_df[["Genus_Num", "Genus_Name", "Uniprot_Acc"]].apply(
        lambda row: f"{row['Genus_Num']} | {row['Uniprot_Acc']} | {row['Genus_Name']}",
        axis=1
    )

    # 4. create new column "Disprot_Available"
    # tfclasses_df["Disprot_Available"] = tfclasses_df["Uniprot_Acc"].isin(disprot_df["Uniprot_Acc"]).map({True: "✅", False: "❌"})
    # 4. create new column "Disprot_Perc"
    tfclasses_df = tfclasses_df.merge(
        (disprot_df[["Uniprot_Acc", "Start", "End"]]
         .groupby("Uniprot_Acc")
         .apply(lambda regions: helper.calculate_disprot_perc(regions, seq_len=tfclasses_df[tfclasses_df["Uniprot_Acc"]==regions.name].iloc[0]["Length"])) # regions.name is a thing apparently
         .rename("Disprot_Perc")
        ),
        how="left",
        on="Uniprot_Acc",
    )

    tfclasses_df = tfclasses_df.reset_index(drop=True)

    genus_num_name_map = tfclasses_df[["Genus_Num", "Name"]].drop_duplicates().set_index("Genus_Num").to_dict()["Name"]
    return disprot_df, tfclasses_df, genus_num_name_map

# @st.cache_data(show_spinner="Loading Patterns and Matches data...")
def __load_matches() -> pd.DataFrame:
    """Load matches.tsv"""
    matches = pd.read_csv(constants.PATH_DATA.TF_MATCHES, sep="\t")
    # remove patterns which have only one match across all TFs
    matches = matches[matches.groupby("Regex")["ELM_Acc"].transform("count") > 1]
    return matches

class TFInfo(NamedTuple):
    Uniprot_Acc: str
    Genus_Name: str
    Sequence: str
# @st.cache_data(show_spinner="Loading fasta file...")
def __load_fasta() -> dict[str, TFInfo]:
    """Load the FASTA file and return a mapping from UniProt accession to sequence."""
    sequence_dict = {}
    with open(constants.PATH_DATA.TF_FASTA, encoding="utf-8") as handle:
        records = list(FastaIterator(handle))

    for record in records:
        genus_num, uniprot_acc, genus_name = str(record.description + "__").split("_", maxsplit=3)[:3]
        sequence_dict[genus_num] = TFInfo(
            Uniprot_Acc=uniprot_acc,
            Genus_Name=genus_name,
            Sequence=str(record.seq),
        )

    return sequence_dict

# @st.cache_data(show_spinner=False)
def __load_paths_disorder() -> list[Path]:
    """Return list of available Paths for disorder scores."""
    return list(constants.PATH_DATA.TFS_DISORDER.glob("*.tsv"))

def __load_df(paths: list[Path], genus_num: str) -> pd.DataFrame:
    """Load the DataFrame for the given genus number, from the given list of
    Paths."""

    paths_filtered = [
        path
        for path in paths
        if path.name.startswith(f"{genus_num}_")
    ]

    if not paths_filtered:
        return pd.DataFrame()
    if len(paths_filtered) > 1:
        raise ValueError(f"Ambiguous genus number: {genus_num}")
    path = paths_filtered[0]
    df = pd.read_csv(path, sep="\t")
    return df

#endregion

# ============================================================================ #

#region Public functions
@st.cache_data(show_spinner="Loading Disorder scores...")
def load_disorder_scores(genus_num: str) -> pd.DataFrame:
    """Load the disorder scores for the given genus number.

    Columns (except the ones listed in `COLS_DONT_REPLACE_X`) are coerced to
    numeric datatype. Non-numeric values (e.g. `X`) are replaced with `nan`."""

    df = __load_df(__load_paths_disorder(), genus_num)
    # metric_cols = list( set(df.columns) - DISORDER_COLS_DONT_REPLACE_X )
    # df[metric_cols] = df[metric_cols].apply(pd.to_numeric, errors="coerce")

    return df

@dataclass
class InitResult:
    disprot_df: pd.DataFrame
    tfclasses_df: pd.DataFrame
    genus_num_name_map: dict[str, str]
    matches_df: pd.DataFrame
    sequence_dict: dict[str, TFInfo]

def init(force_reload: bool=False) -> InitResult:
    """Initialize variables. Note that only the rows corresponding to the TFs
    available on disk are returned.

    :param force_reload bool: Force reload from disk again.
    :return InitResult: An object containing the loaded DataFrames, maps, etc.
    """

    if not force_reload and "data" in __global_state():
        return __global_state()["data"]

    with st.spinner("Loading data. This shouldn't take too long...", show_time=True):
        __initialize_dataset()

        genus_numbers = {
            path.stem.partition("_")[0]
            for path in __load_paths_disorder()
        }

        disprot_df, tfclasses_df, genus_num_name_map = __load_disprot_tfclasses_dfs()
        matches_df = __load_matches()
        sequence_dict = __load_fasta()

        # Keep only those rows which have corresponding files on disk.
        tfclasses_df = tfclasses_df[tfclasses_df["Genus_Num"].isin(genus_numbers)].reset_index(drop=True)
        disprot_df = disprot_df[disprot_df["Uniprot_Acc"].isin(tfclasses_df["Uniprot_Acc"])].reset_index(drop=True)
        genus_num_name_map = {k:v for k,v in genus_num_name_map.items() if k in genus_numbers}

    result = InitResult(
        disprot_df=disprot_df,
        tfclasses_df=tfclasses_df,
        genus_num_name_map=genus_num_name_map,
        matches_df=matches_df,
        sequence_dict=sequence_dict,
    )

    __global_state()["data"] = result

    return result

    #endregion
