import streamlit as st
import sqlite3
import pandas as pd
import os
import base64
import streamlit.components.v1 as components
from datetime import datetime

# --- 1. SETUP FOLDER & DATABASE ---
for folder in ['static/img_profile', 'static/img_events']:
    if not os.path.exists(folder):
        os.makedirs(folder)

def init_db():
    conn = sqlite3.connect('alumni.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS data_anggota (
                    foto_profile TEXT, nama TEXT, alamat TEXT, 
                    kelas_1 TEXT, kelas_2 TEXT, kelas_3 TEXT, 
                    user_id TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS data_agenda (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tanggal TEXT, kegiatan TEXT, lokasi TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS data_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path_foto TEXT, deskripsi TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS data_komentar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_deskripsi TEXT, nama_penulis TEXT, isi_komentar TEXT, waktu TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 2. FUNGSI HELPER ---
def get_image_base64(path):
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return None

# --- 3. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Alumni SMPN 4 Cirebon 86", page_icon="🏫", layout="wide")

if 'menu_aktif' not in st.session_state:
    st.session_state.menu_aktif = "Home"

# --- 4. SIDEBAR NAVIGASI ---
with st.sidebar:
    st.markdown("### 📂 Menu Utama")
    list_menu = ["Home", "Database Alumni", "Berita & Kalender Kegiatan", 
                 "In Memoriam Alumni Sempat 86", "Komunitas", "Networking", "Donasi", "Admin Panel"]
    
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

# --- A. HALAMAN HOME ---
if st.session_state.menu_aktif == "Home":
    st.markdown('<div style="background:#2b5298; padding:30px; border-radius:15px; color:white; text-align:center;"><h1>Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    
    c_spacer, c_daftar, c_masuk = st.columns([7, 1.5, 1.5]) 
    with c_daftar:
        if st.button("📝 Daftar", use_container_width=True):
            st.session_state.menu_aktif = "Form Pendaftaran"
            st.rerun()
    with c_masuk:
        if st.button("🔑 Masuk", use_container_width=True):
            st.session_state.menu_aktif = "Database Alumni"
            st.rerun()

    st.write("---")
    st.subheader("📸 Dokumentasi Kegiatan")
    conn = sqlite3.connect('alumni.db')
    df_event = pd.read_sql_query("SELECT DISTINCT deskripsi FROM data_events WHERE deskripsi != ''", conn)
    
    if not df_event.empty:
        pilihan = st.selectbox("Pilih Event:", df_event['deskripsi'])
        df_foto = pd.read_sql_query("SELECT path_foto FROM data_events WHERE deskripsi = ?", conn, params=(pilihan,))
        list_f = [get_image_base64(p) for p in df_foto['path_foto'] if get_image_base64(p)]
        
        if list_f:
            slides_html = "".join([f'<div class="mySlides fade"><img src="{img}" style="width:100%; height:400px; object-fit:cover; border-radius:15px;"></div>' for img in list_f])
            components.html(f"""
                <div class="slideshow-container">{slides_html}</div>
                <script>
                    let slideIndex = 0; showSlides();
                    function showSlides() {{
                        let slides = document.getElementsByClassName("mySlides");
                        for (let i = 0; i < slides.length; i++) slides[i].style.display = "none";
                        slideIndex++; if (slideIndex > slides.length) slideIndex = 1;
                        if(slides[slideIndex-1]) slides[slideIndex-1].style.display = "block";
                        setTimeout(showSlides, 3000);
                    }}
                </script>
            """, height=410)

            st.write("---")
            st.markdown("### 💬 Komentar Alumni")
            df_k = pd.read_sql_query("SELECT nama_penulis, isi_komentar, waktu FROM data_komentar WHERE event_deskripsi = ? ORDER BY id DESC", conn, params=(pilihan,))
            for _, r in df_k.iterrows():
                ca, cb, cc = st.columns([1, 1.5, 3])
                ca.caption(r['waktu'])
                cb.markdown(f"**{r['nama_penulis']}**")
                cc.info(r['isi_komentar'])
            
            with st.expander("➕ Tulis Komentar"):
                with st.form(f"f_{pilihan}", clear_on_submit=True):
                    n_in = st.text_input("Nama:")
                    p_in = st.text_area("Komentar:")
                    if st.form_submit_button("Kirim 🚀") and p_in:
                        conn.execute("INSERT INTO data_komentar (event_deskripsi, nama_penulis, isi_komentar, waktu) VALUES (?,?,?,?)",
                                     (pilihan, (n_in if n_in else "Tamu"), p_in, datetime.now().strftime("%d/%m/%y %H:%M")))
                        conn.commit(); st.rerun()
    conn.close()

# --- B. HALAMAN FORM PENDAFTARAN ---
elif st.session_state.menu_aktif == "Form Pendaftaran":
    st.title("📝 Form Pendaftaran Alumni")
    if st.button("⬅️ Kembali ke Home"):
        st.session_state.menu_aktif = "Home"; st.rerun()
    
    with st.form("regis_form"):
        col1, col2 = st.columns(2)
        with col1:
            nama = st.text_input("Nama Lengkap")
            alamat = st.text_area("Alamat")
            # FITUR FOTO PROFIL
            foto_prof = st.file_uploader("Upload Foto Profile", type=['jpg','png','jpeg'])
            uid = st.text_input("User ID")
        with col2:
            # FITUR KELAS 1, 2, 3
            k1 = st.text_input("Kelas 1 (contoh: 1A)")
            k2 = st.text_input("Kelas 2")
            k3 = st.text_input("Kelas 3")
            pwd = st.text_input("Password", type="password")
        
        if st.form_submit_button("Simpan Data Alumni"):
            if nama and uid:
                st.balloons()
                st.success(f"Selamat {nama}, pendaftaran Anda berhasil!")
            else:
                st.warning("Mohon isi Nama dan User ID.")

# --- C. HALAMAN LAINNYA ---
elif st.session_state.menu_aktif == "Database Alumni":
    st.title("🔍 Database Alumni")
    st.info("Halaman sedang dikembangkan.")

elif st.session_state.menu_aktif == "Admin Panel":
    st.title("⚙️ Admin Panel")
    tab1, tab2 = st.tabs(["📸 Foto Event", "🗓️ Agenda"])
    with tab1: st.write("Form Upload Foto di sini")
    with tab2: st.write("Form Agenda di sini")

else:
    st.title(st.session_state.menu_aktif)
    st.info("Halaman segera hadir.")
