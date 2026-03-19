import streamlit as st
import sqlite3
import pandas as pd
import os
import base64
import streamlit.components.v1 as components
from datetime import datetime

# --- 1. SETUP FOLDER & DATABASE ---
for folder in ['static/img_profile', 'static/img_events']:
    if not os.path.exists(folder): os.makedirs(folder)

def init_db():
    conn = sqlite3.connect('alumni.db')
    c = conn.cursor()
    # Tabel Anggota Lengkap (Sesuai Poin 4 & 5)
    c.execute('''CREATE TABLE IF NOT EXISTS data_anggota (
                    foto_profile TEXT, nama TEXT, user_id TEXT PRIMARY KEY, 
                    password TEXT, kelas_1 TEXT, kelas_2 TEXT, kelas_3 TEXT, alamat TEXT)''')
    # Tabel Dokumentasi (Sesuai Poin 3)
    c.execute('''CREATE TABLE IF NOT EXISTS data_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, path_foto TEXT, deskripsi TEXT)''')
    # Tabel Komentar (Sesuai Poin 2)
    c.execute('''CREATE TABLE IF NOT EXISTS data_komentar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, event_deskripsi TEXT, 
                    nama_penulis TEXT, isi_komentar TEXT, waktu TEXT)''')
    # Tabel Agenda (Sesuai Poin 2 & 3)
    c.execute('''CREATE TABLE IF NOT EXISTS data_agenda (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, kegiatan TEXT, lokasi TEXT)''')
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

# --- 3. SIDEBAR (Poin 1) ---
with st.sidebar:
    st.title("🏫 SEMPAT 86")
    if st.button("🏠 Home", use_container_width=True): pindah("Home")
    if st.button("🔍 Database Alumni", use_container_width=True): pindah("Database Alumni")
    st.write("---")
    if st.button("⚙️ Admin Panel", use_container_width=True): pindah("Admin Panel")

# --- 4. LOGIKA HALAMAN ---

# --- A. HALAMAN HOME (Poin 2) ---
if st.session_state.menu_aktif == "Home":
    st.markdown('<div style="background:#2b5298;padding:20px;border-radius:10px;color:white;text-align:center;"><h1>Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    
    # Tombol Akses (Poin 2)
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📝 Daftar Anggota Baru", use_container_width=True): pindah("Form Pendaftaran")
    with c2:
        if st.button("🔍 Lihat Database Anggota", use_container_width=True): pindah("Database Alumni")

    # Dokumentasi & Slideshow (Poin 2)
    st.write("---")
    st.subheader("📸 Dokumentasi Kegiatan")
    conn = sqlite3.connect('alumni.db')
    df_ev = pd.read_sql_query("SELECT DISTINCT deskripsi FROM data_events", conn)
    
    if not df_ev.empty:
        pilihan_ev = st.selectbox("Pilih Event:", df_ev['deskripsi'])
        df_f = pd.read_sql_query("SELECT path_foto FROM data_events WHERE deskripsi = ?", conn, params=(pilihan_ev,))
        imgs = [get_image_base64(p) for p in df_f['path_foto'] if get_image_base64(p)]
        
        if imgs:
            slides = "".join([f'<div class="mySlides fade"><img src="{i}" style="width:100%; height:400px; object-fit:cover; border-radius:15px;"></div>' for i in imgs])
            components.html(f'<div class="slideshow-container">{slides}</div><script>let sIdx=0;function showS(){{let s=document.getElementsByClassName("mySlides");for(let i=0;i<s.length;i++)s[i].style.display="none";sIdx++;if(sIdx>s.length)sIdx=1;if(s[sIdx-1])s[sIdx-1].style.display="block";setTimeout(showS,3000)}}showS();</script>', height=410)

            # Fitur Komentar (Poin 2)
            st.write("---")
            st.markdown(f"### 💬 Komentar: {pilihan_ev}")
            df_k = pd.read_sql_query("SELECT waktu, nama_penulis, isi_komentar FROM data_komentar WHERE event_deskripsi = ? ORDER BY id DESC", conn, params=(pilihan_ev,))
            st.table(df_k) if not df_k.empty else st.caption("Belum ada komentar.")
            
            with st.expander("Tulis Komentar"):
                with st.form("f_kom"):
                    n_k = st.text_input("Nama")
                    i_k = st.text_area("Komentar")
                    if st.form_submit_button("Kirim"):
                        conn.execute("INSERT INTO data_komentar (event_deskripsi, nama_penulis, isi_komentar, waktu) VALUES (?,?,?,?)",
                                     (pilihan_ev, n_k, i_k, datetime.now().strftime("%d/%m/%y")))
                        conn.commit(); st.rerun()

    # Tabel Agenda (Poin 2)
    st.write("---")
    st.subheader("🗓️ Agenda Kegiatan")
    df_ag = pd.read_sql_query("SELECT tanggal, kegiatan, lokasi FROM data_agenda", conn)
    st.table(df_ag) if not df_ag.empty else st.info("Belum ada agenda terdekat.")
    conn.close()

# --- B. ADMIN PANEL (Poin 3) ---
elif st.session_state.menu_aktif == "Admin Panel":
    st.title("⚙️ Admin Panel")
    
    tab1, tab2 = st.tabs(["Upload Dokumentasi", "Input Agenda"])
    
    with tab1:
        with st.form("admin_doc", clear_on_submit=True):
            files = st.file_uploader("Upload Foto (Bisa banyak)", accept_multiple_files=True, type=['jpg','png'])
            e_name = st.text_input("Nama Kegiatan")
            if st.form_submit_button("Submit Dokumentasi") and files and e_name:
                conn = sqlite3.connect('alumni.db')
                for f in files:
                    path = f"static/img_events/{f.name}"
                    with open(path, "wb") as save_f: save_f.write(f.getbuffer())
                    conn.execute("INSERT INTO data_events (path_foto, deskripsi) VALUES (?,?)", (path, e_name))
                conn.commit(); conn.close(); st.success("Dokumentasi Berhasil Diupdate!")

    with tab2:
        with st.form("admin_agenda"):
            tgl = st.date_input("Tanggal").strftime("%d-%m-%Y")
            keg = st.text_input("Kegiatan")
            lok = st.text_input("Lokasi")
            if st.form_submit_button("Simpan Agenda"):
                conn = sqlite3.connect('alumni.db')
                conn.execute("INSERT INTO data_agenda (tanggal, kegiatan, lokasi) VALUES (?,?,?)", (tgl, keg, lok))
                conn.commit(); conn.close(); st.success("Agenda Disimpan!")

# --- C. FORM PENDAFTARAN (Poin 4) ---
elif st.session_state.menu_aktif == "Form Pendaftaran":
    st.title("📝 Form Pendaftaran Anggota")
    with st.form("reg_form"):
        f1, f2 = st.columns(2)
        with f1:
            nama = st.text_input("Nama Lengkap")
            uid = st.text_input("ID / Username")
            pwd = st.text_input("Password", type="password")
            foto = st.file_uploader("Upload Foto Profile", type=['jpg','png'])
        with f2:
            k1 = st.text_input("Kelas 1")
            k2 = st.text_input("Kelas 2")
            k3 = st.text_input("Kelas 3")
            almt = st.text_area("Alamat")
        
        if st.form_submit_button("Daftar"):
            if nama and uid and pwd:
                p_foto = f"static/img_profile/{uid}.png" if foto else ""
                if foto:
                    with open(p_foto, "wb") as pf: pf.write(foto.getbuffer())
                conn = sqlite3.connect('alumni.db')
                conn.execute("INSERT INTO data_anggota VALUES (?,?,?,?,?,?,?,?)", (p_foto, nama, uid, pwd, k1, k2, k3, almt))
                conn.commit(); conn.close(); st.success("Pendaftaran Berhasil!"); pindah("Home")

# --- D. DATABASE ALUMNI (Poin 5) ---
elif st.session_state.menu_aktif == "Database Alumni":
    st.title("🔍 Database Alumni")
    conn = sqlite3.connect('alumni.db')
    df = pd.read_sql_query("SELECT foto_profile, nama, kelas_1, kelas_2, kelas_3, alamat FROM data_anggota", conn)
    conn.close()
    if not df.empty:
        df['foto_profile'] = df['foto_profile'].apply(get_image_base64)
        st.data_editor(df, column_config={"foto_profile": st.column_config.ImageColumn("Foto")}, use_container_width=True, hide_index=True)
    else: st.info("Database masih kosong.")
