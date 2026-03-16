---
name: review-paper
description: Review a LaTeX paper or repo with structured feedback on writing, structure, clarity, notation, citations, and consistency. Use when the user wants feedback on a paper draft, specific sections, or the full manuscript.
allowed-tools: Bash, Read, Glob, Grep, Agent, WebSearch
---

Review a LaTeX paper and produce structured, actionable feedback — as a rigorous peer reviewer would.

## Arguments

Parse `$ARGUMENTS`:

- **project**: directory name under `~/experiments/` containing `.tex` files (default: `s_cot_tex`)
- **section NAME**: review only a specific section (e.g. `section introduction`, `section results`). Matched fuzzily against filenames in `sections/`.
- **focus ASPECT**: narrow the review to one concern:
  - `writing` — prose quality, clarity, conciseness, academic tone
  - `structure` — logical flow, section organization, narrative arc
  - `notation` — symbol consistency, undefined terms, notation clashes
  - `citations` — missing refs, stale refs, self-citation balance, claim coverage
  - `figures` — figure/table references, captions, placement, missing visualizations
  - `consistency` — terminology drift, tense shifts, repeated phrases, numbering
  - `camera` — camera-ready checklist (page limit, anonymization, formatting, bib style)
  - (default: all aspects)
- **venue NAME**: target venue conventions (e.g. `neurips`, `icml`, `acl`, `arxiv`). Affects page limits, anonymization rules, citation style checks.
- **diff**: review only files changed since last commit (`git diff HEAD~1 --name-only`)

## Steps

1. **Discover the paper structure.**
   - `ls ~/experiments/<project>/` to find main .tex
   - `ls ~/experiments/<project>/sections/` if present
   - Read `CLAUDE.md` in the project root for context (architecture, status, conventions)
   - Read the main .tex to get the `\input{}` order and preamble (packages, macros, custom commands)

2. **Read the target content.**
   - If `section` is specified: find the matching file and read it.
   - If `diff` is specified: `git -C ~/experiments/<project> diff HEAD~1 --name-only -- '*.tex'` then read those files.
   - Otherwise: read all .tex files in order (abstract → appendix).
   - Also read the `.bib` file for citation review.

3. **Run automated checks (Bash).**
   All in parallel:
   - **Compilation**: `cd ~/experiments/<project> && latexmk -pdf -interaction=nonstopmode <main>.tex 2>&1 | tail -30` — capture warnings/errors
   - **Undefined refs**: `grep -n 'undefined' <main>.log 2>/dev/null | head -20`
   - **TODO/FIXME scan**: `grep -rn 'TODO\|FIXME\|XXX\|HACK' sections/ 2>/dev/null`
   - **Overfull boxes**: `grep -n 'Overfull' <main>.log 2>/dev/null | head -10`
   - **Citation warnings**: `grep -n 'Citation.*undefined\|Empty.*bibitem' <main>.log 2>/dev/null`

4. **Produce the review.**

   Use this structure (output as Markdown, not LaTeX):

   ```markdown
   # Paper Review: <title>
   **Project**: <project> | **Venue**: <venue> | **Date**: YYYY-MM-DD

   ## Summary
   2-3 sentence summary of what the paper does and its main contribution.

   ## Strengths
   - Numbered list of what works well

   ## Weaknesses
   - Numbered list of issues, each with:
     - **Location**: file:line or section name
     - **Severity**: major / minor / nit
     - **Issue**: what's wrong
     - **Suggestion**: concrete fix

   ## Section-by-Section Notes
   ### Abstract
   ...
   ### Introduction
   ...
   (one subsection per paper section)

   ## Notation & Consistency
   - Symbol table: list all math symbols used and where defined
   - Flag any used-before-defined or inconsistent usage

   ## Citations
   - Missing references for unsupported claims
   - Suggested additions from recent literature

   ## Compilation
   - Errors, warnings, overfull boxes, undefined refs

   ## Checklist
   - [ ] Page limit respected
   - [ ] Anonymization (no author names in text/code/paths)
   - [ ] All figures/tables referenced in text
   - [ ] All claims supported by citation or experiment
   - [ ] Reproducibility (hyperparams, seeds, hardware listed)
   - [ ] Appendix material correctly referenced
   ```

5. **Severity guidelines.**
   - **Major**: incorrect claim, missing experiment, logical gap, result doesn't support conclusion
   - **Minor**: unclear sentence, missing reference, notation inconsistency, weak transition
   - **Nit**: typo, grammar, formatting preference, style suggestion

6. **If `focus` is set**, only produce the relevant section of the review (e.g. `focus citations` → only the Citations section + any major issues found).

7. **WebSearch for citation gaps** (only when `focus citations` or full review):
   - For claims without citations, search arXiv for the most relevant supporting paper
   - For the main contribution, search for concurrent/competing work from the last 12 months
   - Limit to 3-5 searches to stay focused

## Example Usage

```
/review-paper                                    # full review of s_cot_tex
/review-paper s_cot_tex section results          # just the results section
/review-paper s_cot_tex focus writing            # prose quality only
/review-paper s_cot_tex focus camera venue neurips  # camera-ready checklist
/review-paper long-vqa diff                      # review only recent changes
/review-paper s_cot_tex focus citations          # citation gap analysis
```

## Known Paper Repos

| Project | Dir | Main .tex | Venue |
|---------|-----|-----------|-------|
| s_cot | s_cot_tex | neurips_2025.tex | NeurIPS 2025 |
| long-vqa | long-vqa | (TBD) | (TBD) |
