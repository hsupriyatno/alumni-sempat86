import streamlit as st
import sqlite3
import pandas as pd
import os
import base64
import streamlit.components.v1 as components
from datetime import datetime

# --- 1. SETUP FOLDER & DATABASE (DIKUNCI) ---
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

# --- 2. NAVIGASI SIDEBAR ---
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

# --- A. HALAMAN HOME (DOKUMEN & AGENDA) ---
if st.session_state.menu_aktif == "Home":
    st.markdown('<div style="background:#2b5298;padding:20px;border-radius:10px;color:white;text-align:center;"><h1>Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📝 Daftar Anggota Baru", use_container_width=True): pindah("Form Pendaftaran")
    with c2:
        if st.button("🔍 Lihat Database Anggota", use_container_width=True): pindah("Database Alumni")

    st.write("---")
    st.subheader("📸 Dokumentasi Kegiatan")
    conn = sqlite3.connect('alumni.db')
    df_ev = pd.read_sql_query("SELECT DISTINCT deskripsi FROM data_events", conn)
    
    if not df_ev.empty:
        pilihan_ev = st.selectbox("Pilih Event:", df_ev['deskripsi'])
        df_f = pd.read_sql_query("SELECT path_foto FROM data_events WHERE deskripsi = ?", conn, params=(pilihan_ev,))
        imgs = [get_image_base64(p) for p in df_f['path_foto'] if get_image_base64(p)]
        
        if imgs:
            slides = "".join([f'<div class="mySlides fade"><img src="{i}" style="width:100%; height:450px; object-fit:cover; border-radius:15px;"></div>' for i in imgs])
            components.html(f'<div class="slideshow-container">{slides}</div><script>let sIdx=0;function showS(){{let s=document.getElementsByClassName("mySlides");for(let i=0;i<s.length;i++)s[i].style.display="none";sIdx++;if(sIdx>s.length)sIdx=1;if(s[sIdx-1])s[sIdx-1].style.display="block";setTimeout(showS,3000)}}showS();</script>', height=460)

            st.write("---")
            st.markdown(f"### 💬 Komentar: {pilihan_ev}")
            df_k = pd.read_sql_query("SELECT waktu, nama_penulis, isi_komentar FROM data_komentar WHERE event_deskripsi = ? ORDER BY id DESC", conn, params=(pilihan_ev,))
            if not df_k.empty: st.table(df_k)
            
            with st.expander("Tulis Komentar"):
                with st.form("f_kom", clear_on_submit=True):
                    n_k = st.text_input("Nama")
                    i_k = st.text_area("Komentar")
                    if st.form_submit_button("Kirim"):
                        conn.execute("INSERT INTO data_komentar (event_deskripsi, nama_penulis, isi_komentar, waktu) VALUES (?,?,?,?)",
                                     (pilihan_ev, n_k, i_k, datetime.now().strftime("%d-%m-%Y")))
                        conn.commit(); st.rerun()
    
    st.write("---")
    st.subheader("🗓️ Agenda Kegiatan")
    df_ag = pd.read_sql_query("SELECT tanggal, kegiatan, lokasi FROM data_agenda", conn)
    if not df_ag.empty: st.table(df_ag)
    conn.close()

# --- B. DATABASE ALUMNI (DIKUNCI) ---
elif st.session_state.menu_aktif == "Database Alumni":
    st.title("🔍 Database Alumni")
    conn = sqlite3.connect('alumni.db')
    df_db = pd.read_sql_query("SELECT foto_profile, nama, kelas_1, kelas_2, kelas_3, alamat FROM data_anggota", conn)
    conn.close()
    if not df_db.empty:
        df_db['foto_profile'] = df_db['foto_profile'].apply(get_image_base64)
        st.data_editor(df_db, column_config={"foto_profile": st.column_config.ImageColumn("Foto")}, use_container_width=True, hide_index=True)

# --- C. IN MEMORIAM (PERBAIKAN TAMPILAN MULTI-DATA) ---
elif st.session_state.menu_aktif == "In Memoriam":
    st.markdown('<div style="background:#424242;padding:20px;border-radius:10px;color:white;text-align:center;"><h1>🌹 In Memoriam Sempat 86</h1></div>', unsafe_allow_html=True)
    st.write("")
    conn = sqlite3.connect('alumni.db')
    # Ambil semua data tanpa filter agar tidak tertutup data terakhir
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
                st.write("---")
    else:
        st.info("Belum ada data In Memoriam.")

# --- D. ADMIN PANEL ---
elif st.session_state.menu_aktif == "Admin Panel":
    st.title("⚙️ Admin Panel")
    t1, t2, t3 = st.tabs(["📸 Dokumentasi", "🗓️ Agenda", "🌹 In Memoriam"])
    
    with t1:
        with st.form("up_doc", clear_on_submit=True):
            f = st.file_uploader("Upload Foto Dokumentasi", accept_multiple_files=True)
            e = st.text_input("Nama Event")
            if st.form_submit_button("Simpan Dokumentasi") and f and e:
                conn = sqlite3.connect('alumni.db')
                for pic in f:
                    p = f"static/img_events/{pic.name}"
                    with open(p, "wb") as save: save.write(pic.getbuffer())
                    conn.execute("INSERT INTO data_events (path_foto, deskripsi) VALUES (?,?)", (p, e))
                conn.commit(); conn.close(); st.success("Dokumentasi Berhasil Disimpan!"); st.rerun()

    with t2:
        with st.form("up_age", clear_on_submit=True):
            tgl = st.date_input("Tanggal").strftime("%d-%m-%Y")
            keg = st.text_input("Kegiatan")
            lok = st.text_input("Lokasi")
            if st.form_submit_button("Simpan Agenda"):
                conn = sqlite3.connect('alumni.db')
                conn.execute("INSERT INTO data_agenda (tanggal, kegiatan, lokasi) VALUES (?,?,?)", (tgl, keg, lok))
                conn.commit(); conn.close(); st.success("Agenda Disimpan!")

    with t3:
        with st.form("up_mem", clear_on_submit=True):
            m_nama = st.text_input("Nama Rekan")
            m_tgl = st.text_input("Tanggal Wafat")
            m_ket = st.text_area("Keterangan")
            m_foto = st.file_uploader("Upload Foto", type=['jpg','png','jpeg'])
            if st.form_submit_button("Simpan In Memoriam"):
                if m_nama and m_foto:
                    # Tambahkan timestamp di nama file agar tidak saling menimpa
                    fname = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{m_foto.name}"
                    p = f"static/img_memoriam/{fname}"
                    with open(p, "wb") as save: save.write(m_foto.getbuffer())
                    conn = sqlite3.connect('alumni.db')
                    conn.execute("INSERT INTO data_memoriam (foto, nama, tanggal_wafat, keterangan) VALUES (?,?,?,?)", (p, m_nama, m_tgl, m_ket))
                    conn.commit(); conn.close(); st.success("Data In Memoriam Disimpan!"); st.rerun()

elif st.session_state.menu_aktif == "Form Pendaftaran":
    st.title("📝 Form Pendaftaran")
    with st.form("reg"):
        n = st.text_input("Nama")
        u = st.text_input("User ID")
        p = st.text_input("Password", type="password")
        if st.form_submit_button("Daftar"):
            conn = sqlite3.connect('alumni.db')
            conn.execute("INSERT INTO data_anggota (nama, user_id, password) VALUES (?,?,?)", (n, u, p))
            conn.commit(); conn.close(); st.success("Berhasil!"); pindah("Home")
