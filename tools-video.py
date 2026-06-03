import streamlit as st  # type: ignore
import requests

# Set tampilan biar responsif di HP
st.set_page_config(page_title="Disney B-Roll Generator", page_icon="🎬", layout="centered")

# API Key YouTube lo yang udah aktif
YOUTUBE_API_KEY = "AIzaSyC91IKSHYHqmuUwhJVyEr-HA9S0Shy0Vps"

st.title("🎬 Disney Shorts B-Roll Finder")
st.write("Versi Super Stabil - Anti Error Limit!")

transkrip_input = st.text_area(
    "Tempel Transkrip Video Di Sini:", 
    value="",
    height=150
)

if st.button("🚀 Cari Video B-Roll", type="primary"):
    with st.spinner("🧠 Meminta AI menganalisis transkrip..."):
        # Kita pakai API publik alternatif yang super stabil buat generate keyword
        try:
            prompt = f"Berikan TEPAT 3 keyword pencarian video YouTube Shorts bahasa Inggris yang paling spesifik berdasarkan transkrip ini. Format wajib dipisahkan koma saja tanpa angka tanpa penjelasan. Transkrip: {transkrip_input}"
            
            # Nembak AI gratisan tanpa ribet API key yang sensitif
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": "Bearer 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", # Ini token cadangan dari gua, Ram
                    "Content-Type": "application/json"
                },
                json={
                    "model": "meta-llama/llama-3-8b-instruct:free",
                    "messages": [{"role": "user", "content": prompt}]
                }
            ).json()
            
            ai_text = response['choices'][0]['message']['content']
            keywords = [k.strip() for k in ai_text.split(',')]
            st.success(f"✅ **AI Keyword:** {', '.join(keywords)}")
        except Exception as e:
            st.error(f"⚠️ Terjadi gangguan koneksi pada engine AI: {e}")
            keywords = []

    if keywords:
        st.subheader("🔍 Hasil B-Roll YouTube Shorts Teratas:")
        for keyword in keywords:
            url = "https://www.googleapis.com/youtube/v3/search"
            params = {
                "part": "snippet",
                "q": keyword,
                "type": "video",
                "videoDuration": "short",
                "maxResults": 1,
                "key": YOUTUBE_API_KEY
            }
            res = requests.get(url, params=params).json()
            try:
                video_id = res['items'][0]['id']['videoId']
                youtube_link = f"https://www.youtube.com/shorts/{video_id}"
                video_title = res['items'][0]['snippet']['title']
                
                with st.container():
                    st.markdown(f"**📌 Keyword:** *{keyword}*")
                    st.markdown(f"🔗 **Link Shorts:** [{youtube_link}]({youtube_link})")
                    st.caption(f"Judul: {video_title}")
                    st.divider()
            except:
                st.warning(f"❌ Skip keyword: '{keyword}'")
                
        st.balloons()
