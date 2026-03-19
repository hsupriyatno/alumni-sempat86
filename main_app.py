import streamlit as st
import sqlite3
import pandas as pd
import os
import base64
import streamlit.components.v1 as components
from datetime import datetime

# --- 1. SETUP ASSET & DATABASE ---
for folder in ['static/img_profile', 'static/img_events']:
    if not os.path.exists(folder): os.makedirs(folder)

def init_db():
    conn = sqlite3.connect('alumni.db')
    c = conn.cursor()
    # Tabel Anggota (Lengkap: Foto, Nama, ID, Pwd, Kls 1-3, Alamat)
    c.execute('''CREATE TABLE IF NOT EXISTS data_anggota (
                    foto_profile TEXT, nama TEXT, user_id TEXT PRIMARY KEY, 
                    password TEXT, kelas_1 TEXT, kelas_2 TEXT, kelas_3 TEXT, alamat TEXT)''')
    # Tabel Dokumentasi
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
    with open(path, "rb") as img_file:
        return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"

# --- 2. NAVIGASI (SIDEBAR) ---
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

# A. HALAMAN HOME
if st.session_state.menu_aktif == "Home":
    st.markdown('<div style="background:#2b5298;padding:40px;border-radius:20px;color:white;text-align:center;"><h1>Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    
    # Tombol Akses
    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📝 Daftar Anggota Baru", use_container_width=True):
            st.session_state.menu_aktif = "Form Pendaftaran"
            st.rerun()
    with c2:
        if st.button("🔍 Lihat Database Anggota", use_container_width=True):
            st.session_state.menu_aktif = "Database Alumni"
            st.rerun()

    # Dokumentasi & Slideshow
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

            # Fitur Komentar
            st.write("---")
            st.markdown(f"### 💬 Komentar: {pilihan_ev}")
            df_k = pd.read_sql_query("SELECT waktu, nama_penulis, isi_komentar FROM data_komentar WHERE event_deskripsi = ? ORDER BY id DESC", conn, params=(pilihan_ev,))
            if not df_k.empty:
                st.table(df_k)
            
            with st.expander("Tulis Komentar"):
                with st.form("f_kom", clear_on_submit=True):
                    n_k = st.text_input("Nama")
                    i_k = st.text_area("Komentar")
                    if st.form_submit_button("Kirim"):
                        conn.execute("INSERT INTO data_komentar (event_deskripsi, nama_penulis, isi_komentar, waktu) VALUES (?,?,?,?)",
                                     (pilihan_ev, n_k, i_k, datetime.now().strftime("%d-%m-%Y")))
                        conn.commit()
                        st.rerun()

    # Tabel Agenda Kegiatan
    st.write("---")
    st.subheader("🗓️ Agenda Kegiatan")
    df_ag = pd.read_sql_query("SELECT tanggal, kegiatan, lokasi FROM data_agenda", conn)
    if not df_ag.empty:
        st.table(df_ag)
    else:
        st.info("Belum ada agenda terdekat.")
    conn.close()

# B. ADMIN PANEL (2 Jenis Form)
elif st.session_state.menu_aktif == "Admin Panel":
    st.title("⚙️ Admin Panel")
    t1, t2 = st.tabs(["📸 Dokumentasi Kegiatan", "🗓️ Agenda Kegiatan"])
    
    with t1:
        with st.form("admin_doc", clear_on_submit=True):
            files = st.file_uploader("Upload Foto (Bisa banyak sekaligus)", accept_multiple_files=True, type=['jpg','png','jpeg'])
            e_name = st.text_input("Nama Kegiatan/Event")
            if st.form_submit_button("Simpan Dokumentasi") and files and e_name:
                conn = sqlite3.connect('alumni.db')
                for f in files:
                    path = f"static/img_events/{f.name}"
                    with open(path, "wb") as save_f: save_f.write(f.getbuffer())
                    conn.execute("INSERT INTO data_events (path_foto, deskripsi) VALUES (?,?)", (path, e_name))
                conn.commit(); conn.close()
                st.success(f"Berhasil mengunggah {len(files)} foto ke event {e_name}!")

    with t2:
        with st.form("admin_agenda", clear_on_submit=True):
            tgl = st.date_input("Tanggal Agenda").strftime("%d-%m-%Y")
            keg = st.text_input("Nama Kegiatan")
            lok = st.text_input("Lokasi")
            if st.form_submit_button("Simpan Agenda"):
                conn = sqlite3.connect('alumni.db')
                conn.execute("INSERT INTO data_agenda (tanggal, kegiatan, lokasi) VALUES (?,?,?)", (tgl, keg, lok))
                conn.commit(); conn.close()
                st.success("Agenda berhasil ditambahkan!")

# C. FORM PENDAFTARAN ANGGOTA
elif st.session_state.menu_aktif == "Form Pendaftaran":
    st.title("📝 Form Pendaftaran Anggota")
    if st.button("⬅️ Kembali ke Home"):
        st.session_state.menu_aktif = "Home"
        st.rerun()
        
    with st.form("reg_form", clear_on_submit=True):
        c_reg1, c_reg2 = st.columns(2)
        with c_reg1:
            nama = st.text_input("Nama Lengkap")
            uid = st.text_input("User ID")
            pwd = st.text_input("Password", type="password")
            foto = st.file_uploader("Upload Foto Profile", type=['jpg','png','jpeg'])
        with c_reg2:
            k1 = st.text_input("Kelas 1 (Contoh: 1-A)")
            k2 = st.text_input("Kelas 2")
            k3 = st.text_input("Kelas 3")
            almt = st.text_area("Alamat Lengkap")
        
        if st.form_submit_button("Daftar Sekarang"):
            if nama and uid and pwd:
                p_foto = f"static/img_profile/{uid}.png" if foto else ""
                if foto:
                    with open(p_foto, "wb") as pf: pf.write(foto.getbuffer())
                conn = sqlite3.connect('alumni.db')
                try:
                    conn.execute("INSERT INTO data_anggota VALUES (?,?,?,?,?,?,?,?)", (p_foto, nama, uid, pwd, k1, k2, k3, almt))
                    conn.commit(); conn.close()
                    st.success("Pendaftaran Berhasil!")
                    st.balloons()
                except:
                    st.error("User ID sudah terdaftar!")
            else:
                st.warning("Mohon lengkapi Nama, ID, dan Password.")

# D. DATABASE ALUMNI
elif st.session_state.menu_aktif == "Database Alumni":
    st.title("🔍 Database Alumni")
    conn = sqlite3.connect('alumni.db')
    df_db = pd.read_sql_query("SELECT foto_profile, nama, kelas_1, kelas_2, kelas_3, alamat FROM data_anggota", conn)
    conn.close()
    if not df_db.empty:
        df_db['foto_profile'] = df_db['foto_profile'].apply(get_image_base64)
        st.data_editor(df_db, column_config={"foto_profile": st.column_config.ImageColumn("Foto")}, use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada data alumni yang terdaftar.")
