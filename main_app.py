import streamlit as st
import sqlite3
import pandas as pd
import os
import base64
import streamlit.components.v1 as components
from datetime import datetime

# --- 1. SETUP FOLDER & DATABASE ---
for folder in ['static/img_profile', 'static/img_events', 'static/img_memoriam']:
    if not os.path.exists(folder): os.makedirs(folder)

def init_db():
    conn = sqlite3.connect('alumni.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS data_anggota (
                    foto_profile TEXT, nama TEXT, user_id TEXT PRIMARY KEY, 
                    password TEXT, kelas_1 TEXT, kelas_2 TEXT, kelas_3 TEXT, alamat TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS data_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, path_foto TEXT, deskripsi TEXT)''')
    # PERBAIKAN: Gunakan nama kolom 'tgl_kegiatan' agar konsisten
    c.execute('''CREATE TABLE IF NOT EXISTS data_agenda (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, tgl_kegiatan DATE, kegiatan TEXT, lokasi TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS data_memoriam (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, foto TEXT, nama TEXT, tanggal_wafat TEXT, keterangan TEXT)''')
    conn.commit()
    conn.close()

init_db()

def get_image_base64(path):
    if not path or not os.path.exists(path): return None
    try:
        with open(path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
    except: return None

# --- 2. NAVIGASI SIDEBAR ---
st.set_page_config(page_title="Alumni SMPN 4 Cirebon 86", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(to bottom, #e3f2fd, #ffffff); }
    [data-testid="stSidebar"] { background-color: #f0f7ff; }
    </style>
    """, unsafe_allow_html=True)

if 'menu_aktif' not in st.session_state:
    st.session_state.menu_aktif = "Home"

def pindah(hal):
    st.session_state.menu_aktif = hal
    st.rerun()

with st.sidebar:
    st.title("🏫 SEMPAT 86")
    st.write("---")
    if st.button("🏠 Home", use_container_width=True): pindah("Home")
    if st.button("🔍 Database Alumni", use_container_width=True): pindah("Database Alumni")
    if st.button("🌹 In Memoriam", use_container_width=True): pindah("In Memoriam")
    if st.button("🤝 Networking", use_container_width=True): pindah("Networking")
    if st.button("💰 Donasi", use_container_width=True): pindah("Donasi")
    st.write("---")
    if st.button("⚙️ Admin Panel", use_container_width=True): pindah("Admin Panel")

# --- 3. LOGIKA HALAMAN ---

# --- A. HOME ---
if st.session_state.menu_aktif == "Home":
    st.markdown('<div style="background:#2b5298;padding:20px;border-radius:10px;color:white;text-align:center;"><h1>Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    
    st.write("")
    # --- TABEL AGENDA URUT TANGGAL ---
    st.subheader("🗓️ Agenda Kegiatan Mendatang")
    conn = sqlite3.connect('alumni.db')
    # Query: Urutkan berdasarkan tgl_kegiatan (ASC = yang paling dekat tanggalnya di atas)
    # Gunakan DESC jika Bapak ingin yang paling jauh/baru diinput ada di atas
    df_ag = pd.read_sql_query("SELECT tgl_kegiatan as Tanggal, kegiatan as Kegiatan, lokasi as Lokasi FROM data_agenda ORDER BY tgl_kegiatan ASC", conn)
    
    if not df_ag.empty:
        # Percantik format tanggal untuk tampilan (DD-MM-YYYY)
        df_ag['Tanggal'] = pd.to_datetime(df_ag['Tanggal']).dt.strftime('%d-%m-%Y')
        st.table(df_ag)
    else:
        st.info("Belum ada agenda kegiatan.")

    # --- SLIDESHOW SLOW MOTION ---
    st.write("---")
    st.subheader("📸 Dokumentasi Kegiatan")
    df_ev = pd.read_sql_query("SELECT DISTINCT deskripsi FROM data_events ORDER BY id DESC", conn)
    if not df_ev.empty:
        pilihan_ev = st.selectbox("Pilih Event:", df_ev['deskripsi'])
        df_f = pd.read_sql_query("SELECT path_foto FROM data_events WHERE deskripsi = ?", conn, params=(pilihan_ev,))
        imgs = [get_image_base64(p) for p in df_f['path_foto'] if get_image_base64(p)]
        if imgs:
            slides = "".join([f'<div class="mySlides fade"><img src="{i}" style="width:100%; height:450px; object-fit:cover; border-radius:15px;"></div>' for i in imgs])
            components.html(f'''
            <style>
                .mySlides {{ display: none; }}
                .fade {{ animation-name: fade; animation-duration: 4.0s; }}
                @keyframes fade {{ from {{opacity: 0}} to {{opacity: 1}} }}
            </style>
            <div class="slideshow-container">{slides}</div>
            <script>
                let sIdx = 0;
                function showS() {{
                    let s = document.getElementsByClassName("mySlides");
                    for (let i = 0; i < s.length; i++) s[i].style.display = "none";
                    sIdx++;
                    if (sIdx > s.length) sIdx = 1;
                    if (s[sIdx-1]) s[sIdx-1].style.display = "block";
                    setTimeout(showS, 7000); 
                }}
                showS();
            </script>
            ''', height=460)
    conn.close()

# --- B. FORM PENDAFTARAN LENGKAP ---
elif st.session_state.menu_aktif == "Form Pendaftaran":
    st.title("📝 Form Pendaftaran")
    with st.form("reg", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            n = st.text_input("Nama Lengkap")
            u = st.text_input("User ID")
            p = st.text_input("Password", type="password")
            almt = st.text_area("Alamat/Domisili")
        with col2:
            k1 = st.selectbox("Kelas 1", ["A","B","C","D","E","F","G","H"])
            k2 = st.selectbox("Kelas 2", ["A","B","C","D","E","F","G","H"])
            k3 = st.selectbox("Kelas 3", ["A","B","C","D","E","F","G","H"])
            foto = st.file_uploader("Photo Profile", type=['jpg','png','jpeg'])
        
        if st.form_submit_button("Daftar Sekarang", use_container_width=True):
            if n and u and p:
                path_f = ""
                if foto:
                    path_f = f"static/img_profile/{u}_{foto.name}"
                    with open(path_f, "wb") as f: f.write(foto.getbuffer())
                conn = sqlite3.connect('alumni.db')
                conn.execute("INSERT INTO data_anggota VALUES (?,?,?,?,?,?,?,?)", (path_f, n, u, p, k1, k2, k3, almt))
                conn.commit(); conn.close()
                st.success("Pendaftaran Berhasil!"); st.balloons()
            else: st.warning("Nama, ID, dan Password wajib diisi.")

# --- C. ADMIN PANEL (INPUT TANGGAL KALENDER) ---
elif st.session_state.menu_aktif == "Admin Panel":
    st.title("⚙️ Admin Panel")
    t1, t2 = st.tabs(["📸 Dokumentasi", "🗓️ Agenda Kegiatan"])
    
    with t2:
        st.write("### Tambah Agenda Baru")
        with st.form("up_age", clear_on_submit=True):
            # Form format tanggal asli (Kalender)
            tgl_input = st.date_input("Pilih Tanggal Acara")
            keg = st.text_input("Nama Kegiatan/Acara")
            lok = st.text_input("Lokasi/Tempat")
            
            if st.form_submit_button("Simpan ke Agenda"):
                if keg and lok:
                    conn = sqlite3.connect('alumni.db')
                    # Simpan tgl_input langsung (Streamlit date_input sudah format YYYY-MM-DD)
                    conn.execute("INSERT INTO data_agenda (tgl_kegiatan, kegiatan, lokasi) VALUES (?,?,?)", 
                                 (tgl_input, keg, lok))
                    conn.commit(); conn.close()
                    st.success("Agenda berhasil disimpan dan sudah urut tanggal!")
                    st.rerun()

# --- HALAMAN LAIN (DATABASE, IN MEMORIAM) ---
elif st.session_state.menu_aktif == "Database Alumni":
    st.title("🔍 Database Alumni")
    conn = sqlite3.connect('alumni.db')
    df_db = pd.read_sql_query("SELECT foto_profile, nama, kelas_1, kelas_2, kelas_3, alamat FROM data_anggota", conn)
    conn.close()
    if not df_db.empty:
        df_db['foto_profile'] = df_db['foto_profile'].apply(get_image_base64)
        st.data_editor(df_db, column_config={"foto_profile": st.column_config.ImageColumn("Foto")}, use_container_width=True, hide_index=True)

elif st.session_state.menu_aktif == "In Memoriam":
    st.markdown('<div style="background:#424242;padding:20px;border-radius:10px;color:white;text-align:center;"><h1>🌹 In Memoriam</h1></div>', unsafe_allow_html=True)
    conn = sqlite3.connect('alumni.db')
    df_mem = pd.read_sql_query("SELECT * FROM data_memoriam ORDER BY id DESC", conn)
    conn.close()
    if not df_mem.empty:
        cols = st.columns(3)
        for i, row in df_mem.iterrows():
            with cols[i % 3]:
                img = get_image_base64(row['foto'])
                if img: st.image(img, use_container_width=True)
                st.subheader(row['nama'])
                st.caption(f"Wafat: {row['tanggal_wafat']}")
                st.write(row['keterangan'])
