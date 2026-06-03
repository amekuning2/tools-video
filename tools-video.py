import streamlit as st
import requests

# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="Disney Shorts B-Roll Finder",
    page_icon="🎬",
    layout="centered"
)

# =====================================
# API KEYS
# =====================================

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]

# =====================================
# UI
# =====================================

st.title("🎬 Disney Shorts B-Roll Finder")
st.write("Generate keyword B-Roll otomatis dari transcript video.")

transcript = st.text_area(
    "📜 Tempel Transkrip Video",
    height=200
)

# =====================================
# GEMINI
# =====================================

def generate_keywords(text):

    prompt = f"""
Generate EXACTLY 3 YouTube Shorts search keywords.

Rules:
- English only
- comma separated
- no numbering
- no explanation

Transcript:

{text}
"""

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-3.1-flash:generateContent?key={GEMINI_API_KEY}"
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ]
    }

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=30
        )

        if response.status_code != 200:
            st.error("Gemini Raw Response:")
            st.code(response.text)
            return []

        data = response.json()

        result = data["candidates"][0]["content"]["parts"][0]["text"]

        keywords = [
            x.strip()
            for x in result.split(",")
            if x.strip()
        ]

        return keywords

    except Exception as e:

        st.error(f"Gemini Error: {e}")

        return []

# =====================================
# YOUTUBE SEARCH
# =====================================

def search_youtube(keyword):

    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": keyword,
        "type": "video",
        "maxResults": 3,
        "key": YOUTUBE_API_KEY
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

        return data.get("items", [])

    except Exception as e:

        st.error(f"YouTube Error: {e}")

        return []

# =====================================
# BUTTON
# =====================================

if st.button("🚀 Cari Video B-Roll"):

    if not transcript.strip():

        st.warning("Masukkan transcript terlebih dahulu.")

    else:

        keywords = generate_keywords(transcript)

        if not keywords:

            st.error("Keyword gagal dibuat.")

        else:

            st.success(
                "Keyword: " + ", ".join(keywords)
            )

            st.subheader("🎥 Hasil YouTube")

            for keyword in keywords:

                st.markdown(f"### 📌 {keyword}")

                videos = search_youtube(keyword)

                if not videos:

                    st.warning("Tidak ada hasil.")

                    continue

                for item in videos:

                    try:

                        video_id = item["id"]["videoId"]

                        title = item["snippet"]["title"]

                        link = (
                            f"https://www.youtube.com/watch?v={video_id}"
                        )

                        st.markdown(
                            f"- [{title}]({link})"
                        )

                    except:

                        pass
