import streamlit as st
import requests

# =====================================================
# CONFIG
# =====================================================

st.set_page_config(
    page_title="Disney Shorts B-Roll Finder",
    page_icon="🎬",
    layout="centered"
)

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]

REQUEST_TIMEOUT = 30

# =====================================================
# UI
# =====================================================

st.title("🎬 Disney Shorts B-Roll Finder")
st.caption("AI-powered Disney B-Roll keyword generator")

st.markdown("""
Paste transcript video Shorts, lalu AI akan:

1. Generate keyword B-Roll paling relevan
2. Cari video YouTube Shorts terkait
3. Menampilkan hasil terbaik
""")

transcript_input = st.text_area(
    "📜 Tempel Transkrip Video",
    placeholder="Paste transcript di sini...",
    height=220
)

# =====================================================
# GEMINI
# =====================================================

def generate_keywords(transcript):

    prompt = f"""
You are a Disney Shorts B-Roll expert.

Generate EXACTLY 3 highly specific YouTube Shorts search keywords.

Rules:
- English only
- highly visual
- cinematic
- Disney park related if applicable
- comma separated only
- no numbering
- no explanation

Transcript:
{transcript}
"""

    try:

        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
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

        response = requests.post(
            url,
            json=payload,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        data = response.json()

        ai_text = (
            data["candidates"][0]
            ["content"]["parts"][0]["text"]
        )

        keywords = [
            x.strip()
            for x in ai_text.split(",")
            if x.strip()
        ]

        return keywords

    except Exception as e:
    st.error("Gemini API sedang sibuk atau mencapai limit.")
    return []

# =====================================================
# YOUTUBE SEARCH
# =====================================================

def search_youtube(keyword):

    url = "https://www.googleapis.com/youtube/v3/search"

    params = {
        "part": "snippet",
        "q": f"{keyword} shorts",
        "type": "video",
        "videoDuration": "short",
        "maxResults": 3,
        "key": YOUTUBE_API_KEY
    }

    try:

        response = requests.get(
            url,
            params=params,
            timeout=REQUEST_TIMEOUT
        )

        response.raise_for_status()

        return response.json().get("items", [])

    except Exception as e:
        st.warning(f"YouTube Error: {e}")
        return []

# =====================================================
# BUTTON
# =====================================================

if st.button("🚀 Cari Video B-Roll", type="primary"):

    if not transcript_input.strip():
        st.warning("Tempel transcript dulu.")
        st.stop()

    with st.spinner("🧠 AI sedang menganalisis transcript..."):

        keywords = generate_keywords(transcript_input)

    if not keywords:
        st.error("Keyword gagal dibuat.")
        st.stop()

    st.success(
        "✅ Keyword ditemukan: "
        + ", ".join(keywords)
    )

    st.divider()

    st.subheader("🎥 Hasil B-Roll YouTube Shorts")

    for keyword in keywords:

        st.markdown(f"## 📌 {keyword}")

        videos = search_youtube(keyword)

        if not videos:
            st.warning(f"Tidak ada hasil untuk {keyword}")
            continue

        for item in videos:

            try:

                video_id = item["id"]["videoId"]

                title = item["snippet"]["title"]

                channel = item["snippet"]["channelTitle"]

                thumbnail = item["snippet"]["thumbnails"]["high"]["url"]

                youtube_link = (
                    f"https://www.youtube.com/shorts/{video_id}"
                )

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

            except:
                pass