---
name: tech-briefing
description: Produce a cited AI, DIY, and self-hosting news brief.
version: 0.1.0
author: Rogério, Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [news, research, ai, diy-electronics, self-hosting]
    category: research
    related_skills: [grounded-citations]
---

# Tech Briefing

Produce a compact, genuinely useful briefing on recent AI, DIY electronics, and
self-hosting technology. This skill governs research quality and the Markdown
artifact; a cron job may schedule it, but scheduling is deliberately separate.

## When to Use

- The user asks for a technology news briefing, digest, or update.
- A scheduled job requests the recurring AI, DIY electronics, and self-hosting briefing.
- The user asks to refresh or re-run the latest briefing.

Do not use for a single-news-topic deep dive or a broad general-news roundup.

## Prerequisites

- Use live retrieval through `web_extract`, browser tools, RSS, or trusted publication pages.
- Load `grounded-citations` before drafting. Its citation ledger is the source of truth for inline citations and the final source list.
- Resolve `OBSIDIAN_VAULT_PATH` before writing. Save finished briefings to `rogerio/tech/` within that vault unless the user names another destination.

## Scope

1. Cover only material published in the previous 72 hours, unless the user supplies a different window. State the exact window in the briefing header.
2. Prioritize this source pool: TechCrunch, The Verge AI, Hacker News, VentureBeat, Hackaday, Phoronix, Ars Technica, vendor engineering blogs, and primary project/release sources.
3. Include only items with technical substance: research, implementations, security incidents, infrastructure, open source, repairability, benchmarks, developer tools, or reproducible builds.
4. Exclude marketing fluff, funding-only stories, and product announcements without a material technical angle.

## Procedure

1. **Set the window.** Obtain the current date/time with `terminal`; calculate the 72-hour cutoff with `terminal`, not mental arithmetic. Completion: the start and end timestamps are recorded.
2. **Collect candidates.** Retrieve source pages or feeds, register every kept source in the citation ledger immediately, and retain publication date plus canonical URL. Completion: every candidate has a retrieved page and date inside the window.
3. **Curate hard.** Deduplicate syndicated coverage and select the stories that matter. Prefer primary sources for claims about releases, vulnerabilities, projects, and technical results. Completion: every included item passes the technical-substance filter.
4. **Draft the briefing.** For each item, provide publication date, title, a 2–4 sentence technical summary, why it matters, and inline citations. Do not overstate claims beyond the retrieved source. Completion: every externally sourced sentence has its ledger citation.
5. **Write the Markdown artifact.** Use this structure:

   ```markdown
   # Tech Briefing — YYYY-MM-DD

   **Coverage window:** YYYY-MM-DD HH:MM UTC to YYYY-MM-DD HH:MM UTC

   ## AI
   ### [Title](canonical URL) — YYYY-MM-DD
   Summary with technical implications.[1]

   ## DIY Electronics
   ...

   ## Self-Hosting & Infrastructure
   ...

   ## Sources
   ```

   Use categories only when there is qualifying material; never pad an empty section. Completion: the artifact is saved as `tech-briefing-YYYY-MM-DD.md`.
6. **Verify and deliver.** Run the grounded-citations verifier in strict mode, then send the verified Markdown file to the requested channel. Completion: verification succeeds and the saved artifact path is reported.

## Editorial Standard

- Favor depth over count: six strong items beats twenty headlines.
- Link the title to the canonical or primary source; citations substantiate the summary.
- Say when a favored outlet had no qualifying recent coverage rather than filling space with old news.
- Mark uncertainty plainly when a claim is preliminary, vendor-reported, or based on a single source.
- Never invent publication dates, benchmarks, release details, or source URLs.

## Pitfalls

- Publication pages can have stale RSS timestamps. Confirm the article's displayed date before including it.
- Hacker News is discovery, not evidence; retrieve the linked primary source before making factual claims.
- A scheduled run must execute the research now. It must not create, alter, or duplicate the cron job.
- A valid citations block does not rescue irrelevant material. Enforce the scope and technical-substance filter first.

## Verification

- Every included item falls within the declared window.
- Every citation maps to a retrieved source and the strict citation verifier passes.
- The saved file exists under `rogerio/tech/` and its filename uses the run date.
- The final response reports the artifact path and any source-pool gaps.
