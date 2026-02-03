# Mini LLM Standardizer — Flask (Replit-friendly)

Tiny Flask API that runs a small local LLM (TinyLlama 1.1B, GGUF) via `llama-cpp-python` to standardize
degree program + university names. It appends two new fields to each row:
- `llm-generated-program`
- `llm-generated-university`

## Quickstart

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Run in CLI mode (recommended for batch processing):
   ```bash
   python app.py --file applicant_data.json --stdout > applicant_data_llm.json
   ```

3. Or run as Flask server:
   ```bash
   python app.py --serve
   ```
   The first run downloads a small GGUF model from Hugging Face (defaults to TinyLlama 1.1B Chat Q4_K_M).

4. Test with sample data:
   ```bash
   python app.py --file sample_data.json --stdout
   ```

## CLI mode

```bash
python app.py --file cleaned_applicant_data.json --stdout > full_out.jsonl
```

## Config (env vars)

- `MODEL_REPO` (default: `TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF`)
- `MODEL_FILE` (default: `tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf`)
- `N_THREADS` (default: CPU count)
- `N_CTX` (default: 2048)
- `N_GPU_LAYERS` (default: 0 — CPU only)

If memory is tight, try:
```bash
export MODEL_FILE=tinyllama-1.1b-chat-v1.0.Q3_K_M.gguf
python app.py --file applicant_data.json --stdout
```

## Notes
- Strict JSON prompting + a rules-first fallback keep tiny models on task.
- Extend the few-shots and the fallback patterns in `app.py` for higher accuracy on your dataset.
- Output includes original fields plus `llm_generated_program` and `llm_generated_university`.
