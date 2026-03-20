import re
import tempfile
import gradio as gr

from db import init_db, save_evaluation, export_to_excel
from providers import MODEL_NAMES, call_model, call_custom_endpoint, MODEL_REGISTRY

# ---------------------------------------------------------------------------
# Initialise database on import
# ---------------------------------------------------------------------------
init_db()

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
URL_RE = re.compile(r"^https?://\S+$")


def _sanitize_nickname(nick: str) -> str:
    return nick.strip()[:50]


def _validate_url(url: str) -> bool:
    return bool(URL_RE.match(url.strip()))


# ---------------------------------------------------------------------------
# Event handlers
# ---------------------------------------------------------------------------

def send_to_both(
    prompt: str,
    left_url: str,
    left_model: str,
    left_key: str,
    right_name: str,
    right_key: str,
):
    """Call both models and return their responses."""
    if not prompt or not prompt.strip():
        raise gr.Error("Please enter a prompt.")

    # Left — custom endpoint
    left_response = ""
    left_err = ""
    if left_url and left_url.strip():
        if not _validate_url(left_url):
            left_err = "⚠️ Invalid URL format. Use http:// or https://."
        else:
            try:
                left_response = call_custom_endpoint(
                    left_url.strip(), left_model.strip() or "default", prompt, left_key
                )
            except Exception as e:
                left_err = f"⚠️ Left model error: {e}"

    # Right — registry model
    right_response = ""
    right_err = ""
    try:
        right_response = call_model(right_name, prompt, right_key)
    except Exception as e:
        right_err = f"⚠️ Right model error: {e}"

    return (
        left_response if not left_err else left_err,
        right_response if not right_err else right_err,
    )


def submit_evaluation(
    nickname: str,
    prompt: str,
    left_url: str,
    left_model: str,
    left_response: str,
    left_comment: str,
    left_grade: int,
    right_name: str,
    right_response: str,
    right_comment: str,
    right_grade: int,
):
    """Validate and persist an evaluation."""
    nickname = _sanitize_nickname(nickname)
    if not nickname:
        raise gr.Error("Nickname is required.")
    if not prompt or not prompt.strip():
        raise gr.Error("Prompt is empty — send a prompt first.")
    if not left_response.strip() and not right_response.strip():
        raise gr.Error("No responses to evaluate — send a prompt first.")
    if left_grade < 1 or left_grade > 10:
        raise gr.Error("Left grade must be between 1 and 10.")
    if right_grade < 1 or right_grade > 10:
        raise gr.Error("Right grade must be between 1 and 10.")

    entry = MODEL_REGISTRY.get(right_name, {})
    right_provider = entry.get("provider", "unknown")

    save_evaluation(
        nickname=nickname,
        prompt=prompt,
        left_model_name=left_model.strip() or "custom",
        left_model_endpoint=left_url.strip(),
        left_response=left_response,
        left_comment=left_comment,
        left_grade=int(left_grade),
        right_model_name=right_name,
        right_provider=right_provider,
        right_response=right_response,
        right_comment=right_comment,
        right_grade=int(right_grade),
    )
    gr.Info("✅ Evaluation saved!")


def download_report():
    """Export all evaluations to a temp .xlsx and return as a downloadable file."""
    tmp = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
    export_to_excel(tmp.name)
    return tmp.name


# ---------------------------------------------------------------------------
# Gradio Blocks UI
# ---------------------------------------------------------------------------

with gr.Blocks(title="LLM Compare") as demo:
    gr.Markdown("# 🔍 LLM Compare\nSide-by-side comparison of two language models.")

    # ---- Top bar: nickname ---------------------------------------------------
    with gr.Row():
        nickname = gr.Textbox(
            label="Your Nickname",
            placeholder="Enter a nickname (required)",
            scale=2,
        )

    # ---- Prompt area ---------------------------------------------------------
    with gr.Row():
        prompt = gr.Textbox(
            label="Prompt",
            placeholder="Type your prompt here…",
            lines=4,
            scale=4,
        )
        send_btn = gr.Button("🚀 Send to Both", variant="primary", scale=1)

    # ---- Two-column layout ---------------------------------------------------
    with gr.Row(equal_height=True):
        # ---- LEFT: custom model ----------------------------------------------
        with gr.Column():
            gr.Markdown("### 🧪 Your Model (OpenAI-compatible endpoint)")
            left_url = gr.Textbox(
                label="API Endpoint URL",
                placeholder="https://your-endpoint.example.com/v1",
            )
            left_model = gr.Textbox(
                label="Model Name",
                placeholder="e.g. my-model-v1",
            )
            left_key = gr.Textbox(
                label="API Key",
                placeholder="(optional)",
                type="password",
            )
            left_response = gr.Textbox(
                label="Response",
                lines=12,
                interactive=False,
            )
            left_comment = gr.Textbox(
                label="Comment",
                placeholder="Your thoughts on this response…",
                lines=2,
            )
            left_grade = gr.Slider(
                minimum=1,
                maximum=10,
                step=1,
                value=5,
                label="Grade (1–10)",
            )

        # ---- RIGHT: reference model ------------------------------------------
        with gr.Column():
            gr.Markdown("### 📚 Reference Model")
            right_name = gr.Dropdown(
                choices=MODEL_NAMES,
                value=MODEL_NAMES[0],
                label="Select Model",
            )
            right_key = gr.Textbox(
                label="API Key (optional — default provided)",
                placeholder="Leave blank to use default key",
                type="password",
            )
            right_response = gr.Textbox(
                label="Response",
                lines=12,
                interactive=False,
            )
            right_comment = gr.Textbox(
                label="Comment",
                placeholder="Your thoughts on this response…",
                lines=2,
            )
            right_grade = gr.Slider(
                minimum=1,
                maximum=10,
                step=1,
                value=5,
                label="Grade (1–10)",
            )

    # ---- Action buttons ------------------------------------------------------
    with gr.Row():
        submit_btn = gr.Button("💾 Submit Evaluation", variant="primary")
        download_btn = gr.Button("📥 Download Report (.xlsx)")
    report_file = gr.File(label="Report", visible=False)

    # ---- Wiring --------------------------------------------------------------
    send_btn.click(
        fn=send_to_both,
        inputs=[prompt, left_url, left_model, left_key, right_name, right_key],
        outputs=[left_response, right_response],
    )

    submit_btn.click(
        fn=submit_evaluation,
        inputs=[
            nickname,
            prompt,
            left_url,
            left_model,
            left_response,
            left_comment,
            left_grade,
            right_name,
            right_response,
            right_comment,
            right_grade,
        ],
        outputs=[],
    )

    download_btn.click(
        fn=download_report,
        inputs=[],
        outputs=[report_file],
    ).then(lambda: gr.update(visible=True), outputs=[report_file])


if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())
