#!/usr/bin/env python3
"""Turn the Curriculum-Vitae LaTeX sources into a Hugo data file.

The CV lives in its own repository (github.com/ewtodd/Curriculum-Vitae) and is
written for moderncv/biblatex, not for the web.  Rather than keep a second,
hand-maintained copy of the same facts in this repository, the site build reads
that repository directly: this script parses the `sections/*.tex` files and the
two `.bib` files into `data/cv.json`, which `layouts/cv/single.html` renders.
The committed `CV.pdf` is copied to `static/cv/CV.pdf` alongside it.

Both outputs are generated and gitignored.  `nix build` runs this with the
`curriculum-vitae` flake input as the source, so bumping that input is the whole
update procedure; `cv-import` in the dev shell does the same thing from a local
checkout.

The parsing is deliberately specific to how that CV is written rather than
general LaTeX: only the commands moderncv actually uses are understood.  When
something unrecognised turns up it is passed through as text rather than
dropped, so a new construct degrades to a slightly ugly line instead of a
missing entry.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

# --------------------------------------------------------------------------
# LaTeX -> HTML
# --------------------------------------------------------------------------

# Single-token replacements that need no arguments.  Everything here renders as
# literal text, so it is escaped for HTML at the point of substitution.
SYMBOLS = {
    "alpha": "\u03b1",
    "beta": "\u03b2",
    "gamma": "\u03b3",
    "delta": "\u03b4",
    "mu": "\u03bc",
    "nu": "\u03bd",
    "pi": "\u03c0",
    "sigma": "\u03c3",
    "tau": "\u03c4",
    "chi": "\u03c7",
    "rightarrow": "\u2192",
    "to": "\u2192",
    "leftarrow": "\u2190",
    "pm": "\u00b1",
    "times": "\u00d7",
    "cdot": "\u00b7",
    "ldots": "\u2026",
    "dots": "\u2026",
    "LaTeX": "LaTeX",
    "TeX": "TeX",
    "aa": "\u00e5",
    "AA": "\u00c5",
    "o": "\u00f8",
    "O": "\u00d8",
    "ss": "\u00df",
    "ae": "\u00e6",
    "AE": "\u00c6",
    "&": "&",
    "%": "%",
    "_": "_",
    "#": "#",
    "$": "$",
    "{": "{",
    "}": "}",
    " ": " ",
    ",": "\u2009",
    ";": "\u2009",
    "!": "",
    "quad": "\u2003",
    "qquad": "\u2003\u2003",
    "par": "\n",
}

# Accents written as \'e, \"o, \~n and friends.
ACCENTS = {
    "'": {"a": "\u00e1", "e": "\u00e9", "i": "\u00ed", "o": "\u00f3", "u": "\u00fa",
          "c": "\u0107", "n": "\u0144", "s": "\u015b", "y": "\u00fd"},
    "`": {"a": "\u00e0", "e": "\u00e8", "i": "\u00ec", "o": "\u00f2", "u": "\u00f9"},
    '"': {"a": "\u00e4", "e": "\u00eb", "i": "\u00ef", "o": "\u00f6", "u": "\u00fc",
          "y": "\u00ff"},
    "^": {"a": "\u00e2", "e": "\u00ea", "i": "\u00ee", "o": "\u00f4", "u": "\u00fb"},
    "~": {"a": "\u00e3", "n": "\u00f1", "o": "\u00f5"},
    "c": {"c": "\u00e7", "C": "\u00c7", "s": "\u015f"},
    "=": {"a": "\u0101", "e": "\u0113", "i": "\u012b", "o": "\u014d", "u": "\u016b"},
    ".": {"a": "\u0227", "e": "\u0117", "o": "\u022f", "z": "\u017c"},
    "v": {"c": "\u010d", "s": "\u0161", "z": "\u017e", "r": "\u0159", "e": "\u011b"},
    "u": {"a": "\u0103", "g": "\u011f", "u": "\u016d"},
}

# Commands taking one argument that map onto a single HTML element.
WRAPPERS = {
    "textbf": "strong",
    "mkbibbold": "strong",
    "textit": "em",
    "emph": "em",
    "mkbibemph": "em",
    "textsuperscript": "sup",
    "textsubscript": "sub",
    "underline": "u",
    "texttt": "code",
    "mkbibquote": None,  # handled specially: wraps in typographic quotes
}

# Commands whose one argument is kept but rendered as plain text.
TRANSPARENT_1 = {
    "textsc", "textrm", "textsf", "textnormal", "text", "mathrm", "mbox",
    "hbox", "centering", "RaggedRight", "small", "footnotesize", "normalsize",
    "protect", "bibstring", "mkbibname",
}

# Commands whose arguments are discarded entirely (spacing, layout, hints).
DISCARD_1 = {
    "vspace", "hspace", "vspace*", "hspace*", "label", "index", "phantom",
    "raisebox", "colorlet", "definecolor", "setlength", "addbibresource",
    "input", "include", "hypersetup", "usepackage", "documentclass",
    "moderncvcolor", "moderncvstyle", "name", "nopagenumbers", "makecvhead",
}

# Commands with no arguments that are dropped outright.
DISCARD_0 = {
    "noindent", "pagebreak", "newpage", "clearpage", "hfill", "vfill",
    "sloppy", "raggedright", "columnwidth", "textwidth", "linewidth",
    "makecvhead", "nopagenumbers", "smallskip", "medskip", "bigskip",
}


def _esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class TexParser:
    """A small recursive LaTeX-to-HTML converter.

    Not a TeX implementation: it walks the source once, emitting HTML for the
    handful of constructs this CV uses and falling back to escaped text for
    anything else.  `math` tracks whether we are inside `$...$`, which is the
    only place `^` and `_` are treated as super/subscript.
    """

    def __init__(self, src: str) -> None:
        self.s = src
        self.i = 0
        self.n = len(src)

    # -- low-level scanning -------------------------------------------------

    def _skip_space(self) -> None:
        while self.i < self.n:
            c = self.s[self.i]
            if c == "%":
                while self.i < self.n and self.s[self.i] != "\n":
                    self.i += 1
            elif c.isspace():
                self.i += 1
            else:
                return

    def _read_group(self) -> str | None:
        """Read one `{...}` group, returning its raw contents."""
        self._skip_space()
        if self.i >= self.n or self.s[self.i] != "{":
            return None
        depth = 0
        start = self.i + 1
        while self.i < self.n:
            c = self.s[self.i]
            if c == "\\":
                self.i += 2
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    body = self.s[start:self.i]
                    self.i += 1
                    return body
            self.i += 1
        return self.s[start:]

    def _read_optional(self) -> str | None:
        """Read one `[...]` optional argument if present."""
        self._skip_space()
        if self.i >= self.n or self.s[self.i] != "[":
            return None
        depth = 0
        start = self.i + 1
        while self.i < self.n:
            c = self.s[self.i]
            if c == "[":
                depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0:
                    body = self.s[start:self.i]
                    self.i += 1
                    return body
            self.i += 1
        return self.s[start:]

    def _read_token(self) -> str:
        """Read the argument of a command that may be a group or one token."""
        g = self._read_group()
        if g is not None:
            return g
        self._skip_space()
        if self.i < self.n:
            c = self.s[self.i]
            if c == "\\":
                self.i += 1
                name = self._read_name()
                return "\\" + name
            self.i += 1
            return c
        return ""

    def _read_name(self) -> str:
        m = re.match(r"[A-Za-z]+\*?", self.s[self.i:])
        if m:
            self.i += m.end()
            return m.group(0)
        if self.i < self.n:
            c = self.s[self.i]
            self.i += 1
            return c
        return ""

    # -- conversion ---------------------------------------------------------

    def convert(self, math: bool = False, stop: str | None = None) -> str:
        out: list[str] = []
        while self.i < self.n:
            c = self.s[self.i]
            if stop and self.s.startswith(stop, self.i):
                self.i += len(stop)
                break
            if c == "%":
                while self.i < self.n and self.s[self.i] != "\n":
                    self.i += 1
                continue
            if c == "\\":
                self.i += 1
                out.append(self._command(math))
                continue
            if c == "{":
                body = self._read_group() or ""
                out.append(sub_convert(body, math))
                continue
            if c == "}":
                # Unbalanced close; consume so we always terminate.
                self.i += 1
                continue
            if c == "$":
                self.i += 1
                if self.s.startswith("$", self.i):  # display math
                    self.i += 1
                    inner = self.convert(math=True, stop="$$")
                else:
                    inner = self.convert(math=True, stop="$")
                out.append(_finish_math(inner))
                continue
            if c == "~":
                self.i += 1
                out.append("&nbsp;")
                continue
            if math and c == "-":
                self.i += 1
                out.append("−")
                continue
            if math and c in "^_":
                self.i += 1
                arg = self._read_token()
                tag = "sup" if c == "^" else "sub"
                out.append(f"<{tag}>{sub_convert(arg, True)}</{tag}>")
                continue
            if c == "-" and self.s.startswith("---", self.i):
                self.i += 3
                out.append("\u2014")
                continue
            if c == "-" and self.s.startswith("--", self.i):
                self.i += 2
                out.append("\u2013")
                continue
            if c == "\n":
                self.i += 1
                out.append("\n")
                continue
            self.i += 1
            out.append(_esc(c))
        return "".join(out)

    def _command(self, math: bool) -> str:
        name = self._read_name()

        if name == "begin" or name == "end":
            self._read_group()
            self._read_optional()
            self._read_group()  # some environments take a width argument
            return ""

        if name in ("href", "url"):
            first = self._read_group() or ""
            if name == "url":
                url = first.strip()
                return f'<a href="{_esc(url)}" rel="noopener">{_esc(url)}</a>'
            text = self._read_group() or ""
            return (f'<a href="{_esc(first.strip())}" rel="noopener">'
                    f'{sub_convert(text, math)}</a>')

        if name == "texorpdfstring":
            tex = self._read_group() or ""
            self._read_group()
            return sub_convert(tex, math)

        if name == "iso":
            a = self._read_group() or ""
            b = self._read_group() or ""
            return f"<sup>{sub_convert(a, True)}</sup>{sub_convert(b, math)}"

        if name == "yearabove":
            # {month}{year} typeset stacked in the PDF; reads better inline.
            month = self._read_group() or ""
            year = self._read_group() or ""
            return f"{sub_convert(month, math)} {sub_convert(year, math)}".strip()

        if name in WRAPPERS:
            arg = self._read_group()
            if arg is None:
                arg = self._read_token()
            inner = sub_convert(arg, math)
            tag = WRAPPERS[name]
            if tag is None:
                return f"\u201c{inner}\u201d"
            return f"<{tag}>{inner}</{tag}>"

        if name in TRANSPARENT_1:
            arg = self._read_group()
            if arg is None:
                return ""
            return sub_convert(arg, math)

        if name in DISCARD_1:
            self._read_optional()
            self._read_group()
            return ""

        if name in ("newline", "\\", "cr"):
            self._read_optional()
            # A forced break is a paragraph boundary here; a plain source
            # newline is only a space, exactly as TeX treats them.
            return "\n\n"

        if name in ACCENTS:
            arg = self._read_token()
            base = arg.strip("{}")
            table = ACCENTS[name]
            if base in table:
                return table[base]
            return _esc(base)

        if name in SYMBOLS:
            return _esc(SYMBOLS[name])

        if name in DISCARD_0:
            return ""

        # Unknown command.  Keep any braced argument's text so content is never
        # silently lost, and drop the command name itself.
        arg = self._read_group()
        if arg is not None:
            return sub_convert(arg, math)
        return ""


def sub_convert(src: str, math: bool = False) -> str:
    return TexParser(src).convert(math=math)


def _finish_math(inner: str) -> str:
    """Tidy the text left over from a `$...$` run.

    Most math in this CV is a nuclide superscript or an arrow, which the parser
    has already turned into markup.  What remains is usually a bare variable
    name, and those read better italicised.
    """
    stripped = re.sub(r"<[^>]+>", "", inner).strip()
    if len(stripped) == 1 and stripped.isalpha():
        return f"<em>{inner}</em>"
    return inner


def tex_to_html(src: str) -> str:
    """Convert, keeping paragraph breaks and only paragraph breaks.

    TeX joins consecutive lines into one paragraph and breaks only on a blank
    line or an explicit `\\newline`, so the same rule is applied here: real
    breaks are protected, everything else collapses to a space.
    """
    html = sub_convert(src)
    html = re.sub(r"[ \t]+", " ", html)
    html = re.sub(r"\n[ \t]*\n[\s]*", "\x00", html)
    html = re.sub(r"\s*\n\s*", " ", html)
    return html.replace("\x00", "\n").strip()


def tex_to_inline(src: str) -> str:
    """Convert to HTML and collapse breaks: for anything that is one line."""
    return re.sub(r"\s*\n\s*", " ", tex_to_html(src)).strip()


def tex_to_dates(src: str) -> str:
    """Convert a moderncv date range and normalise the dash inside it.

    The CV writes ranges as `--`, as `-`, and with `$\\,\\,$` padding around
    "Present", none of which survive as-is.  Date fields are the only place a
    hyphen means a range, so collapsing them here is safe.
    """
    text = tex_to_inline(src)
    text = re.sub(r"[\s ]*[–—-][\s ]*", "–", text)
    return re.sub(r"[\s ]{2,}", " ", text).strip()


def plain(html: str) -> str:
    """Strip tags and entities, for `description` meta and sort keys."""
    text = re.sub(r"<[^>]+>", "", html)
    for ent, ch in (("&nbsp;", " "), ("&amp;", "&"), ("&lt;", "<"), ("&gt;", ">")):
        text = text.replace(ent, ch)
    return re.sub(r"\s+", " ", text).strip()


# --------------------------------------------------------------------------
# Block structure
# --------------------------------------------------------------------------

def strip_comments(src: str) -> str:
    out = []
    for line in src.splitlines():
        idx = 0
        while True:
            idx = line.find("%", idx)
            if idx == -1:
                break
            if idx > 0 and line[idx - 1] == "\\":
                idx += 1
                continue
            line = line[:idx]
            break
        out.append(line)
    return "\n".join(out)


def split_items(body: str) -> list[str]:
    """Split the body of an itemize/enumerate on `\\item`."""
    parts = re.split(r"\\item\b", body)
    return [p for p in (x.strip() for x in parts[1:]) if p]


def extract_env(src: str, env: str) -> tuple[str | None, str]:
    """Pull the first `\\begin{env}...\\end{env}` out, returning (body, rest)."""
    open_re = re.compile(r"\\begin\{" + env + r"\}")
    m = open_re.search(src)
    if not m:
        return None, src
    depth = 1
    pos = m.end()
    token = re.compile(r"\\(begin|end)\{" + env + r"\}")
    while depth:
        t = token.search(src, pos)
        if not t:
            return src[m.end():], src[:m.start()]
        depth += 1 if t.group(1) == "begin" else -1
        pos = t.end()
        if depth == 0:
            return src[m.end():t.start()], src[:m.start()] + src[t.end():]
    return None, src


def parse_description(src: str) -> tuple[list[str], list[str]]:
    """Split a moderncv description into (lead paragraphs, bullet list)."""
    bullets: list[str] = []
    rest = src
    while True:
        body, rest = extract_env(rest, "itemize")
        if body is None:
            break
        bullets.extend(tex_to_inline(item) for item in split_items(body))
    lead_html = tex_to_html(rest)
    leads = [ln.strip() for ln in lead_html.split("\n") if ln.strip()]
    return leads, [b for b in bullets if b]


def read_commands(src: str, names: set[str]) -> list[tuple[str, list[str]]]:
    """Scan for the given commands, returning (name, args) in source order."""
    found: list[tuple[str, list[str]]] = []
    arity = {
        "cventry": 6,
        "cvitem": 2,
        "cvitemwithcomment": 3,
        "section": 1,
        "subsection": 1,
    }
    i = 0
    n = len(src)
    while i < n:
        m = re.compile(r"\\([A-Za-z]+)").search(src, i)
        if not m:
            break
        name = m.group(1)
        if name not in names:
            i = m.end()
            continue
        p = TexParser(src)
        p.i = m.end()
        args = []
        for _ in range(arity.get(name, 1)):
            args.append(p._read_group() or "")
        found.append((name, args))
        i = p.i
    return found


def parse_entry_section(src: str) -> list[dict]:
    """Education / research / teaching: `\\cventry` with optional subsections.

    In `research.tex` each position is followed by `\\subsection{Project}`
    blocks that belong to it, with empty `\\subsection{}` used purely as a
    spacer.  Treating a non-empty subsection as a child of the most recent
    entry is what reassembles that nesting.
    """
    entries: list[dict] = []
    for name, args in read_commands(src, {"cventry", "subsection"}):
        if name == "cventry":
            dates, title, org, location, grade, desc = args
            leads, bullets = parse_description(desc)
            entries.append({
                "dates": tex_to_dates(dates),
                "title": tex_to_inline(title),
                "org": tex_to_inline(org),
                "location": tex_to_inline(location),
                "grade": tex_to_inline(grade),
                "notes": leads,
                "bullets": bullets,
                "projects": [],
            })
        else:
            title = tex_to_inline(args[0])
            if not title or not entries:
                continue
            entries[-1]["projects"].append({"title": title, "notes": [], "bullets": []})
    return entries


def attach_project_bodies(src: str, entries: list[dict]) -> None:
    """Fill in the prose that follows each `\\subsection` in research.tex.

    `read_commands` gives the headings; the bodies are whatever sits between one
    heading and the next command, so they are collected in a second pass over
    the raw source.
    """
    marks = [(m.start(), m.end()) for m in re.finditer(r"\\subsection\{", src)]
    if not marks:
        return
    bodies: list[tuple[str, str]] = []
    for idx, (start, _) in enumerate(marks):
        p = TexParser(src)
        p.i = start + len("\\subsection")
        heading = tex_to_inline(p._read_group() or "")
        end = marks[idx + 1][0] if idx + 1 < len(marks) else len(src)
        body = src[p.i:end]
        # A following \cventry starts the next position, not this project.
        cut = body.find("\\cventry")
        if cut != -1:
            body = body[:cut]
        bodies.append((heading, body))

    flat = [(e, p) for e in entries for p in e["projects"]]
    lookup: dict[str, list[str]] = {}
    for heading, body in bodies:
        if heading:
            lookup.setdefault(heading, []).append(body)
    for _entry, proj in flat:
        queue = lookup.get(proj["title"])
        if not queue:
            continue
        leads, bullets = parse_description(queue.pop(0))
        proj["notes"] = leads
        proj["bullets"] = bullets


def parse_item_section(src: str) -> list[dict]:
    """Honors / grants: `\\cvitem` and `\\cvitemwithcomment`."""
    items = []
    for name, args in read_commands(src, {"cvitem", "cvitemwithcomment"}):
        if name == "cvitem":
            items.append({
                "date": tex_to_inline(args[0]),
                "title": tex_to_inline(args[1]),
                "comment": "",
            })
        else:
            items.append({
                "date": tex_to_inline(args[0]),
                "title": tex_to_inline(args[1]),
                "comment": tex_to_inline(args[2]),
            })
    return items


def parse_tabular(body: str) -> list[dict]:
    """Two-column `label & value \\\\` rows, as used by the skills table."""
    rows = []
    for raw in re.split(r"\\\\(?:\[[^\]]*\])?", body):
        raw = raw.strip()
        if not raw or raw.startswith("\\hline"):
            continue
        cells = [c for c in re.split(r"(?<!\\)&", raw)]
        if len(cells) < 2:
            continue
        label = tex_to_inline(cells[0]).rstrip(":")
        value = tex_to_inline("&".join(cells[1:]))
        if label or value:
            rows.append({"label": label, "value": value})
    return rows


def parse_skills_section(src: str) -> list[dict]:
    """Skills: each `\\cvitem` is a group, some holding a nested tabular."""
    groups = []
    for name, args in read_commands(src, {"cvitem"}):
        if name != "cvitem":
            continue
        label = tex_to_inline(args[0])
        body = args[1]
        table, rest = extract_env(body, "tabular")
        if table is not None:
            # `\begin{tabular}{@{}l @{\hspace{1em}} l@{}}` — the column spec
            # nests braces, so it has to be matched rather than pattern-stripped.
            spec = TexParser(table)
            if spec._read_group() is not None:
                table = table[spec.i:]
            groups.append({"label": label, "value": "", "rows": parse_tabular(table)})
        else:
            groups.append({"label": label, "value": tex_to_inline(rest), "rows": []})
    return [g for g in groups if g["label"]]


# --------------------------------------------------------------------------
# BibTeX
# --------------------------------------------------------------------------

def parse_bib(text: str) -> dict[str, dict]:
    """Parse the subset of BibTeX these two files use."""
    entries: dict[str, dict] = {}
    for m in re.finditer(r"@(\w+)\s*\{", text):
        kind = m.group(1).lower()
        i = m.end()
        depth = 1
        start = i
        while i < len(text) and depth:
            c = text[i]
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
            i += 1
        body = text[start:i - 1]
        key, _, fields_src = body.partition(",")
        key = key.strip()
        if not key:
            continue
        entries[key] = {"type": kind, "key": key, "fields": _parse_fields(fields_src)}
    return entries


def _parse_fields(src: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    i = 0
    n = len(src)
    while i < n:
        m = re.compile(r"\s*(\w+)\s*=\s*").match(src, i)
        if not m:
            i += 1
            continue
        name = m.group(1).lower()
        i = m.end()
        if i < n and src[i] == "{":
            depth = 0
            start = i + 1
            while i < n:
                if src[i] == "{":
                    depth += 1
                elif src[i] == "}":
                    depth -= 1
                    if depth == 0:
                        break
                i += 1
            value = src[start:i]
            i += 1
        elif i < n and src[i] == '"':
            start = i + 1
            i += 1
            while i < n and src[i] != '"':
                i += 1
            value = src[start:i]
            i += 1
        else:
            start = i
            while i < n and src[i] != ",":
                i += 1
            value = src[start:i]
        fields[name] = re.sub(r"\s+", " ", value).strip()
        while i < n and src[i] in ", \n\t":
            i += 1
    return fields


def split_names(raw: str) -> list[str]:
    """Split a BibTeX author field on ` and `, respecting braces."""
    names, depth, buf = [], 0, []
    i = 0
    while i < len(raw):
        c = raw[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        if depth == 0 and raw.startswith(" and ", i):
            names.append("".join(buf).strip())
            buf = []
            i += 5
            continue
        buf.append(c)
        i += 1
    if buf:
        names.append("".join(buf).strip())
    return [n for n in names if n]


def format_name(raw: str, family_of_interest: str) -> tuple[str, bool]:
    """Render one author as `E. Todd`, and say whether it is the CV's owner.

    A fully braced name (`{CMS HGCAL Collaboration}`) is a corporate author and
    is passed through untouched, which is what biblatex does too.
    """
    raw = raw.strip()
    if raw.startswith("{") and raw.endswith("}"):
        return tex_to_inline(raw[1:-1]), False
    if "," in raw:
        family, _, given = raw.partition(",")
    else:
        parts = raw.split()
        family = parts[-1] if parts else raw
        given = " ".join(parts[:-1])
    initials = []
    for token in given.replace(".", " ").split():
        letter = token[0]
        if letter == "\\" and len(token) > 1:
            letter = token[1]
        initials.append(f"{letter}.")
    family_html = tex_to_inline(family.strip())
    is_owner = plain(family_html).lower() == family_of_interest.lower()
    rendered = " ".join(initials + [family_html]).strip()
    return rendered, is_owner


def format_authors(raw: str, max_names: int = 3, owner: str = "Todd") -> str:
    names = split_names(raw)
    rendered = []
    for name in names[:max_names]:
        text, is_owner = format_name(name, owner)
        rendered.append(f"<strong>{text}</strong>" if is_owner else text)
    joined = ", ".join(rendered)
    if len(names) > max_names:
        joined += ", et al."
    return joined


def cite_keys(src: str) -> list[str]:
    """The `\\fullcite{...}` keys, in the order the section lists them."""
    return re.findall(r"\\fullcite\{([^}]+)\}", src)


def build_reference(entry: dict) -> dict:
    fields = entry["fields"]
    doi = fields.get("doi", "").strip()
    url = fields.get("url", "").strip()
    if not url and doi:
        url = f"https://doi.org/{doi}"
    title = tex_to_inline(fields.get("title", ""))
    venue = tex_to_inline(fields.get("journal", "") or fields.get("howpublished", ""))
    note = tex_to_inline(fields.get("note", ""))
    status = ""
    for candidate in (venue, note):
        low = plain(candidate).lower()
        if low in ("under review", "in press", "submitted", "in preparation", "accepted"):
            status = plain(candidate)
    if plain(venue).lower() == status.lower():
        venue = ""
    if plain(note).lower() == status.lower():
        note = ""
    return {
        "key": entry["key"],
        "type": entry["type"],
        "authors": format_authors(fields.get("author", "")),
        "title": title,
        "venue": venue,
        "note": note,
        "status": status,
        "year": plain(tex_to_inline(fields.get("year", ""))),
        "doi": doi,
        "url": url,
    }


# --------------------------------------------------------------------------
# Driver
# --------------------------------------------------------------------------

SECTION_TITLES = {
    "education": "Education",
    "research": "Research Experience",
    "publications": "Publications",
    "presentations": "Presentations",
    "teaching": "Teaching Experience",
    "honors": "Honors and Awards",
    "grants": "Grants",
    "skills": "Skills",
}

# Order on the page, which is not the order of the PDF: the web version leads
# with what a visitor is most likely to be looking for.
SECTION_ORDER = [
    "education", "research", "publications", "presentations",
    "teaching", "honors", "grants", "skills",
]


def section_title(src: str, fallback: str) -> str:
    m = re.search(r"\\section\{([^}]*)\}", src)
    return tex_to_inline(m.group(1)) if m else fallback


def read(path: Path) -> str:
    return strip_comments(path.read_text(encoding="utf-8"))


def build(source: Path, rev: str, updated: str) -> dict:
    sections_dir = source / "sections"
    if not sections_dir.is_dir():
        raise SystemExit(f"cv-import: no sections/ directory under {source}")

    bib: dict[str, dict] = {}
    for name in ("publications.bib", "presentations.bib"):
        path = source / name
        if path.exists():
            bib.update(parse_bib(path.read_text(encoding="utf-8")))

    sections = []
    for slug in SECTION_ORDER:
        path = sections_dir / f"{slug}.tex"
        if not path.exists():
            continue
        src = read(path)
        title = section_title(src, SECTION_TITLES.get(slug, slug.title()))

        if slug in ("publications", "presentations"):
            refs = [build_reference(bib[k]) for k in cite_keys(src) if k in bib]
            sections.append({"id": slug, "title": title, "kind": "references",
                             "references": refs})
        elif slug == "skills":
            sections.append({"id": slug, "title": title, "kind": "skills",
                             "groups": parse_skills_section(src)})
        elif slug in ("honors", "grants"):
            sections.append({"id": slug, "title": title, "kind": "awards",
                             "awards": parse_item_section(src)})
        else:
            entries = parse_entry_section(src)
            if slug == "research":
                attach_project_bodies(src, entries)
            sections.append({"id": slug, "title": title, "kind": "entries",
                             "entries": entries})

    contact = parse_contact(source / "CV.tex")

    return {
        "source": {
            "repo": "https://github.com/ewtodd/Curriculum-Vitae",
            "rev": rev,
            "short_rev": rev[:7] if rev else "",
            "updated": updated,
        },
        "contact": contact,
        "sections": sections,
    }


def parse_contact(cv_tex: Path) -> dict:
    """Pull the identity block out of CV.tex so the page has one source too."""
    if not cv_tex.exists():
        return {}
    src = read(cv_tex)
    contact: dict[str, str] = {}
    m = re.search(r"\\name\{([^}]*)\}\{([^}]*)\}", src)
    if m:
        contact["name"] = tex_to_inline(f"{m.group(1)} {m.group(2)}")
    m = re.search(r"\\email\{([^}]*)\}", src)
    if m:
        contact["email"] = plain(tex_to_inline(m.group(1)))
    for m in re.finditer(r"\\social\[([^\]]*)\]\{([^}]*)\}", src):
        contact[m.group(1).strip()] = plain(tex_to_inline(m.group(2)))
    return contact


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", nargs="?", default=os.environ.get("CV_SOURCE", "../Curriculum-Vitae"),
                    help="path to a checkout of the Curriculum-Vitae repository")
    ap.add_argument("--site", default=os.environ.get("SITE_ROOT", "."),
                    help="root of this Hugo site (default: current directory)")
    ap.add_argument("--rev", default=os.environ.get("CV_REV", ""),
                    help="revision of the CV source, recorded in the output")
    ap.add_argument("--updated", default=os.environ.get("CV_UPDATED", ""),
                    help="ISO date of that revision, recorded in the output")
    args = ap.parse_args()

    source = Path(args.source).expanduser()
    site = Path(args.site).expanduser()
    if not source.is_dir():
        print(f"cv-import: {source} is not a directory", file=sys.stderr)
        return 1

    data = build(source, args.rev, args.updated)

    pdf = source / "CV.pdf"
    if pdf.exists():
        dest = site / "static" / "cv"
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(pdf, dest / "CV.pdf")
        data["pdf"] = "/cv/CV.pdf"

    out = site / "data" / "cv.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    counts = ", ".join(
        f"{s['id']}: {len(s.get('entries') or s.get('references') or s.get('awards') or s.get('groups') or [])}"
        for s in data["sections"]
    )
    print(f"cv-import: wrote {out} ({counts})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
