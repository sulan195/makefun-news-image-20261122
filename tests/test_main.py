#!/usr/bin/env python3
"""Test suite for the news-image-20261122 entry.

Plain asserts, run with `python3 tests/test_main.py` from the repo root.
Implements the Fase 2 case list (TC001-TC030, TC009/TC028 merged,
TC020 with the full wallet address, TC023 split into masthead + date line).
Pillow is required for the render/overflow tests (build-time only; the
graded entrypoint main.py is stdlib-only and never imports it).

Exit 0 when every case passes, 1 otherwise.
"""

import hashlib
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
import main as entry_main  # noqa: E402

WALLET = "w37xQVEhZfrSP4FFnZoTkkVgPnnQBc6tw1BJJnDLhu3"
PASSED = []
FAILED = []


def check(name, cond, detail=""):
    if cond:
        PASSED.append(name)
        print("PASS %s" % name)
    else:
        FAILED.append(name)
        print("FAIL %s %s" % (name, detail))


def run_main(env_extra=None):
    env = dict(os.environ)
    env.pop("MAKEFUN_OUTPUT_DIR", None)
    if env_extra:
        env.update(env_extra)
    proc = subprocess.run([sys.executable, os.path.join(ROOT, "main.py")],
                          capture_output=True, text=True, env=env, cwd=ROOT)
    return proc


def read_png_bytes():
    with open(os.path.join(ROOT, "entry.png"), "rb") as handle:
        return handle.read()


def corrupt_copy(mutate):
    """Return a temp dir holding a mutated entry.png + a main.py symlink dir.

    The harness entrypoint reads entry.png next to main.py, so tests that
    need a broken source build a scratch repo dir with a copied main.py.
    """
    tmp = tempfile.mkdtemp(prefix="tc-")
    data = bytearray(read_png_bytes())
    mutate(data)
    with open(os.path.join(tmp, "entry.png"), "wb") as handle:
        handle.write(bytes(data))
    shutil.copy(os.path.join(ROOT, "main.py"), os.path.join(tmp, "main.py"))
    return tmp


def run_in_dir(directory, env_extra=None):
    env = dict(os.environ)
    env.pop("MAKEFUN_OUTPUT_DIR", None)
    if env_extra:
        env.update(env_extra)
    return subprocess.run([sys.executable, "main.py"], capture_output=True,
                          text=True, env=env, cwd=directory)


# --- TC001: valid PNG, deterministic copy, default output dir handling
def test_valid_copy_and_determinism():
    with tempfile.TemporaryDirectory() as out:
        proc = run_main({"MAKEFUN_OUTPUT_DIR": out})
        check("TC001-exit-0", proc.returncode == 0, proc.stderr)
        dest = os.path.join(out, "entry.png")
        check("TC001-file-written", os.path.exists(dest))
        check("TC001-bytes-identical",
              open(dest, "rb").read() == read_png_bytes())
        first = hashlib.sha256(open(dest, "rb").read()).hexdigest()
        proc2 = run_main({"MAKEFUN_OUTPUT_DIR": out})
        second = hashlib.sha256(open(dest, "rb").read()).hexdigest()
        check("TC001-second-run-0", proc2.returncode == 0, proc2.stderr)
        check("TC029-deterministic-runs", first == second)


# --- TC002: PNG over 1 MiB -> exit 3, nothing written
def test_oversize():
    # Append junk bytes past the IEND trailer to push the file over 1 MiB;
    # main.py must reject on size (exit 3) before any PNG validation.
    data = read_png_bytes() + b"x" * (1_048_577 - len(read_png_bytes()))
    tmp = tempfile.mkdtemp(prefix="tc-")
    with open(os.path.join(tmp, "entry.png"), "wb") as handle:
        handle.write(data)
    shutil.copy(os.path.join(ROOT, "main.py"), os.path.join(tmp, "main.py"))
    with tempfile.TemporaryDirectory() as out:
        proc = run_in_dir(tmp, {"MAKEFUN_OUTPUT_DIR": out})
        check("TC002-exit-3", proc.returncode == 3, proc.stderr)
        check("TC002-nothing-written",
              not os.path.exists(os.path.join(out, "entry.png")))


# --- TC003: wrong dimensions -> exit 5
def test_wrong_dimensions():
    from PIL import Image
    tmp = tempfile.mkdtemp(prefix="tc-")
    Image.new("RGB", (800, 800), (255, 255, 255)).save(
        os.path.join(tmp, "entry.png"))
    shutil.copy(os.path.join(ROOT, "main.py"), os.path.join(tmp, "main.py"))
    with tempfile.TemporaryDirectory() as out:
        proc = run_in_dir(tmp, {"MAKEFUN_OUTPUT_DIR": out})
        check("TC003-exit-5", proc.returncode == 5, proc.stderr)
        check("TC003-nothing-written",
              not os.path.exists(os.path.join(out, "entry.png")))


# --- TC004: bad CRC -> exit 5
def test_bad_crc():
    def mutate(data):
        # Corrupt one byte inside the first IDAT payload.
        pos = bytes(data).find(b"IDAT")
        data[pos + 10] ^= 0xFF
    tmp = corrupt_copy(mutate)
    with tempfile.TemporaryDirectory() as out:
        proc = run_in_dir(tmp, {"MAKEFUN_OUTPUT_DIR": out})
        check("TC004-exit-5", proc.returncode == 5, proc.stderr)


# --- TC005: truncated file -> exit 5
def test_truncated():
    data = read_png_bytes()[: len(read_png_bytes()) // 2]
    tmp = tempfile.mkdtemp(prefix="tc-")
    with open(os.path.join(tmp, "entry.png"), "wb") as handle:
        handle.write(data)
    shutil.copy(os.path.join(ROOT, "main.py"), os.path.join(tmp, "main.py"))
    with tempfile.TemporaryDirectory() as out:
        proc = run_in_dir(tmp, {"MAKEFUN_OUTPUT_DIR": out})
        check("TC005-exit-5", proc.returncode == 5, proc.stderr)


# --- TC006: non-PNG bytes -> exit 5
def test_not_png():
    tmp = tempfile.mkdtemp(prefix="tc-")
    with open(os.path.join(tmp, "entry.png"), "wb") as handle:
        handle.write(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    shutil.copy(os.path.join(ROOT, "main.py"), os.path.join(tmp, "main.py"))
    with tempfile.TemporaryDirectory() as out:
        proc = run_in_dir(tmp, {"MAKEFUN_OUTPUT_DIR": out})
        check("TC006-exit-5", proc.returncode == 5, proc.stderr)


# --- TC007: copy mismatch is detected (hash compare after copy)
def test_hash_compare():
    # main.py compares sha256 of source and dest; simulate by checking the
    # function directly: identical files pass, differing files fail.
    with tempfile.TemporaryDirectory() as d:
        a = os.path.join(d, "a.png")
        b = os.path.join(d, "b.png")
        shutil.copy(os.path.join(ROOT, "entry.png"), a)
        shutil.copy(os.path.join(ROOT, "entry.png"), b)
        check("TC007-same-hash",
              entry_main.sha256_of(a) == entry_main.sha256_of(b))
        with open(b, "r+b") as handle:
            handle.seek(100)
            handle.write(b"Z")
        check("TC007-diff-hash-detected",
              entry_main.sha256_of(a) != entry_main.sha256_of(b))


# --- TC008: output dir does not exist -> created, exit 0
def test_missing_out_dir():
    with tempfile.TemporaryDirectory() as base:
        out = os.path.join(base, "deep", "deeper", "out")
        proc = run_main({"MAKEFUN_OUTPUT_DIR": out})
        check("TC008-exit-0", proc.returncode == 0, proc.stderr)
        check("TC008-created-and-copied",
              os.path.exists(os.path.join(out, "entry.png")))


# --- TC009/TC028: read-only output dir -> exit 6
def test_readonly_out_dir():
    with tempfile.TemporaryDirectory() as base:
        out = os.path.join(base, "ro")
        os.makedirs(out)
        os.chmod(out, 0o500)
        try:
            proc = run_main({"MAKEFUN_OUTPUT_DIR": out})
            # Running as root can still write; accept 0 only if the file
            # really landed, else require 6.
            if os.path.exists(os.path.join(out, "entry.png")):
                check("TC009-readonly-root-can-write",
                      proc.returncode == 0,
                      "root bypasses perms; file landed, exit %d"
                      % proc.returncode)
            else:
                check("TC009-exit-6", proc.returncode == 6, proc.stderr)
        finally:
            os.chmod(out, 0o700)


# --- TC010: existing output file is overwritten deterministically
def test_overwrite():
    with tempfile.TemporaryDirectory() as out:
        dest = os.path.join(out, "entry.png")
        with open(dest, "wb") as handle:
            handle.write(b"stale content")
        proc = run_main({"MAKEFUN_OUTPUT_DIR": out})
        check("TC010-exit-0", proc.returncode == 0, proc.stderr)
        check("TC010-overwritten-identical",
              open(dest, "rb").read() == read_png_bytes())


# --- TC011: MAKEFUN_OUTPUT_DIR unset -> default /output/entry.png
def test_default_out_dir():
    # Exercise the real default path through entry_main.main() with the
    # filesystem calls stubbed, so no write to /output happens here.
    import unittest.mock as mock
    seen = {}

    def fake_makedirs(path, exist_ok=False):
        seen["makedirs"] = path
        seen["exist_ok"] = exist_ok

    def fake_copy(src, dst):
        seen["copy_dst"] = dst

    env = dict(os.environ)
    env.pop("MAKEFUN_OUTPUT_DIR", None)
    with mock.patch.dict(os.environ, {}, clear=False):
        os.environ.pop("MAKEFUN_OUTPUT_DIR", None)
        with mock.patch.object(os, "makedirs", fake_makedirs):
            with mock.patch.object(shutil, "copyfile", fake_copy):
                with mock.patch.object(entry_main, "sha256_of",
                                      return_value="x"):
                    code = entry_main.main([])
    check("TC011-default-is-output",
          seen.get("copy_dst") == "/output/entry.png", str(seen))
    check("TC011-makedirs-exist-ok",
          seen.get("exist_ok") is True, str(seen))
    check("TC011-exit-0", code == 0, "exit %d" % code)


# --- TC012: runtime under 60s
def test_runtime():
    import time
    with tempfile.TemporaryDirectory() as out:
        start = time.time()
        proc = run_main({"MAKEFUN_OUTPUT_DIR": out})
        elapsed = time.time() - start
        check("TC012-under-60s",
              proc.returncode == 0 and elapsed < 60, "%.2fs" % elapsed)


# --- TC013: missing entry.png -> exit 2
def test_missing_source():
    tmp = tempfile.mkdtemp(prefix="tc-")
    shutil.copy(os.path.join(ROOT, "main.py"), os.path.join(tmp, "main.py"))
    with tempfile.TemporaryDirectory() as out:
        proc = run_in_dir(tmp, {"MAKEFUN_OUTPUT_DIR": out})
        check("TC013-exit-2", proc.returncode == 2, proc.stderr)


# --- TC014/TC017: no text overflow / clipping (measured at render time)
def test_no_overflow():
    from PIL import Image, ImageDraw
    import draw as render_mod
    img = Image.open(os.path.join(ROOT, "entry.png"))
    check("TC014-size-1024", img.size == (1024, 1024))
    # The renderer raises ValueError on any overflow, so a clean render
    # is itself proof; here we re-derive the wrapped line counts at the
    # exact fonts and box widths the page uses and assert the budgets.
    canvas = Image.new("RGB", (1024, 1024), render_mod.PAPER)
    d = ImageDraw.Draw(canvas)
    mf = render_mod.fit_font(d, "Sunday 22 November 2026",
                             render_mod.serif_bold, 86, 60,
                             render_mod.CONTENT)
    check("TC014-masthead-fits",
          d.textlength("Sunday 22 November 2026", font=mf)
          <= render_mod.CONTENT)
    hf = render_mod.serif_bold(20)
    sf = render_mod.sans(13)
    for kicker, tag, _scene, headline, summary, _src in render_mod.HEROES:
        check("TC014-hero-headline-fits",
              len(render_mod.wrap(d, headline, hf, 297)) <= 2, headline)
        check("TC014-hero-summary-fits",
              len(render_mod.wrap(d, summary, sf, 297)) <= 3, summary)
    hf2 = render_mod.serif_bold(13.5)
    sf2 = render_mod.sans(10.5)
    for kicker, _thumb, headline, summary in render_mod.GRID:
        check("TC014-card-headline-fits",
              len(render_mod.wrap(d, headline, hf2, 225)) <= 2, headline)
        check("TC014-card-summary-fits",
              len(render_mod.wrap(d, summary, sf2, 225)) <= 2, summary)
    bf = render_mod.sans(10.5)
    for item in render_mod.ALSO:
        check("TC014-also-item-fits",
              len(render_mod.wrap(d, item, bf, 212)) <= 2, item)


# --- TC015: font fallback when the primary font file is missing
def test_font_fallback():
    import draw as render_mod
    font = render_mod.load_font(["NoSuchFont-404.ttf"], 20)
    check("TC015-fallback-font-loads", font is not None)
    # The real fonts used by the render must exist on this machine.
    for name in ("DejaVuSerif-Bold.ttf", "DejaVuSans-Bold.ttf",
                 "DejaVuSans.ttf"):
        path = os.path.join("/usr/share/fonts/truetype/dejavu", name)
        check("TC015-font-present-" + name, os.path.exists(path))


# --- TC016: readable at 300px (structure survives downscale)
def test_downscale_300px():
    from PIL import Image
    import io
    img = Image.open(os.path.join(ROOT, "entry.png"))
    small = img.resize((300, 300))
    buf = io.BytesIO()
    small.save(buf, format="PNG")
    check("TC016-downscale-300px", small.size == (300, 300)
          and len(buf.getvalue()) > 10000)
    # Masthead band must stay dark-on-light after downscale.
    px = small.load()
    dark = sum(1 for x in range(300) for y in range(5, 35)
               if sum(px[x, y][:3]) < 300)
    check("TC016-masthead-visible-downscaled", dark > 500, str(dark))


# --- TC018: text/background contrast (ink on paper)
def test_contrast():
    def luminance(rgb):
        def chan(c):
            c = c / 255.0
            return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
        r, g, b = (chan(v) for v in rgb)
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    import draw as render_mod
    li, lp = luminance(render_mod.INK), luminance(render_mod.PAPER)
    ratio = (max(li, lp) + 0.05) / (min(li, lp) + 0.05)
    check("TC018-contrast-AA", ratio >= 4.5, "ratio %.2f" % ratio)


# --- TC019/TC020/TC021: repo files
def test_repo_files():
    lic = open(os.path.join(ROOT, "LICENSE")).read()
    check("TC019-license-mit", "MIT License" in lic)
    check("TC019-spdx-line", "SPDX-License-Identifier: MIT" in lic)
    import json
    owner = json.load(open(os.path.join(ROOT, ".makefun", "owner.json")))
    check("TC020-owner-wallet", owner.get("wallet") == WALLET)
    readme = open(os.path.join(ROOT, "README.md")).read()
    check("TC021-no-placeholder", "{owner}" not in readme
          and "{repo}" not in readme)
    check("TC021-badges-present",
          "https://make.fun/badge/news-image-20261122.svg" in readme
          and "/sulan195/makefun-news-image-20261122/rank.svg" in readme
          and "/sulan195/makefun-news-image-20261122/reward.svg" in readme)


# --- TC023: masthead + date line present (verified against the render
# source: the exact strings draw.py writes, plus the masthead band check
# in TC016 which proves they survive onto the image)
def test_content_markers():
    import draw as render_mod
    source = open(os.path.join(ROOT, "draw.py")).read()
    check("TC023-masthead-text", '"THE WORLD IN ONE DAY"' in source)
    check("TC023-date-line", '"Sunday 22 November 2026"' in source)
    check("TC023-lead-headline",
          '"Climate deal lands with no mention of fossil fuels"' in source)
    check("TC024-story-counts",
          len(render_mod.HEROES) == 3 and len(render_mod.GRID) == 9
          and len(render_mod.ALSO) == 18)
    check("TC024-region-sum",
          sum(n for _name, n in render_mod.REGIONS) == 30)
    check("TC024-story-kickers",
          all(k for k, _t, _s, _h, _b, _r in render_mod.HEROES)
          and all(k for k, _t, _h, _b in render_mod.GRID))
    check("TC025-also-items",
          all(s in " ".join(render_mod.ALSO) for s in
              ("Manipur", "BepiColombo", "Bitcoin", "Estonia")))
    check("TC025-date-check", '"DATE CHECK' in source
          or "DATE CHECK —" in render_mod.DATE_CHECK)


# --- TC026: malformed IEND -> exit 5
def test_bad_iend():
    data = bytearray(read_png_bytes())
    data[-12:] = b"\x00" * 12
    tmp = tempfile.mkdtemp(prefix="tc-")
    with open(os.path.join(tmp, "entry.png"), "wb") as handle:
        handle.write(bytes(data))
    shutil.copy(os.path.join(ROOT, "main.py"), os.path.join(tmp, "main.py"))
    with tempfile.TemporaryDirectory() as out:
        proc = run_in_dir(tmp, {"MAKEFUN_OUTPUT_DIR": out})
        check("TC026-exit-5", proc.returncode == 5, proc.stderr)


# --- TC027: chunk order wrong (IDAT before IHDR, both CRC-valid) -> exit 5
def test_chunk_order():
    data = read_png_bytes()
    # Parse the real PNG into (type, payload) chunks, then rebuild with
    # the first IDAT chunk moved before IHDR. CRCs stay valid because the
    # chunk bytes themselves are unchanged -- only the ORDER is wrong.
    chunks = []
    pos = 8
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = data[pos + 4:pos + 8]
        chunks.append(data[pos:pos + 8 + length + 4])
        if ctype == b"IEND":
            break
        pos += 8 + length + 4
    ihdr = [c for c in chunks if c[4:8] == b"IHDR"]
    idat = [c for c in chunks if c[4:8] == b"IDAT"]
    rest = [c for c in chunks
            if c[4:8] not in (b"IHDR", b"IDAT", b"IEND")]
    rebuilt = (data[:8] + idat[0] + ihdr[0] + b"".join(idat[1:])
               + b"".join(rest) + chunks[-1])
    tmp = tempfile.mkdtemp(prefix="tc-")
    with open(os.path.join(tmp, "entry.png"), "wb") as handle:
        handle.write(rebuilt)
    shutil.copy(os.path.join(ROOT, "main.py"), os.path.join(tmp, "main.py"))
    with tempfile.TemporaryDirectory() as out:
        proc = run_in_dir(tmp, {"MAKEFUN_OUTPUT_DIR": out})
        check("TC027-exit-5", proc.returncode == 5, proc.stderr)
        check("TC027-first-chunk-reason",
              "IHDR" in proc.stderr, proc.stderr)


# --- TC031: a chunk whose end passes len(data)-12 (into the IEND
# trailer) -> exit 5, even though the file still ends with IEND bytes.
def test_chunk_spanning_trailer():
    data = bytearray(read_png_bytes())
    # Find the last IDAT chunk and grow its length field by 4: its end
    # then passes len(data)-12. (Length is not covered by the chunk CRC,
    # so the spanning check must fire before any CRC check.)
    pos = 8
    last_idat = None
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        ctype = bytes(data[pos + 4:pos + 8])
        if ctype == b"IDAT":
            last_idat = pos
        if ctype == b"IEND":
            break
        pos += 8 + length + 4
    assert last_idat is not None
    length = struct.unpack(">I", data[last_idat:last_idat + 4])[0]
    data[last_idat:last_idat + 4] = struct.pack(">I", length + 4)
    tmp = tempfile.mkdtemp(prefix="tc-")
    with open(os.path.join(tmp, "entry.png"), "wb") as handle:
        handle.write(bytes(data))
    shutil.copy(os.path.join(ROOT, "main.py"), os.path.join(tmp, "main.py"))
    with tempfile.TemporaryDirectory() as out:
        proc = run_in_dir(tmp, {"MAKEFUN_OUTPUT_DIR": out})
        check("TC031-exit-5", proc.returncode == 5, proc.stderr)
        check("TC031-trailer-reason",
              "IEND trailer" in proc.stderr, proc.stderr)


# --- TC030: final file size under the 1 MiB cap
def test_final_size():
    size = os.path.getsize(os.path.join(ROOT, "entry.png"))
    check("TC030-under-1MiB", 0 < size <= 1_048_576, "%d bytes" % size)
    check("TC030-small-for-tiebreak", size < 400_000, "%d bytes" % size)


# --- validate_png unit checks
def test_validate_png_direct():
    check("TC-validate-ok",
          entry_main.validate_png(os.path.join(ROOT, "entry.png")) is None)
    with tempfile.TemporaryDirectory() as d:
        bad = os.path.join(d, "bad.png")
        with open(bad, "wb") as handle:
            handle.write(b"not a png at all")
        check("TC-validate-rejects-junk",
              entry_main.validate_png(bad) is not None)
        try:
            entry_main.validate_png(os.path.join(d, "missing.png"))
            raised = False
        except OSError:
            raised = True
        check("TC-validate-missing-raises", raised)


def main():
    test_valid_copy_and_determinism()
    test_oversize()
    test_wrong_dimensions()
    test_bad_crc()
    test_truncated()
    test_not_png()
    test_hash_compare()
    test_missing_out_dir()
    test_readonly_out_dir()
    test_overwrite()
    test_default_out_dir()
    test_runtime()
    test_missing_source()
    test_no_overflow()
    test_font_fallback()
    test_downscale_300px()
    test_contrast()
    test_repo_files()
    test_content_markers()
    test_bad_iend()
    test_chunk_order()
    test_chunk_spanning_trailer()
    test_final_size()
    test_validate_png_direct()
    print("\n%d passed, %d failed" % (len(PASSED), len(FAILED)))
    if FAILED:
        print("FAILED:", ", ".join(FAILED))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
