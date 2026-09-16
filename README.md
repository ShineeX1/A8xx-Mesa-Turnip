<p align="center">
  <img src="logo.png" alt="Banners-Turnip" width="600"/>
</p>

# Banners-Turnip
[![Discord](https://img.shields.io/badge/Discord-Join%20Server-5865F2?logo=discord&logoColor=white)](https://discord.gg/n8S4G2WZQ4)


> Automated, bleeding-edge builds of the [Mesa Turnip](https://docs.mesa3d.org/drivers/freedreno.html) Vulkan driver, compiled directly from the latest upstream Mesa commits. Every release ships each driver twice: for [AdrenoTools](https://github.com/K11MCH1/AdrenoToolsDrivers)-compatible apps (X11), and for Bannerlator Wayland containers.

[![Build Turnip (Combined)](https://github.com/The412Banner/Banners-Turnip/actions/workflows/turnip_build_combined.yml/badge.svg?branch=A8xx)](https://github.com/The412Banner/Banners-Turnip/actions/workflows/turnip_build_combined.yml)
[![Latest Release](https://img.shields.io/github/v/release/The412Banner/Banners-Turnip?label=latest%20release&color=blue)](https://github.com/The412Banner/Banners-Turnip/releases/latest)

---

## What Is This?

[Turnip](https://docs.mesa3d.org/drivers/freedreno.html) is the open-source Mesa Vulkan driver for Qualcomm Adreno GPUs — developed as part of the [Mesa](https://gitlab.freedesktop.org/mesa/mesa) project and maintained by the Freedreno community. Unlike the proprietary Qualcomm driver, Turnip is fully open-source and often ships fixes and feature support ahead of official Qualcomm releases.

This repo automatically builds Turnip from the absolute latest commit on `mesa/main` — no waiting for official Mesa releases. A [Mesa upstream watcher](.github/workflows/mesa-watcher.yml) polls for new commits every hour and triggers a fresh build automatically whenever `mesa/main` advances. Each driver comes as two ZIPs from the same Mesa commit and patches:

- an [AdrenoTools](https://github.com/K11MCH1/AdrenoToolsDrivers)-compatible ZIP you can drop straight into any compatible app (BannerHub/BCI, Winlator, Bannerlator X11, etc.);
- a **Wayland** ZIP for Bannerlator Wayland containers.

---

## Driver Variants & Downloads

Each release ships three drivers, each as two ZIPs built from the same Mesa commit and patches. Pick the driver for your GPU, then the ZIP for where you use it:

| Driver | GPUs | X11 / AdrenoTools ZIP | Bannerlator Wayland ZIP |
| :--- | :--- | :--- | :--- |
| **Standard** | Adreno 6xx / 7xx (Snapdragon 8 Gen 3 and older) | `Turnip-<tag>.zip` | `Turnip-<tag>-Wayland.zip` |
| **A8xx** (experimental) | Adreno 810 / 825 / 829 / 830 / 840 (Snapdragon 8 Elite) | `Turnip-<tag>-A8xx.zip` | `Turnip-<tag>-A8xx-Wayland.zip` |
| **A710 / A720 / A722** (experimental) | Adreno 710 / 720 / 722 | `Turnip-<tag>-710-720-Test.zip` | `Turnip-<tag>-710-720-Test-Wayland.zip` |

- **X11 / AdrenoTools ZIP:** BannerHub/BCI, Winlator, Bannerlator X11 containers and any other AdrenoTools app.
- **Wayland ZIP:** Bannerlator **Wayland containers** only. It's a Linux-style Vulkan driver (KGSL, Wayland, bionic) with Bannerlator's zero-copy patch, built by [`build_turnip_wayland.sh`](build_turnip_wayland.sh). It doesn't load as an AdrenoTools driver, and an X11 ZIP doesn't work as a Wayland game driver.
- CI checks every ZIP before it's attached. If a Wayland build fails, the release still ships its X11 ZIPs and the release notes say which Wayland ZIP is missing.

[**Download latest →**](https://github.com/The412Banner/Banners-Turnip/releases/latest) · [**Full build history →**](Mesa-commit-history.md)

### A6xx / A7xx — Standard

Pure Mesa `main`, no source patches. Compatible with Adreno 600–700 series GPUs (Snapdragon 600–800 series, including 7 Gen and 8 Gen 1–3).

### A710 / A720 / A722 — Experimental / Work in Progress

Injects hardware-specific GPU entries and magic registers for Adreno 710, 720, and 722 on top of Mesa `main` via [`a710-720.py`](patches/a710-720.py) — based on community research by [Vauzi-17](https://github.com/Vauzi-17/710). No upstream Mesa support exists for these GPUs yet. Early results are promising. Recommended: force sysmem mode via `TU_DEBUG=sysmem` until GMEM is confirmed stable. Winlator users: set `WRAPPER_BLIT=1`.

### A8xx — Experimental

Targets Adreno 800-series (Snapdragon 8 Elite — A810, A825, A829, A830, A840). Built from Mesa `main` with the following on top (the same for the X11 and Wayland ZIPs):

| Patch | What it does |
| :--- | :--- |
| [`a8xx_gen8.patch`](patches/a8xx_gen8.patch) | 13 commits from whitebelyash's [`turnip/gen8`](https://github.com/whitebelyash/mesa-unified) stack (as shipped in tu_v29 / StevenMXZ v33): A8xx GPU configs, UBWC gralloc detection, `disable_gmem` GPU property, Steam Deck spoof (`TU_DEBUG=deck_emu`), A810 fixes |
| [`a8xx_shared_mem.py`](patches/a8xx_shared_mem.py) | `cs_shared_mem_size` 32 KiB → 64 KiB on every device entry |

Tips: `TU_DEBUG=sysmem` if an A830 looks glitchy; `TU_DEBUG=deck_emu` if a game won't start. **Use at your own risk.**

---

## Workflows

| Workflow | Trigger | What it builds |
| :--- | :--- | :--- |
| **Build Turnip (Combined)** | Auto (mesa-watcher) or manual | Standard + A8xx + A710/A720/A722, Android and Wayland builds in parallel from one Mesa commit; each ZIP is checked in CI, then published as a single tagged release with notes written from what built (manual runs can set `dry_run` to build and verify without publishing) |
| **Build Turnip A8xx (Experimental)** | Manual | Standalone A8xx test build — faster iteration outside the release cycle |
| **Build Turnip (Perf 6xx/7xx)** | Manual | A6xx/A7xx only, compiled with `-O3` + ThinLTO for performance testing |

---

## Installation

- **BannerHub / BCI:** Component Manager → Add New Component → select the X11 / AdrenoTools ZIP
- **AdrenoTools-compatible apps (Winlator, Bannerlator X11, etc.):** load the X11 / AdrenoTools ZIP in GPU driver settings
- **Bannerlator Wayland containers:** *Import Wayland game driver (.zip)* → select the `-Wayland.zip`, then pick it as the container's Wayland game driver

---

## Latest Build

<!-- LATEST_BUILD_START -->
| | |
| :--- | :--- |
| **Mesa version** | 26.3.0 |
| **Vulkan version** | Vulkan 1.4.362 |
| **Commit** | [`06a6743`](https://gitlab.freedesktop.org/mesa/mesa/-/commit/06a6743aacc17b08b612e0f85c1ecb6c841034dd) |
| **Commit date** | 2026-09-16 |
| **Commit title** | kraid: Check restricted fields during decoding |
| **Build date** | 20260916 |
| **Downloads** | X11 / AdrenoTools: 3 ZIPs · Bannerlator Wayland: 3 ZIPs |
| **Release** | [v26.3.0-20260916-r5](https://github.com/The412Banner/Banners-Turnip/releases/tag/v26.3.0-20260916-r5) |
<!-- LATEST_BUILD_END -->

---

## Recent Builds (Last 24 Hours)

<!-- RECENT_BUILDS_START -->
| Tag | Date | Commit | Description | Vulkan |
| :--- | :--- | :--- | :--- | :--- |
| [v26.3.0-20260916-r5](https://github.com/The412Banner/Banners-Turnip/releases/tag/v26.3.0-20260916-r5) | 2026-09-16 | [`06a6743`](https://gitlab.freedesktop.org/mesa/mesa/-/commit/06a6743aacc17b08b612e0f85c1ecb6c841034dd) | kraid: Check restricted fields during decoding | Vulkan 1.4.362 |
| [v26.3.0-20260916-r4](https://github.com/The412Banner/Banners-Turnip/releases/tag/v26.3.0-20260916-r4) | 2026-09-16 | [`e84389c`](https://gitlab.freedesktop.org/mesa/mesa/-/commit/e84389c8d594c258e9330229a8bddd182c81b93a) | d3d12: scope AV1 film grain output redirect to reference-only configs | Vulkan 1.4.362 |
| [v26.3.0-20260916-r3](https://github.com/The412Banner/Banners-Turnip/releases/tag/v26.3.0-20260916-r3) | 2026-09-16 | [`2846d7e`](https://gitlab.freedesktop.org/mesa/mesa/-/commit/2846d7e13d9dce17e2441ca3f168f34d1e918fd5) | radeonsi: wait for graphics shaders differently on GFX10-11.7 | Vulkan 1.4.362 |
| [v26.3.0-20260916-r2](https://github.com/The412Banner/Banners-Turnip/releases/tag/v26.3.0-20260916-r2) | 2026-09-16 | [`848eb4f`](https://gitlab.freedesktop.org/mesa/mesa/-/commit/848eb4f3153e8f03d382b5145ea45068a11971d9) | v3dv: remove render pass fields from pipeline | Vulkan 1.4.362 |
| [v26.3.0-20260916](https://github.com/The412Banner/Banners-Turnip/releases/tag/v26.3.0-20260916) | 2026-09-16 | [`9df9c70`](https://gitlab.freedesktop.org/mesa/mesa/-/commit/9df9c70f17214c4f04843d2b180ce03f8c3eef4a) | intel/brw/xe3+: Consider trivial scheduling heuristic in pre-RA scheduling pass. | Vulkan 1.4.362 |
| [v26.3.0-20260915-r6](https://github.com/The412Banner/Banners-Turnip/releases/tag/v26.3.0-20260915-r6) | 2026-09-15 | [`f9f8f77`](https://gitlab.freedesktop.org/mesa/mesa/-/commit/f9f8f777d01feee8f46fcd1ba037ee51203becda) | etnaviv: blt: Clear each 128-bit plane with its own clear bits | Vulkan 1.4.362 |
| [v26.3.0-20260915-r5](https://github.com/The412Banner/Banners-Turnip/releases/tag/v26.3.0-20260915-r5) | 2026-09-15 | [`822120d`](https://gitlab.freedesktop.org/mesa/mesa/-/commit/822120d6d5c0109f98c3fbf85ec716c5d1fa00b6) | etnaviv: Drop the fragment shader R/B swap | Vulkan 1.4.362 |
<!-- RECENT_BUILDS_END -->

---

## Release Tags

Tags follow the format `v{mesa-version}-{YYYYMMDD}`:

| Tag | Meaning |
| :--- | :--- |
| `v26.2.0-20260427` | First build of the day |
| `v26.2.0-20260427-r2` | Second build of the same day |
| `v26.2.0-20260427-r3` | Third build of the same day |

The `-r` counter starts fresh each day. Multiple builds on the same day happen when Mesa receives more than one commit within 24 hours — each new upstream commit triggers a new build.

---

## Forking / Self-Hosting

You can fork this repo and get fully automated builds running with minimal setup — no custom secrets or external accounts required. All CI uses the built-in `GITHUB_TOKEN`.

**After forking:**

1. **Enable Actions** — GitHub disables Actions on forks by default. Go to **Settings → Actions → General** and set it to *Allow all actions*.

2. **Enable write permissions for Actions** — Under **Settings → Actions → General → Workflow permissions**, select *Read and write permissions*. This is required for the watcher to commit hash files, update the README, and trigger builds.

3. **Reset state files** — The repo ships with state files that track upstream positions. Reset them so your fork starts clean:
   - `mesa_hash.txt` — clear or delete (watcher records the current Mesa HEAD here; a stale value skips the first build trigger)
   - `steven_last_tag.txt` — clear or delete (same, for the StevenMXZ release watcher)
   - `perf_build_number.txt` — set to `1` (incremented and committed by the perf build workflow; leaving it at the current value just means your first perf build gets a higher number, which is harmless but confusing)

4. **Keep the branch named `A8xx`** — The README auto-update step in `turnip_build_combined.yml` has `A8xx` hardcoded in four places (`git fetch/checkout/pull/push origin A8xx`). If you rename the branch, that step will fail and your README won't auto-update. Either keep the branch as `A8xx` or do a find-and-replace in `.github/workflows/turnip_build_combined.yml` to match your branch name.

5. **Update cosmetic repo references** *(optional)* — A few strings in the workflows reference the original repo: patch links in release note bodies and `"author"` in `meta.json`. Search for `The412Banner` in `.github/` and in `build_turnip*.sh`, and update to your own username/repo if desired. These don't affect build functionality.

6. **Kick off your first build** — GitHub Actions schedules don't fire automatically on forks until the repo sees some activity. Manually trigger either:
   - **Mesa Upstream Watcher** → *Run workflow* — records the current Mesa HEAD and fires a combined build if it's new
   - **Build Turnip (Combined)** → *Run workflow* — builds and publishes a release immediately without waiting for the watcher

Once those steps are done, the watcher polls Mesa upstream every hour and triggers a fresh build automatically — no further maintenance needed.

---

## Credits

This project wouldn't exist without the hard work and dedication of these community members. A huge thank you to each of them for sharing their knowledge, publishing their work openly, and being available to help — they're the reason any of this is possible.

| | |
| :--- | :--- |
| [**Mesa / Freedreno**](https://gitlab.freedesktop.org/mesa/mesa) | The open-source project that Turnip is part of — without Mesa and the Freedreno community's ongoing development, none of this exists. |
| [**whitebelyash**](https://github.com/whitebelyash) | Author of the [mesa-tu8](https://github.com/whitebelyash/mesa-tu8) A8xx patchset — the foundation of our A8xx driver variant. His research into A810/A825/A829/A830 GPU enablement, KGSL support, and UBWC fixes made Snapdragon 8 Elite Turnip support possible. |
| [**Vauzi**](https://github.com/Vauzi-17) | Author of the [A710/A720/A722 GPU enablement work](https://github.com/Vauzi-17/710) — hardware-specific magic registers, tuned GPU properties, and chip ID research that our experimental 710/720/722 test build is built on. |
| [**bylaws**](https://github.com/bylaws) | Creator of [libadrenotools](https://github.com/bylaws/libadrenotools) — the driver loading framework that makes all of this usable on Android without root. Without libadrenotools, custom Turnip builds would have no delivery mechanism. |
| [**Kimchi**](https://github.com/K11MCH1) | Maintainer of [AdrenoToolsDrivers](https://github.com/K11MCH1/AdrenoToolsDrivers) — one of the most well-established and trusted custom driver repositories in the Android GPU community, built on top of libadrenotools. |
| [**StevenMXZ**](https://github.com/StevenMXZ) | For his ongoing Turnip builds and releases that the community relies on, and for making his work openly available for others to build upon. |

Also thanks to anyone I forgot and not listed — the Android GPU community is full of people whose contributions quietly make things work, and they deserve recognition too.

---

<sub>☕ [Support on Ko-fi](https://ko-fi.com/the412banner)</sub>


## Community

Join our Discord: https://discord.gg/n8S4G2WZQ4
