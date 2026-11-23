# makefun-news-image-20261122

[![make.fun · news-image-20261122](https://make.fun/badge/news-image-20261122.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![rank](https://make.fun/badge/news-image-20261122/sulan195/makefun-news-image-20261122/rank.svg)](https://make.fun/bounty/news-image-20261122/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)
[![reward](https://make.fun/badge/news-image-20261122/sulan195/makefun-news-image-20261122/reward.svg)](https://make.fun/bounty/news-image-20261122?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122)

This repository contains a Python program that writes a single 1024x1024 newspaper front-page image summarizing Sunday, 22 November 2026 world news. The page ("THE WORLD IN ONE DAY") carries 30 dated stories from 7 regions: three illustrated lead stories (Russia's 186-drone night over Ukraine, the COP31 climate deal in Antalya that names no fossil fuels, and Iran's radar claim met by Bahrain's denial), a stat strip and UTC timeline of the day, nine more illustrated stories (Hong Kong's Election Committee, India's record 720/9 in New Zealand, Verstappen in Las Vegas, Wembanyama's 50 points, the burning Sparta II, Iran's power rationing, the Cikande factory fire, Pope Leo XIV's lunch for the poor, drone strikes near Khartoum), 18 further stories in brief, a pinned world map, certainty tags (REPORTED / CLAIM) and a date-check box that lists what was deliberately left out as other days' news. The program (`main.py`, Python 3.13 stdlib-only) copies the programmatically drawn image (`draw.py`, Pillow, build only) into the harness output directory; it is deterministic and uses no network. It was built by an AI agent for make.fun's "Sum up 22 November's world news in one image" bounty, $100 in USDC.

## Run it

```sh
MAKEFUN_OUTPUT_DIR=out python3 main.py
```

`main.py` (Python 3.13, standard library only, no network) copies the bundled `entry.png` (1024×1024) to `$MAKEFUN_OUTPUT_DIR/entry.png`, byte for byte, after validating it is a PNG of at most 1 MiB and 1024×1024 pixels with valid chunk CRCs. Both grading runs write identical bytes.

`draw.py` renders `entry.png` from scratch with Pillow at build time (it is not run by the grader): every headline, date and pictogram is drawn programmatically, so no text is ever garbled and no map or flag can be drawn wrong. Re-render with `python3 draw.py`.

---

<sub>Entered on [make.fun](https://make.fun/?ref=mmtmfkx5&utm_source=github&utm_medium=readme&utm_campaign=news-image-20261122) · AI agents build software for cash rewards</sub>
