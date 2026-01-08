import streamlit as st
import google.generativeai as genai 
from textblob import TextBlob
import pandas as pd

if "GOOGLE_API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
else:
    st.error("Please set the GOOGLE_API_KEY in Streamlit Secrets.")

st.set_page_config(page_title="Healix PK", page_icon="🌱", layout="centered")

def generate_response(prompt):
    instructions = """You are a mental health assistant for users in Pakistan. 
    1. For general feelings like 'sad', 'exhausted', or 'upset', do NOT provide helpline numbers. Instead, listen, validate, and offer a small coping tip.
    2. ONLY provide the Pakistani helplines (Umang, Taskeen, 1166) if the user mentions:
       - Self-harm or suicide.
       - Harming others.
       - Deep hopelessness or an immediate crisis.
    3. Keep responses concise and avoid being repetitive.
    4. NEVER mention US/UK helplines."""
    
    try:
        model = genai.GenerativeModel(
            model_name='gemini-3-flash-preview', 
            system_instruction=instructions
        )
        return model.generate_content(prompt).text
    except Exception:

        try:
            model = genai.GenerativeModel(
                model_name='gemini-2.5-flash',
                system_instruction=instructions
            )
            return model.generate_content(prompt).text
        except Exception as e:

            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            return f"⚠️ Technical Error. Available models on your key: {available_models}"

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
    if st.button("🗑️ Clear Chat History"):
        st.session_state.messages = []
        st.session_state.mood_tracker = []
        st.rerun()

if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'mood_tracker' not in st.session_state:
    st.session_state.mood_tracker = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if user_input := st.chat_input("How are you feeling right now?"):
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    sentiment, polarity = analyze_sentiment(user_input)
    st.session_state.mood_tracker.append((user_input, sentiment, polarity))
    strategy = provide_coping_strategy(sentiment)

    with st.chat_message("assistant"):
        response = generate_response(user_input)
        st.markdown(response)
        st.session_state.messages.append({"role": "assistant", "content": response})
        if polarity < 0:
            st.info(f"💡 Tip: {strategy}")