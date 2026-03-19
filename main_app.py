import streamlit as st
import sqlite3
import pandas as pd
import os
import base64
from datetime import datetime
import streamlit.components.v1 as components

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Alumni SEMPAT 86", layout="wide")

# Buat folder penyimpanan jika belum ada
for folder in ["static/img_profile", "static/img_events"]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# --- 2. FUNGSI DATABASE & HELPER ---
def get_image_base64(path):
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
    return None

def init_db():
    conn = sqlite3.connect('alumni.db')
    # Tabel Anggota
    conn.execute('''CREATE TABLE IF NOT EXISTS data_anggota 
                    (foto TEXT, nama TEXT, alamat TEXT, k1 TEXT, k2 TEXT, k3 TEXT, user_id TEXT PRIMARY KEY, password TEXT)''')
    # Tabel Event
    conn.execute('''CREATE TABLE IF NOT EXISTS data_events 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, path_foto TEXT, deskripsi TEXT)''')
    # Tabel Komentar
    conn.execute('''CREATE TABLE IF NOT EXISTS data_komentar 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, event_deskripsi TEXT, nama_penulis TEXT, isi_komentar TEXT, waktu TEXT)''')
    # Tabel Agenda
    conn.execute('''CREATE TABLE IF NOT EXISTS data_agenda 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, kegiatan TEXT, lokasi TEXT, status TEXT)''')
    conn.commit()
    conn.close()

# Jalankan inisialisasi database
init_db()

# --- 3. SESSION STATE ---
if 'menu_aktif' not in st.session_state:
    st.session_state.menu_aktif = "Home"

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("### 📂 Menu Utama")
    list_menu = ["Home", "Database Alumni", "Berita & Kalender Kegiatan", 
                 "In Memoriam Alumni Sempat 86", "Komunitas", "Networking", 
                 "Donasi", "Admin Panel"]
    
    current_idx = 0
    if st.session_state.menu_aktif in list_menu:
        current_idx = list_menu.index(st.session_state.menu_aktif)
    elif st.session_state.menu_aktif == "Form Pendaftaran":
        current_idx = 0
        
    menu_pilihan = st.radio("Pilih Halaman:", list_menu, index=current_idx)
    if menu_pilihan != st.session_state.menu_aktif and st.session_state.menu_aktif != "Form Pendaftaran":
        st.session_state.menu_aktif = menu_pilihan
        st.rerun()

# --- 5. LOGIKA HALAMAN ---

# A. HOME
if st.session_state.menu_aktif == "Home":
    st.markdown('<div style="background-color:#1e478a; padding:20px; border-radius:10px; text-align:center;"><h1 style="color:white;">Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    
    # Tombol Hidden Form
    c1, c2, c3 = st.columns([7, 1.5, 1.5])
    with c2:
        if st.button("📝 Daftar", use_container_width=True):
            st.session_state.menu_aktif = "Form Pendaftaran"
            st.rerun()
    with c3:
        if st.button("🔑 Masuk", use_container_width=True):
            st.session_state.menu_aktif = "Database Alumni"
            st.rerun()

    st.write("---")
    st.subheader("📸 Dokumentasi Kegiatan")
    
    conn = sqlite3.connect('alumni.db')
    df_event = pd.read_sql_query("SELECT DISTINCT deskripsi FROM data_events", conn)
    
    if not df_event.empty:
        pilihan = st.selectbox("Pilih Event:", df_event['deskripsi'])
        df_foto = pd.read_sql_query("SELECT path_foto FROM data_events WHERE deskripsi = ?", conn, params=(pilihan,))
        list_f = [get_image_base64(p) for p in df_foto['path_foto'] if get_image_base64(p)]
        
        if list_f:
            # Slideshow HTML
            slides_html = "".join([f'<div class="mySlides fade"><img src="{img}" style="width:100%; height:400px; object-fit:cover; border-radius:15px;"></div>' for img in list_f])
            components.html(f"""
                <div class="slideshow-container">{slides_html}</div>
                <script>
                    let slideIndex = 0; showSlides();
                    function showSlides() {{
                        let slides = document.getElementsByClassName("mySlides");
                        for (let i = 0; i < slides.length; i++) slides[i].style.display = "none";
                        slideIndex++; if (slideIndex > slides.length) slideIndex = 1;
                        slides[slideIndex-1].style.display = "block";
                        setTimeout(showSlides, 3000);
                    }}
                </script>
            """, height=410)

            # Bagian Komentar
            st.write("---")
            st.markdown("### 💬 Komentar Alumni")
            df_k = pd.read_sql_query("SELECT nama_penulis, isi_komentar, waktu FROM data_komentar WHERE event_deskripsi = ? ORDER BY id DESC", conn, params=(pilihan,))
            
            for _, r in df_k.iterrows():
                col_a, col_b, col_c = st.columns([1, 1.5, 3])
                col_a.caption(r['waktu'])
                col_b.markdown(f"**{r['nama_penulis']}**")
                col_c.info(r['isi_komentar'])
            
            with st.expander("➕ Tulis Komentar"):
                with st.form(f"f_{pilihan}", clear_on_submit=True):
                    n_in = st.text_input("Nama:")
                    p_in = st.text_area("Komentar:")
                    if st.form_submit_button("Kirim 🚀") and p_in:
                        conn.execute("INSERT INTO data_komentar (event_deskripsi, nama_penulis, isi_komentar, waktu) VALUES (?,?,?,?)",
                                     (pilihan, (n_in if n_in else "Tamu"), p_in, datetime.now().strftime("%d/%m/%y %H:%M")))
                        conn.commit()
                        st.rerun()
    conn.close()

# B. FORM PENDAFTARAN (HIDDEN)
elif st.session_state.menu_aktif == "Form Pendaftaran":
    st.title("📝 Pendaftaran Alumni")
    if st.button("⬅️ Kembali"):
        st.session_state.menu_aktif = "Home"; st.rerun()
        
    with st.form("reg"):
        n = st.text_input("Nama Lengkap")
        uid = st.text_input("ID/Username")
        pwd = st.text_input("Password", type="password")
        if st.form_submit_button("Daftar"):
            if n and uid and pwd:
                conn = sqlite3.connect('alumni.db')
                try:
                    conn.execute("INSERT INTO data_anggota (nama, user_id, password) VALUES (?,?,?)", (n, uid, pwd))
                    conn.commit()
                    st.balloons()
                    st.success("Berhasil!")
                    st.session_state.menu_aktif = "Database Alumni"
                    st.rerun()
                except: st.error("ID sudah ada")
                finally: conn.close()

# C. DATABASE ALUMNI
elif st.session_state.menu_aktif == "Database Alumni":
    st.title("🔍 Database Alumni")
    conn = sqlite3.connect('alumni.db')
    df_all = pd.read_sql_query("SELECT nama, user_id FROM data_anggota", conn)
    st.dataframe(df_all, use_container_width=True)
    conn.close()

# D. ADMIN PANEL
elif st.session_state.menu_aktif == "Admin Panel":
    st.title("⚙️ Admin Panel")
    with st.form("add_event"):
        f_up = st.file_uploader("Foto", type=['jpg','png'], accept_multiple_files=True)
        desc = st.text_input("Nama Event")
        if st.form_submit_button("Simpan"):
            conn = sqlite3.connect('alumni.db')
            for f in f_up:
                path = os.path.join("static/img_events", f.name)
                with open(path, "wb") as file: file.write(f.getbuffer())
                conn.execute("INSERT INTO data_events (path_foto, deskripsi) VALUES (?,?)", (path, desc))
            conn.commit(); conn.close(); st.rerun()

# E. LAIN-LAIN
else:
    st.title(st.session_state.menu_aktif)
    st.info("Halaman sedang dikembangkan.")
