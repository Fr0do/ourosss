---
name: review-paper
description: Review a LaTeX paper or repo with structured feedback on writing, structure, clarity, notation, citations, and consistency. Use when the user wants feedback on a paper draft, specific sections, or the full manuscript.
allowed-tools: Bash, Read, Glob, Grep, Agent, WebSearch
---

Review a LaTeX paper and produce structured, actionable feedback — as a rigorous peer reviewer would.

## Setup

Read `~/.claude/research-env.md` to resolve paper repo paths, main .tex filenames, and target venues.

## Arguments

Parse `$ARGUMENTS`:

- **project**: project name from research-env (default: first paper repo listed)
- **section NAME**: review only a specific section. Matched fuzzily against filenames in `sections/`.
- **focus ASPECT**: narrow the review to one concern:
  - `writing` — prose quality, clarity, conciseness, academic tone
  - `structure` — logical flow, section organization, narrative arc
  - `notation` — symbol consistency, undefined terms, notation clashes
  - `citations` — missing refs, stale refs, self-citation balance, claim coverage
  - `figures` — figure/table references, captions, placement, missing visualizations
  - `consistency` — terminology drift, tense shifts, repeated phrases, numbering
  - `camera` — camera-ready checklist (page limit, anonymization, formatting, bib style)
  - (default: all aspects)
- **venue NAME**: override target venue from research-env (e.g. `neurips`, `icml`, `acl`, `arxiv`)
- **diff**: review only files changed since last commit (`git diff HEAD~1 --name-only`)

## Steps

1. **Discover the paper structure.**
   - List the paper directory to find main .tex
   - List `sections/` subdirectory if present
   - Read `CLAUDE.md` in the project root for context
   - Read the main .tex to get the `\input{}` order and preamble (packages, macros, custom commands)

2. **Read the target content.**
   - If `section` specified: find the matching file and read it.
   - If `diff` specified: `git diff HEAD~1 --name-only -- '*.tex'` then read those files.
   - Otherwise: read all .tex files in order (abstract → appendix).
   - Also read the `.bib` file for citation review.

3. **Run automated checks (Bash).**
   All in parallel:
   - **Compilation**: `latexmk -pdf -interaction=nonstopmode <main>.tex 2>&1 | tail -30`
   - **Undefined refs**: `grep -n 'undefined' <main>.log | head -20`
   - **TODO/FIXME scan**: `grep -rn 'TODO\|FIXME\|XXX\|HACK' sections/`
   - **Overfull boxes**: `grep -n 'Overfull' <main>.log | head -10`
   - **Citation warnings**: `grep -n 'Citation.*undefined\|Empty.*bibitem' <main>.log`

4. **Produce the review.**

   ```markdown
   # Paper Review: <title>
   **Project**: <project> | **Venue**: <venue> | **Date**: YYYY-MM-DD

   ## Summary
   2-3 sentence summary of the paper's contribution.

   ## Strengths
   - Numbered list of what works well

   ## Weaknesses
   - Numbered list, each with:
     - **Location**: file:line or section name
     - **Severity**: major / minor / nit
     - **Issue**: what's wrong
     - **Suggestion**: concrete fix

   ## Section-by-Section Notes
   (one subsection per paper section)

   ## Notation & Consistency
   - Symbol table: all math symbols and where defined
   - Flag used-before-defined or inconsistent usage

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
   - **Major**: incorrect claim, missing experiment, logical gap
   - **Minor**: unclear sentence, missing reference, notation inconsistency
   - **Nit**: typo, grammar, formatting preference

6. **If `focus` is set**, only produce the relevant section of the review.

7. **WebSearch for citation gaps** (only when `focus citations` or full review):
   - For claims without citations, search arXiv for supporting papers
   - For the main contribution, search for concurrent work from the last 12 months
   - Limit to 3-5 searches

## Example Usage

```
/review-paper
/review-paper section results
/review-paper focus writing
/review-paper focus camera venue neurips
/review-paper diff
```
