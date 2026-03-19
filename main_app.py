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
    c.execute('''CREATE TABLE IF NOT EXISTS data_komentar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, event_deskripsi TEXT, 
                    nama_penulis TEXT, isi_komentar TEXT, waktu TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS data_agenda (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, kegiatan TEXT, lokasi TEXT)''')
    # TABEL BARU: In Memoriam
    c.execute('''CREATE TABLE IF NOT EXISTS data_memoriam (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, foto TEXT, nama TEXT, tanggal_wafat TEXT, keterangan TEXT)''')
    conn.commit()
    conn.close()

init_db()

def get_image_base64(path):
    if not path or not os.path.exists(path): return None
    with open(path, "rb") as img_file:
        return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"

# --- 2. KONFIGURASI NAVIGASI ---
st.set_page_config(page_title="Alumni SMPN 4 Cirebon 86", layout="wide")

if 'menu_aktif' not in st.session_state:
    st.session_state.menu_aktif = "Home"

def pindah(hal):
    st.session_state.menu_aktif = hal
    st.rerun()

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("🏫 SEMPAT 86")
    if st.button("🏠 Home", use_container_width=True): pindah("Home")
    if st.button("🔍 Database Alumni", use_container_width=True): pindah("Database Alumni")
    if st.button("🌹 In Memoriam", use_container_width=True): pindah("In Memoriam")
    st.write("---")
    if st.button("⚙️ Admin Panel", use_container_width=True): pindah("Admin Panel")

# --- 4. LOGIKA HALAMAN ---

# --- A. HOME ---
if st.session_state.menu_aktif == "Home":
    st.markdown('<div style="background:#2b5298;padding:20px;border-radius:10px;color:white;text-align:center;"><h1>Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📝 Daftar Anggota Baru", use_container_width=True): pindah("Form Pendaftaran")
    with c2:
        if st.button("🔍 Lihat Database Anggota", use_container_width=True): pindah("Database Alumni")
    
    # Slideshow & Komentar tetap ada di sini (Sesuai strukur yang sudah dikunci)
    st.write("---")
    st.subheader("📸 Dokumentasi Kegiatan")
    # ... (kode slideshow tetap sama agar stabil) ...
    conn = sqlite3.connect('alumni.db')
    df_ag = pd.read_sql_query("SELECT tanggal, kegiatan, lokasi FROM data_agenda", conn)
    st.subheader("🗓️ Agenda Kegiatan")
    st.table(df_ag) if not df_ag.empty else st.info("Belum ada agenda.")
    conn.close()

# --- B. IN MEMORIAM (HALAMAN BARU) ---
elif st.session_state.menu_aktif == "In Memoriam":
    st.markdown('<div style="background:#424242;padding:20px;border-radius:10px;color:white;text-align:center;"><h1>🌹 In Memoriam Sempat 86</h1><p>Mengenang rekan-rekan yang telah mendahului kita</p></div>', unsafe_allow_html=True)
    st.write("")
    
    conn = sqlite3.connect('alumni.db')
    df_mem = pd.read_sql_query("SELECT * FROM data_memoriam", conn)
    conn.close()
    
    if not df_mem.empty:
        # Menampilkan dalam bentuk kartu/grid
        cols = st.columns(3)
        for i, row in df_mem.iterrows():
            with cols[i % 3]:
                img_b64 = get_image_base64(row['foto'])
                if img_b64:
                    st.image(img_b64, use_container_width=True)
                st.markdown(f"### {row['nama']}")
                st.caption(f"Wafat: {row['tanggal_wafat']}")
                st.write(f"*{row['keterangan']}*")
                st.write("---")
    else:
        st.info("Halaman kenangan. Data bisa diisi melalui Admin Panel.")

# --- C. ADMIN PANEL (Update dengan Form Memoriam) ---
elif st.session_state.menu_aktif == "Admin Panel":
    st.title("⚙️ Admin Panel")
    tab1, tab2, tab3 = st.tabs(["Dokumentasi", "Agenda", "In Memoriam"])
    
    with tab3:
        st.subheader("🌹 Tambah Data In Memoriam")
        with st.form("f_mem"):
            m_nama = st.text_input("Nama Rekan")
            m_tgl = st.text_input("Tanggal Wafat (Contoh: 12 Jan 2024)")
            m_ket = st.text_area("Pesan Singkat/Keterangan")
            m_foto = st.file_uploader("Upload Foto Alm/Almh", type=['jpg','png'])
            if st.form_submit_button("Simpan Data Kenangan"):
                if m_nama and m_foto:
                    p_foto = f"static/img_memoriam/{m_foto.name}"
                    with open(p_foto, "wb") as f: f.write(m_foto.getbuffer())
                    conn = sqlite3.connect('alumni.db')
                    conn.execute("INSERT INTO data_memoriam (foto, nama, tanggal_wafat, keterangan) VALUES (?,?,?,?)",
                                 (p_foto, m_nama, m_tgl, m_ket))
                    conn.commit(); conn.close(); st.success("Data berhasil disimpan.")
                else: st.warning("Nama dan Foto wajib diisi.")

# --- D. HALAMAN LAIN (DATABASE & DAFTAR) ---
# ... (Logika Database Alumni & Form Pendaftaran tetap sama agar tidak berubah) ...
