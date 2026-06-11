import streamlit as st
import requests
import json
import re

# =====================================
# PAGE CONFIG
# =====================================

st.set_page_config(
    page_title="B-Roll Finder — Long Video",
    page_icon="🎬",
    layout="centered"
)

# =====================================
# API KEYS
# =====================================

GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
YOUTUBE_API_KEY = st.secrets["YOUTUBE_API_KEY"]

# =====================================
# STYLING
# =====================================

st.markdown("""
<style>
    .segment-header {
        background: linear-gradient(90deg, #1a1a2e 0%, #16213e 100%);
        border-left: 4px solid #e94560;
        padding: 10px 16px;
        border-radius: 0 8px 8px 0;
        margin: 16px 0 8px 0;
        color: #ffffff;
        font-weight: 600;
        font-size: 1.05rem;
    }
    .keyword-badge {
        display: inline-block;
        background: #e94560;
        color: white;
        padding: 3px 10px;
        border-radius: 20px;
        font-size: 0.82rem;
        margin: 2px 4px 2px 0;
        font-weight: 500;
    }
    .video-card {
        background: #0f3460;
        border-radius: 8px;
        padding: 8px 12px;
        margin: 4px 0;
        color: #e0e0e0;
        font-size: 0.9rem;
    }
    .info-box {
        background: #1a1a2e;
        border: 1px solid #e94560;
        border-radius: 8px;
        padding: 10px 14px;
        color: #e0e0e0;
        font-size: 0.88rem;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

# =====================================
# UI HEADER
# =====================================

st.title("🎬 B-Roll Finder — Long Video")
st.write("Generate B-Roll keywords per segment from long video transcripts.")

# =====================================
# INPUT MODE TOGGLE
# =====================================

input_mode = st.radio(
    "📥 Input Method",
    ["🔗 YouTube URL (Auto Fetch)", "📋 Paste Transcript Manually"],
    horizontal=True
)

transcript = ""

# ---- AUTO FETCH ----
if input_mode == "🔗 YouTube URL (Auto Fetch)":

    youtube_url = st.text_input(
        "YouTube Video URL",
        placeholder="https://www.youtube.com/watch?v=..."
    )

    if st.button("📥 Fetch Transcript"):

        if not youtube_url.strip():
            st.warning("Masukkan URL YouTube terlebih dahulu.")

        else:
            try:
                from youtube_transcript_api import YouTubeTranscriptApi
                from youtube_transcript_api._errors import (
                    TranscriptsDisabled,
                    NoTranscriptFound,
                    VideoUnavailable
                )

                # Extract video ID
                video_id_match = re.search(
                    r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{11})",
                    youtube_url
                )

                if not video_id_match:
                    st.error("URL tidak valid. Pastikan format URL benar.")
                else:
                    video_id = video_id_match.group(1)

                    with st.spinner("Fetching transcript..."):

                        try:
                            transcript_list = YouTubeTranscriptApi.get_transcript(
                                video_id,
                                languages=["en", "id"]
                            )
                        except NoTranscriptFound:
                            # Try any available language
                            transcripts = YouTubeTranscriptApi.list_transcripts(video_id)
                            transcript_obj = next(iter(transcripts))
                            transcript_list = transcript_obj.fetch()

                        full_transcript = " ".join(
                            [item["text"] for item in transcript_list]
                        )

                        st.session_state["fetched_transcript"] = full_transcript
                        st.success(
                            f"✅ Transcript fetched! "
                            f"({len(full_transcript.split())} words)"
                        )

            except ImportError:
                st.error(
                    "Package `youtube-transcript-api` belum terinstall. "
                    "Tambahkan ke `requirements.txt` Streamlit."
                )
            except TranscriptsDisabled:
                st.error(
                    "❌ Transcript/CC dinonaktifkan untuk video ini. "
                    "Gunakan manual paste dari youtubetotranscript.com"
                )
            except VideoUnavailable:
                st.error("❌ Video tidak tersedia atau private.")
            except Exception as e:
                st.error(f"❌ Gagal fetch transcript: {e}")
                st.info(
                    "💡 Coba gunakan manual paste dari "
                    "[youtubetotranscript.com](https://youtubetotranscript.com/transcript)"
                )

    # Show fetched transcript preview
    if "fetched_transcript" in st.session_state:
        transcript = st.session_state["fetched_transcript"]
        with st.expander("👁 Preview Transcript (100 words)"):
            preview = " ".join(transcript.split()[:100]) + "..."
            st.write(preview)

        if st.button("🗑 Clear Fetched Transcript"):
            del st.session_state["fetched_transcript"]
            st.rerun()

# ---- MANUAL PASTE ----
else:

    st.markdown(
        '<div class="info-box">💡 Ambil transcript dari '
        '<a href="https://youtubetotranscript.com/transcript" target="_blank">'
        'youtubetotranscript.com</a> lalu paste di bawah.</div>',
        unsafe_allow_html=True
    )

    if "manual_transcript" not in st.session_state:
        st.session_state.manual_transcript = ""

    transcript = st.text_area(
        "📜 Paste Transcript",
        value=st.session_state.manual_transcript,
        height=250,
        key="manual_transcript_box",
        placeholder="Paste full transcript here..."
    )

    if st.button("🗑 Clear"):
        st.session_state.manual_transcript = ""
        st.rerun()

# =====================================
# MODEL SELECTOR
# =====================================

model = st.selectbox(
    "🤖 Gemini Model",
    [
        "gemini-2.5-flash",
        "gemini-2.5-flash-lite-preview-06-17",
        "gemini-2.0-flash",
        "gemini-1.5-flash",
    ]
)

# =====================================
# GEMINI — SEGMENTATION + KEYWORDS
# =====================================

def generate_segments_and_keywords(text, model):
    """
    Ask Gemini to:
    1. Split transcript into topic-based segments
    2. Generate 5 B-roll keywords per segment
    Returns list of dicts: [{segment_title, keywords: [...]}, ...]
    """

    prompt = f"""
You are a B-Roll video research assistant for long-form video content.

Analyze the transcript below and do the following:
1. Identify distinct topic/context shifts (segments). Each segment should represent a clear change in subject matter, story beat, or theme.
2. Give each segment a short descriptive title (max 6 words).
3. For each segment, generate EXACTLY 5 B-roll search keywords.

Keyword rules:
- English only
- Specific and visual (optimized to find B-roll footage or reference videos on YouTube)
- Use real names (people, places, products, games, movies, shows, brands) if mentioned
- Do NOT invent topics not present in the transcript
- Avoid overly generic terms like "people talking" or "daily life"
- Each keyword should be different and cover a different visual angle of the segment

Return ONLY valid JSON — no explanation, no markdown fences, no preamble.

Format:
[
  {{
    "segment_title": "Title of segment",
    "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
  }},
  ...
]

Transcript:
{text}
"""

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?key={GEMINI_API_KEY}"
    )

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "temperature": 0.4
        }
    }

    try:

        response = requests.post(url, json=payload, timeout=60)

        if response.status_code == 429:
            st.error(
                "🚫 Gemini API quota reached. "
                "Please try again later or use a different API key."
            )
            return []

        elif response.status_code != 200:
            st.error(f"Gemini API Error ({response.status_code}): {response.text}")
            return []

        data = response.json()
        raw = data["candidates"][0]["content"]["parts"][0]["text"]

        # Strip markdown fences if present
        raw = re.sub(r"```json|```", "", raw).strip()

        segments = json.loads(raw)
        return segments

    except json.JSONDecodeError as e:
        st.error(f"❌ Failed to parse Gemini response as JSON: {e}")
        st.code(raw, language="text")
        return []

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

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        return data.get("items", [])

    except Exception as e:
        st.error(f"YouTube Error ({keyword}): {e}")
        return []

# =====================================
# MAIN BUTTON
# =====================================

# Resolve final transcript value
if input_mode == "🔗 YouTube URL (Auto Fetch)":
    final_transcript = st.session_state.get("fetched_transcript", "").strip()
else:
    final_transcript = transcript.strip()

st.divider()

if st.button("🚀 Generate B-Roll by Segment", type="primary"):

    if not final_transcript:
        st.warning("Transcript kosong. Fetch dari URL atau paste manual terlebih dahulu.")

    else:

        word_count = len(final_transcript.split())
        st.info(f"📝 Processing transcript ({word_count} words)...")

        with st.spinner("Gemini is analyzing segments and generating keywords..."):
            segments = generate_segments_and_keywords(final_transcript, model)

        if not segments:
            st.error("Gagal generate segmentasi. Coba lagi atau ganti model.")

        else:

            st.success(f"✅ {len(segments)} segments detected!")

            # ---- BUILD COPY TEXT ----
            copy_text = "B-ROLL RESULTS — LONG VIDEO\n"
            copy_text += "=" * 40 + "\n\n"

            for idx, seg in enumerate(segments, 1):

                seg_title = seg.get("segment_title", f"Segment {idx}")
                keywords = seg.get("keywords", [])

                # Segment header
                st.markdown(
                    f'<div class="segment-header">🎬 Segment {idx}: {seg_title}</div>',
                    unsafe_allow_html=True
                )

                copy_text += f"SEGMENT {idx}: {seg_title}\n"

                # Keywords badges
                badge_html = "".join(
                    f'<span class="keyword-badge">🔍 {kw}</span>'
                    for kw in keywords
                )
                st.markdown(badge_html, unsafe_allow_html=True)

                copy_text += "Keywords: " + ", ".join(keywords) + "\n\n"

                # YouTube search per keyword
                with st.expander(f"🎥 YouTube Results for Segment {idx}"):

                    for kw in keywords:

                        st.markdown(f"**📌 {kw}**")
                        copy_text += f"  📌 {kw}\n"

                        videos = search_youtube(kw)

                        if not videos:
                            st.caption("Tidak ada hasil.")
                            copy_text += "  Tidak ada hasil.\n\n"
                            continue

                        for item in videos:
                            try:
                                video_id = item["id"]["videoId"]
                                title = item["snippet"]["title"]
                                link = f"https://www.youtube.com/watch?v={video_id}"
                                st.markdown(f"- [{title}]({link})")
                                copy_text += f"  - {title}\n    {link}\n"
                            except Exception:
                                pass

                        copy_text += "\n"

                copy_text += "-" * 40 + "\n\n"

            # ---- DOWNLOAD & COPY ----
            st.divider()
            st.subheader("📋 Export Results")

            col1, col2 = st.columns(2)

            with col1:
                st.download_button(
                    label="💾 Download Results (.txt)",
                    data=copy_text,
                    file_name="broll_longvideo_results.txt",
                    mime="text/plain",
                    use_container_width=True
                )

            with col2:
                st.code(copy_text[:500] + "\n...[truncated]", language="text")