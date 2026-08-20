import streamlit as st
import sounddevice as sd
from scipy.io.wavfile import write
import requests
import speech_recognition as sr
import urllib.parse
import re

# --- ΡΥΘΜΙΣΗ ΣΕΛΙΔΑΣ & DARK MODE ---
st.set_page_config(page_title="AI Music Finder", layout="wide")

if "history" not in st.session_state:
    st.session_state.history = []

# --- ΑΡΙΣΤΕΡΗ ΜΠΑΡΑ (SIDEBAR) ---
with st.sidebar:
    st.header("⚙️ Ρυθμίσεις AI")
    
    # Προσθέτουμε επιλογή γλώσσας για το Speech-to-Text
    lang_choice = st.selectbox(
        "Σε ποια γλώσσα θα τραγουδήσεις;",
        ["Αγγλικά (English)", "Ελληνικά (Greek)"]
    )
    
    # Αντιστοίχιση της επιλογής με τους επίσημους κωδικούς γλωσσών του AI
    if lang_choice == "Αγγλικά (English)":
        ai_language = "en-US"
    else:
        ai_language = "el-GR"
        
    st.divider()
    st.header("🗂️ Ιστορικό Αναζητήσεων")
    st.write("Τα τραγούδια που βρήκες σήμερα:")
    
    if not st.session_state.history:
        st.caption("Το ιστορικό είναι άδειο.")
    else:
        for item in reversed(st.session_state.history):
            st.write(f"• **{item['title']}** - {item['artist']}")
    
    st.divider()
    st.caption("Minimal Music Finder v4.0")

# --- ΚΥΡΙΩΣ ΠΕΡΙΕΧΟΜΕΝΟ ---
st.title("🌌 Global AI Music Finder")
st.write("Επιλέξτε γλώσσα από την αριστερή μπάρα, πατήστε το κουμπί και πείτε τους στίχους που θυμάστε.")

col1, col2 = st.columns(2)

with col1:
    if st.button("🎤 Έναρξη Ηχογράφησης (5 δευτερόλεπτα)", use_container_width=True):
        st.info("🎙️ Το μικρόφωνο είναι ανοιχτό... Πείτε τους στίχους τώρα!")
        
        fs = 44100
        duration = 5
        audio_path = "C:\\music\\output.wav"
        
        # Ηχογράφηση
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()
        write(audio_path, fs, recording)
        
        # 1. Μετατροπή Φωνής σε Κείμενο
        st.info("🧠 Το AI επεξεργάζεται τη φωνή σας...")
        recognizer = sr.Recognizer()
        spoken_text = ""
        
        try:
            with sr.AudioFile(audio_path) as source:
                audio_data = recognizer.record(source)
                # Χρησιμοποιούμε τη μεταβλητή ai_language που αλλάζει δυναμικά από τη Sidebar
                spoken_text = recognizer.recognize_google(audio_data, language=ai_language)
                st.success(f"🗣️ Το AI άκουσε: \"{spoken_text}\"")
        except sr.UnknownValueError:
            st.error("❌ Δεν ακούστηκαν καθαροί στίχοι. Δοκιμάστε ξανά πιο δυνατά ή πιο καθαρά.")
        except Exception:
            st.warning("⚠️ Πρόβλημα με την αναγνώριση της φωνής.")

        # 2. Αναζήτηση στο Ίντερνετ & Εύρεση YouTube Video
        if spoken_text:
            st.info("🔍 Αναζήτηση στην παγκόσμια βάση δεδομένων...")
            spoken_text = str(spoken_text)
            clean_search = spoken_text.replace(" ", "%20")
            url = f"https://apple.com{clean_search}&entity=song&limit=1"
            headers = {"User-Agent": "Mozilla/5.0"}
            
            try:
                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    data = response.json()
                    results = data.get('results', [])
                    
                    if results:
                        song = results[0]
                        title = song.get('trackName', 'Unknown')
                        artist = song.get('artistName', 'Unknown')
                        album_img = song.get('artworkUrl100', '')
                        preview_url = song.get('previewUrl', '')
                        
                        # --- ΑΝΑΖΗΤΗΣΗ ΣΤΟ YOUTUBE ---
                        st.info("📺 Αναζήτηση ολόκληρου του βίντεο στο YouTube...")
                        search_query = f"{title} {artist} official audio"
                        encoded_query = urllib.parse.quote(search_query)
                        youtube_url = f"https://youtube.com{encoded_query}"
                        
                        youtube_response = requests.get(youtube_url, headers=headers)
                        video_ids = re.findall(r"watch\?v=(\S{11})", youtube_response.text)
                        
                        youtube_video_link = ""
                        if video_ids:
                            youtube_video_link = f"https://youtube.com{video_ids[0]}"
                        
                        # Προσθήκη στο ιστορικό
                        if not st.session_state.history or st.session_state.history[-1]["title"] != title:
                            st.session_state.history.append({"title": title, "artist": artist})
                        
                        st.balloons()
                        st.markdown("---")
                        st.subheader("🎯 Το τραγούδι βρέθηκε!")
                        
                        # Εμφάνιση Αποτελεσμάτων
                        img_col, text_col = st.columns(2)
                        with img_col:
                            if album_img:
                                big_img = album_img.replace("100x100bb", "300x300bb")
                                st.image(big_img, use_container_width=True)
                        with text_col:
                            st.title(title)
                            st.header(artist)
                            
                            if youtube_video_link:
                                st.write("📺 Δείτε ολόκληρο το βίντεο από το YouTube:")
                                st.video(youtube_video_link)
                            elif preview_url:
                                st.write("🎵 Δεν βρέθηκε βίντεο, ακούστε ένα δείγμα:")
                                st.audio(preview_url)
                        
                        st.rerun()
                    else:
                        st.warning("❌ Οι στίχοι αναγνωρίστηκαν, αλλά δεν βρέθηκε τέτοιο τραγούδι στο ίντερνετ.")
                else:
                    st.error("🚨 Σφάλμα διακομιστή.")
            except Exception as e:
                st.error(f"Σφάλμα σύνδεσης: {e}")