import streamlit as st
import sqlite3
import pandas as pd
import os
import base64
import streamlit.components.v1 as components
from datetime import datetime

# --- 1. SETUP FOLDER ---
folders = ['static/img_profile', 'static/img_events']
for folder in folders:
    if not os.path.exists(folder):
        os.makedirs(folder)

# --- 2. FUNGSI KONVERSI GAMBAR (DIPERBAIKI UNTUK CLOUD) ---
def get_image_base64(path):
    if not path: return None
    
    # Menghapus path lokal laptop jika terbawa di database
    # Misal: 'C:/DATA/...' atau 'app/static/...' akan menjadi 'static/...'
    clean_path = path.replace('\\', '/')
    if 'static/' in clean_path:
        clean_path = 'static/' + clean_path.split('static/')[-1]
    
    if os.path.exists(clean_path):
        with open(clean_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{encoded}"
    return None

# --- 3. DATABASE SETUP ---
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
    conn.commit()
    conn.close()

init_db()

# --- 4. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Alumni SMPN 4 Cirebon 86", page_icon="🏫", layout="wide")

if 'menu_aktif' not in st.session_state:
    st.session_state.menu_aktif = "Home"

def pindah_halaman(nama_halaman):
    st.session_state.menu_aktif = nama_halaman

# --- 5. STYLE CSS ---
st.markdown("""
    <style>
    .main-header { background: #2b5298; padding: 40px; border-radius: 20px; color: white; text-align: center; margin-bottom: 10px; }
    .stButton > button { border-radius: 10px; height: 45px; }
    </style>
""", unsafe_allow_html=True)

# --- 6. SIDEBAR NAVIGASI ---
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

# --- 7. LOGIKA KONTEN HALAMAN ---

# A. HALAMAN HOME
if st.session_state.menu_aktif == "Home":
    st.markdown('<div class="main-header"><h1>Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    
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
    df_list_event = pd.read_sql_query("SELECT DISTINCT deskripsi FROM data_events WHERE deskripsi != ''", conn)
    
    if not df_list_event.empty:
        pilihan_event = st.selectbox("Pilih Event untuk Dilihat:", df_list_event['deskripsi'])
        df_foto = pd.read_sql_query("SELECT path_foto FROM data_events WHERE deskripsi = ?", conn, params=(pilihan_event,))
        list_foto = [get_image_base64(p) for p in df_foto['path_foto'] if get_image_base64(p)]
        
        if list_foto:
            html_slides = "".join([f'<div class="mySlides fade"><img src="{img}"></div>' for img in list_foto])
            html_code = f"""
            <style>
                .slideshow-container {{ max-width: 1000px; position: relative; margin: auto; }}
                .mySlides {{ display: none; }}
                img {{ vertical-align: middle; border-radius: 15px; width: 100%; height: 400px; object-fit: cover; }}
                .fade {{ animation-name: fade; animation-duration: 1.5s; }}
                @keyframes fade {{ from {{opacity: .4}} to {{opacity: 1}} }}
            </style>
            <div class="slideshow-container">{html_slides}</div>
            <script>
                let slideIndex = 0; showSlides();
                function showSlides() {{
                    let i; let slides = document.getElementsByClassName("mySlides");
                    for (i = 0; i < slides.length; i++) {{ slides[i].style.display = "none"; }}
                    slideIndex++; if (slideIndex > slides.length) {{slideIndex = 1}}
                    if(slides[slideIndex-1]) {{ slides[slideIndex-1].style.display = "block"; }}
                    setTimeout(showSlides, 3000);
                }}
            </script>
            """
            components.html(html_code, height=410)
            
            # FITUR KOMENTAR (DI BAWAH FOTO)
            st.write("---")
            st.markdown("### 💬 Komentar Alumni")
            df_komen = pd.read_sql_query("SELECT nama_penulis, isi_komentar, waktu FROM data_komentar WHERE event_deskripsi = ? ORDER BY id DESC", 
                                        conn, params=(pilihan_event,))
            
            if not df_komen.empty:
                for _, row in df_komen.iterrows():
                    c1, c2, c3 = st.columns([1, 1.5, 3])
                    c1.markdown(f"<small style='color:gray;'>{row['waktu']}</small>", unsafe_allow_html=True)
                    c2.markdown(f"**{row['nama_penulis']}**")
                    c3.info(row['isi_komentar'])
            
            with st.expander("➕ Tulis Komentar"):
                with st.form(key=f"form_komen_{pilihan_event}", clear_on_submit=True):
                    nama_in = st.text_input("Nama Bapak/Ibu:")
                    pesan_in = st.text_area("Tulis sapaan atau komentar:")
                    if st.form_submit_button("Kirim Komentar 🚀") and pesan_in:
                        waktu_skrg = datetime.now().strftime("%d/%m/%y %H:%M")
                        nama_final = nama_in if nama_in else "Tamu"
                        conn.execute("INSERT INTO data_komentar (event_deskripsi, nama_penulis, isi_komentar, waktu) VALUES (?,?,?,?)",
                                  (pilihan_event, nama_final, pesan_in, waktu_skrg))
                        conn.commit()
                        st.rerun()
    conn.close()

    st.write("---")
    st.subheader("🗓️ Agenda Kegiatan Mendatang")
    # (Logika Tabel Agenda Bapak di sini)

# B. HALAMAN FORM PENDAFTARAN (HIDDEN)
elif st.session_state.menu_aktif == "Form Pendaftaran":
    st.title("📝 Form Pendaftaran Alumni")
    if st.button("⬅️ Kembali ke Home"):
        st.session_state.menu_aktif = "Home"; st.rerun()

    with st.form("form_regis", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            nama = st.text_input("Nama Lengkap:")
            alamat = st.text_area("Alamat:")
            user_id = st.text_input("ID / Username:")
            password = st.text_input("Password:", type="password")
        with col2:
            k1 = st.text_input("Kelas 1:")
            k2 = st.text_input("Kelas 2:")
            k3 = st.text_input("Kelas 3:")
            foto = st.file_uploader("Upload Foto Profile", type=['jpg','png','jpeg'])
            
        if st.form_submit_button("Daftar Sekarang 🚀"):
            if nama and user_id and password:
                conn = sqlite3.connect('alumni.db')
                # (Simpan data dan tampilkan st.balloons() di sini)
                conn.commit(); conn.close()
                st.balloons()
                st.session_state.menu_aktif = "Database Alumni"
                st.rerun()

# C. HALAMAN DATABASE ALUMNI
elif st.session_state.menu_aktif == "Database Alumni":
    st.title("🔍 Database Alumni")
    # (Logika menampilkan tabel alumni)

# D. HALAMAN ADMIN PANEL
elif st.session_state.menu_aktif == "Admin Panel":
    st.title("⚙️ Admin Panel")
    # (Logika Upload Foto Event & Agenda)

# E. HALAMAN LAINNYA
else:
    st.title(f"📂 {st.session_state.menu_aktif}")
    st.info("Halaman ini sedang dalam pengembangan.")
