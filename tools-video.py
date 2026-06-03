import streamlit as st
import requests
from typing import List

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="Disney Shorts B-Roll Finder",
    page_icon="🎬",
    layout="centered"
)

OPENROUTER_API_KEY = st.secrets["OPENROUTER_API_KEY"]
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL = "google/gemini-2.5-flash"

MAX_RESULTS_PER_KEYWORD = 3
REQUEST_TIMEOUT = 30

# =====================================================
# UI
# =====================================================

st.title("🎬 Disney Shorts B-Roll Finder")
st.caption("AI-powered Disney B-Roll keyword generator")

st.markdown(
    """
Paste transcript video Shorts, lalu AI akan:
1. Generate keyword B-Roll paling relevan  
2. Cari video YouTube Shorts terkait  
3. Menampilkan hasil terbaik
"""
)

transcript_input = st.text_area(
    "📜 Tempel Transkrip Video",
    placeholder="Paste transcript di sini...",
    height=220
)

# =====================================================
# FUNCTIONS
# =====================================================

def generate_keywords(transcript: str) -> List[str]:

    prompt = f"""
You are a Disney Shorts B-Roll keyword expert.

Based on this transcript, generate EXACTLY 3 highly specific YouTube Shorts search keywords in English.

Rules:
- highly visual
- cinematic b-roll friendly
- Disney parks / attractions / ambience / food / guests / rides if relevant
- avoid generic words
- no explanation
- no numbering
- comma separated only

Transcript:
{transcript}
"""

    try:
        response = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        if "choices" not in data:
            st.error("❌ OpenRouter response invalid")
            with st.expander("Debug Response"):
                st.json(data)
            return []

        ai_text = data["choices"][0]["message"]["content"]

        keywords = []

        for item in ai_text.split(","):
            cleaned = item.strip()

            if cleaned and cleaned not in keywords:
                keywords.append(cleaned)

        return keywords

    except requests.exceptions.Timeout:
        st.error("⌛ Request timeout ke OpenRouter")
        return []

    except Exception as e:
        st.error(f"❌ OpenRouter Error: {str(e)}")
        return []


def search_youtube(keyword: str):

    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": f"{keyword} shorts",
        "type": "video",
        "videoDuration": "short",
        "maxResults": MAX_RESULTS_PER_KEYWORD,
        "key": YOUTUBE_API_KEY
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        return data.get("items", [])

    except Exception as e:
        st.warning(f"⚠️ YouTube Error ({keyword})")
        return []


# =====================================================
# BUTTON ACTION
# =====================================================

if st.button("🚀 Cari Video B-Roll", type="primary"):

    if not transcript_input.strip():
        st.warning("⚠️ Tempel transkrip dulu.")
        st.stop()

    with st.spinner("🧠 AI sedang menganalisis transcript..."):

        keywords = generate_keywords(transcript_input)

    if not keywords:
        st.error("❌ Keyword gagal dibuat.")
        st.stop()

    st.success(
        "✅ Keyword ditemukan:\n\n"
        + " • ".join(keywords)
    )

    st.divider()

    st.subheader("🎥 Hasil B-Roll YouTube Shorts")

    for keyword in keywords:

        st.markdown(f"## 📌 {keyword}")

        videos = search_youtube(keyword)

        if not videos:
            st.warning(f"Tidak ada hasil untuk: {keyword}")
            continue

        for item in videos:

            try:
                video_id = item["id"]["videoId"]
                snippet = item["snippet"]

                title = snippet["title"]
                channel = snippet["channelTitle"]
                thumbnail = snippet["thumbnails"]["high"]["url"]

                youtube_link = (
                    f"https://www.youtube.com/shorts/{video_id}"
                )

                with st.container():

                    col1, col2 = st.columns([1, 2])

                    with col1:
                        st.image(
                            thumbnail,
                            use_container_width=True
                        )

                    with col2:
                        st.markdown(
                            f"### [{title}]({youtube_link})"
                        )
                        st.caption(
                            f"📺 {channel}"
                        )
                        st.link_button(
                            "Open Shorts",
                            youtube_link
                        )

                    st.divider()

            except Exception:
                continue

    st.balloons()