---
name: label-dataset
description: Label any HuggingFace dataset or JSONL file using Claude via the CLI subprocess pattern. Generalizes the musique-traces generate_traces.py approach. Use when the user wants to annotate, classify, or generate completions for a dataset.
allowed-tools: Bash, Read, Write, Agent
---

Generate labels/annotations for a dataset using Claude (billed via Claude Code, no API key needed).
Reuses the async subprocess + resume-safe JSONL pattern from `musique-traces/generate_traces.py`.

## Arguments

Parse `$ARGUMENTS` for flags (any order):

- `--input PATH_OR_HF_DATASET` — HuggingFace dataset ID (e.g. `dgslibisey/MuSiQue`) or local JSONL path
- `--output PATH` — output JSONL path (default: `<dataset_name>_labeled.jsonl`)
- `--model MODEL` — claude model (default: `haiku`; options: `haiku`, `sonnet`, `opus`)
- `--concurrency N` — parallel workers (default: 5)
- `--system-prompt TEXT` — override default system prompt
- `--field FIELD` — input field to pass as prompt (default: auto-detect: `question`, `text`, `input`, `prompt`)
- `--split SPLIT` — dataset split to use (default: `train`)
- `--limit N` — process only first N examples (for debug)

## Steps

1. Parse arguments from `$ARGUMENTS`.

2. Read the reference implementation:
   ```
   /Users/mkurkin/experiments/musique-traces/generate_traces.py
   ```
   This contains the canonical async + resume-safe JSONL pattern.

3. Use the Agent tool (Sonnet subagent) to generate a new Python script at `/tmp/label_dataset_run.py` that adapts the reference implementation for the requested dataset/field/model/concurrency. Key adaptations:
   - Load from HF datasets or local JSONL based on `--input` type
   - Use the user's `--field` as the prompt field (fallback: serialize full example as JSON)
   - Use `--system-prompt` if provided
   - Resume by tracking `id` field (or enumerate index if absent)
   - Write `{**example, "label": response}` to output JSONL

4. Run the generated script:
   ```bash
   python /tmp/label_dataset_run.py
   ```
   Stream output to user.

5. On completion, report: total processed, skipped (resumed), output path, approx token cost (~650 tokens/example × N).

## Reference Implementation

Canonical implementation: `/Users/mkurkin/experiments/musique-traces/generate_traces.py`

Key patterns to preserve:
- Semaphore for concurrency throttling
- `tqdm.asyncio.tqdm.as_completed()` for progress
- Resume via `done_ids` set built from existing JSONL
- `proc.communicate(input=prompt.encode())` via claude CLI

## Example Usage

```
/label-dataset --input dgslibisey/MuSiQue --field question --concurrency 8 --model haiku
/label-dataset --input ./my_data.jsonl --output labeled.jsonl --system-prompt "Classify sentiment: positive/negative/neutral"
/label-dataset --input openai/gsm8k --split test --limit 100 --model sonnet
```
