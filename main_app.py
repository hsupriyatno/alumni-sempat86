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

# --- 2. FUNGSI KONVERSI GAMBAR KE BASE64 ---
def get_image_base64(path):
    if not path: return None
    clean_path = path.replace('app/', '')
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
                 "In Memoriam Alumni Sempat 86", "Komunitas", "Networking", "Donasi", "Admin Panel"]
    
    if st.session_state.menu_aktif in list_menu:
        idx = list_menu.index(st.session_state.menu_aktif)
    else:
        idx = 0
        
    menu_pilihan = st.radio("Pilih Halaman:", list_menu, index=idx)
    if menu_pilihan != st.session_state.menu_aktif:
        st.session_state.menu_aktif = menu_pilihan
        st.rerun()

# --- 7. LOGIKA HALAMAN ---

# --- A. HALAMAN HOME ---
if st.session_state.menu_aktif == "Home":
    st.markdown('<div class="main-header"><h1>Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    
    # Tombol Akses Cepat
    c_spacer, c_daftar, c_masuk = st.columns([7, 1.5, 1.5]) 
    with c_daftar:
        if st.button("📝 Daftar", use_container_width=True):
            pindah_halaman("Form Pendaftaran"); st.rerun()
    with c_masuk:
        if st.button("🔑 Masuk", use_container_width=True):
            pindah_halaman("Database Alumni"); st.rerun()

    st.write("---")

    # 1. Slideshow Foto Event Dinamis Berdasarkan Filter
    st.subheader("📸 Dokumentasi Kegiatan")
    conn = sqlite3.connect('alumni.db')
    df_list_event = pd.read_sql_query("SELECT DISTINCT deskripsi FROM data_events WHERE deskripsi != ''", conn)
    
    if not df_list_event.empty:
        pilihan_event = st.selectbox("Pilih Event untuk Dilihat:", df_list_event['deskripsi'])
        df_foto = pd.read_sql_query("SELECT path_foto FROM data_events WHERE deskripsi = ?", conn, params=(pilihan_event,))
        
        list_foto = []
        for p in df_foto['path_foto']:
            b64 = get_image_base64(p)
            if b64: list_foto.append(b64)
        
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
                    slides[slideIndex-1].style.display = "block";
                    setTimeout(showSlides, 3000);
                }}
            </script>
            """
            components.html(html_code, height=410)
            st.markdown(f"<div style='text-align: center; margin-top: -10px;'><strong>📍 Event: {pilihan_event}</strong></div>", unsafe_allow_html=True)
    else:
        st.info("Belum ada foto dokumentasi.")
    conn.close()

    st.write("---")

    # 2. Agenda Kegiatan (DENGAN LOGIKA URUT TANGGAL)
    st.subheader("🗓️ Agenda Kegiatan Mendatang")
    conn = sqlite3.connect('alumni.db')
    df_agenda = pd.read_sql_query("SELECT tanggal, kegiatan, lokasi, status FROM data_agenda", conn)
    conn.close()
    
    if not df_agenda.empty:
        # LOGIKA SORTING TANGGAL:
        # 1. Ubah string tanggal ke format datetime agar bisa diurutkan
        df_agenda['tanggal_dt'] = pd.to_datetime(df_agenda['tanggal'], format='%d %B %Y')
        # 2. Urutkan berdasarkan tanggal terdekat (Ascending)
        df_agenda = df_agenda.sort_values(by='tanggal_dt', ascending=True)
        # 3. Buat tampilan tabel tanpa kolom pembantu 'tanggal_dt'
        st.table(df_agenda[['tanggal', 'kegiatan', 'lokasi', 'status']])
    else:
        st.info("Belum ada agenda kegiatan.")

# --- B. HALAMAN ADMIN PANEL ---
elif st.session_state.menu_aktif == "Admin Panel":
    st.title("⚙️ Admin Panel - Data Entry")
    tab1, tab2 = st.tabs(["📸 Upload Foto Event", "🗓️ Input Agenda"])
    
    with tab1:
        st.subheader("Tambah Dokumentasi Foto")
        with st.form("form_foto", clear_on_submit=True):
            files_foto = st.file_uploader("Pilih Foto-foto Event", type=['jpg','png','jpeg'], accept_multiple_files=True)
            deskripsi = st.text_input("Deskripsi Event (Misal: Bukber 2026)")
            if st.form_submit_button("🚀 Simpan Semua Foto") and files_foto:
                conn = sqlite3.connect('alumni.db')
                c = conn.cursor()
                for f_upload in files_foto:
                    nama_file = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{f_upload.name}"
                    path_simpan = os.path.join("static/img_events", nama_file)
                    with open(path_simpan, "wb") as f:
                        f.write(f_upload.getbuffer())
                    c.execute("INSERT INTO data_events (path_foto, deskripsi) VALUES (?,?)", (path_simpan, deskripsi))
                conn.commit(); conn.close()
                st.success("Foto berhasil ditambahkan!"); st.rerun()

    with tab2:
        st.subheader("Tambah Agenda Baru")
        with st.form("form_agenda", clear_on_submit=True):
            tgl = st.date_input("Tanggal Kegiatan")
            keg = st.text_input("Nama Kegiatan")
            lok = st.text_input("Lokasi")
            stat = st.selectbox("Status", ["Terencana", "Persiapan", "Selesai"])
            if st.form_submit_button("Simpan Agenda") and keg:
                conn = sqlite3.connect('alumni.db')
                c = conn.cursor()
                # Simpan dengan format standar: Tanggal NamaBulan Tahun
                c.execute("INSERT INTO data_agenda (tanggal, kegiatan, lokasi, status) VALUES (?,?,?,?)", 
                          (tgl.strftime("%d %B %Y"), keg, lok, stat))
                conn.commit(); conn.close()
                st.success("Agenda berhasil disimpan!"); st.rerun()

# --- C. HALAMAN DATABASE (Placeholder) ---
elif st.session_state.menu_aktif == "Database Alumni":
    st.title("🔍 Database Alumni")
    st.info("Tampilkan data alumni di sini...")