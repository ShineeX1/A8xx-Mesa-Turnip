#!/usr/bin/env python3
"""Write the combined release's body from what this run actually produced.

Inputs:
  --info DIR      release-info/ from the resolve job (tag, Mesa commit, versions, dates)
  --zips DIR      every driver zip the build legs uploaded
  --reports DIR   the verify_driver_zip.py report of each leg that got as far as uploading
  --out FILE      release body (Markdown)
  --assets FILE   the zip paths to attach, one per line: only zips whose report says verified,
                  whose sha256 matches the downloaded file and whose Mesa commit is this run's

Exit 3 when the standard Android driver is not among them: without it there is no release
(same rule as before the Wayland legs existed). Anything else missing is written into the body.
"""
import argparse
import glob
import hashlib
import json
import os
import re
import sys

REPO_BLOB = "https://github.com/{repo}/blob/{ref}/{path}"

DRIVERS = [
    {
        "variant": "regular", "suffix": "", "label": "A6xx / A7xx", "kind": "Standard",
        "gpus": "Adreno 6xx / 7xx: Snapdragon 600-800 series, 7 Gen, 8 Gen 1-3",
    },
    {
        "variant": "a8xx", "suffix": "-A8xx", "label": "A8xx", "kind": "Snapdragon 8 Elite",
        "gpus": "Adreno 840 / 830 / 829 / 825 / 810: Snapdragon 8 Elite",
    },
    {
        "variant": "710-720-test", "suffix": "-710-720-Test", "label": "A710 / A720 / A722", "kind": "Experimental",
        "gpus": "Adreno 710 / 720 / 722 (unverified on hardware)",
    },
]


def read_info(d, name):
    try:
        with open(os.path.join(d, name + ".txt")) as f:
            return f.read().strip()
    except OSError:
        return ""


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def md_cell(s):
    return s.replace("|", "\\|").replace("<", "&lt;")


def mib(n):
    return f"{n / (1024 * 1024):.1f} MB"


def patch_commits(path):
    """[(subject, author)] from a git format-patch series."""
    out, author = [], None
    try:
        text = open(path, encoding="utf-8", errors="replace").read()
    except OSError:
        return out
    for line in text.splitlines():
        if line.startswith("From: "):
            author = re.sub(r"\s*<[^>]*>\s*$", "", line[6:]).strip()
        elif line.startswith("Subject: "):
            subj = re.sub(r"^\[PATCH[^\]]*\]\s*", "", line[9:]).strip()
            out.append((subj, author or "unknown"))
            author = None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--info", required=True)
    ap.add_argument("--zips", required=True)
    ap.add_argument("--reports", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--assets", required=True)
    ap.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "The412Banner/Banners-Turnip"))
    ap.add_argument("--ref", default="A8xx", help="branch the patch links point at")
    ap.add_argument("--workdir", default=".", help="repo checkout (patch files)")
    a = ap.parse_args()

    tag = read_info(a.info, "tag")
    githash_full = read_info(a.info, "githash_full")
    if not tag or not re.fullmatch(r"[0-9a-f]{40}", githash_full):
        print("release-info is incomplete (tag / githash_full)", file=sys.stderr)
        return 2
    info = {k: read_info(a.info, k) for k in
            ("mesa_version", "build_date", "githash", "commit_date", "commit_title", "vulkan_version")}
    mesa_url = f"https://gitlab.freedesktop.org/mesa/mesa/-/commit/{githash_full}"

    reports = {}
    for p in glob.glob(os.path.join(a.reports, "**", "*.json"), recursive=True):
        try:
            r = json.load(open(p))
            reports[r["zip"]] = r
        except Exception as e:  # noqa: BLE001
            print(f"ignoring unreadable report {p}: {e}", file=sys.stderr)

    # Status of each of the six files.
    legs = {}
    assets = []
    for drv in DRIVERS:
        for platform in ("android", "wayland"):
            name = f"Turnip-{tag}{drv['suffix']}{'-Wayland' if platform == 'wayland' else ''}.zip"
            path = os.path.join(a.zips, name)
            rep = reports.get(name)
            why = ""
            if not os.path.isfile(path):
                why = "did not build"
            elif rep is None:
                why = "no verification report"
            elif not rep.get("verified"):
                why = "failed verification"
            elif rep.get("platform") != platform:
                why = "report is for another platform"
            elif rep.get("mesa_commit") != githash_full:
                why = f"built Mesa {str(rep.get('mesa_commit'))[:10]}, not this release's commit"
            elif rep.get("sha256") != sha256(path):
                why = "zip differs from the verified one"
            ok = not why
            legs[(drv["variant"], platform)] = {"name": name, "ok": ok, "why": why, "report": rep,
                                                "size": os.path.getsize(path) if os.path.isfile(path) else 0}
            if ok:
                assets.append(path)
            print(f"{name}: {'OK' if ok else 'NOT INCLUDED (' + why + ')'}")

    unexpected = sorted(set(os.path.basename(p) for p in glob.glob(os.path.join(a.zips, "*.zip")))
                        - {l["name"] for l in legs.values()})
    for u in unexpected:
        print(f"::warning::unexpected zip {u} is not attached")

    with open(a.assets, "w") as f:
        f.write("".join(p + "\n" for p in assets))

    std = legs[("regular", "android")]
    if not std["ok"]:
        print(f"::error::Standard (A6xx/A7xx) Android driver {std['name']}: {std['why']} - nothing to publish.")
        return 3

    L = []
    w = L.append
    android_ok = [d for d in DRIVERS if legs[(d["variant"], "android")]["ok"]]
    android_bad = [d for d in DRIVERS if not legs[(d["variant"], "android")]["ok"]]
    wayland_bad = [d for d in DRIVERS if not legs[(d["variant"], "wayland")]["ok"]]

    w("> ⚠️ **AUTOMATED BUILD — Not guaranteed stable. Use at your own risk.**")
    w("> Built and checked by CI from the Mesa commit below. **Not tested on a device.**")
    w("")
    if android_bad:
        w(f"> ⚠️ **Partial release — {len(android_ok)} of 3 Android drivers.** These failed this run and are NOT included:")
        for d in android_bad:
            leg = legs[(d["variant"], "android")]
            w(f"> - {d['label']} (`{leg['name']}`): {leg['why']}")
        w("")
    for d in wayland_bad:
        leg = legs[(d["variant"], "wayland")]
        also = " The Android zip of this driver is not affected." if legs[(d["variant"], "android")]["ok"] else ""
        w(f"> ⚠️ **Wayland build of {d['label']} failed this run** (`{leg['name']}`: {leg['why']}) and is NOT included.{also}")
        w("")
    w("---")
    w("")
    w("### Mesa Upstream")
    w("")
    w("| | |")
    w("| :--- | :--- |")
    w(f"| **Version** | {info['mesa_version']} |")
    w(f"| **Commit** | [`{info['githash']}`]({mesa_url}) |")
    w(f"| **Vulkan version** | {info['vulkan_version']} |")
    w(f"| **Commit date** | {info['commit_date']} |")
    w(f"| **Commit title** | {md_cell(info['commit_title'])} |")
    w(f"| **Build date** | {info['build_date']} |")
    w("")
    w("Every driver in this release, Android and Wayland, is built from this one commit.")
    w("")
    w("---")
    w("")
    w("### Which file?")
    w("")
    w("| Driver | GPUs | Android zip (X11 / AdrenoTools) | Wayland zip (Bannerlator Wayland) |")
    w("| :--- | :--- | :--- | :--- |")

    def cell(variant, platform):
        leg = legs[(variant, platform)]
        return f"`{leg['name']}`" if leg["ok"] else "❌ failed this run"

    for d in DRIVERS:
        w(f"| **{d['label']}** ({d['kind']}) | {d['gpus']} | {cell(d['variant'], 'android')} | {cell(d['variant'], 'wayland')} |")
    w("")
    w("- **Android zip** → Bannerlator / Winlator (or any AdrenoTools app): import it as a **GPU driver**. "
      "This is the driver for X11 containers.")
    w("- **Wayland zip** → Bannerlator **Wayland containers** only: **Import Wayland game driver (.zip)**, then pick it "
      "as the container's Wayland game driver. It is a Linux-style Vulkan ICD: it does not load as an AdrenoTools "
      "driver, and an Android zip does not work as a Wayland game driver.")
    w("")
    w("---")
    w("")

    def gpu_line(variant, prefix_re, what):
        names = set()
        for platform in ("android", "wayland"):
            leg = legs[(variant, platform)]
            if leg["ok"]:
                names |= {n for n in leg["report"].get("gpu_names", []) if re.match(prefix_re, n)}
        if names:
            w(f"{what} in this build: " + ", ".join(f"`{n}`" for n in sorted(names)) + ".")
            w("")

    # --- A6xx / A7xx
    w("### A6xx / A7xx — Standard")
    w("")
    w("The everyday driver for most Adreno phones — **Snapdragon 600–800 series** (7 Gen, 8 Gen 1–3). Built straight "
      "from the latest upstream Mesa with no extra patches, so it's the safest, most-compatible pick. Not sure which "
      "file to grab? It's this one.")
    w("")
    w("<details>")
    w("<summary>Technical details</summary>")
    w("")
    w("Pure Mesa `main` at the commit above, no source patches. The Android build applies three inline NDK r29 "
      "compatibility fixes at build time:")
    w("")
    w("- `buffer_handle_t` typedef fix (`native_handle.h`)")
    w("- `hnd->handle` void-cast fix (`u_gralloc_fallback.c`)")
    w("- `native_buffer->handle` cast fix (`vk_android.c`)")
    w("")
    w("The Wayland build adds only the Wayland build changes listed under **Wayland builds** below.")
    w("")
    w("</details>")
    w("")
    w("---")
    w("")

    # --- A8xx
    a8 = legs[("a8xx", "android")]["report"] or legs[("a8xx", "wayland")]["report"] or {}
    a8_patch = a8.get("extra_patch") or "patches/a8xx_gen8.patch"
    a8_scripts = [s for s in (a8.get("extra_script") or "patches/a8xx_shared_mem.py").split(":") if s]
    commits = patch_commits(os.path.join(a.workdir, a8_patch))
    w("### A8xx — Snapdragon 8 Elite")
    w("")
    w("For the newest **Snapdragon 8 Elite** phones — **Adreno 840 / 830 / 829 / 825 / 810**. whitebelyash's "
      "`turnip/gen8` A8xx stack (as shipped in [tu_v29](https://github.com/whitebelyash/AdrenoToolsDrivers/releases/tag/tu_v29) "
      "and [StevenMXZ v33](https://github.com/StevenMXZ/Adreno-Tools-Drivers/releases/tag/v33)), rebuilt on the latest "
      "Mesa. Still experimental, so a couple of tips:")
    w("")
    w("- **A830 looking glitchy?** Add `TU_DEBUG=sysmem` to your environment.")
    w("- **A game won't start on Qualcomm?** Try `TU_DEBUG=deck_emu` (spoofs a Steam Deck).")
    w("")
    w("<details>")
    w("<summary>Technical details — patches and provenance</summary>")
    w("")
    gpu_line("a8xx", r"^Adreno \(TM\) 8", "Adreno 8xx entries")
    patch_url = REPO_BLOB.format(repo=a.repo, ref=a.ref, path=a8_patch)
    if commits:
        w(f"**[{os.path.basename(a8_patch)}]({patch_url}) — {len(commits)} commits** from "
          "[whitebelyash/mesa-unified](https://github.com/whitebelyash/mesa-unified) `turnip/gen8`:")
        w("")
        for subj, author in commits:
            w(f"- {md_cell(subj)} — *{md_cell(author)}*")
        w("")
    for s in a8_scripts:
        s_url = REPO_BLOB.format(repo=a.repo, ref=a.ref, path=s)
        if os.path.basename(s) == "a8xx_shared_mem.py":
            w(f"Plus [`a8xx_shared_mem.py`]({s_url}): `cs_shared_mem_size` 32 KiB → 64 KiB on every device entry in "
              "`freedreno_devices.py` (whitebelyash's \"increase shared mem size\" commit).")
        else:
            w(f"Plus [`{os.path.basename(s)}`]({s_url}).")
        w("")
    try:
        if "force_render_mode_reason" in open(os.path.join(a.workdir, a8_patch), errors="replace").read():
            w("**Banners-Turnip local delta:** the series' `disable_gmem` hunk uses `force_render_mode_reason` "
              "(Mesa's current name for `gmem_disable_reason`) so it builds against current Mesa `main`.")
            w("")
    except OSError:
        pass
    w("</details>")
    w("")
    w("---")
    w("")

    # --- 710/720/722
    t7 = legs[("710-720-test", "android")]["report"] or legs[("710-720-test", "wayland")]["report"] or {}
    t7_scripts = [s for s in (t7.get("extra_script") or "patches/a710-720.py").split(":") if s]
    w("### A710 / A720 / A722 — Experimental")
    w("")
    w("An experimental test build with its own **Adreno 710 / 720 / 722** entries: tuned GPU properties and magic "
      "registers from hardware traces, replacing any upstream entry for those chip IDs. ⚠️ **Not yet verified on "
      "real hardware.** If you try it:")
    w("")
    w("- Set `TU_DEBUG=sysmem` in your emulator/app environment.")
    w("- **Winlator users:** also set `WRAPPER_BLIT=1`.")
    w("")
    w("It only activates on those chip IDs; the standard zip is not affected.")
    w("")
    w("<details>")
    w("<summary>Technical details</summary>")
    w("")
    gpu_line("710-720-test", r"^FD7(10|20|22)$", "A710/A720/A722 entries")
    for s in t7_scripts:
        s_url = REPO_BLOB.format(repo=a.repo, ref=a.ref, path=s)
        src = ""
        try:
            src = open(os.path.join(a.workdir, s), errors="replace").read()
        except OSError:
            pass
        ids = [(g, c) for g, c in (("A710", "0x07010000"), ("A720", "0x43020000"), ("A722", "0x43020100")) if c in src]
        w(f"Pure Mesa `main` plus [`{os.path.basename(s)}`]({s_url}) (from [Vauzi-17/710](https://github.com/Vauzi-17/710)), "
          "which writes those per-GPU entries into `freedreno_devices.py`"
          + (": " + ", ".join(f"**{g}** (`{c}`)" for g, c in ids) if ids else "") + ".")
        w("")
    w("</details>")
    w("")
    w("---")
    w("")

    # --- Wayland
    wl_reports = [legs[(d["variant"], "wayland")]["report"] for d in DRIVERS if legs[(d["variant"], "wayland")]["ok"]]
    w("### Wayland builds")
    w("")
    if not wl_reports:
        w("No Wayland build succeeded this run, so this release has no `-Wayland.zip` files.")
        w("")
    else:
        w("The `-Wayland.zip` files are the same drivers — same Mesa commit, same per-driver patches and scripts as the "
          "Android zips — built the way the Turnips in Bannerlator's Wayland Proton layer are built: a Linux-style Vulkan "
          "ICD on bionic that the Vulkan loader inside the Wine container loads. Each zip holds "
          "`libvulkan_freedreno.so`, the `libdrm.so` it was linked against, and `meta.json`.")
        w("")
        r0 = wl_reports[0]
        termux = r0.get("termux", {})
        wp = r0.get("wayland_patches", {})
        kgsl = {r.get("wayland_patches", {}).get("kgsl_wait_assert") for r in wl_reports}
        w("<details>")
        w("<summary>Technical details</summary>")
        w("")
        w(f"- NDK {r0.get('ndk', '?').replace('android-ndk-', '')}, API {r0.get('api', '?')}, "
          "`-Dplatforms=wayland -Dfreedreno-kmds=msm,kgsl`, Turnip target only, not stripped.")
        w(f"- Linked against Termux libwayland {termux.get('libwayland', '?')} and libdrm {termux.get('libdrm', '?')}. "
          "`libwayland-client.so` comes from Bannerlator's Wayland layer.")
        w("- Wayland-only source changes on top of each driver's recipe:")
        w("  - Mesa's Android detection off (a Linux-style build on bionic, like Termux's Mesa)")
        w("  - `no_pthread_cancel.py`: bionic has no `pthread_cancel` (VK_KHR_display WSI threads)")
        if kgsl == {"applied"}:
            w("  - KGSL timestamp wait: a warning instead of an assert on an unexpected errno")
        elif kgsl == {"not-found"}:
            w("  - KGSL timestamp wait: no change needed (Mesa no longer has that assert)")
        w(f"  - `banner_ahb_wsi.py`: Bannerlator zero-copy presentation (`banner_ahb_v1`: swapchain images on gralloc "
          f"buffers, UBWC where the device allows), from {wp.get('source', 'the wayland branch')}")
        w("- CI checks every Wayland zip before attaching it: bionic `libc.so` + `libwayland-client.so` + `libdrm.so` "
          "linked and no libhardware / libnativewindow / libsync / glibc, `vk_icdGetInstanceProcAddr` exported, `wl_` "
          "symbols present, every libwayland-client / libdrm symbol it imports present in the versions Bannerlator's "
          "Wayland layer ships, and the zip layout Bannerlator's Wayland game driver import takes.")
        w("")
        w("| Wayland zip | NEEDED | `vk_icdGetInstanceProcAddr` | `wl_` symbols |")
        w("| :--- | :--- | :--- | :--- |")
        for r in wl_reports:
            exported = "exported" if "vk_icdGetInstanceProcAddr" in r.get("vk_icd_exports", []) else "missing"
            w(f"| `{r['zip']}` | `{' '.join(r.get('needed', []))}` | {exported} | {r.get('wl_symbols', 0)} |")
        w("")
        w("</details>")
        w("")
    w("---")
    w("")
    w("### Files")
    w("")
    w("| File | Size | SHA-256 |")
    w("| :--- | :--- | :--- |")
    for d in DRIVERS:
        for platform in ("android", "wayland"):
            leg = legs[(d["variant"], platform)]
            if leg["ok"]:
                w(f"| `{leg['name']}` | {mib(leg['size'])} | `{leg['report']['sha256']}` |")
    w("")
    w("---")
    w("")
    w("### Installation")
    w("")
    w("- **Bannerlator / Winlator / AdrenoTools apps (X11):** load the **Android** ZIP in GPU driver settings")
    w("- **BannerHub / BCI:** Component Manager → Add New Component → select the **Android** ZIP")
    w("- **Bannerlator Wayland containers:** **Import Wayland game driver (.zip)** → select the **Wayland** ZIP, then pick "
      "it as the container's Wayland game driver")

    with open(a.out, "w") as f:
        f.write("\n".join(L) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
