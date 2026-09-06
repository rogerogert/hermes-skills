---
name: calories
description: Analyzes food photos sent in chat to estimate calories and macros, logs each meal to a daily nutrition log, and answers /calories commands (today, week, goal, history, undo) for progress tracking.
version: 1.0.0
author: Rogério (adapted from luna-calorie-tracker by Sidney Schwartz, github.com/sidneyschwartz/luna-calorie-tracker)
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [health, nutrition, tracking, vision]
    category: health
    requires_toolsets: [file_operations, terminal, vision]
---

# Calorie Tracker

Track daily caloric intake from food photos. When the user sends a picture of a meal, analyze
it with your own vision capability, estimate calories and macros, log it, and keep a running
daily total. Also answer `/calories` commands for summaries, goals, history, and corrections.

This skill does **not** call out to any external AI provider or require its own API key — it
uses whichever model you already have configured as your main provider in Hermes. If that model
doesn't accept images natively, Hermes routes the image through its own auxiliary vision
pathway automatically; see **Setup notes** below for what that requires.

## When to use this

- The user sends a photo of food or a meal — as a chat attachment, pasted image, or via a
  connected gateway (Telegram, etc.) — analyze and log it, without waiting for a command.
- The user types `/calories` or `/calories <subcommand>` — run that subcommand.
- If an image clearly isn't food, don't log it — say so and let normal conversation continue.

## Setup notes (read once before relying on this)

- **Vision toolset.** This install's "Blank Slate" setup only enabled Provider/Model, File
  Operations, and Terminal. Image analysis needs the `vision` toolset too — enable it with
  `hermes tools` (interactive) before this skill can see photos.
- **Check your model's native vision support.** Confirm whether your configured main model
  accepts images directly. If it's text-only, Hermes falls back to the `vision_analyze`
  auxiliary tool, which uses whatever model is set under `auxiliary.vision` in
  `~/.hermes/config.yaml` — set that to a vision-capable model if you haven't already.
- **Known gateway issue.** There's an open upstream bug (NousResearch/hermes-agent#25118)
  where images arriving through the Telegram gateway can fail vision analysis even though the
  file caches locally. Test with a photo sent directly via the `hermes` CLI first; if that
  works but Telegram doesn't, it's this bug, not a problem with this skill.
- **Data directory.** On first use, create `${HERMES_SKILL_DIR}/data/` if it doesn't exist yet
  (`mkdir -p`). All logs for this skill live there — nothing is written outside the skill's own
  folder.

## On a food photo — analysis & logging

1. **Analyze the image** using your vision capability:
   - Identify every food item visible.
   - Estimate portion sizes (grams or ml). Use plate size as a reference (standard dinner
     plate ≈ 10 inches / 25 cm) when nothing else is given.
   - Calculate: Calories, Protein (g), Carbs (g), Fat (g), Fiber (g).
   - Assign a confidence score (0–1) for the estimate.

2. **Respond with a structured summary:**
   ```
   🍽️ Meal Logged!

   📸 Items detected:
   - [Food item 1]: [portion] — [calories] kcal (P: [x]g | C: [x]g | F: [x]g)
   - [Food item 2]: [portion] — [calories] kcal (P: [x]g | C: [x]g | F: [x]g)

   📊 Meal Total: [total] kcal
   Protein: [x]g | Carbs: [x]g | Fat: [x]g | Fiber: [x]g
   Confidence: [score]

   📅 Daily Running Total: [X] kcal ([meals] meals logged today)
   ```
   If a daily goal is set (see `/calories goal`), append the progress line described there.

3. **Read today's log first**, then append. Before writing, read
   `${HERMES_SKILL_DIR}/data/YYYY-MM-DD.md` for today's date (create it if it doesn't exist)
   so the running total is accurate. Append a new meal block:
   ```markdown
   ## Meal [N] — [HH:MM]
   - **Items**: [comma-separated food items]
   - **Calories**: [total] kcal
   - **Protein**: [x]g | **Carbs**: [x]g | **Fat**: [x]g | **Fiber**: [x]g
   - **Confidence**: [score]
   ```

4. **Rewrite the summary block at the top** of that day's file after every meal:
   ```markdown
   # Daily Nutrition Log — [YYYY-MM-DD]
   **Total Calories**: [X] kcal | **Meals**: [N]
   **Protein**: [X]g | **Carbs**: [X]g | **Fat**: [X]g | **Fiber**: [X]g
   ---
   ```

## Slash commands

### `/calories` (no argument)
Same as `/calories today`.

### `/calories today`

Read `${HERMES_SKILL_DIR}/data/YYYY-MM-DD.md` for today's date and display its summary and
meal entries. If it does not exist, say "Nothing logged today."

### `/calories week`

Read the last 7 days of `${HERMES_SKILL_DIR}/data/YYYY-MM-DD.md` files (skip any that do not
exist), calculate weekly totals and daily averages, and show a mini bar chart:

```
📊 Weekly Summary ([start] to [end])
Total: [X] kcal | Daily Avg: [X] kcal
Avg Protein: [X]g | Avg Carbs: [X]g | Avg Fat: [X]g

Mon: ████████░░ 1,850 kcal
Tue: ██████████ 2,200 kcal
Wed: ███████░░░ 1,600 kcal
...
```

Scale bars to the highest logged day in the window (10 blocks). Skip missing days silently;
don't treat them as zero-calorie days in the displayed average.

### `/calories goal [number]`

If the user provides a `[number]`, save it to `${HERMES_SKILL_DIR}/data/goal.md` as:
`Daily Calorie Goal: <number> kcal`.

If no number is provided, read the local goal file. If no goal is set, say so and omit the
progress line from daily and weekly summaries.

### `/calories history [food]`
Search `${HERMES_SKILL_DIR}/data/*.md` for entries mentioning `[food]` (case-insensitive —
`grep -il` via the terminal toolset works well here) and report: the last date it was eaten,
its average calories across those entries, and how many times it appears.

### `/calories undo`
Remove the most recent `## Meal N — HH:MM` block from today's file and recompute/rewrite the
daily summary block at the top. If today's file has no meals, say there's nothing to undo.

## Vision analysis guidelines

- Consider plate size as a portion reference (standard dinner plate ≈ 10 inches / 25 cm).
- Account for hidden calories: cooking oils, sauces, dressings, butter.
- For packaged foods, read the label if it's visible and legible in the image.
- If a food item is ambiguous, state your assumption (e.g., "assuming whole milk, not skim")
  rather than silently picking one.
- For restaurant meals, estimate on the higher side — restaurants use more oil/butter than a
  home-cooked equivalent.
- If you genuinely cannot identify a food, ask the user to clarify instead of guessing.
- Calorie estimates from a photo are approximations (typically ±20–30%). Say so if the user
  pushes on precision — don't present an estimate as measured fact.

## Data layout

```
${HERMES_SKILL_DIR}/data/
  goal.md            # daily calorie goal, saved by /calories goal
  2026-08-24.md      # one file per day — summary header + meal entries
  2026-08-25.md
  ...
```

Everything this skill writes stays inside its own `data/` folder — nothing touches Hermes'
own `~/.hermes/memories/` (that's the agent's general conversation memory, a separate thing).

## Gotchas

- Always read today's file before appending, so the running total in the header is correct —
  don't compute it from memory of the conversation.
- If `${HERMES_SKILL_DIR}/data/` doesn't exist yet, create it before the first write
  (`mkdir -p`) rather than failing.
- Portion-size assumptions compound across a day — if the user corrects an estimate, prefer
  their number for that entry rather than re-deriving it.
- `/calories week` should skip missing days silently, not treat them as zero-calorie days in
  the displayed average unless the user asks for that framing.
