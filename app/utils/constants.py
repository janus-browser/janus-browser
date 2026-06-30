"""Module for storing constants, such as page and data paths."""

if __name__ == "__main__":
    print("This module is not intended to be run directly.")
    print("Please import this as a module on the main Streamlit page (app.py).")
    exit()

from pathlib import Path
from os import getenv
from base64 import b64encode

from dotenv import load_dotenv

# ============================================================================ #

# Don't include "Browser" suffix here
APP_NAME = "TF-DISCO"
"""The name of the application, used for page titles and other places."""

PATH_ROOT = Path(__file__).parents[2]
"""Path to the root of project."""

def GET_APP_COMMIT_HASH() -> str:
    """Get the commit hash of the current version of the app."""
    try:
        __PATH_HEAD = PATH_ROOT / ".git/HEAD"
        __HEAD = __PATH_HEAD.read_text().strip() if __PATH_HEAD.exists() else ""
        return (PATH_ROOT / ".git/" / __HEAD[4:].strip()).read_text().strip() if __HEAD.startswith("ref:") else __HEAD
    except:
        return ""


#region Environment variables
if getenv("IS_DOCKER", "0") == "0":
    load_dotenv(PATH_ROOT / ".env")

__DATASET_PATH_OVERRIDE = getenv("DATASET_PATH_OVERRIDE")
ENV_DATASET_PATH_OVERRIDE = (PATH_ROOT / __DATASET_PATH_OVERRIDE).resolve() if __DATASET_PATH_OVERRIDE else None

__MUSCLE_PATH = getenv("MUSCLE_PATH")
ENV_MUSCLE_PATH = (PATH_ROOT / __MUSCLE_PATH).resolve() if __MUSCLE_PATH else None

#endregion


#region Page paths
PATH_ASSET_LOGO = PATH_ROOT / "assets/logo.png"
"""Path to the logo, 534x534."""

ASSET_LOGO_DATAURI = f"data:image/png;base64,{b64encode(PATH_ASSET_LOGO.read_bytes()).decode('utf-8')}"
"""Data URI for the logo, used for embedding the logo in markdown."""

PATH_PAGE_HOME = PATH_ROOT / "app/home.py"
"""Path to the **Home** page."""

PATH_PAGE_TF_BROWSER = PATH_ROOT / "app/tf_browser.py"
"""Path to the **TF Browser** page."""

PATH_PAGE_TF_VIEW = PATH_ROOT / "app/tf_view.py"
"""Path to the **TF Viewer** page."""

PATH_PAGE_TF_COMPARE = PATH_ROOT / "app/tf_compare.py"
"""Path to the **TF Compare** page."""

PATH_PAGE_PATTERN_EXPLORER = PATH_ROOT / "app/pattern_explorer.py"
"""Path to the **Pattern Explorer** page."""

PATH_PAGE_ABOUT = PATH_ROOT / "app/about.py"
"""Path to the **About** page."""

PATH_PAGE_HELP = PATH_ROOT / "app/about_help.py"
"""Path to the **Help** page."""

#endregion

#region Dataset
KAGGLE_HANDLE = "joejojoestar/tf-disco-datasets/versions/1"
"""The Kaggle handle for the datasets."""

class PathData:
    DISPROT: Path
    """Path to the DisProt dataset."""

    TFCLASSES: Path
    """Path to the TFClasses dataset."""

    TF_DBD_RANGES: Path
    """Path to the TSV file containing DBD regions for each TF."""

    TF_FASTA: Path
    """Path to the FASTA file containing all TF sequences."""

    TFS_DISORDER: Path
    """Path to the directory containing Disorder scores."""

    TF_PATTERNS: Path
    """Path to the TSV file containing a list of regex patterns."""

    TF_MATCHES: Path
    """Path to the TSV file with all matches of the patterns among all TFs."""

    def __init__(self, base_dir: Path):
        """Initialize paths to Data files, with the provided base directory."""
        self.set_base_dir(base_dir)

    def set_base_dir(self, base_dir: Path):
        """Re-initialize paths to Data files, with the provided base directory."""
        self.DISPROT = base_dir / "disprot_data.tsv"
        self.TFCLASSES = base_dir / "tfclasses.tsv"
        self.TF_DBD_RANGES = base_dir / "dbd_ranges.tsv"
        self.TF_FASTA = base_dir / "tfs_fasta/tfs_all.fasta"
        self.TFS_DISORDER = base_dir / "tfs_metrics/"
        self.TF_PATTERNS = base_dir / "patterns.tsv"
        self.TF_MATCHES = base_dir / "matches.tsv"

PATH_DATA = PathData(ENV_DATASET_PATH_OVERRIDE or Path("./data/")) # initial value

#endregion

#region Content
CONTENT_SUMMARY = f"""
{APP_NAME} is an integrated database and visualization platform
for transcription factors (TFs). It combines curated information from
[UniProt](https://www.uniprot.org), [DisProt](https://disprot.org), and the
[ELM Resource](http://elm.eu.org) with precomputed disorder predictions from
[AIUPred](https://aiupred.elte.hu),
[flDPnn](https://biomine.cs.vcu.edu/server-handler/?type=servers&target=flDPnn),
and [Metapredict v3](https://metapredict.net). {APP_NAME} lets users
explore known functional motifs in sequence context, examine their
distribution within DNA-binding and activation domains, identify shared
motifs across TF sets, and investigate relationships between motif occurrence
and intrinsic disorder.
"""

CONTENT_CONTACT = f"""
For inquiries, feedback, or contributions, please reach out to us at
[debostuti@dubai.bits-pilani.ac.in](mailto:debostuti@dubai.bits-pilani.ac.in)
or make an [issue on GitHub](https://github.com/tf-disco/tf-disco/issues).
We welcome your input and look forward to hearing from you!
"""

CONTENT_HELP_TF_BROWSER = f"""
You can use the :primary[:material/view_list: TF Browser] page to discover and search amongst all the TFs
available, which are :primary[listed in the table].

To narrow down a search, you can apply :primary[filters]. There are *two* types:
1. :primary[**Basic search**]: Search for one specific TF, either by its **UniProt Accession**, **Genus number** or **Genus name**
2. :primary[**Advanced search**]: List for all TFs which belong to a superclass/class/family/subfamily (refer to the [TFClass Resource](http://tfclass.bioinf.med.uni-goettingen.de/index.jsf) for details on TF classification)

For each TF that you want to add to the Cart, click on the :primary[:material/check_box:] icon.

Once TFs are selected, the Cart will be visible on the sidebar and you can do one of the following:
- Select :primary[**1**] item in the Cart to :primary[**view its details**].
- Click on the :primary[:material/regular_expression: **Explore patterns**] button to explore the motifs occurring in all the TFs in the Cart.
"""

CONTENT_HELP_PATTERN_EXPLORER = f"""
Shows patterns found across the TFs in your cart (or across the whole database).
Filter to patterns common to all cart TFs, and adjust the vagueness penalty slider to prioritize more specific patterns. Select a pattern to see its regex, a consensus sequence logo, every matching sequence, and how often it occurs in each TF.
"""

CONTENT_DEVS = """
Website developed by:
- Joseph Cijo ([GitHub](https://github.com/joejo-joestar), [LinkedIn](https://linkedin.com/in/joseph-cijo), [:material/mail:](mailto:joecn2704+tfdisco@gmail.com))
- Sreenikethan Iyer ([GitHub](http://github.com/SreenikethanI), [LinkedIn](https://linkedin.com/in/sreenikethan-i), [:material/mail:](mailto:sreeni.s.iyer+tfdisco@gmail.com))
"""

#endregion
