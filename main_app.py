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

# --- 2. NAVIGASI ---
st.set_page_config(page_title="Alumni SMPN 4 Cirebon 86", layout="wide")

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
    st.write("---")
    if st.button("⚙️ Admin Panel", use_container_width=True): pindah("Admin Panel")

# --- 3. LOGIKA HALAMAN ---

# --- A. IN MEMORIAM (PERBAIKAN TAMPILAN SEMUA DATA) ---
if st.session_state.menu_aktif == "In Memoriam":
    st.markdown('<div style="background:#424242;padding:20px;border-radius:10px;color:white;text-align:center;"><h1>🌹 In Memoriam Sempat 86</h1></div>', unsafe_allow_html=True)
    st.write("")
    
    conn = sqlite3.connect('alumni.db')
    # Mengambil semua data tanpa terkecuali
    df_mem = pd.read_sql_query("SELECT * FROM data_memoriam ORDER BY id DESC", conn)
    conn.close()
    
    if not df_mem.empty:
        # Membuat grid 3 kolom agar foto muncul berjejer, bukan menumpuk
        cols = st.columns(3)
        for index, row in df_mem.iterrows():
            with cols[index % 3]: # Ini kuncinya agar data terbagi ke kolom 1, 2, dan 3
                img_b64 = get_image_base64(row['foto'])
                if img_b64:
                    st.image(img_b64, use_container_width=True)
                st.subheader(row['nama'])
                st.markdown(f"**Wafat:** {row['tanggal_wafat']}")
                st.write(f"*{row['keterangan']}*")
                st.write("---")
    else:
        st.info("Belum ada data kenangan yang dimasukkan.")

# --- B. ADMIN PANEL (PASTIKAN TAB MEMORIAM BENAR) ---
elif st.session_state.menu_aktif == "Admin Panel":
    st.title("⚙️ Admin Panel")
    t1, t2, t3 = st.tabs(["📸 Dokumentasi", "🗓️ Agenda", "🌹 In Memoriam"])
    
    with t3:
        with st.form("up_mem", clear_on_submit=True):
            m_nama = st.text_input("Nama Lengkap Rekan")
            m_tgl = st.text_input("Tanggal Wafat")
            m_ket = st.text_area("Keterangan/Pesan")
            m_foto = st.file_uploader("Upload Foto", type=['jpg','png','jpeg'])
            if st.form_submit_button("Simpan Data"):
                if m_nama and m_foto:
                    # Simpan foto dengan nama unik berdasarkan timestamp agar tidak tertukar
                    fname = f"mem_{int(datetime.now().timestamp())}_{m_foto.name}"
                    p_path = f"static/img_memoriam/{fname}"
                    with open(p_path, "wb") as f: f.write(m_foto.getbuffer())
                    
                    conn = sqlite3.connect('alumni.db')
                    conn.execute("INSERT INTO data_memoriam (foto, nama, tanggal_wafat, keterangan) VALUES (?,?,?,?)", 
                                 (p_path, m_nama, m_tgl, m_ket))
                    conn.commit(); conn.close()
                    st.success(f"Data {m_nama} berhasil disimpan!"); st.rerun()

# --- C. HALAMAN LAIN (KUNCI AGAR TETAP STABIL) ---
elif st.session_state.menu_aktif == "Home":
    st.markdown('<div style="background:#2b5298;padding:20px;border-radius:10px;color:white;text-align:center;"><h1>Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    # ... (Logika Home seperti sebelumnya agar Dokumentasi & Agenda tidak hilang) ...
    conn = sqlite3.connect('alumni.db')
    df_ev = pd.read_sql_query("SELECT DISTINCT deskripsi FROM data_events", conn)
    if not df_ev.empty:
        p_ev = st.selectbox("Pilih Event:", df_ev['deskripsi'])
        df_f = pd.read_sql_query("SELECT path_foto FROM data_events WHERE deskripsi = ?", conn, params=(p_ev,))
        imgs = [get_image_base64(p) for p in df_f['path_foto'] if get_image_base64(p)]
        if imgs:
            slides = "".join([f'<div class="mySlides fade"><img src="{i}" style="width:100%; height:450px; object-fit:cover; border-radius:15px;"></div>' for i in imgs])
            components.html(f'<div class="slideshow-container">{slides}</div><script>let sIdx=0;function showS(){{let s=document.getElementsByClassName("mySlides");for(let i=0;i<s.length;i++)s[i].style.display="none";sIdx++;if(sIdx>s.length)sIdx=1;if(s[sIdx-1])s[sIdx-1].style.display="block";setTimeout(showS,3000)}}showS();</script>', height=460)
    conn.close()

elif st.session_state.menu_aktif == "Database Alumni":
    st.title("🔍 Database Alumni")
    conn = sqlite3.connect('alumni.db')
    df = pd.read_sql_query("SELECT foto_profile, nama, kelas_1, kelas_2, kelas_3, alamat FROM data_anggota", conn)
    conn.close()
    if not df.empty:
        df['foto_profile'] = df['foto_profile'].apply(get_image_base64)
        st.data_editor(df, column_config={"foto_profile": st.column_config.ImageColumn("Foto")}, use_container_width=True, hide_index=True)
