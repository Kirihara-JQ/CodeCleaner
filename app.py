import os
import torch
import gradio as gr
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel
import time
from datetime import datetime

# ================= 1. 基础配置 =================
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

# 获取当前脚本所在的绝对路径
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
LORA_PATH = os.path.join(CURRENT_DIR, "models")

BASE_MODEL_PATH = "Qwen/Qwen2.5-Coder-1.5B-Instruct"


def get_log(message):
    timestamp = datetime.now().strftime("%H:%M:%S")
    return f"[{timestamp}] {message}"


print("🌌 [SYSTEM] Initializing Neural Network...")

try:
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL_PATH)
    if torch.cuda.is_available():
        device = "cuda"
        print("✅ GPU Detected.")
        model = AutoModelForCausalLM.from_pretrained(BASE_MODEL_PATH, torch_dtype=torch.float16, device_map="auto")
    else:
        device = "cpu"
        print("⚠️ CPU Mode Active.")
        model = AutoModelForCausalLM.from_pretrained(BASE_MODEL_PATH, device_map="cpu", torch_dtype=torch.float32)

    model = PeftModel.from_pretrained(model, LORA_PATH)
    model.eval()
    print("🚀 Core Module Loaded!")
except Exception as e:
    print(f"❌ Error: {e}")
    exit()


# ================= 2. 核心逻辑 =================
def clean_code_engine(user_code, temperature, max_tokens, history, current_logs):
    if not user_code.strip():
        return history, current_logs + "\n" + get_log("⚠️ Warning: Empty input."), None, "🔴 IDLE", "0.00s"

    start_time = time.time()
    process_log = current_logs + "\n" + get_log("🚀 Processing...")

    system_prompt = "你是一个资深的 Python 代码重构专家。请将用户的代码重构为符合 Google Style 规范、包含完整文档注释（Docstring）和类型提示（Type Hints）的高质量代码。"
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_code}
    ]
    text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

    try:
        with torch.no_grad():
            generated_ids = model.generate(
                model_inputs.input_ids,
                max_new_tokens=int(max_tokens),
                temperature=temperature,
                top_p=0.9
            )

        generated_ids = [output_ids[len(input_ids):] for input_ids, output_ids in
                         zip(model_inputs.input_ids, generated_ids)]
        response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

        elapsed_time = time.time() - start_time
        time_str = f"{elapsed_time:.2f}s"

        if history is None: history = []
        history.append([user_code, response])

        filename = f"refactored_code_{int(time.time())}.py"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(response)

        return history, process_log + "\n" + get_log("✅ Done."), filename, "🟢 READY", time_str

    except Exception as e:
        return history, process_log + "\n" + get_log(f"❌ Error: {e}"), None, "🔴 ERROR", "0.00s"


def clear_all():
    return [], "System Ready...", None, "🟢 READY", "0.00s", ""

# ================= 3. 定制 CSS =================
custom_css = """
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Rajdhani:wght@500;700&display=swap');

/* 1. 根变量覆盖 */
:root, body, .gradio-container {
    --body-background-fill: #050505 !important;
    --block-background-fill: #111827 !important;
    --block-border-color: #1f2937 !important;
    --input-background-fill: #0f172a !important;
    --text-color: #e2e8f0 !important;
    --body-text-color: #e2e8f0 !important;
    --block-label-background-fill: transparent !important;
    --background-fill-primary: #111827 !important;
}

/* 2. 基础组件 */
.block, .panel, .form {
    background-color: var(--block-background-fill) !important;
    border-color: var(--block-border-color) !important;
}

/* 3. 聊天框样式 */
#chatbot {
    background-color: #080a0f !important;
    border: 1px solid #334155 !important;
    height: 650px !important;
}

/* --- 用户气泡 (深灰底荧光蓝字) --- */
.message.user, .message.user > div {
    background-color: #0f172a !important;
    color: #00f2ff !important;
    border: 1px solid #00f2ff !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* --- 机器人气泡 (深灰底荧光绿字) --- */
.message.bot, .message.bot > div {
    background-color: #0f172a !important;
    color: #00ff9d !important;            
    border: 1px solid #00ff9d !important; 
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
}

/* --- 代码块容器通用样式 --- */
.message pre {
    margin: 10px 0 !important;
    padding: 15px !important;
    background-color: #0d1117 !important; 
    border: 1px solid #0d1117 !important; 
    border-radius: 6px !important;
}

/* 代码字体通用设置 */
.message pre code {
    line-height: 2.0 !important; 
    font-family: 'JetBrains Mono', 'Microsoft YaHei', monospace !important;
    font-size: 14px !important;
    background-color: transparent !important;
    white-space: pre-wrap !important;
}

/* 强制用户代码全蓝 */
.message.user pre code, 
.message.user pre code span {
    color: #00f2ff !important;
}

/* 强制Agent代码全绿 */
.message.bot pre code, 
.message.bot pre code span {
    color: #00ff9d !important;
}

/* 5. 输入框 */
textarea, input {
    background-color: #0f172a !important;
    color: #00f2ff !important;
    border: 1px solid #0f172a !important;
}

/* 6. 标签 */
span.block-label {
    background: transparent !important;
    color: #94a3b8 !important;
    font-weight: bold;
}

/* 7. 标题 */
.header-title {
    font-family: 'Rajdhani', sans-serif;
    font-size: 3.5rem;
    font-weight: 700;
    color: #fff;
    text-align: center;
    text-shadow: 0 0 10px #00f2ff;
    letter-spacing: 4px;
    margin-bottom: 5px;
}
.header-sub {
    color: #3b82f6;
    text-align: center;
    font-family: 'JetBrains Mono', monospace;
    letter-spacing: 2px;
    margin-bottom: 20px;
}

/* 8. 状态指示器 */
.status-indicator textarea {
    text-align: center !important;
    font-weight: 900 !important;
    font-size: 1.2rem !important;
    color: #00ff9d !important;
    background-color: #000 !important;
    border: 1px solid #00ff9d !important;
}

footer { display: none !important; }
"""


# ================= 4. 界面布局 =================
with gr.Blocks(css=custom_css, title="Code Cleaner Ultimate") as demo:
    with gr.Column():
        gr.HTML("""
            <div class="header-title">CODE CLEANER // ULTIMATE</div>
            <div class="header-sub">SYSTEM READY | QWEN2.5 ENGINE ACTIVE</div>
        """)

    with gr.Row():
        # 左侧 HUD
        with gr.Column(scale=1, min_width=320, variant="panel"):
            gr.Markdown("### 📡 SYSTEM STATUS")
            with gr.Row():
                status_box = gr.Textbox(value="🟢 READY", label="CORE STATUS", interactive=False,
                                        elem_classes="status-indicator")
                time_box = gr.Textbox(value="0.00s", label="LAST RUN", interactive=False,
                                      elem_classes="status-indicator")

            gr.Markdown("---")
            gr.Markdown("### 🎛️ PARAMETERS")
            temp_slider = gr.Slider(0.1, 1.0, value=0.6, step=0.1, label="Creativity")
            token_slider = gr.Slider(256, 2048, value=1024, step=128, label="Max Tokens")

            gr.Markdown("---")
            gr.Markdown("### 📟 SYSTEM LOGS")
            log_box = gr.Textbox(value="System initialized...", lines=10, max_lines=10, label=None, interactive=False)

            gr.Markdown("---")
            download_btn = gr.File(label="📥 EXPORT RESULT", visible=True)

        # 右侧 终端
        with gr.Column(scale=3, variant="panel"):
            gr.Markdown("### 💻 TERMINAL INTERFACE")
            chatbot = gr.Chatbot(label="Conversation", elem_id="chatbot")

            with gr.Row():
                user_input = gr.Textbox(show_label=False, placeholder=">>> Input Legacy Code Here...", lines=5)

            with gr.Row():
                clear_btn = gr.Button("RESET SYSTEM", variant="secondary")
                submit_btn = gr.Button("INITIALIZE REFACTOR", variant="primary")

    # 事件
    submit_btn.click(
        fn=lambda: ("🟡 PROCESSING", "Computing..."),
        inputs=None, outputs=[status_box, time_box], queue=False
    ).then(
        fn=clean_code_engine,
        inputs=[user_input, temp_slider, token_slider, chatbot, log_box],
        outputs=[chatbot, log_box, download_btn, status_box, time_box]
    ).then(
        fn=lambda: "", inputs=None, outputs=[user_input]
    )

    user_input.submit(
        fn=lambda: ("🟡 PROCESSING", "Computing..."),
        inputs=None, outputs=[status_box, time_box], queue=False
    ).then(
        fn=clean_code_engine,
        inputs=[user_input, temp_slider, token_slider, chatbot, log_box],
        outputs=[chatbot, log_box, download_btn, status_box, time_box]
    ).then(
        fn=lambda: "", inputs=None, outputs=[user_input]
    )

    clear_btn.click(clear_all, None, [chatbot, log_box, download_btn, status_box, time_box, user_input])

# 启动
if __name__ == "__main__":
    demo.queue()
    demo.launch(inbrowser=True)