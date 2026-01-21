import streamlit as st
import google.generativeai as genai 
from textblob import TextBlob
import pandas as pd
import time

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Please set the GOOGLE_API_KEY in Streamlit Secrets.")

st.set_page_config(page_title="Healix PK", page_icon="🌱", layout="centered")

def generate_response(prompt, attached_file=None):
    instructions = """
    ROLE: You are 'Healix', a supportive mental health assistant for Pakistan.
    
    GUARDRAILS: 
    - ONLY discuss mental health, stress, and well-being.
    - If asked about shopping, travel, or general facts, say: "I am here to support your mental health. I cannot provide advice on shopping or travel. How are you feeling emotionally?"
    
    RESPONSE STYLE:
    - BE BALANCED: Do not give one-sentence answers, but do not exceed 2 short paragraphs.
    - BE EMPATHETIC: Use active listening (e.g., "I hear that you're feeling...").
    - Ask ONE follow-up question to help the user reflect.
    - Use clear, simple language.
    
    PAKISTAN CONTEXT:
    - Be culturally sensitive.
    - ONLY provide Pakistani helplines (Umang: 0311-7786264, Taskeen: 0316-8275336) if there is a CRISIS (suicide/harm).
    - For general sadness, provide a 3-step relaxation exercise instead of a phone number.
    - Crisis helplines (Umang/Taskeen) ONLY for self-harm/suicide mentions.
    
    PAKISTAN-SPECIFIC RESOURCES:
    - If a user asks for a psychiatrist or clinic, suggest they check verified platforms like:
        1. Marham.pk or Oladoc (for verified doctor listings).
        2. The Psychiatry departments at Aga Khan University Hospital or Shifa International.
        3. Mention that Healix cannot vouch for specific individuals, only platforms.
"""
    
    for attempt in range(3):
        try:
            model = genai.GenerativeModel(
                model_name='gemini-2.5-flash', 
                system_instruction=instructions
            )
            
            chat_history = []
            for msg in st.session_state.messages:
                role = "user" if msg["role"] == "user" else "model"
                chat_history.append({"role": role, "parts": [msg["content"]]})
            
            chat_session = model.start_chat(history=chat_history)
            
            content_parts = [prompt]
            if attached_file:
                mime_type = attached_file.type
                content_parts.append({
                    "mime_type": mime_type,
                    "data": attached_file.getvalue()
                })
                
            response = chat_session.send_message(content_parts)
            return response.text
            
        except Exception as e:
            if "429" in str(e) and attempt < 2:
                time.sleep(12) 
                continue
            return "I'm a little overwhelmed right now. Please try again in a moment."

def analyze_sentiment(text):
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    if polarity > 0.5: return "Very Positive", polarity
    elif 0.1 < polarity <= 0.5: return "Positive", polarity
    elif -0.1 <= polarity <= 0.1: return "Neutral", polarity
    elif -0.5 < polarity < -0.1: return "Negative", polarity
    else: return "Very Negative", polarity

def provide_coping_strategy(sentiment):
    strategies = {
        "Very Positive": "Keep up the positive vibes! Share this happiness with someone.",
        "Positive": "It's great to see you're feeling positive. Keep it up!",
        "Neutral": "Feeling neutral is okay. Maybe take a short walk or drink some water.",
        "Negative": "It seems you're feeling down. Try a small relaxing activity like deep breathing.",
        "Very Negative": "I'm concerned about you. Please consider reaching out to a friend or a local helpline."
    }
    return strategies.get(sentiment, "Keep going!")

st.title("🌱 Healix")
st.caption("A safe space for support and reflection in Pakistan.")

with st.sidebar:
    st.markdown("""
        <p style="color: #ff4b4b; font-weight: bold; margin-bottom: 5px;">⚠️ MEDICAL DISCLAIMER</p>
            <p style="color: #ff4b4b; font-size: 0.85rem;">
                This chatbot is an AI tool designed for emotional support and reflection. 
                <b>It is NOT a replacement for a professional therapist, doctor, or medical advice.</b> 
                If you are in crisis, please contact the helplines below immediately.
            </p>
        """, unsafe_allow_html=True)
    
    st.divider()
    st.title("Pakistan Resources")
    st.error("🚨 **Emergency Helplines**")
    st.markdown("""
    - **Umang Pakistan:** 0311-7786264 (24/7)
    - **Taskeen Helpline:** 0316-8275336
    - **Government Health Line:** 1166
    - **Rozan Helpline:** 0304-1111741
    """)
    st.divider()
    if st.button("🗑️ Reset Chat"):
        st.session_state.messages = []
        st.session_state.mood_tracker = []
        st.session_state.voice_draft = ""
        st.session_state.awaiting_review = False
        st.rerun()

if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'mood_tracker' not in st.session_state:
    st.session_state.mood_tracker = []
if 'voice_draft' not in st.session_state:
    st.session_state.voice_draft = ""
if 'awaiting_review' not in st.session_state:
    st.session_state.awaiting_review = False

for idx, message in enumerate(st.session_state.messages):
    col_msg, col_copy = st.columns([9, 1])

    with col_msg:
        with st.chat_message(message["role"]):
             st.markdown(message["content"])

    with col_copy:
        copy_key = f"copy_{idx}"
       
        if st.button("📋", key=copy_key, help=f"Copy {message['role']} message"):
            st.toast("Click the copy icon in the text box below ✅")
            st.code(message["content"], language="markdown")

if st.session_state.awaiting_review:
    st.info("🎙️ Transcribed text — review or edit before sending")

    edited_text = st.text_area(
        "Your message:",
        value=st.session_state.voice_draft,
        height=120
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🚀 Send"):
            st.session_state.ready_to_process = edited_text
            st.session_state.voice_draft = ""
            st.session_state.awaiting_review = False
            st.rerun()

    with col2:
        if st.button("❌ Discard"):
            st.session_state.voice_draft = ""
            st.session_state.awaiting_review = False
            st.rerun()

user_input = st.chat_input(
    "How are you feeling right now?", 
    accept_file=True, 
    file_type=["png", "jpg", "jpeg"],
    accept_audio=True
)

text_content = ""
active_file = None

if user_input:
    if user_input.audio:
        with st.status("Transcribing audio...", expanded=False):
            try:
                audio_bytes = user_input.audio.getvalue()
                transcriber = genai.GenerativeModel(
                model_name="gemini-2.5-flash"
            )
                transcript_response = transcriber.generate_content([
                   """
                   You are a speech-to-text engine.
                   Transcribe the audio EXACTLY as spoken.

                   Rules:
                   - Do NOT paraphrase
                   - Do NOT summarize
                   - Do NOT guess unclear words
                   - Keep names, accents, and grammar exactly as heard
                   - If a word is unclear, write [unclear]
                   - Return ONLY the raw transcript text
                  """,
                   {
                      "mime_type": user_input.audio.type,
                      "data": audio_bytes
                   }
             ])

                st.session_state.voice_draft = transcript_response.text.strip()
                st.session_state.awaiting_review = True
                st.rerun()

            except Exception as e:
                st.error("Transcription failed. Please try typing.")
    else:
        text_content = user_input.text if user_input.text else "Sent a file."
        active_file = user_input.files[0] if user_input.files else None

elif "ready_to_process" in st.session_state:
    text_content = st.session_state.ready_to_process
    del st.session_state.ready_to_process

if text_content and not st.session_state.awaiting_review:
    st.session_state.messages.append({"role": "user", "content": text_content})
    
    with st.chat_message("user"):
        st.markdown(text_content)
        if active_file:
            st.image(active_file)

    sentiment, polarity = analyze_sentiment(text_content)
    st.session_state.mood_tracker.append((text_content, sentiment, polarity))
    strategy = provide_coping_strategy(sentiment)

    with st.chat_message("assistant"):
        response = generate_response(text_content, attached_file=active_file)
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})

        if polarity < 0:
            st.info(f"💡 Tip: {strategy}")