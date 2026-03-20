## Plan: LLM Comparison Web App (Gradio)

Build a Gradio Blocks app with two-column side-by-side LLM comparison. Left: user's custom model via OpenAI-compatible API endpoint. Right: selectable provider models (OpenAI, Anthropic, Gemini, Qwen, Yi) with default API keys from HF Spaces secrets. Users enter a nickname, prompt both models, then comment and grade (1-10) each response. All evaluations persist to SQLite. Admin can download all data as Excel (.xlsx). Deploy on HuggingFace Spaces.

---

### Phase 1: Project Setup
1. Create `requirements.txt` with: `gradio`, `openai`, `anthropic`, `google-generativeai`, `openpyxl`
2. Update `README.md` with project description and setup instructions

### Phase 2: Database Layer — `db.py`
3. Create SQLite helper with `init_db()` to create the `evaluations` table with columns: `id`, `timestamp`, `nickname`, `prompt`, `left_model_name`, `left_model_endpoint`, `left_response`, `left_comment`, `left_grade`, `right_model_name`, `right_provider`, `right_response`, `right_comment`, `right_grade`
4. Add `save_evaluation(...)` function to insert a row
5. Add `export_to_excel(filepath)` function using `openpyxl` to dump all rows to .xlsx

### Phase 3: LLM Provider Abstraction — `providers.py`
6. Define a model registry dict mapping display name → (provider, model_id, base_url, env_var_name):
   - **OpenAI** (`gpt-4o`, `gpt-4o-mini`): `openai` SDK, default base
   - **Anthropic** (`claude-sonnet-4-20250514`): `anthropic` SDK
   - **Google Gemini** (`gemini-2.0-flash`): `google-generativeai` SDK
   - **Qwen** (`qwen-plus`): `openai` SDK with DashScope base URL
   - **Yi** (`yi-large`): `openai` SDK with 01.AI base URL
7. Implement `call_model(provider, model_name, prompt, api_key)` — dispatches to the correct SDK, falls back to env var key if user key is empty
8. Implement `call_custom_endpoint(base_url, model_name, prompt, api_key)` — uses `openai` SDK with user-supplied base_url for the left-side custom model

### Phase 4: Gradio UI — `app.py`
9. Build Gradio Blocks layout:
   - **Top bar**: Nickname text input (required)
   - **Prompt area**: Shared textbox + "Send to both" button
   - **Two-column `gr.Row`**:
     - **Left** ("Your Model"): API endpoint URL, model name, API key, response display, comment textbox, grade slider (1-10)
     - **Right** ("Reference Model"): model dropdown (from registry), API key (optional, default provided), response display, comment textbox, grade slider (1-10)
   - **Submit Evaluation** button → saves to SQLite
   - **Download Report** button → exports .xlsx file
10. Wire "Send to both" → calls both models, displays responses
11. Wire "Submit Evaluation" → validates inputs, saves to DB, shows success notification
12. Wire "Download Report" → exports SQLite to temp .xlsx, returns as `gr.File`

### Phase 5: Security & Configuration
13. Default API keys from env vars (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `DASHSCOPE_API_KEY`, `YI_API_KEY`), set as HF Spaces secrets. User-provided keys override per-session only — never stored. All keys processed server-side only.
14. Input sanitization: validate URL format for left endpoint, sanitize nickname (max 50 chars)

### Phase 6: Deployment
15. Create HuggingFace Space (Gradio SDK), push code
16. Set repository secrets for default API keys
17. End-to-end test on live Space

---

**Relevant files**
- `app.py` — Main Gradio Blocks UI, event wiring, layout (new)
- `db.py` — SQLite init, save, export functions (new)
- `providers.py` — Model registry, API call dispatch (new)
- `requirements.txt` — Python dependencies (new)
- `README.md` — Update with project info (existing)

**Verification**
1. Launch locally with `python app.py`, verify two-column layout renders
2. Test left column with a local OpenAI-compatible endpoint (e.g. Ollama)
3. Test right column with each provider using default keys
4. Submit evaluation → verify row in SQLite
5. Download report → verify .xlsx has all columns populated
6. Test validation (missing nickname, missing grade → error)
7. Deploy to HF Spaces, set secrets, run full end-to-end

**Further Considerations**
1. **SQLite persistence on HF Spaces**: Ephemeral storage resets on restart. Recommend enabling persistent storage and placing DB under `/data`. Alternative: periodic backup to HF Dataset.
2. **Rate limiting**: Consider adding per-nickname rate limiting to prevent abuse of default API keys.
3. **Streaming responses**: Initial version uses non-streaming calls; streaming can be added later for better UX.
