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
                    id INTEGER PRIMARY KEY AUTOINCREMENT, path_foto TEXT, deskripsi TEXT, bulan_tahun TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS data_komentar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, event_deskripsi TEXT, 
                    nama_penulis TEXT, isi_komentar TEXT, waktu TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS data_agenda (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, kegiatan TEXT, lokasi TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS data_memoriam (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, foto TEXT, nama TEXT, tanggal_wafat TEXT, keterangan TEXT)''')
    
    # Cek kolom bulan_tahun untuk mencegah error
    try:
        c.execute("ALTER TABLE data_events ADD COLUMN bulan_tahun TEXT")
    except:
        pass
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

if st.session_state.menu_aktif == "Home":
    st.markdown('<div style="background:#2b5298;padding:20px;border-radius:10px;color:white;text-align:center;"><h1>Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#b8860b; font-style:italic; font-size:20px; text-align:center; font-weight:bold; margin-top:10px;">"Menyambung Kisah, Mempererat Persaudaraan."</p>', unsafe_allow_html=True)
    
    # Tombol Navigasi Cepat
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📝 Daftar Anggota Baru", use_container_width=True): pindah("Admin Panel")
    with col_b:
        if st.button("🔍 Lihat Database Anggota", use_container_width=True): pindah("Database Alumni")

    st.write("---")
    st.subheader("🗓️ Agenda Kegiatan (Mendatang)")
    conn = sqlite3.connect('alumni.db')
    df_ag = pd.read_sql_query("SELECT * FROM data_agenda", conn)
    if not df_ag.empty:
        st.table(df_ag[['tanggal', 'kegiatan', 'lokasi']])
    
    st.write("---")
    st.subheader("📸 Dokumentasi Kegiatan")
    df_ev = pd.read_sql_query("SELECT DISTINCT deskripsi, bulan_tahun FROM data_events", conn)
    if not df_ev.empty:
        df_ev['label'] = df_ev['deskripsi'] + " (" + df_ev['bulan_tahun'].fillna("-") + ")"
        pilih = st.selectbox("Pilih Event:", df_ev['label'])
        real_desc = df_ev[df_ev['label'] == pilih]['deskripsi'].values[0]
        
        # Galeri Foto
        df_f = pd.read_sql_query("SELECT path_foto FROM data_events WHERE deskripsi = ?", conn, params=(real_desc,))
        for p_foto in df_f['path_foto']:
            img = get_image_base64(p_foto)
            if img: st.image(img, use_container_width=True)
    conn.close()

elif st.session_state.menu_aktif == "Admin Panel":
    st.title("⚙️ Admin Panel")
    t1, t2, t3, t4, t5 = st.tabs(["👥 Input Alumni", "📸 Dokumentasi", "🗓️ Agenda", "🌹 In Memoriam", "🗑️ Hapus Data"])
    
    with t1:
        with st.form("f_alumni", clear_on_submit=True):
            nama_in = st.text_input("Nama Lengkap")
            id_in = st.text_input("User ID")
            if st.form_submit_button("Simpan"):
                conn = sqlite3.connect('alumni.db')
                conn.execute("INSERT OR REPLACE INTO data_anggota (nama, user_id) VALUES (?,?)", (nama_in, id_in))
                conn.commit(); conn.close(); st.success("Data Tersimpan!")

    with t2:
        with st.form("f_doc", clear_on_submit=True):
            files = st.file_uploader("Upload Foto", accept_multiple_files=True)
            ev_n = st.text_input("Nama Event")
            bln = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
            thn = st.selectbox("Tahun", [str(y) for y in range(2020, 2030)])
            if st.form_submit_button("Upload"):
                if files and ev_n:
                    conn = sqlite3.connect('alumni.db')
                    for f in files:
                        path = f"static/img_events/{f.name}"
                        with open(path, "wb") as s: s.write(f.getbuffer())
                        conn.execute("INSERT INTO data_events (path_foto, deskripsi, bulan_tahun) VALUES (?,?,?)", (path, ev_n, f"{bln} {thn}"))
                    conn.commit(); conn.close(); st.success("Berhasil!"); st.rerun()

    with t3:
        with st.form("f_agenda", clear_on_submit=True):
            tgl = st.date_input("Tanggal")
            keg = st.text_input("Kegiatan")
            lok = st.text_input("Lokasi")
            if st.form_submit_button("Simpan Agenda"):
                conn = sqlite3.connect('alumni.db')
                conn.execute("INSERT INTO data_agenda (tanggal, kegiatan, lokasi) VALUES (?,?,?)", (str(tgl), keg, lok))
                conn.commit(); conn.close(); st.success("Agenda Tersimpan!")

    with t4:
        with st.form("f_mem", clear_on_submit=True):
            n_mem = st.text_input("Nama")
            f_mem = st.file_uploader("Foto")
            if st.form_submit_button("Simpan In Memoriam"):
                if n_mem and f_mem:
                    path = f"static/img_memoriam/{f_mem.name}"
                    with open(path, "wb") as s: s.write(f_mem.getbuffer())
                    conn = sqlite3.connect('alumni.db')
                    conn.execute("INSERT INTO data_memoriam (foto, nama) VALUES (?,?)", (path, n_mem))
                    conn.commit(); conn.close(); st.success("Tersimpan!")

    with t5:
        st.subheader("Hapus Data")
        # Logika hapus bisa ditambahkan di sini

elif st.session_state.menu_aktif == "Database Alumni":
    st.title("🔍 Database Alumni")
    conn = sqlite3.connect('alumni.db')
    df = pd.read_sql_query("SELECT nama, user_id FROM data_anggota", conn)
    st.dataframe(df, use_container_width=True)
    conn.close()

elif st.session_state.menu_aktif == "In Memoriam":
    st.title("🌹 In Memoriam")
    conn = sqlite3.connect('alumni.db')
    df_m = pd.read_sql_query("SELECT * FROM data_memoriam", conn)
    conn.close()
    if df_m.empty:
        st.info("Belum ada data.")
    else:
        for idx, row in df_m.iterrows():
            st.write(f"### {row['nama']}")
