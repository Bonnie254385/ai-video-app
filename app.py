import streamlit as st
import os
import requests
from supabase import create_client
from datetime import date

# --- SECRETS ---
FAL_KEY = st.secrets.get("FAL_KEY", "")
SUPABASE_URL = st.secrets.get("SUPABASE_URL", "")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY", "")
STRIPE_LINK = "https://buy.stripe.com/your_link" 
ADMIN_PASS = "Boss123" 

st.set_page_config(page_title="AI Video Pro")

# Connect Database
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    st.warning("Setup in progress... Please add your Database Keys.")
    st.stop()

# --- LOGIN ---
if 'user_email' not in st.session_state:
    st.title("🎬 AI Video Maker")
    email = st.text_input("Enter Email:").lower()
    if st.button("Start"):
        if email:
            st.session_state.user_email = email
            st.rerun()
    st.stop()

email = st.session_state.user_email

# --- CHECK LIMITS ---
res = supabase.table("user_credits").select("*").eq("email", email).execute()
if not res.data:
    supabase.table("user_credits").insert({"email": email}).execute()
    user = {"email": email, "credits_used": 0, "is_pro": False, "last_reset": str(date.today())}
else:
    user = res.data[0]

if user['last_reset'] != str(date.today()):
    supabase.table("user_credits").update({"credits_used": 0, "last_reset": str(date.today())}).eq("email", email).execute()
    user['credits_used'] = 0

# --- APP UI ---
st.title("🎬 Generate AI Video")
is_admin = st.sidebar.text_input("Admin", type="password") == ADMIN_PASS

if user['is_pro'] or is_admin:
    st.sidebar.success("UNLIMITED MODE")
    can_gen = True
else:
    left = 2 - user['credits_used']
    st.sidebar.info(f"Credits: {max(0, left)} left today")
    can_gen = user['credits_used'] < 2

prompt = st.text_area("Video Description:", placeholder="A cat flying through space...")
platform = st.selectbox("Format", ["TikTok (9:16)", "YouTube (16:9)"])

if st.button("Generate"):
    if not can_gen:
        st.error("Limit reached! Upgrade for more.")
        st.link_button("🚀 Upgrade to Pro", STRIPE_LINK)
    elif not prompt:
        st.warning("Write a prompt first!")
    else:
        with st.spinner("AI is thinking..."):
            aspect = "9:16" if "TikTok" in platform else "16:9"
            headers = {"Authorization": f"Key {FAL_KEY}", "Content-Type": "application/json"}
            payload = {"prompt": prompt, "aspect_ratio": aspect}
            
            # This uses the Luma Dream Machine model
            response = requests.post("https://queue.fast-api.ai/fal-ai/luma-dream-machine", json=payload, headers=headers)
            
            if response.status_code == 200:
                video_url = response.json().get("video", {}).get("url")
                st.video(video_url)
                if not is_admin:
                    supabase.table("user_credits").update({"credits_used": user['credits_used'] + 1}).eq("email", email).execute()
            else:
                st.error("Error. Check your API Keys.")
