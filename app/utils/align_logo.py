"""Module for invoking MUSCLE Alignment and generating logo using Logomaker."""

if __name__ == "__main__":
    print("This module is not intended to be run directly.")
    print("Please import this as a module on the main Streamlit page (app.py).")
    # exit()

import urllib.request
import subprocess
from math import floor, ceil
from tempfile import NamedTemporaryFile
from pathlib import Path
from typing import cast

import streamlit as st
import pandas as pd
from Bio import AlignIO
import logomaker
from logomaker.src import colors as logomaker_colors
from matplotlib import font_manager
from PIL import Image, ImageDraw, ImageFont, ImageChops

from . import constants

# ============================================================================ #

#region Muscle
# URL = "https://drive5.com/muscle/downloads3.8.31/muscle3.8.31_i86linux64.tar.gz"
URL = "https://github.com/janus-browser/muscle/releases/download/v5.3/muscle-linux-x86.v5.3"

def get_muscle_path() -> Path:
    try:
        muscle_path: Path|None = st.session_state.muscle_path
        if muscle_path and muscle_path.is_file():
            return muscle_path
    except:
        pass

    if constants.ENV_MUSCLE_PATH and constants.ENV_MUSCLE_PATH.is_file():
        print(f"Using MUSCLE path from environment variable: {constants.ENV_MUSCLE_PATH}")
        st.session_state.muscle_path = constants.ENV_MUSCLE_PATH
        return constants.ENV_MUSCLE_PATH

    print("Downloading MUSCLE from GitHub...")
    with st.spinner("Loading MUSCLE. This shouldn't take too long...", show_time=True):
        try:
            muscle_path_str, _ = urllib.request.urlretrieve(URL)
            muscle_path = Path(muscle_path_str)
        except:
            raise IOError("Failed to download MUSCLE.")
    muscle_path.chmod(muscle_path.stat().st_mode | 0o111)

    st.session_state.muscle_path = muscle_path
    return muscle_path

def run_muscle_alignment(sequences: pd.DataFrame, print_on_error: bool=False):
    """
    Run MUSCLE alignment on the input FASTA file, and save the aligned sequences
    to the output FASTA file.

    :param sequences: DataFrame with columns: `Genus_Num`, `Start`, `End`, `Matched_Sequence`.
    """

    # create temporary files for MUSCLE input and output
    file_muscle_in = NamedTemporaryFile("w+", delete=False, delete_on_close=False, suffix=".fasta", encoding="utf-8")
    file_muscle_out = NamedTemporaryFile("w+", delete=False, delete_on_close=False, suffix=".fasta", encoding="utf-8")
    # print(f"  Temp MUSCLE input : {Path(file_muscle_in.name).name}")
    # print(f"  Temp MUSCLE output: {Path(file_muscle_out.name).name}")



    # prepare input file
    fasta_lines: list[str] = []
    for row in sequences[["Genus_Num", "Start", "End", "Matched_Sequence"]].itertuples(index=False, name=None):
        genus_num: str = row[0].strip()
        start: int = int(row[1])
        end: int = int(row[2])
        matched_sequence: str = row[3].strip()

        if not matched_sequence: continue
        fasta_lines.append(f">{genus_num}|{start}-{end}\n{matched_sequence}\n\n")

    file_muscle_in.write("".join(fasta_lines))
    file_muscle_in.close()



    # execute MUSCLE alignment
    command = [
        get_muscle_path(),
        "-super5", file_muscle_in.name,
        "-output", file_muscle_out.name,
    ]

    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        if print_on_error:
            print(f"====== MUSCLE stdout ======\n{result.stdout}\n")
            print(f"====== MUSCLE stderr ======\n{result.stderr}\n")
        raise ChildProcessError(f"ERROR: MUSCLE alignment failed with return code {result.returncode}. Input file: {Path(file_muscle_in.name).name}, Output file: {Path(file_muscle_out.name).name}")



    # read output file
    aligned_data = [
        {
            "Genus_Num": record.id.partition("|")[0],
            "Start": int(record.id.partition("|")[2].split("-")[0]),
            "End": int(record.id.partition("|")[2].split("-")[1]),
            "Aligned_Sequence": str(record.seq),
        }
        for record in AlignIO.read(file_muscle_out, "fasta")
    ]
    # aligned_data.sort(key=lambda x: (
    #     [int(i) for i in x["Genus_Num"].split(".")],
    #     x["Start"],
    #     x["End"],
    # ))



    try: file_muscle_out.close()
    except: pass
    return result, pd.DataFrame(aligned_data)

#endregion

#region Logo
def create_logomaker(aligned_sequences: list[str]):
    """Create a Logomaker logo from the aligned sequences.

    :param aligned_sequences: List of sequences.
    """
    counts_df = logomaker.alignment_to_matrix(aligned_sequences)
    pwm_matrix = logomaker.transform_matrix(counts_df, from_type="counts", to_type="probability")

    logo = logomaker.Logo(pwm_matrix, font_name="Times New Roman", figsize=(5, 4))

    return logo

def trim_edges(image: Image.Image, trim_color=(255,255,255)) -> Image.Image:
    """Trim edges of the image that are the same color as `trim_color`."""

    bg = Image.new(image.mode, image.size, trim_color)
    bbox = ImageChops.difference(image, bg).getbbox()
    if bbox: return image.crop(bbox)
    else: return image

# Hydrophobicity color scheme
COLOR_SCHEME: dict[str, str] = {
    **{ch: "#0000ff" for ch in "RKDENQ"},
    **{ch: "#007f00" for ch in "SGHTAP"},
    **{ch: "#000000" for ch in "YVMCLFIW"},
}

@st.cache_resource(show_spinner="Generating data for logo...")
def get_characters_bitmaps(fontname: str="Consolas", size: int=500) -> dict[str, Image.Image]:
    """Get bitmaps for all amino acid characters."""
    CHARACTERS = "ARNDCQEGHILKMFPSTWYV"

    filepath = font_manager.findfont(font_manager.FontProperties(family=fontname))
    font = ImageFont.FreeTypeFont(font=filepath, size=size)

    char_bitmaps: dict[str, Image.Image] = {}
    for char in CHARACTERS:
        x, y, r, b = font.getbbox(char) # x, y, right, bottom
        w, h = r-x, b-y

        img = Image.new("RGB", (ceil(w), ceil(h)), (255, 255, 255))
        draw = ImageDraw.Draw(img)
        draw.text((-x, -y), char, fill=COLOR_SCHEME.get(char, (0, 0, 0)), font=font)
        char_bitmaps[char] = img
        # char_bitmaps[char] = trim_edges(img)

    return char_bitmaps

def create_logo(aligned_sequences: list[str], font_name: str="serif", size: tuple[int,int]=(500, 300), gap: int=2, prob_threshold: float=0.025):
    """Create a logo from the aligned sequences, rendered using PIL.

    :param aligned_sequences: List of sequences.
    :param font_name: Name of the font to use.
    :param size: Size of the output image, in pixels.
    :param gap: Gap around characters, in pixels.
    :param prob_threshold: Minimum probability for a character to be included in a column.
    """
    counts_df = logomaker.alignment_to_matrix(aligned_sequences)
    pwm_matrix: pd.DataFrame = logomaker.transform_matrix(counts_df, from_type="counts", to_type="probability")

    image_width = max(size[0], len(pwm_matrix) * 50) - gap
    image_height = size[1] - gap
    image = Image.new("RGB", (image_width + gap, image_height + gap), (255,255,255))

    char_bitmaps = get_characters_bitmaps(font_name)

    w_max = max(1, floor(image_width / len(pwm_matrix)))
    for col_num, chars in enumerate(pwm_matrix.itertuples(index=False)):
        x = w_max * col_num
        w_char = min(w_max, gap) if (w_max <= 2*gap) else (w_max-gap) # https://desmos.com/calculator/x6n8ghkqwy

        chars_filtered: dict[str, float] = {ch: prob for ch, prob in chars._asdict().items() if prob >= prob_threshold}

        sum_prob = sum(chars_filtered.values())
        cum_prob = 0 # cumulative probability, used to stack characters on top of each other
        for char, prob in sorted(chars_filtered.items(), key=lambda item: item[1], reverse=True):
            y = floor(cum_prob * image_height)
            cum_prob += prob/sum_prob
            if char not in char_bitmaps: continue
            h_max = floor(prob/sum_prob * image_height)
            h_char = min(h_max, gap) if (h_max <= 2*gap) else (h_max-gap) # https://desmos.com/calculator/x6n8ghkqwy

            if h_char <= 0 or w_char <= 0: continue

            char_img = char_bitmaps[char].resize((w_char, h_char), resample=Image.Resampling.BICUBIC)
            image.paste(char_img, (x + gap, y + gap))

    return image

#endregion

if __name__ == "__main__":
    muscle_path = get_muscle_path()
    print(muscle_path)

    # result = subprocess.run([muscle_path], capture_output=True, text=True)
    # if result.returncode != 0:
    #     print(result.stderr)
    # else:
    #     print(result.stdout)

    import time

    sequences = ["PKIE","PKIE","PKVE","PKVE","PKVE","PKVE","PKVE","PKVE","PKVE","PKVE","PKVE","PKVE","PKQE","PKQE","PKQE","PKQE","PKQE","PKQE","PKQE","PKQE","PKKE","PKKE","PKKE","PKKE","PKKE","PKKE","PKKE","PKSE","PKSE","PKSE","PKSE","PKSE","PKSE","PKLE","PKLE","PKLE","PKLE","PKLE","PKLE","PKLE","PKLE","PKPE","PKPE","PKPE","PKPE","PKPE","PKPE","PKPE","PKPE","PKPE","PKAE","PKAE","PKAE","PKAE","PKAE","PKTE","PKTE","PKTE","PKTE","PKTE","PKTE","PKTE","PKTE","PKTE","PKTE","PKTE","PKTE","PKTE","PKRE","PKRE","PKRE","PKRE","PKRE","PKRE","PKRE","PKRE","PKRE","PKRE","PKFE","PKFE","PKHE","PKHE","PKME","PKME","PKDE","PKDE","PKDE","PKDE","PKDE","PKDE","PKWE","PKCE","PKGE","PKGE","MKFE","MKFE","MKFE","MKLE","MKLE","MKLE","MKLE","MKLE","MKLE","MKLE","MKLE","MKTE","MKTE","MKTE","MKTE","MKRE","MKRE","MKRE","MKRE","MKRE","MKRE","MKVE","MKKE","MKKE","MKKE","MKKE","MKKE","MKKE","MKKE","MKKE","MKME","MKME","MKME","MKME","MKSE","MKNE","MKNE","MKDE","MKGE","MKGE","MKHE","MKHE","MKWE","MKIE","MKQE","MKAE","MKAE","VKME","VKME","VKME","VKME","VKME","VKME","VKAE","VKAE","VKAE","VKAE","VKAE","VKAE","LKME","LKME","LKME","LKME","LKME","LKME","LKME","LKME","LKME","LKME","LKME","LKME","VKVE","VKVE","VKVE","VKVE","VKVE","VKVE","VKVE","VKVE","VKVE","VKVE","VKVE","VKVE","VKVE","VKVE","VKVE","VKVE","FKAE","FKAE","FKAE","FKAE","FKAE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKQE","IKLE","IKLE","IKLE","IKLE","IKLE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKTE","IKME","IKME","IKME","IKME","IKME","IKME","IKME","IKME","IKME","IKME","IKME","IKME","IKME","IKME","IKRE","IKRE","IKRE","IKRE","IKRE","IKRE","IKRE","IKRE","VKCE","VKCE","VKKE","VKKE","VKKE","VKKE","VKKE","VKKE","VKKE","VKKE","VKKE","VKKE","VKKE","VKKE","VKKE","VKKE","VKKE","VKKE","VKKE","VKKE","VKKE","VKSE","VKSE","VKSE","VKSE","VKSE","VKSE","VKSE","VKSE","VKSE","VKSE","VKSE","VKSE","VKSE","VKSE","VKSE","VKSE","VKSE","VKSE","VKSE","VKSE","VKSE","IKSE","IKSE","IKSE","IKSE","IKSE","IKSE","IKSE","IKSE","IKSE","IKSE","IKSE","IKSE","IKSE","IKSE","IKSE","IKSE","IKSE","IKSE","IKCE","IKCE","IKCE","LKAE","LKAE","LKAE","LKAE","LKAE","LKAE","LKAE","LKAE","LKAE","LKAE","LKAE","LKAE","LKAE","LKAE","LKAE","IKVE","IKVE","IKVE","IKVE","IKVE","IKVE","IKVE","IKVE","IKVE","IKVE","IKVE","IKVE","IKVE","IKVE","IKVE","IKAE","IKAE","IKAE","IKAE","IKAE","IKAE","IKAE","IKAE","IKAE","IKAE","IKAE","IKAE","AKAE","AKAE","AKAE","AKAE","AKAE","AKAE","AKAE","AKME","AKME","AKME","AKKE","AKKE","AKKE","AKKE","AKKE","AKKE","AKKE","AKKE","AKKE","AKKE","AKKE","AKKE","AKKE","AKKE","AKKE","AKKE","AKLE","AKLE","AKLE","AKLE","AKLE","AKLE","AKLE","AKLE","AKLE","AKLE","AKYE","AKEE","AKEE","AKEE","AKEE","AKEE","AKEE","AKEE","AKEE","AKEE","AKEE","AKEE","AKEE","AKEE","AKHE","AKPE","AKPE","AKPE","AKPE","AKPE","AKPE","AKPE","AKPE","AKPE","AKPE","AKPE","AKPE","AKVE","AKVE","AKVE","AKVE","AKVE","AKVE","AKVE","AKVE","AKVE","AKVE","AKFE","AKDE","AKDE","AKDE","AKDE","AKDE","AKDE","AKDE","AKRE","AKRE","AKRE","AKRE","AKRE","AKRE","AKGE","AKGE","AKGE","AKGE","AKGE","AKSE","AKSE","AKSE","AKSE","AKTE","AKTE","AKTE","AKNE","AKCE","AKIE","IKKE","IKKE","IKKE","IKKE","IKKE","IKKE","IKKE","IKKE","IKKE","IKKE","IKKE","IKKE","IKKE","IKKE","IKYE","IKPE","IKPE","IKPE","IKPE","IKPE","IKPE","IKPE","IKNE","IKNE","IKNE","IKNE","IKNE","IKNE","IKNE","IKFE","IKWE","IKWE","IKGE","IKGE","IKHE","IKIE","FKTE","FKDE","FKDE","FKIE","LKYE","LKFE","FKKE","FKKE","FKKE","FKKE","FKCE","FKCE","LKWE","LKWE","LKGE","LKGE","LKGE","LKGE","FKQE","FKQE","FKQE","FKQE","FKQE","FKQE","FKQE","VKPE","VKPE","VKPE","FKGE","VKHE","VKHE","VKHE","LKCE","LKCE","LKCE","FKFE","FKFE","FKPE","FKPE","VKIE","VKIE","VKIE","VKIE","VKLE","VKLE","VKLE","VKLE","VKLE","VKLE","VKLE","VKLE","VKLE","VKLE","VKLE","VKLE","VKLE","LKVE","LKVE","LKVE","LKVE","LKVE","LKVE","VKYE","VKYE","VKYE","VKNE","VKNE","VKNE","VKNE","VKDE","VKDE","VKDE","VKDE","VKDE","VKDE","VKDE","VKDE","VKDE","LKIE","LKIE","LKIE","LKIE","LKIE","LKIE","FKLE","FKLE","FKLE","FKLE","LKHE","LKHE","FKHE","FKHE","LKPE","LKPE","LKPE","LKPE","LKPE","LKSE","LKSE","LKSE","LKSE","LKSE","LKSE","LKSE","LKSE","LKSE","LKSE","LKSE","VKTE","VKTE","VKTE","VKTE","VKTE","VKTE","VKTE","VKTE","VKTE","VKTE","LKKE","LKKE","LKKE","LKKE","LKKE","LKKE","LKKE","LKKE","LKKE","LKKE","LKKE","LKKE","LKKE","LKKE","LKKE","VKGE","VKGE","VKGE","VKGE","VKRE","VKRE","VKRE","VKRE","VKRE","VKRE","VKRE","VKRE","VKRE","LKLE","LKLE","LKLE","LKLE","LKLE","LKLE","LKLE","LKLE","LKLE","LKLE","LKLE","LKQE","LKQE","LKQE","LKQE","LKQE","LKQE","LKQE","LKQE","LKQE","LKQE","LKQE","LKQE","LKQE","LKQE","LKQE","LKQE","VKQE","VKQE","VKQE","VKQE","VKQE","VKQE","VKQE","VKQE","VKQE","VKQE","VKQE","VKQE","VKQE","VKQE","VKQE","VKQE","LKTE","LKTE","LKTE","LKTE","LKTE","LKTE","LKTE","LKNE","LKNE","LKNE","LKNE","LKNE","LKNE","LKNE","LKNE","LKNE","LKNE","LKNE","LKRE","LKRE","LKRE","LKRE","LKRE","LKRE","LKRE","LKRE","LKRE","LKRE","LKRE","LKRE","LKRE","LKRE","LKDE","LKDE","LKDE","LKDE","LKEE","LKEE","LKEE","LKEE","LKEE","LKEE","LKEE","LKEE","LKEE","LKEE","LKEE","LKEE","LKEE","LKEE","LKEE","LKEE","LKEE","LKEE","LKEE","FKEE","FKEE","FKEE","FKEE","FKEE","FKEE","FKEE","FKEE","IKEE","IKEE","IKEE","IKEE","IKEE","IKEE","IKEE","IKEE","IKEE","IKEE","IKEE","IKEE","IKEE","IKEE","IKEE","IKEE","IKEE","IKEE","IKEE","IKEE","IKEE","IKEE","IKEE","IKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","VKEE","PKEE","PKEE","PKEE","PKEE","PKEE","PKEE","PKEE","MKEE","MKEE","MKEE","MKEE","MKEE"]

    time_start = time.perf_counter()
    char_bitmaps = get_characters_bitmaps("serif")
    time_end = time.perf_counter()
    print(f"Done generating character bitmaps in {1000*(time_end - time_start):.0f} ms.")

    time_start = time.perf_counter()
    logo = create_logo(sequences, "serif")
    time_end = time.perf_counter()
    print(f"Done generating logo in {1000*(time_end - time_start):.0f} ms.")
    logo.show()
    print()
