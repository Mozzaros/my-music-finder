import streamlit as st
import sounddevice as sd
from scipy.io.wavfile import write
import requests
import speech_recognition as sr
import urllib.parse
import re
import librosa
import numpy as np

st.set_page_config(page_title="AI Music Finder", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []

# --- SIDEBAR ---
with st.sidebar:
    st.header("⚙️ Ρυθμίσεις AI")
    lang_choice = st.selectbox("Γλώσσα τραγουδιού:", ["Αγγλικά (English)", "Ελληνικά (Greek)"])
    ai_language = "en-US" if lang_choice == "Αγγλικά (English)" else "el-GR"
        
    st.divider()
    st.header("🗂️ Ιστορικό")
    if not st.session_state.history:
        st.caption("Το ιστορικό είναι άδειο.")
    else:
        for item in reversed(st.session_state.history):
            st.write(f"• **{item['title']}** - {item['artist']}")

# --- ΚΥΡΙΩΣ ΠΕΡΙΕΧΟΜΕΝΟ ---
st.title("🌌 Global AI Music Finder")
st.write("Πατήστε το κουμπί, πείτε τους στίχους και το AI θα βρει το κομμάτι, το BPM και το βίντεο!")

col1, col2 = st.columns(2)

with col1:
    if st.button("🎤 Έναρξη Ηχογράφησης (5 δευτερόλεπτα)", use_container_width=True):
        st.info("🎙️ Το μικρόφωνο είναι ανοιχτό... Τραγουδήστε!")
        
        fs = 44100
        duration = 5
        audio_path = "C:\\music\\output.wav"
        
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()
        write(audio_path, fs, recording)
        
        # 1. Speech to Text
        st.info("🧠 Το AI αναλύει τη φωνή...")
        recognizer = sr.Recognizer()
        spoken_text = ""
        try:
            with sr.AudioFile(audio_path) as source:
                audio_data = recognizer.record(source)
                spoken_text = recognizer.recognize_google(audio_data, language=ai_language)
                st.success(f"🗣️ Ακούστηκε: \"{spoken_text}\"")
        except:
            st.error("❌ Δεν ακούστηκαν καθαροί στίχοι.")

        # 2. Παγκόσμια Αναζήτηση & Αυτόματο BPM
        if spoken_text:
            st.info("🔍 Αναζήτηση στο ίντερνετ...")
            clean_search = spoken_text.replace(" ", "%20")
            url = f"https://apple.com{clean_search}&entity=song&limit=1"
            
            try:
                response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).json()
                results = response.get('results', [])
                
                if results:
                    song = results[0]
                    title = song.get('trackName', 'Unknown')
                    artist = song.get('artistName', 'Unknown')
                    album_img = song.get('artworkUrl100', '')
                    
                    # ΑΥΤΟΜΑΤΗ ΕΥΡΕΣΗ BPM: Ψάχνουμε στο Jamendo API για την ταχύτητα του συγκεκριμένου καλλιτέχνη/τίτλου
                    st.info("📊 Υπολογισμός επίσημου BPM από τη βάση δεδομένων...")
                    jamendo_url = f"https://jamendo.com{urllib.parse.quote(title)}&limit=1"
                    jam_resp = requests.get(jamendo_url).json()
                    jam_results = jam_resp.get('results', [])
                    
                    # Αν βρει το BPM στο ίντερνετ το παίρνει, αλλιώς βάζει έναν μέσο όρο 120 BPM για ασφάλεια
                    official_bpm = float(jam_results[0].get('audio_properties', {}).get('bpm', 120)) if jam_results else 120
                    
                    # ΑΝΑΛΥΣΗ ΤΟΥ ΔΙΚΟΥ ΣΟΥ ΡΥΘΜΟΥ
                    y, sr_librosa = librosa.load(audio_path, sr=fs)
                    tempo, _ = librosa.beat.beat_track(y=y, sr=sr_librosa)
                    user_bpm = float(tempo[0]) if hasattr(tempo, "__len__") else float(tempo)
                    
                    # --- YouTube ---
                    search_query = f"{title} {artist} official audio"
                    encoded_query = urllib.parse.quote(search_query)
                    youtube_url = f"https://youtube.com{encoded_query}"
                    youtube_response = requests.get(youtube_url, headers={"User-Agent": "Mozilla/5.0"})
                    video_ids = re.findall(r"watch\?v=(\S{11})", youtube_response.text)
                    youtube_video_link = f"https://youtube.com{video_ids[0]}" if video_ids else ""
                    
                    if not st.session_state.history or st.session_state.history[-1]["title"] != title:
                        st.session_state.history.append({"title": title, "artist": artist})
                    
                    st.balloons()
                    st.markdown("---")
                    st.subheader("🎯 Το τραγούδι βρέθηκε!")
                    
                    img_col, text_col = st.columns(2)
                    with img_col:
                        if album_img:
                            st.image(album_img.replace("100x100bb", "300x300bb"), use_container_width=True)
                    with text_col:
                        st.title(title)
                        st.header(artist)
                        st.write(f"🎵 Επίσημο Tempo τραγουδιού: **{official_bpm} BPM**")
                        st.write(f"⏱️ Ο δικός σου ρυθμός: **{user_bpm:.1f} BPM**")
                        
                        if youtube_video_link:
                            st.video(youtube_video_link)
                else:
                    st.warning("❌ Δεν βρέθηκε το τραγούδι.")
            except Exception as e:
                st.error(f"Σφάλμα: {e}")