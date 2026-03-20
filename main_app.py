import streamlit as st
import sqlite3
import pandas as pd
import os
import base64
import streamlit.components.v1 as components
from datetime import datetime

# --- 1. SETUP FOLDER & DATABASE ---
for folder in ['static/img_profile', 'static/img_events', 'static/img_memoriam']:
    if not os.path.exists(folder):
        os.makedirs(folder)

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

# --- 2. NAVIGASI SIDEBAR & TEMA ---
st.set_page_config(page_title="Alumni SMPN 4 Cirebon 86", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(to bottom, #e3f2fd, #ffffff); }
    [data-testid="stSidebar"] { background-color: #f0f7ff; }
    .slideshow-container { position: relative; max-width: 1000px; margin: auto; }
    .mySlides { display: none; }
    .fade { animation-name: fade; animation-duration: 1.5s; }
    @keyframes fade { from {opacity: .4} to {opacity: 1} }
    </style>
    """, unsafe_allow_html=True)

if 'menu_aktif' not in st.session_state:
    st.session_state.menu_aktif = "Home"

def pindah(hal):
    st.session_state.menu_aktif = hal
    st.rerun()

with st.sidebar:
    st.title("🏫 SEMPAT 86")
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
    st.markdown('<div style="background:#2b5298;padding:20px;border-radius:10px;color:white;text-align:center;box-shadow: 2px 2px 10px rgba(0,0,0,0.1);"><h1>Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    
    st.markdown("""
        <div style="text-align:center; padding:30px 20px; font-family: 'Times New Roman', serif; background: rgba(255,255,255,0.4); border-radius:15px; margin-top:10px;">
            <p style="font-size:24px; color:#b8860b; font-style:italic; font-weight:bold; margin-bottom:10px; text-shadow: 1px 1px 2px rgba(0,0,0,0.1);">
                "Menyambung Kisah, Mempererat Persaudaraan. Jarak boleh membentang, waktu boleh berlalu, namun ikatan kita tetap satu."
            </p>
            <p style="font-size:18px; color:#333333; line-height:1.8; max-width:850px; margin:auto; font-weight: 500;">
                Mari jadikan kenangan masa sekolah sebagai energi untuk terus bergerak, berdampak, dan berkarya di bidang masing-masing.
            </p>
            <h2 style="color:#b8860b; font-style:italic; margin-top:20px; font-weight:bold;">Satu almamater, sejuta karya, selamanya saudara</h2>
        </div>
    """, unsafe_allow_html=True)
    
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📝 Daftar Anggota Baru", use_container_width=True): pindah("Form Pendaftaran")
    with c2:
        if st.button("🔍 Lihat Database Anggota", use_container_width=True): pindah("Database Alumni")

    st.write("---")
    st.subheader("🗓️ Agenda Kegiatan (Mendatang)")
    conn = sqlite3.connect('alumni.db')
    df_ag = pd.read_sql_query("SELECT tanggal, kegiatan, lokasi FROM data_agenda", conn)
    
    if not df_ag.empty:
        df_ag['tanggal_dt'] = pd.to_datetime(df_ag['tanggal'], errors='coerce')
        df_ag = df_ag.sort_values(by='tanggal_dt', ascending=True)
        df_ag['tanggal'] = df_ag['tanggal_dt'].dt.strftime('%d %B %Y')
        df_ag_view = df_ag[['tanggal', 'kegiatan', 'lokasi
