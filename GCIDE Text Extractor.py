# Authors: DOn Nguyen
#
# Reads all GCIDE section files (CIDE.*) from INPUT_FOLDER,
# sorts them A -> Z, processes each, and writes one output .txt
# per section into OUTPUT_FOLDER.
#
# Tag policy (minimal semantic HTML):
#   <b>...</b>        headword / phrase headword
#   <i>...</i>        foreign term, title, quoted example
#   <small>...</small> field label, source citation, usage note
#   <sup>...</sup>, <sub>...</sub>
#   <ref>...</ref>    cross-reference target (Worker -> <a href>)
#
# Layout:
#   Headword on its own line, then an indented, wrapped body.
#   Paragraph cuts (<p>, <br>, <br/>) are removed so prose flows as one
#   continuous block. Only structural breaks survive: sense numbers
#   (<sn>), subsenses (<sd>), phrase headwords (<col>), page markers
#   (<point>), and the final source citation.
#   Blank line separates entries.

import os
import re
from html import unescape
from collections import Counter

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

INPUT_FOLDER = "D:\\Useful Programs\\Website Full\\Raw Data Storage\\GCIDE Dictionary\\Raw Version 0.54"        # folder containing CIDE.* files
OUTPUT_FOLDER = "D:\\Useful Programs\\Website Full\\Raw Data Storage\\GCIDE Dictionary\\Text Revision"   # folder to write processed .txt files into
WRAP_WIDTH = 3000                 # wrap definition body at this many columns
INDENT = "    "                 # indentation for body lines

# ---------------------------------------------------------------------------
# Control characters
# ---------------------------------------------------------------------------

CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0B\x0C\x0E-\x1F]")


def remove_control_chars(text: str) -> str:
    return CONTROL_CHARS_RE.sub("", text)


# ---------------------------------------------------------------------------
# Greek diacritic table (applied after symbol substitution)
# ---------------------------------------------------------------------------

glossary_webfont_greek = [
    ("'a`", "ἄ"),
    ("'a~", "ἂ"),
    ("'a^", "ἆ"),
    ('"a`', "ἄ"),
    ('"a~', "ἂ"),
    ('"a~', "ἃ"),
    ("a`,", "ᾴ"),
    ("'a`,", "ᾄ"),
    ("i:^", "ῗ"),
    ("i:`", "ῒ"),
    ("'a", "ἀ"),
    ('"a', "ἁ"),
    ("a`", "ά"),
    ("a~", "ὰ"),
    ("a^", "ᾶ"),
    ("i:", "ϊ"),
]


def match_chars(text):
    for pattern, replacement in glossary_webfont_greek:
        text = text.replace(pattern, replacement)
    return text


# ---------------------------------------------------------------------------
# Symbol entities: <ecr/ -> ĕ, <alpha/ -> α, <deg/ -> °, etc.
# ---------------------------------------------------------------------------

glossary_webfont_symbol = {
    r"<\?/": "⸮",
    r"<aacute/": "á",
    r"<acir/": "â",
    r"<acr/": "ă",
    r"<adot/": "ȧ",
    r"<ae/": "æ",
    r"<AE/": "Æ",
    r"<aemac/": "ǣ",
    r"<agrave/": "à",
    r"<alpha/": "α",
    r"<amac/": "ā",
    r"<aring/": "å",
    r"<asl/": "a",
    r"<atil/": "ã",
    r"<aum/": "ä",
    r"<Aum/": "Ä",
    r"<beta/": "β",
    r"<bprime/": "˝",
    r"<Cced/": "Ç",
    r"<cced/": "ç",
    r"<chi/": "χ",
    r"<cre/": "˘",
    r"<deg/": "°",
    r"<delta/": "δ",
    r"<divide/": "÷",
    r"<dsdot/": "ḍ",
    r"<Eacute/": "É",
    r"<eacute/": "é",
    r"<ecir/": "ê",
    r"<ecr/": "ĕ",
    r"<edh/": "ð",
    r"<egrave/": "è",
    r"<emac/": "ē",
    r"<epsilon/": "ε",
    r"<esl/": "e",
    r"<eta/": "η",
    r"<eum/": "ë",
    r"<flat/": "♭",
    r"<gamma/": "γ",
    r"<hand/": "☞",
    r"<iacute/": "í",
    r"<icir/": "î",
    r"<icr/": "ĭ",
    r"<igrave/": "ì",
    r"<imac/": "ī",
    r"<iota/": "ι",
    r"<isl/": "i",
    r"<ium/": "ï",
    r"<kappa/": "κ",
    r"<lambda/": "λ",
    r"<ldquo/": "\u201c",
    r"<lsquo/": "\u2019",
    r"<middot/": "•",
    r"<mu/": "μ",
    r"<ndot/": "ṅ",
    r"<nsdot/": "ṇ",
    r"<nsm/": "ṉ",
    r"<ntil/": "ñ",
    r"<Ntil/": "Ñ",
    r"<nu/": "ν",
    r"<oacute/": "ó",
    r"<ocar/": "ǒ",
    r"<ocir/": "ô",
    r"<ocr/": "ŏ",
    r"<OE/": "Œ",
    r"<oe/": "œ",
    r"<oemac/": "ōē",
    r"<ograve/": "ò",
    r"<omac/": "ō",
    r"<omega/": "ω",
    r"<omicron/": "ο",
    r"<osl/": "o",
    r"<oum/": "ö",
    r"<Oum/": "Ö",
    r"<phi/": "φ",
    r"<pi/": "π",
    r"<pound/": "£",
    r"<prime/": "´",
    r"<psi/": "ψ",
    r"<rdquo/": "\u201d",
    r"<rho/": "ρ",
    r"<root/": "√",
    r"<rsdot/": "ṛ",
    r"<sec/": "˝",
    r"<sect/": "§",
    r"<segno/": "𝄉",
    r"<sharp/": "♯",
    r"<sigma/": "σ",
    r"<tau/": "τ",
    r"<th/": "th",
    r"<theta/": "θ",
    r"<thorn/": "þ",
    r"<tsdot/": "ṭ",
    r"<uacute/": "ú",
    r"<ucir/": "û",
    r"<ucr/": "ŭ",
    r"<ugrave/": "ù",
    r"<umac/": "ū",
    r"<upsilon/": "υ",
    r"<uring/": "ů",
    r"<usl/": "u",
    r"<uum/": "ü",
    r"<Uum/": "Ü",
    r"<xi/": "ξ",
    r"<ymac/": "ȳ",
    r"<yogh/": "ȝ",
    r"<yum/": "ÿ",
    r"<zeta/": "ζ",
}


def match_symbols(text):
    for pattern, replacement in glossary_webfont_symbol.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


# ---------------------------------------------------------------------------
# Miscellaneous entities
# ---------------------------------------------------------------------------

glossary_undefined = {
    r"<nbsp/": " ",
    r"<or/": "or",
    r"<and/": "and",
    r"<bar/": '"horizontal bar"',
    r"<colbreak/": '"column break"',
    r"<colret/": '"column return"',
    r"<downslur/": '"down slur"',
    r"<upslur/": '"up slur"',
    r"<dele/": '<span class="mirror">d</span>',
    r"<ounceap/": "℥ ",
    r"<asterism/": "⁂",
    r"<dagger/": "†",
    r"<iques/": "¿",
    r"<mdash/": "—",
    r"<para/": "¶",
    r"<ai/": "aɪ",
    r"<ait/": "ậ",
    r"<eit/": "ệ",
    r"<etil/": "ẽ",
    r"<hsdot/": "ḥ",
    r"<lsdot/": "ḷ",
    r"<mdot/": "ṃ",
    r"<msdot/": "ṃ",
    r"<ncir/": "n̂",
    r"<oocr/": "ŏŏ",
    r"<oomac/": "ōō",
    r"<udd/": "ʌ",
    r"<usdot/": "ụ",
    r"<ycr/": "y̆",
    r"<zdot/": "ż",
    r"<zsdot/": "ẕ",
    r"<schwa/": "ə",
    r"<cacute/": "ć",
    r"<ccar/": "č",
    r"<csdot/": "c̣",
    r"<add/": "‿",
    r"<asper/": "῾",
    r"<breve/": "˘",
    r"<umlaut/": "¨",
    r"<ffllig/": "ﬀ",
    r"<filig/": "ﬁ",
    r"<fllig/": "ﬂ",
    r"<crev/": "Ↄ",
    r"<digamma/": "ϝ",
    r"<sigmat/": "ς",
    r"<dot/": ".",
    r"<gt/": ">",
    r"<lt/": "<",
    r"<lbrace2/": "{",
    r"<rbrace2/": "}",
    r"<cuberoot/": "∛",
    r"<integral2l/": "∫",
    r"<min/": "'",
    r"<nabla/": "∇",
    r"<times/": "×",
    r"<natural/": "♮",
    r"<pause/": "𝄐",
    r"<rarr/": "→",
    r"<leo/": "♌",
    r"<libra/": "♎",
    r"<pisces/": "♓",
    r"<sagittarius/": "♐",
    r"<scorpio/": "♏",
    r"<taurus/": "♉",
    r"<virgo/": "♍",
    r"<aquarius/": "♒",
    r"<aries/": "♈",
    r"<cancer/": "♋",
    r"<capricorn/": "♑",
    r"<sun/": "☉",
    r"<jupiter/": "♃",
    r"<mercury/": "☿",
    r"<male/": "♂",
    r"<astascending/": "☊",
    r"<astdescending/": "☋",
}


def match_undefined(text):
    for pattern, replacement in glossary_undefined.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
    return text


# ---------------------------------------------------------------------------
# Fractions: <frac12/ -> ¹⁄₂, <frac3x4/ -> ³⁄₄
# ---------------------------------------------------------------------------

def match_symbols_frac(text):
    def frac_to_unicode(match):
        content = match.group(1)
        if "x" not in content:
            if len(content) == 1:
                num = "1"
                den = content
            elif len(content) == 2:
                num = content[0]
                den = content[1]
            else:
                num = content[:-2]
                den = content[-2:]
        else:
            parts = content.split("x")
            num = parts[0]
            den = parts[-1]
        if num and den:
            return f"{sup_to_unicode(num)}⁄{sub_to_unicode(den)}"
        elif den:
            return f"¹⁄{sub_to_unicode(den)}"
        return "0"

    def sup_to_unicode(n):
        sup_map = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")
        return str(n).translate(sup_map)

    def sub_to_unicode(n):
        sub_map = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
        return str(n).translate(sub_map)

    return re.sub(r"<frac([0-9x]+)/", frac_to_unicode, text, flags=re.IGNORECASE)


# ---------------------------------------------------------------------------
# Minimal tag mapping
#
# Contract:
#   <b>...</b>        headword / phrase headword
#   <i>...</i>        foreign term, title, quoted example
#   <small>...</small> field label, source citation, usage note
#   <sup>...</sup>, <sub>...</sub>
#   <ref>...</ref>    cross-reference target
#
# Everything else is stripped to plain text, with structural tags turned
# into newlines (see structural_breaks below).
# ---------------------------------------------------------------------------

BOLD_TAGS = [
    "abbr", "adjf", "amorph", "col", "conjf", "decf",
    "h1", "h2", "plw", "singf", "singw", "spn", "b", "bold",
    "hw", "hwf", "headword",
]

ITALIC_TAGS = [
    "altsp", "asp", "booki", "centered", "colp", "ecol",
    "figcap", "figtitle", "film", "gen", "grk", "i", "it",
    "itran", "itrans", "jour", "markp", "mcol", "pluf",
    "publ", "ship", "title", "tradename", "ver",
]

SMALL_TAGS = [
    "comm", "contxt", "ex", "examp", "figref", "figure",
    "fld", "fr", "illu", "illust", "img", "iref", "mark",
    "note", "syn", "uex", "wnote", "wordforms", "xex",
    "pos", "pr", "ety", "sn", "sd",
]

REF_TAGS = [
    "er", "cref", "ant", "grp", "hypen", "intensi",
    "inv", "isa", "ref", "sig", "simto", "stype", "stypec",
]

# All remaining known tags are stripped to plain text.
PLAIN_TAGS = [
    "as", "au", "cas", "cd", "cd2", "chform", "chformi",
    "chname", "chreact", "city", "company", "corpn",
    "country", "cs", "date", "datey", "def", "def2",
    "edi", "ent", "epos", "exp", "fexp", "fract", "fu",
    "funct", "geog", "mathex", "method", "methodfor",
    "mord", "musfig", "nmorph", "org", "perf", "persfn",
    "person", "plain", "plu", "pre", "qex", "qpers",
    "qperson", "ratio", "refs", "river", "root", "sc",
    "see", "sing", "specif", "state", "tt", "unit",
    "usage", "vertical", "vinc", "vmorph", "w16ns",
    "wf", "wns",
    "altname", "altnpluf", "antiquetype", "blacklettertype",
    "boldfacetype", "bourgeoistype", "boxtype",
    "clarendontype", "englishtype", "extendedtype",
    "frenchelzevirtype", "germantype", "gothictype",
    "greatprimertype", "longprimertype", "miniontype",
    "nonpareiltype", "oldenglishtype", "oldstyletype",
    "pearltype", "picatype", "ptcl", "q", "sansserif",
    "scripttype", "smpicatype", "subtypes", "tr", "tran",
    "typewritertype", "universbold", "xlati",
    "bio", "biography", "branchof", "causedby", "causedbyp",
    "causes", "causesp", "class", "cnvto", "colf", "compof",
    "conseq", "consof", "contains", "contr", "corr", "cp",
    "divof", "emits", "ets", "etsep", "fam", "hascons",
    "kingdom", "member", "members", "membof", "ord", "part",
    "partof", "parts", "phylum", "prod", "prodby",
    "prodmac", "prodp", "recipr", "sfield", "stage",
    "stageof", "subclass", "subfam", "subord", "suborder",
    "subphylum", "usedby", "usedfor", "uses", "var", "varn",
    "rj",
]


def strip_tags(text, tags):
    for tag in tags:
        text = re.sub(
            rf"<{tag}>(.*?)</{tag}>",
            r"\1",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
    return text


def wrap_tags(text, tags, open_tag, close_tag):
    for tag in tags:
        text = re.sub(
            rf"<{tag}>(.*?)</{tag}>",
            rf"{open_tag}\1{close_tag}",
            text,
            flags=re.DOTALL | re.IGNORECASE,
        )
    return text


# ---------------------------------------------------------------------------
# Structural tags -> newlines
# ---------------------------------------------------------------------------

def structural_breaks(text):
    # <p> boundaries -> blank line
    text = re.sub(r"</p>\s*<p>", "\n\n", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<p>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)

    # <br/> and <br> -> single newline
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)

    # <point[N]>...</point[N]> -> small marker on its own line
    text = re.sub(
        r"<point\[(\d{1,2}(?:\.\d)?)\]>(.*?)</point\[\1\]>",
        r"\n<small>point\1.</small> \2\n",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # <sn>N.</sn> -> newline + number
    text = re.sub(
        r"<sn>(\d+)\.</sn>",
        r"\n\n\1. ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"<sn>(\d+)</sn>",
        r"\n\n\1. ",
        text,
        flags=re.IGNORECASE,
    )

    # <sd>(a)</sd> -> newline + subsense marker
    text = re.sub(
        r"<sd>(\([a-z0-9]+\))</sd>",
        r"\n\n    \1 ",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"<sd>(.*?)</sd>",
        r"\n\n    \1 ",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # <source>...</source> -> small citation on own line
    text = re.sub(
        r"\[\s*<source>(.*?)</source>\s*\]",
        r"\n\n<small>[\1]</small>\n\n",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # <col>...</col> phrase headwords -> their own line
    text = re.sub(
        r"<col>(.*?)</col>",
        r"\n<b>\1</b>",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # <mhw>{ ... }</mhw> -> bracketed alternatives
    text = re.sub(
        r"<mhw>\{\s*(.*?)\s*\}</mhw>",
        r"[\1]",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # <qau>...</qau> -> bracketed attribution
    text = re.sub(
        r"<qau>(.*?)</qau>",
        r"[\1]",
        text,
        flags=re.DOTALL | re.IGNORECASE,
    )

    return text


# ---------------------------------------------------------------------------
# Whitespace handling: preserve newlines, squeeze horizontal space
# ---------------------------------------------------------------------------

def normalize_whitespace(text):
    # Collapse runs of spaces/tabs (not newlines) to a single space
    text = re.sub(r"[ \t]+", " ", text)
    # Strip trailing spaces on lines
    text = re.sub(r" *\n *", "\n", text)
    # Collapse runs of 3+ newlines to 2 (one blank line)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


# ---------------------------------------------------------------------------
# Line wrapping with indentation
# ---------------------------------------------------------------------------

def wrap_paragraph(paragraph, width, indent=""):
    """Wrap a single paragraph (no newlines) to width columns."""
    if not paragraph:
        return []
    words = paragraph.split(" ")
    lines = []
    current = indent
    for word in words:
        if not word:
            continue
        if current == indent:
            candidate = current + word
        else:
            candidate = current + " " + word
        if len(candidate) > width and current != indent:
            lines.append(current)
            current = indent + word
        else:
            current = candidate
    if current != indent:
        lines.append(current)
    return lines


def wrap_body(text, width, indent="    "):
    """Wrap each paragraph of the body, preserving blank lines."""
    out_lines = []
    paragraphs = re.split(r"\n\n+", text)
    for i, para in enumerate(paragraphs):
        para = para.strip("\n")
        if not para:
            continue
        if i > 0:
            out_lines.append("")
        # Preserve any single newlines inside a paragraph as hard breaks
        sub_lines = para.split("\n")
        for j, sub in enumerate(sub_lines):
            if j > 0:
                out_lines.append(indent + sub.strip())
            else:
                out_lines.extend(wrap_paragraph(sub.strip(), width, indent))
    return out_lines


# ---------------------------------------------------------------------------
# Main tag processing pipeline
# ---------------------------------------------------------------------------

def process_definition(raw):
    if not raw.strip():
        return ""

    text = remove_control_chars(raw)
    text = unescape(text)

    # Structural first (creates newlines)
    text = structural_breaks(text)

    # Symbol / entity substitution
    text = match_symbols(text)
    text = match_symbols_frac(text)
    text = match_undefined(text)
    text = match_chars(text)

    # Inline tag mapping
    text = wrap_tags(text, BOLD_TAGS, "<b>", "</b>")
    text = wrap_tags(text, ITALIC_TAGS, "<i>", "</i>")
    text = wrap_tags(text, SMALL_TAGS, "<small>", "</small>")
    text = wrap_tags(text, REF_TAGS, "<ref>", "</ref>")

    # Remaining known tags: strip to plain
    text = strip_tags(text, PLAIN_TAGS)

    # Strip any residual <xxx>...</xxx> we didn't map (safety net)
    text = re.sub(r"</?[a-zA-Z][^>]*>", "", text)

    # Remove stray entity tags <foo/ that survived substitution
    text = re.sub(r"<[a-zA-Z][a-zA-Z0-9]*/", "", text)

    # Normalize whitespace
    text = normalize_whitespace(text)
    text = text.strip()

    return text


# ---------------------------------------------------------------------------
# Entry parsing
# ---------------------------------------------------------------------------

ENT_LINE_RE = re.compile(r"^<p><ent>([^<]+?)</ent><br/?", re.IGNORECASE)


def parse_entries_raw(full_text):
    lines = full_text.splitlines(keepends=True)
    ent_line_indices = []
    ent_words = []

    for idx, line in enumerate(lines):
        m = ENT_LINE_RE.match(line)
        if m:
            ent_line_indices.append(idx)
            ent_words.append(m.group(1).strip())

    if not ent_line_indices:
        return []

    entries = []
    for i, (start_idx, word) in enumerate(zip(ent_line_indices, ent_words)):
        end_idx = (
            ent_line_indices[i + 1]
            if i + 1 < len(ent_line_indices)
            else len(lines)
        )

        line = lines[start_idx]
        br_pos = line.find("<br/")
        first_part = line[br_pos + len("<br/") :].strip() if br_pos >= 0 else ""
        rest_parts = " ".join(
            l.strip() for l in lines[start_idx + 1 : end_idx]
        )
        raw = (first_part + "\n" + rest_parts).strip()
        entries.append((word, raw))

    return entries


# ---------------------------------------------------------------------------
# Output formatting
# ---------------------------------------------------------------------------

def format_entry(word, body, width=WRAP_WIDTH):
    """Render one entry as multi-line text."""
    lines = [word]
    if body:
        body_lines = wrap_body(body, width, indent="    ")
        lines.extend(body_lines)
    lines.append("")  # blank line separator between entries
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Section discovery (A -> Z)
# ---------------------------------------------------------------------------

def find_section_files(folder):
    """Find CIDE.* files in folder, sorted A -> Z."""
    if not os.path.isdir(folder):
        raise FileNotFoundError(f"Input folder not found: {folder}")

    files = [
        f for f in os.listdir(folder)
        if f.startswith("CIDE.") and os.path.isfile(os.path.join(folder, f))
    ]
    if not files:
        raise FileNotFoundError(
            f"No CIDE.* files found in {folder}"
        )

    def sort_key(name):
        suffix = name[len("CIDE."):]
        # Strip any leading zeros for numeric comparison
        m = re.match(r"^0*(\d+)$", suffix)
        if m:
            return (0, int(m.group(1)), name)
        return (1, suffix.upper(), name)

    files.sort(key=sort_key)
    return [os.path.join(folder, f) for f in files]

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Input folder:  {INPUT_FOLDER}")
    print(f"Output folder: {OUTPUT_FOLDER}")

    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    section_files = find_section_files(INPUT_FOLDER)
    print(f"Found {len(section_files)} section files:")
    for f in section_files:
        print(f"  {os.path.basename(f)}")

    total_entries = 0

    for section_path in section_files:
        section_name = os.path.basename(section_path)
        out_name = section_name + ".txt"
        out_path = os.path.join(OUTPUT_FOLDER, out_name)

        print(f"\nProcessing {section_name} ...")
        with open(section_path, "r", encoding="utf-8", errors="replace") as f:
            full_text = f.read()

        entries = parse_entries_raw(full_text)
        print(f"  Parsed {len(entries)} entries")

        output_chunks = []
        for i, (word, raw) in enumerate(entries):
            body = process_definition(raw)
            output_chunks.append(format_entry(word, body))
            if (i + 1) % 5000 == 0:
                print(f"  Processed {i + 1}/{len(entries)}")

        output_text = "\n".join(output_chunks)

        with open(out_path, "w", encoding="utf-8") as f:
            f.write(output_text)

        total_entries += len(entries)
        print(f"  Wrote {out_path}")

    print(f"\nDone. Total entries across all sections: {total_entries}")
    print(f"Output written to: {OUTPUT_FOLDER}")


if __name__ == "__main__":
    main()