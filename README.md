# Dead by Daylight Perk Randomiser

A web app that randomises perk builds for Killer and Survivor in Dead by Daylight.

## Use

Open `index.html` in any browser. Choose Killer or Survivor, pick how many perks (1–4), then click **Randomise**. Each perk reel spins and stops one after another. Click any perk (rolled card or in the **All Perks** list) to read its description. Use **Copy build** to copy the rolled perks, or **Export/Import Perks** to save and load perk data.

## Updating perks

New perks are added to the game over time. To refresh the perk list:

```bash
python update_perks.py
```

This scrapes the current perk list from the Dead by Daylight wiki and writes `dbd-perks.json`. Then open the app, click **Import Perks**, and select `dbd-perks.json`. The imported data is saved in your browser, so it persists.

## Files

- `index.html` — the app (self-contained, icons embedded).
- `update_perks.py` — scraper to refresh the perk list.
- `dbd-perks.json` — generated perk data (created by the scraper).
PY