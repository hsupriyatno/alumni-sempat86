import streamlit as st
import sqlite3
import pandas as pd
import os
import base64
from datetime import datetime
import streamlit.components.v1 as components

# --- 1. KONFIGURASI & FOLDER ---
st.set_page_config(page_title="Alumni SEMPAT 86", layout="wide")

for folder in ["static/img_profile", "static/img_events"]:
    if not os.path.exists(folder):
        os.makedirs(folder)

# --- 2. FUNGSI DATABASE & HELPER ---
def get_image_base64(path):
    if path and os.path.exists(path):
        with open(path, "rb") as f:
            return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
    return None

def init_db():
    conn.execute('''CREATE TABLE IF NOT EXISTS data_komentar 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 event_deskripsi TEXT, 
                 nama_penulis TEXT, 
                 isi_komentar TEXT, 
                 waktu TEXT)''')
    conn = sqlite3.connect('alumni.db')
    conn.execute('''CREATE TABLE IF NOT EXISTS data_anggota 
                    (foto TEXT, nama TEXT, alamat TEXT, k1 TEXT, k2 TEXT, k3 TEXT, user_id TEXT PRIMARY KEY, password TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS data_events 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, path_foto TEXT, deskripsi TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS data_komentar 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, event_deskripsi TEXT, nama_penulis TEXT, isi_komentar TEXT, waktu TEXT)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS data_agenda 
                    (id INTEGER PRIMARY KEY AUTOINCREMENT, tanggal TEXT, kegiatan TEXT, lokasi TEXT, status TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. SESSION STATE ---
if 'menu_aktif' not in st.session_state:
    st.session_state.menu_aktif = "Home"

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("### 📂 Menu Utama")
    list_menu = ["Home", "Database Alumni", "Berita & Kalender Kegiatan", 
                 "In Memoriam Alumni Sempat 86", "Komunitas", "Networking", 
                 "Donasi", "Admin Panel"]
    
    current_idx = 0
    if st.session_state.menu_aktif in list_menu:
        current_idx = list_menu.index(st.session_state.menu_aktif)
    elif st.session_state.menu_aktif == "Form Pendaftaran":
        current_idx = 0
        
    menu_pilihan = st.radio("Pilih Halaman:", list_menu, index=current_idx)
    if menu_pilihan != st.session_state.menu_aktif and st.session_state.menu_aktif != "Form Pendaftaran":
        st.session_state.menu_aktif = menu_pilihan
        st.rerun()

# --- 5. LOGIKA HALAMAN ---

# A. HOME (Slideshow + Komentar + Agenda)
if st.session_state.menu_aktif == "Home":
    st.markdown('<div style="background-color:#1e478a; padding:20px; border-radius:10px; text-align:center;"><h1 style="color:white;">Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    
    # --- PERBAIKAN TOMBOL DAFTAR ---
    c1, c2, c3 = st.columns([7, 1.5, 1.5])
    with c2:
        if st.button("📝 Daftar", key="btn_daftar_home", use_container_width=True):
            st.session_state.menu_aktif = "Form Pendaftaran"
            st.rerun() # Memaksa aplikasi pindah ke form pendaftaran
    with c3:
        if st.button("🔑 Masuk", key="btn_masuk_home", use_container_width=True):
            st.session_state.menu_aktif = "Database Alumni"
            st.rerun()

    st.write("---")
    st.subheader("📸 Dokumentasi Kegiatan")
    
    conn = sqlite3.connect('alumni.db')
    df_event = pd.read_sql_query("SELECT DISTINCT deskripsi FROM data_events WHERE deskripsi != ''", conn)
    
    if not df_event.empty:
        pilihan = st.selectbox("Pilih Event:", df_event['deskripsi'])
        df_foto = pd.read_sql_query("SELECT path_foto FROM data_events WHERE deskripsi = ?", conn, params=(pilihan,))
        list_f = [get_image_base64(p) for p in df_foto['path_foto'] if get_image_base64(p)]
        
        if list_f:
            # Slideshow Utama
            slides_html = "".join([f'<div class="mySlides fade"><img src="{img}" style="width:100%; height:400px; object-fit:cover; border-radius:15px;"></div>' for img in list_f])
            components.html(f"""
                <div class="slideshow-container">{slides_html}</div>
                <script>
                    let slideIndex = 0; showSlides();
                    function showSlides() {{
                        let slides = document.getElementsByClassName("mySlides");
                        for (let i = 0; i < slides.length; i++) slides[i].style.display = "none";
                        slideIndex++; if (slideIndex > slides.length) slideIndex = 1;
                        if(slides[slideIndex-1]) slides[slideIndex-1].style.display = "block";
                        setTimeout(showSlides, 3000);
                    }}
                </script>
            """, height=410)

            # --- FITUR KOMENTAR (DIPASANG DI SINI) ---
            st.write("---")
            st.markdown("### 💬 Komentar Alumni")
            
            # Ambil komentar dari database
            df_k = pd.read_sql_query("""
                SELECT nama_penulis, isi_komentar, waktu 
                FROM data_komentar 
                WHERE event_deskripsi = ? 
                ORDER BY id DESC
            """, conn, params=(pilihan,))
            
            for _, r in df_k.iterrows():
                col_a, col_b, col_c = st.columns([1, 1.5, 3])
                col_a.caption(r['waktu'])
                col_b.markdown(f"**{r['nama_penulis']}**")
                col_c.info(r['isi_komentar'])
            
            with st.expander("➕ Tulis Komentar"):
                with st.form(f"f_komen_{pilihan}", clear_on_submit=True):
                    n_in = st.text_input("Nama Bapak/Ibu:")
                    p_in = st.text_area("Tulis komentar atau sapaan:")
                    if st.form_submit_button("Kirim Komentar 🚀"):
                        if p_in:
                            waktu_skrg = datetime.now().strftime("%d/%m/%y %H:%M")
                            conn.execute("INSERT INTO data_komentar (event_deskripsi, nama_penulis, isi_komentar, waktu) VALUES (?,?,?,?)",
                                         (pilihan, (n_in if n_in else "Tamu"), p_in, waktu_skrg))
                            conn.commit()
                            st.success("Komentar terkirim!")
                            st.rerun()
    else:
        st.info("Belum ada foto dokumentasi. Silakan upload melalui Admin Panel.")
    
    conn.close()

# B. FORM PENDAFTARAN LENGKAP
elif st.session_state.menu_aktif == "Form Pendaftaran":
    st.title("📝 Form Pendaftaran Alumni")
    if st.button("⬅️ Kembali"):
        st.session_state.menu_aktif = "Home"; st.rerun()
    
    with st.form("regis_lengkap"):
        col1, col2 = st.columns(2)
        with col1:
            nama = st.text_input("Nama Lengkap")
            alamat = st.text_area("Alamat")
            uid = st.text_input("ID/Username (Unik)")
            pwd = st.text_input("Password", type="password")
        with col2:
            k1 = st.text_input("Kelas 1 (Contoh: 1A)")
            k2 = st.text_input("Kelas 2")
            k3 = st.text_input("Kelas 3")
            f_profile = st.file_uploader("Upload Foto Profile", type=['jpg','png','jpeg'])
            
        if st.form_submit_button("Daftar Sekarang 🚀"):
            if nama and uid and pwd:
                path_p = ""
                if f_profile:
                    path_p = f"static/img_profile/{uid}_{f_profile.name}"
                    with open(path_p, "wb") as f: f.write(f_profile.getbuffer())
                
                conn = sqlite3.connect('alumni.db')
                try:
                    conn.execute("INSERT INTO data_anggota VALUES (?,?,?,?,?,?,?,?)", (path_p, nama, alamat, k1, k2, k3, uid, pwd))
                    conn.commit(); st.balloons(); st.success(f"Selamat {nama}!"); st.session_state.menu_aktif = "Database Alumni"; st.rerun()
                except: st.error("ID sudah digunakan.")
                finally: conn.close()

# C. DATABASE ALUMNI LENGKAP
elif st.session_state.menu_aktif == "Database Alumni":
    st.title("🔍 Database Alumni")
    conn = sqlite3.connect('alumni.db')
    df_db = pd.read_sql_query("SELECT foto, nama, k1 as 'Kelas 1', k2 as 'Kelas 2', k3 as 'Kelas 3', alamat FROM data_anggota", conn)
    st.dataframe(df_db, use_container_width=True)
    conn.close()

# D. ADMIN PANEL (Tab Dokumentasi & Agenda Berdampingan)
elif st.session_state.menu_aktif == "Admin Panel":
    st.title("⚙️ Admin Panel")
    tab1, tab2 = st.tabs(["📸 Upload Dokumentasi", "🗓️ Input Agenda"])
    
    with tab1:
        with st.form("admin_foto"):
            files = st.file_uploader("Pilih Foto-foto", type=['jpg','png','jpeg'], accept_multiple_files=True)
            desc_event = st.text_input("Nama Event (Misal: Bukber 2026)")
            if st.form_submit_button("Simpan Dokumentasi") and files:
                conn = sqlite3.connect('alumni.db')
                for f in files:
                    p = f"static/img_events/{datetime.now().strftime('%Y%m%d%H%M%S')}_{f.name}"
                    with open(p, "wb") as file: file.write(f.getbuffer())
                    conn.execute("INSERT INTO data_events (path_foto, deskripsi) VALUES (?,?)", (p, desc_event))
                conn.commit(); conn.close(); st.success("Foto tersimpan!"); st.rerun()

    with tab2:
        with st.form("admin_agenda"):
            tgl = st.date_input("Tanggal")
            keg = st.text_input("Kegiatan")
            lok = st.text_input("Lokasi")
            stat = st.selectbox("Status", ["Terencana", "Persiapan", "Selesai"])
            if st.form_submit_button("Simpan Agenda") and keg:
                conn = sqlite3.connect('alumni.db')
                conn.execute("INSERT INTO data_agenda (tanggal, kegiatan, lokasi, status) VALUES (?,?,?,?)", 
                             (tgl.strftime("%d %B %Y"), keg, lok, stat))
                conn.commit(); conn.close(); st.success("Agenda tersimpan!"); st.rerun()

# E. LAIN-LAIN
else:
    st.title(st.session_state.menu_aktif)
    st.info("Halaman sedang dikembangkan.")
