# The live demo: a chat page made with Gradio, for a ZeroGPU Space of Hugging Face. The chat
# logic is in chat.py. make demo runs the same page on the Mac with llama-swap.
# Run: python app.py (the Space) or make demo (the Mac)

import os
import sys
from pathlib import Path

# The Space has no .env, so the demo profile is the default there. make demo sets mac
os.environ.setdefault("MRAG_PROFILE", "demo")
# On the Space the platform code lies in src/ next to this file. In the repo it is installed
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import chat
import gradio as gr
import spaces

from mrag import service
from mrag.config import get_settings

# Loads the model before the first visitor, because ZeroGPU wants models loaded at start
service.start()

# On the Space this runs on the shared GPU for at most 60 s, the time limit of the demo
# profile. Outside ZeroGPU the decorator returns the function unchanged
answer = spaces.GPU(duration=60)(chat.answer)

note = chat.QUOTA_NOTE if get_settings().profile == "demo" else chat.LOCAL_NOTE
demo = gr.ChatInterface(
    answer,
    title="multiagent-ai-lab demo",
    description=f"{note} A plain chat for now. Questions over files come later.",
    api_name="chat",
)

if __name__ == "__main__":
    demo.launch()
