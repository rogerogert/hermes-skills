---
name: tech-briefing
description: Use when producing a curated technical news briefing.
version: 0.2.0
author: Rogério, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [news, research, ai, diy-electronics, self-hosting, home-automation]
    category: research
    related_skills: [grounded-citations, obsidian]
---

# Tech Briefing

Produce a useful editorial briefing, not a digest of whichever changelogs are easiest to fetch. Cover AI, DIY electronics, self-hosting/infrastructure, and home automation. Scheduling belongs to cron; never create or alter jobs during a briefing run.

## Prerequisites

- Load `grounded-citations` and `obsidian`. Resolve `OBSIDIAN_VAULT_PATH`; the established vault here is `/home/hermes/.hermes/vault/`.
- Use live retrieval. Prefer configured `web_search` for discovery and `web_extract` for article bodies; RSS, project APIs, and browsers are fallbacks, not excuses to shrink the editorial scope. Do not modify provider configuration during a run.
- Create a unique run directory under `${HERMES_HOME:-~/.hermes}/cache/tech-briefing/<UTC-timestamp>/`. Use its `ledger.json` with `sources.py --ledger <absolute-path>` on EVERY citation command. Never reset the shared default ledger.

## Coverage and cross-edition memory

1. Obtain current UTC time with `terminal`; compute timestamps in code, not mentally. End the window at run start.
2. Read recent `rogerio/tech/tech-briefing-*.md` artifacts across BOTH Monday and Thursday jobs, not merely this job's continuity context. Use the latest earlier edition whose research status is COMPLETE and whose artifact and strict verification succeeded. Start at that edition's recorded coverage end. Thus Thursday-to-Monday is covered in full rather than losing a day.
3. For migration only, a legacy edition without a research-status field may serve as the baseline when its saved artifact and successful strict verification are confirmed in the prior run log; label this `legacy-verified baseline` in the audit, not retrospectively COMPLETE. If no eligible edition exists, cover the previous 72 hours and declare bootstrap mode. If the last complete edition is more than seven days old, cover seven days and explicitly disclose the uncovered interval. A DEGRADED edition must NOT advance this watermark; recover its interval next time and deduplicate stories it already delivered.
4. Honor an explicit user-supplied window instead, but mark that edition `watermark_eligible: false` unless it starts at or before the existing recurring coverage end and extends it contiguously. COMPLETE describes research quality, not watermark eligibility; select only eligible COMPLETE editions as future baselines. Record start, end, baseline artifact, eligibility, outstanding gaps, and mode in `research.json` and the artifact. Preserve previously delivered canonical URLs and story identities for deduplication; include an old story only for a material new development and explain the delta. Research coverage and delivery state are separate: confirm delivery from cron execution/delivery records before calling stories delivered; a saved artifact alone is not proof. If delivery is failed or unknown, include a compact recovery summary of those stories rather than silently suppressing them.
5. Save `tech-briefing-YYYY-MM-DD.md` under `rogerio/tech/`; if that filename already exists, preserve it and use `tech-briefing-YYYY-MM-DD-HHMMSS.md` instead. Retain the research directory and link its absolute path from the artifact.

## Discovery before selection

- Survey at least eight distinct publications/project organizations across all four topics, including at least three independent editorial outlets. Attempt discovery even for categories that look quiet. Prefer primary evidence for the final technical claims.
- Source pool: Ars Technica, The Verge AI, TechCrunch, VentureBeat, Hackaday, CNX Software, Phoronix, Hacker News linked articles, Hugging Face research, vendor engineering blogs, Home Assistant, ESPHome, Open Home Foundation, and relevant self-hosted projects. Hacker News is discovery, not evidence.
- Build a candidate pool of at least twelve dated, in-window stories BEFORE selecting. If genuinely fewer exist after broad discovery, retain what you found and explain the shortfall; never invent or pad candidates. A quiet news window is not an infrastructure failure.
- Record attempted sources, retrieval method, errors, candidate title, canonical URL, publication timestamp and its evidence, category, concise relevance/novelty judgment, and keep/reject reason in `research.json`. Append progress after each batch so failures do not erase the audit trail.
- Count discovery coverage honestly: blocked attempts do not count as surveyed content. If a source fails, try one appropriate alternative such as its RSS feed or primary linked source; avoid repeated identical failing calls.

## Editorial selection

- Aim for four to eight strong stories, fewer when justified; never fill a category for symmetry. Prefer practical relevance, material novelty, reproducible projects, independent technical analysis, consequential research, and security changes over release frequency.
- AI: emphasize useful capabilities, agents/developer tools, open models, evaluation methodology, and inference improvements. Distinguish vendor claims from independent results.
- DIY: prioritize buildable electronics, firmware, repairability, and documented hardware. Retro curiosities belong only when the engineering insight is genuinely useful.
- Self-hosting: favor deployable projects, operations, backups, networking, privacy, and meaningful infrastructure changes.
- Home automation: prioritize Home Assistant, Matter/Thread/Zigbee, ESPHome, local-first control, energy monitoring, security/privacy, and reproducible setups.
- Limit routine patch/beta release roundups to ONE story per edition, unless additional releases fix consequential security/reliability issues or materially affect a known user deployment. Explain the exception. Never assume the user runs a package merely because they self-host.
- Avoid domination by one outlet or repository: normally no more than two stories from one organization. Seek independent coverage rather than filling the briefing from a familiar GitHub repository list.
- Exclude funding-only news, marketing, unsupported product claims, and recycled stories. Record editorial exceptions rather than quietly relaxing these rules.

## Evidence and drafting

1. Retrieve the full selected article or primary release notes. Search snippets and feed headlines are insufficient for body-level claims. Full-text RSS may support only claims actually present in its stored text; otherwise fetch the linked article.
2. Confirm publication date on the article or release API (`published_at`, not an unrelated update date); exclude undated or out-of-window candidates. Save the evidence text and date provenance per selected story in the run directory.
3. Register each SELECTED supporting source at retrieval, before drafting. Keep rejected/discovery-only sources in research.json, not the final citation ledger: strict mode rejects uncited ledger entries. Retrieve selected bodies again if needed to register directly from retrieval rather than reconstructing sources from prose. Attach at least one verbatim supporting quote per cited source with the complete invocation `python "$S" --ledger <absolute-ledger-path> quote <id> --text "<verbatim quote>" --from <saved-evidence-file>`, where `$S` is the installed grounded-citations `scripts/sources.py`. Never reconstruct the ledger from a finished draft.
4. Write a linked title, publication date, a 2–4 sentence technical summary, and a specific why-it-matters statement per item. Cite factual statements using ledger IDs; label preliminary/vendor-reported results. Do not add generic upgrade advice or forced profanity as editorial substance.
5. Include the exact UTC coverage window, baseline edition, research status (COMPLETE or DEGRADED), the relevant topic headings, source gaps, retrieval failures/fallbacks, and generated Sources section. Distinguish 'nothing qualifying found among surveyed sources' from 'nothing was published'.

## Verification, status, and delivery

- Generate Sources mechanically with `sources.py --ledger <path> render --replace-in <draft>`.
- Require `sources.py --ledger <path> verify <draft> --strict --evidence --min-coverage 0.7`. The strict citation verifier passes only a citation/provenance check, NOT factual truth, date accuracy, breadth, or editorial relevance; check those separately against `research.json` and saved evidence.
- Mark COMPLETE only when broad discovery succeeded, every selected story has dated body evidence, and artifact/citation checks pass. Fewer than twelve real candidates can still be COMPLETE when all discovery requirements were met and the shortfall is explained.
- Mark DEGRADED prominently when discovery breadth could not be met, extraction failures left material source gaps, or required evidence/verification is missing. Report the actual blocker and fallbacks in the final response; never advertise a degraded run as a normal verified success. A fallback that fully restores breadth and evidence may be COMPLETE, but still disclose it.
- If no reliable briefing can be produced, return `[CRON_FAILURE]` on the first line followed by the blocker, not invented news. Save the failure audit without advancing the complete coverage watermark. Do not use `[SILENT]` to hide retrieval failure.
- Retain only public source evidence and sanitized errors in the audit; never store credentials, authenticated URLs, or raw sensitive tool responses.
- Keep research.json, ledger.json, evidence files, verification result, and final artifact path together in the run audit. Verify the final saved artifact, not just a temporary draft. Use file tools; if the vault write fails, report it rather than claiming the file was saved.
- In a cron run, the scheduler delivers the FINAL RESPONSE. Return the actual briefing with clickable source URLs and its artifact path; do not send a second message yourself and do not return only a filesystem path or a MEDIA tag. Incomplete source access must be visible in that delivered text.

## Completion checklist

- Coverage spans the previous complete edition across both jobs, with explicit bootstrap/cap exceptions and cross-edition deduplication.
- Discovery breadth, candidate selection, publication evidence, and failures are auditable in the unique run directory.
- The selection is a useful mix of developments, not repeated minor patch notes.
- Every cited source has saved supporting evidence and strict verification succeeds before claiming verification.
- The final response contains the briefing itself, honest research status, source gaps, and saved artifact/audit paths.
