---
name: deep-research
description: Bootstrap a new LaTeX research paper project with deep literature review. Use when the user wants to start a new paper, create a paper proposal, or bootstrap a research project with LaTeX scaffolding.
allowed-tools: Bash, Read, Write, Edit, Agent, WebSearch, WebFetch, Grep, Glob
---

Bootstrap a new LaTeX paper project at ~/experiments/ following the established s_cot_tex pattern.

## Input

Parse `$ARGUMENTS` to extract:
- **topic**: research topic or paper idea (required)
- **venue**: target venue/conference (default: NeurIPS 2025)
- **project_name**: short project identifier for the directory (infer from topic if not given)

## Steps

### Phase 1: Deep Research

1. Use WebSearch to find 10-20 relevant recent papers on the topic. Focus on:
   - Key foundational works
   - State-of-the-art methods (last 2 years)
   - Closely related concurrent work
   - Relevant benchmarks and datasets

2. For the most important papers (top 5-8), use WebFetch on their arXiv abstract pages to get:
   - Full title, authors, year
   - Abstract summary
   - Key contributions

3. Synthesize a research gap analysis:
   - What has been done
   - What is missing
   - Where the proposed work fits

### Phase 2: Paper Proposal

4. Draft a paper proposal covering:
   - **Title**: Concise, descriptive
   - **Core idea**: 2-3 sentence elevator pitch
   - **Key contributions** (3-4 bullet points)
   - **Proposed methodology**: High-level approach
   - **Expected experiments**: Datasets, baselines, metrics
   - **Why this matters**: Significance and novelty

5. Present the proposal to the user and ask for approval/refinements before proceeding to Phase 3.

### Phase 3: Project Scaffolding

6. Create the project directory at `~/experiments/<project_name>_tex/`:

```
<project_name>_tex/
├── <venue_style>.tex           # Main LaTeX file with \input{sections/...}
├── <venue_style>.sty           # Venue style file (copy from appropriate template)
├── <venue_style>.bib           # Bibliography with discovered references
├── sections/
│   ├── 00_abstract.tex         # Abstract (draft from proposal)
│   ├── 01_introduction.tex     # Introduction (scaffolded with key points)
│   ├── 02_related_work.tex     # Related work (organized by research themes)
│   ├── 03_methodology.tex      # Methodology (placeholder structure)
│   ├── 04_experiments.tex      # Experimental setup (datasets, baselines)
│   ├── 05_results.tex          # Results (placeholder tables/figures)
│   ├── 06_conclusion.tex       # Conclusion (placeholder)
│   └── 07_appendix.tex         # Appendix (placeholder)
├── CLAUDE.md                   # Project instructions for Claude
├── .gitignore                  # LaTeX artifacts
└── PROPOSAL.md                 # Full proposal document
```

7. Main `.tex` file structure (modeled on s_cot_tex):
   - Venue-appropriate document class and style
   - Standard packages: hyperref, url, booktabs, amsfonts, amsmath, nicefrac, microtype, xcolor, graphicx
   - Modular `\input{sections/XX_name.tex}` for each section
   - Bibliography at the end

8. Populate sections with substantive drafts:
   - `00_abstract.tex`: Full draft abstract based on proposal
   - `01_introduction.tex`: Motivation, problem statement, contributions list, paper outline
   - `02_related_work.tex`: Organized paragraphs with citations for each research theme
   - Other sections: Skeleton with subsection headers and TODO comments

9. Generate `.bib` file with all discovered references in proper BibTeX format.

10. Create `CLAUDE.md` with:
    - Project identity and submission target
    - Repository layout
    - Core technical approach summary
    - How to work on the project (compile, edit, etc.)
    - Current status

11. Create `.gitignore`:
    ```
    *.aux *.bbl *.blg *.log *.out *.pdf *.fdb_latexmk *.fls *.synctex.gz
    ```

12. Initialize git repo: `cd ~/experiments/<project_name>_tex && git init && git add -A && git commit -m "bootstrap: <project_name> paper scaffold"`

### Phase 4: Summary

13. Report to the user:
    - Project location
    - Paper title and key contributions
    - Number of references found
    - Next steps (what to write/refine first)

## Venue Style Files

For known venues, download the appropriate style:
- **NeurIPS**: Copy from ~/experiments/s_cot_tex/neurips_2025.sty if available
- **ICML/ICLR/ACL/EMNLP**: Use WebFetch to download from the official template page
- **arXiv preprint**: Use plain article class

## Guidelines

- One sentence per line in .tex files (cleaner git diffs)
- Use `\citet` and `\citep` for citations when natbib is available
- Keep the abstract under 250 words
- Draft introduction should be ~1.5 pages
- Related work should reference all discovered papers
- Use descriptive commit messages
