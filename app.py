# -*- coding: utf-8 -*-
"""app.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1X9hkW6j052EjB-V8ebl0zuqdAwvJWds9
"""

import os
import time
import requests
import gradio as gr
from huggingface_hub import login
from dotenv import load_dotenv
from PIL import Image
import io

# Load environment variables
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN")
if HF_TOKEN is None:
    raise ValueError("Hugging Face token not found. Please set HF_TOKEN in the .env file.")

# Authenticate with Hugging Face
login(token=HF_TOKEN)

# API Endpoints
WHISPER_API_URL = "https://api-inference.huggingface.co/models/openai/whisper-large-v3"
TRANSLATION_API_URL = "https://api-inference.huggingface.co/models/facebook/nllb-200-distilled-600M"
IMAGE_API_URL = "https://api-inference.huggingface.co/models/black-forest-labs/FLUX.1-schnell"
TEXT_GEN_API_URL = "https://api-inference.huggingface.co/models/deepseek-ai/DeepSeek-R1-Distill-Qwen-32B"

# Headers for API requests
headers = {"Authorization": f"Bearer {HF_TOKEN}"}

def query_whisper(audio_file):
    with open(audio_file, "rb") as f:
        data = f.read()
    response = requests.post(WHISPER_API_URL, headers=headers, data=data)
    return response.json()

def query_translation(text, max_retries=5, retry_delay=10):
    payload = {"inputs": text, "parameters": {"src_lang": "tam_Taml", "tgt_lang": "eng_Latn"}}
    for _ in range(max_retries):
        response = requests.post(TRANSLATION_API_URL, headers=headers, json=payload)
        result = response.json()
        if isinstance(result, list) and len(result) > 0:
            return result[0]["translation_text"]
        elif isinstance(result, dict) and "translation_text" in result:
            return result["translation_text"]
        time.sleep(retry_delay)
    return "Translation failed."

def query_flux_image(prompt, max_retries=5, retry_delay=10):
    payload = {"inputs": prompt}
    for _ in range(max_retries):
        response = requests.post(IMAGE_API_URL, headers=headers, json=payload)
        if response.status_code == 200 and response.headers.get('Content-Type', '').startswith('image/'):
            return Image.open(io.BytesIO(response.content))
        time.sleep(retry_delay)
    return None

def query_text_generation(prompt, max_retries=5, retry_delay=10):
    payload = {"inputs": prompt}
    for _ in range(max_retries):
        response = requests.post(TEXT_GEN_API_URL, headers=headers, json=payload)
        result = response.json()
        print("Text Generation API Response:", result)  # Debugging log
        if isinstance(result, dict) and "generated_text" in result:
            return result["generated_text"]
        elif isinstance(result, list) and len(result) > 0 and "generated_text" in result[0]:
            return result[0]["generated_text"]
        time.sleep(retry_delay)
    return "Text generation failed."

def process_audio(audio_file):
    if not audio_file:
        return "No audio file provided.", "", None, ""
    try:
        whisper_result = query_whisper(audio_file)
        tamil_text = whisper_result.get("text", "Error in transcription")
        english_text = query_translation(tamil_text)
        generated_image = query_flux_image(english_text)
        generated_text = query_text_generation(english_text)
        return tamil_text, english_text, generated_image, generated_text
    except Exception as e:
        return f"Error: {str(e)}", "", None, ""

# Gradio Interface
iface = gr.Interface(
    fn=process_audio,
    inputs=gr.Audio(type="filepath", label="Upload Tamil Audio"),
    outputs=[
        gr.Textbox(label="Tamil Transcription"),
        gr.Textbox(label="English Translation"),
        gr.Image(label="Generated Image"),
        gr.Textbox(label="Generated Text"),
    ],
    title="Speech-to-Image & Text Generation",
    description="Upload a Tamil audio file to generate transcription, English translation, AI-generated image, and further text expansion.",
)

iface.launch(share=True, server_name="0.0.0.0", server_port=7860)