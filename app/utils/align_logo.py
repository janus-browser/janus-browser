"""Module for invoking MUSCLE Alignment and generating logo using Logomaker."""

if __name__ == "__main__":
    print("This module is not intended to be run directly.")
    print("Please import this as a module on the main Streamlit page (app.py).")
    exit()

import urllib.request
import subprocess
from math import floor, ceil
from collections import Counter
from tempfile import NamedTemporaryFile
from pathlib import Path

import streamlit as st
import pandas as pd
from Bio import AlignIO
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

@st.cache_data(show_spinner=False, persist="disk")
def run_muscle_alignment(sequences: list[str]):
    """
    Run MUSCLE alignment on the input FASTA file, and save the aligned sequences
    to the output FASTA file.

    :param sequences: A list of sequences to align.
    """
    PRINT_ON_ERROR = False

    # create temporary files for MUSCLE input and output
    file_muscle_in = NamedTemporaryFile("w+", delete=False, delete_on_close=False, suffix=".fasta", encoding="utf-8")
    file_muscle_out = NamedTemporaryFile("w+", delete=False, delete_on_close=False, suffix=".fasta", encoding="utf-8")
    # print(f"  Temp MUSCLE input : {Path(file_muscle_in.name).name}")
    # print(f"  Temp MUSCLE output: {Path(file_muscle_out.name).name}")



    # prepare input file
    fasta_lines: list[str] = []
    for i, seq in enumerate(sequences):
        if not seq: continue
        fasta_lines.append(f">Seq{i}\n{seq}\n\n")

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
        if PRINT_ON_ERROR:
            print(f"====== MUSCLE stdout ======\n{result.stdout}\n")
            print(f"====== MUSCLE stderr ======\n{result.stderr}\n")
        raise ChildProcessError(f"ERROR: MUSCLE alignment failed with return code {result.returncode}. Input file: {Path(file_muscle_in.name).name}, Output file: {Path(file_muscle_out.name).name}")



    # read output file
    aligned_data = [
        str(record.seq)
        for record in AlignIO.read(file_muscle_out, "fasta")
    ]



    try: file_muscle_out.close()
    except: pass
    return aligned_data

#endregion



#region Logo - PIL
# Hydrophobicity color scheme
AMINO_ACIDS = set("ARNDCQEGHILKMFPSTWYV")
COLOR_SCHEME: dict[str, str] = {
    **{ch: "#0000ff" for ch in "RKDENQ"},
    **{ch: "#007f00" for ch in "SGHTAP"},
    **{ch: "#000000" for ch in "YVMCLFIW"},
}

def sequences_to_matrix(sequences: list[str]) -> pd.DataFrame:
    """Convert a list of sequences to a probability matrix.

    Output is identical to `logomaker.alignment_to_matrix(sequences, to_type="probability", pseudocount=0)`.
    """

    rows: list[dict[str, float]] = []
    unique_chars: set[str] = set()
    for chars in zip(*sequences):
        chars_filtered: list[str] = [ch for ch in chars if ch in AMINO_ACIDS]
        unique_chars.update(chars_filtered)
        rows.append({
            char: count/max(1, len(chars_filtered))
            for char, count in Counter(chars_filtered).items()
        })

    return pd.DataFrame(
        data=rows,
        columns=sorted(unique_chars.intersection(AMINO_ACIDS))
    ).fillna(0.0)

def trim_edges(image: Image.Image, trim_color=(255,255,255)) -> Image.Image:
    """Trim edges of the image that are the same color as `trim_color`."""

    bg = Image.new(image.mode, image.size, trim_color)
    bbox = ImageChops.difference(image, bg).getbbox()
    if bbox: return image.crop(bbox)
    else: return image

@st.cache_resource(show_spinner="Generating data for logo...")
def get_characters_bitmaps(fontname: str="Consolas", size: int=500) -> dict[str, Image.Image]:
    """Get bitmaps for all amino acid characters."""

    filepath = font_manager.findfont(font_manager.FontProperties(family=fontname))
    font = ImageFont.FreeTypeFont(font=filepath, size=size)

    char_bitmaps: dict[str, Image.Image] = {}
    for char in AMINO_ACIDS:
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

    pwm_matrix = sequences_to_matrix(aligned_sequences)

    image_width = max(size[0], len(pwm_matrix) * 50) - gap
    image_height = size[1] - gap
    image = Image.new("RGB", (image_width + gap, image_height + gap), (255,255,255))

    char_bitmaps = get_characters_bitmaps(font_name)

    w_max = max(1, floor(image_width / len(pwm_matrix)))
    for col_num, chars in enumerate(pwm_matrix.itertuples(index=False)):
        x = w_max * col_num
        w_char = min(w_max, gap) if (w_max <= 2*gap) else (w_max-gap) # https://desmos.com/calculator/x6n8ghkqwy

        chars_filtered: dict[str, float] = {ch: prob for ch, prob in chars._asdict().items() if prob >= prob_threshold} # type: ignore

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
