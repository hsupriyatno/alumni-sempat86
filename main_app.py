import streamlit as st
import sqlite3
import pandas as pd
import os
import base64
import streamlit.components.v1 as components
from datetime import datetime

# --- 1. SETUP FOLDER & DATABASE (DIKUNCI) ---
for folder in ['static/img_profile', 'static/img_events']:
    if not os.path.exists(folder): os.makedirs(folder)

def init_db():
    conn = sqlite3.connect('alumni.db')
    c = conn.cursor()
    # Tabel Anggota (Lengkap: Foto, Nama, ID, Pwd, Kelas 1, 2, 3, Alamat)
    c.execute('''CREATE TABLE IF NOT EXISTS data_anggota (
                    foto_profile TEXT, nama TEXT, user_id TEXT PRIMARY KEY, 
                    password TEXT, kelas_1 TEXT, kelas_2 TEXT, kelas_3 TEXT, alamat TEXT)''')
    # Tabel Dokumentasi Foto
    c.execute('''CREATE TABLE IF NOT EXISTS data_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, path_foto TEXT, deskripsi TEXT)''')
    # Tabel Komentar
    c.execute('''CREATE TABLE IF NOT EXISTS data_komentar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, event_deskripsi TEXT, 
                    nama_penulis TEXT, isi_komentar TEXT, waktu TEXT)''')
    # Tabel Agenda
    c.execute('''CREATE TABLE IF NOT EXISTS data_agenda (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, kegiatan TEXT, lokasi TEXT)''')
    conn.commit()
    conn.close()

init_db()

def get_image_base64(path):
    if not path or not os.path.exists(path): return None
    try:
        with open(path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
    except: return None

# --- 2. KONFIGURASI NAVIGASI SIDEBAR ---
st.set_page_config(page_title="Alumni SMPN 4 Cirebon 86", layout="wide")

if 'menu_aktif' not in st.session_state:
    st.session_state.menu_aktif = "Home"

with st.sidebar:
    st.title("🏫 SEMPAT 86")
    if st.button("🏠 Home", use_container_width=True): 
        st.session_state.menu_aktif = "Home"
        st.rerun()
    if st.button("🔍 Database Alumni", use_container_width=True): 
        st.session_state.menu_aktif = "Database Alumni"
        st.rerun()
    st.write("---")
    if st.button("⚙️ Admin Panel", use_container_width=True): 
        st.session_state.menu_aktif = "Admin Panel"
        st.rerun()

# --- 3. LOGIKA HALAMAN ---

# --- HALAMAN 1: HOME (KUNCI) ---
if st.session_state.menu_aktif == "Home":
    # Banner Welcome (Biru)
    st.markdown('<div style="background:#2b5298;padding:40px;border-radius:20px;color:white;text-align:center;"><h1>Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    
    # Baris Tombol Utama
    st.write("")
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📝 Daftar Anggota Baru", use_container_width=True):
            st.session_state.menu_aktif = "Form Pendaftaran"
            st.rerun()
    with col_b:
        if st.button("🔍 Lihat Database Anggota", use_container_width=True):
            st.session_state.menu_aktif = "Database Alumni"
            st.rerun()

    # Dokumentasi Slideshow
    st.write("---")
    st.subheader("📸 Dokumentasi Kegiatan")
    conn = sqlite3.connect('alumni.db')
    df_ev = pd.read_sql_query("SELECT DISTINCT deskripsi FROM data_events", conn)
    
    if not df_ev.empty:
        pilihan_ev = st.selectbox("Pilih Nama Event:", df_ev['deskripsi'])
        df_f = pd.read_sql_query("SELECT path_foto FROM data_events WHERE deskripsi = ?", conn, params=(pilihan_ev,))
        imgs = [get_image_base64(p) for p in df_f['path_foto'] if get_image_base64(p)]
        
        if imgs:
            slides = "".join([f'<div class="mySlides fade"><img src="{i}" style="width:100%; height:450px; object-fit:cover; border-radius:15px;"></div>' for i in imgs])
            components.html(f'<div class="slideshow-container">{slides}</div><script>let sIdx=0;function showS(){{let s=document.getElementsByClassName("mySlides");for(let i=0;i<s.length;i++)s[i].style.display="none";sIdx++;if(sIdx>s.length)sIdx=1;if(s[sIdx-1])s[sIdx-1].style.display="block";setTimeout(showS,3000)}}showS();</script>', height=460)

            # Fitur Komentar
            st.write("---")
            st.markdown(f"### 💬 Komentar: {pilihan_ev}")
            df_k = pd.read_sql_query("SELECT waktu, nama_penulis, isi_komentar FROM data_komentar WHERE event_deskripsi = ? ORDER BY id DESC", conn, params=(pilihan_ev,))
            if not df_k.empty:
                st.table(df_k)
            
            with st.expander("Tulis Komentar Baru"):
                with st.form("f_kom", clear_on_submit=True):
                    n_k = st.text_input("Nama Anda")
                    i_k = st.text_area("Isi Komentar/Sapaan")
                    if st.form_submit_button("Kirim Komentar"):
                        conn.execute("INSERT INTO data_komentar (event_deskripsi, nama_penulis, isi_komentar, waktu) VALUES (?,?,?,?)",
                                     (pilihan_ev, n_k, i_k, datetime.now().strftime("%d-%m-%Y")))
                        conn.commit()
                        st.rerun()

    # Tabel Agenda Kegiatan
    st.write("---")
    st.subheader("🗓️ Agenda Kegiatan Alumni")
    df_ag = pd.read_sql_query("SELECT tanggal, kegiatan, lokasi FROM data_agenda", conn)
    if not df_ag.empty:
        st.table(df_ag)
    else:
        st.info("Belum ada agenda terdaftar.")
    conn.close()

# --- HALAMAN 2: ADMIN PANEL (KUNCI) ---
elif st.session_state.menu_aktif == "Admin Panel":
    st.title("⚙️ Admin Panel")
    t_doc, t_age = st.tabs(["📸 Dokumentasi Kegiatan", "🗓️ Agenda Kegiatan"])
    
    with t_doc:
        with st.form("admin_doc", clear_on_submit=True):
            up_files = st.file_uploader("Upload Foto-foto (Bisa lebih dari satu)", accept_multiple_files=True, type=['jpg','png','jpeg'])
            up_name = st.text_input("Masukkan Nama Event")
            if st.form_submit_button("Simpan Dokumentasi") and up_files and up_name:
                conn = sqlite3.connect('alumni.db')
                for f in up_files:
                    p = f"static/img_events/{f.name}"
                    with open(p, "wb") as save_f: save_f.write(f.getbuffer())
                    conn.execute("INSERT INTO data_events (path_foto, deskripsi) VALUES (?,?)", (p, up_name))
                conn.commit(); conn.close()
                st.success(f"Berhasil! {len(up_files)} foto ditambahkan ke event {up_name}.")

    with t_age:
        with st.form("admin_age", clear_on_submit=True):
            a_tgl = st.date_input("Tanggal").strftime("%d-%m-%Y")
            a_keg = st.text_input("Nama Kegiatan")
            a_lok = st.text_input("Lokasi Acara")
            if st.form_submit_button("Tambah Agenda"):
                conn = sqlite3.connect('alumni.db')
                conn.execute("INSERT INTO data_agenda (tanggal, kegiatan, lokasi) VALUES (?,?,?)", (a_tgl, a_keg, a_lok))
                conn.commit(); conn.close()
                st.success("Agenda baru berhasil disimpan!")

# --- HALAMAN 3: FORM PENDAFTARAN (KUNCI) ---
elif st.session_state.menu_aktif == "Form Pendaftaran":
    st.title("📝 Form Pendaftaran Anggota")
    if st.button("⬅️ Kembali ke Home"):
        st.session_state.menu_aktif = "Home"
        st.rerun()
        
    with st.form("reg_full", clear_on_submit=True):
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            r_nama = st.text_input("Nama Lengkap")
            r_uid = st.text_input("ID / Username")
            r_pwd = st.text_input("Password", type="password")
            r_foto = st.file_uploader("Upload Foto Profile", type=['jpg','png','jpeg'])
        with col_r2:
            r_k1 = st.text_input("Kelas 1")
            r_k2 = st.text_input("Kelas 2")
            r_k3 = st.text_input("Kelas 3")
            r_almt = st.text_area("Alamat Saat Ini")
        
        if st.form_submit_button("Selesaikan Pendaftaran"):
            if r_nama and r_uid and r_pwd:
                path_p = f"static/img_profile/{r_uid}.png" if r_foto else ""
                if r_foto:
                    with open(path_p, "wb") as pf: pf.write(r_foto.getbuffer())
                conn = sqlite3.connect('alumni.db')
                try:
                    conn.execute("INSERT INTO data_anggota VALUES (?,?,?,?,?,?,?,?)", (path_p, r_nama, r_uid, r_pwd, r_k1, r_k2, r_k3, r_almt))
                    conn.commit(); conn.close()
                    st.success("Data berhasil disimpan! Selamat bergabung!"); st.balloons()
                except: st.error("User ID sudah digunakan.")
            else: st.warning("Nama, ID, dan Password wajib diisi.")

# --- HALAMAN TAMBAHAN: DATABASE ALUMNI ---
elif st.session_state.menu_aktif == "Database Alumni":
    st.title("🔍 Database Alumni SMPN 4 Cirebon 86")
    conn = sqlite3.connect('alumni.db')
    df_res = pd.read_sql_query("SELECT foto_profile, nama, kelas_1, kelas_2, kelas_3, alamat FROM data_anggota", conn)
    conn.close()
    if not df_res.empty:
        df_res['foto_profile'] = df_res['foto_profile'].apply(get_image_base64)
        st.data_editor(df_res, column_config={"foto_profile": st.column_config.ImageColumn("Foto Profile")}, use_container_width=True, hide_index=True)
    else: st.info("Database masih kosong. Silakan mendaftar terlebih dahulu.")
