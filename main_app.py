import streamlit as st
import sqlite3
import pandas as pd
import os
import base64
import streamlit.components.v1 as components
from datetime import datetime

# --- 1. SETUP FOLDER ---
folders = ['static/img_profile', 'static/img_events']
for folder in folders:
    if not os.path.exists(folder):
        os.makedirs(folder)

# --- 2. FUNGSI KONVERSI GAMBAR ---
def get_image_base64(path):
    if not path: return None
    clean_path = path.replace('\\', '/')
    if 'static/' in clean_path:
        clean_path = 'static/' + clean_path.split('static/')[-1]
    
    full_path = os.path.join("static", clean_path) if not clean_path.startswith("static") else clean_path
    
    if os.path.exists(full_path):
        with open(full_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{encoded}"
    return None

# --- 3. DATABASE SETUP (TERMASUK TABEL KOMENTAR) ---
def init_db():
    conn = sqlite3.connect('alumni.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS data_anggota (
                    foto_profile TEXT, nama TEXT, alamat TEXT, 
                    kelas_1 TEXT, kelas_2 TEXT, kelas_3 TEXT, 
                    user_id TEXT PRIMARY KEY, password TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS data_agenda (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tanggal TEXT, kegiatan TEXT, lokasi TEXT, status TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS data_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path_foto TEXT, deskripsi TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS data_komentar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_deskripsi TEXT,
                    nama_penulis TEXT,
                    isi_komentar TEXT,
                    waktu TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 4. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Alumni SMPN 4 Cirebon 86", page_icon="🏫", layout="wide")

if 'menu_aktif' not in st.session_state:
    st.session_state.menu_aktif = "Home"

# --- 5. SIDEBAR NAVIGASI ---
with st.sidebar:
    st.markdown("### 📂 Menu Utama")
    list_menu = ["Home", "Database Alumni", "Berita & Kalender Kegiatan", 
                 "In Memoriam Alumni Sempat 86", "Komunitas", "Networking", "Donasi", "Admin Panel"]
    menu_pilihan = st.radio("Pilih Halaman:", list_menu, index=list_menu.index(st.session_state.menu_aktif))
    if menu_pilihan != st.session_state.menu_aktif:
        st.session_state.menu_aktif = menu_pilihan
        st.rerun()

# --- 6. LOGIKA HALAMAN HOME (GANTI TOTAL BAGIAN INI) ---
if st.session_state.menu_aktif == "Home":
    st.markdown('<div style="background: #2b5298; padding: 30px; border-radius: 15px; color: white; text-align: center;"><h1>Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    st.write("---")

    # --- SLIDESHOW DOKUMENTASI ---
    st.subheader("📸 Dokumentasi Kegiatan")
    conn = sqlite3.connect('alumni.db')
    df_list_event = pd.read_sql_query("SELECT DISTINCT deskripsi FROM data_events WHERE deskripsi != ''", conn)
    
    if not df_list_event.empty:
        pilihan_event = st.selectbox("Pilih Event untuk Dilihat:", df_list_event['deskripsi'])
        
        # Ambil data foto
        df_foto = pd.read_sql_query("SELECT path_foto FROM data_events WHERE deskripsi = ?", conn, params=(pilihan_event,))
        list_foto = [get_image_base64(p) for p in df_foto['path_foto'] if get_image_base64(p)]
        
        if list_foto:
            if len(list_foto) > 1:
                html_slides = "".join([f'<div class="mySlides fade"><img src="{img}" style="width:100%; height:450px; object-fit:cover; border-radius:15px;"></div>' for img in list_foto])
                html_code = f"""
                <style>
                    .mySlides {{display: none;}}
                    .fade {{ animation: fadeanim 1.5s; }}
                    @keyframes fadeanim {{ from {{opacity: .4}} to {{opacity: 1}} }}
                </style>
                <div class="slideshow-container">{html_slides}</div>
                <script>
                    let slideIndex = 0;
                    function showSlides() {{
                        let slides = document.getElementsByClassName("mySlides");
                        for (let i = 0; i < slides.length; i++) {{ slides[i].style.display = "none"; }}
                        slideIndex++;
                        if (slideIndex > slides.length) {{slideIndex = 1}}
                        if (slides[slideIndex-1]) {{ slides[slideIndex-1].style.display = "block"; }}
                        setTimeout(showSlides, 3000);
                    }}
                    showSlides();
                </script>
                """
                components.html(html_code, height=460)
            else:
                st.image(list_foto[0], use_container_width=True, caption=f"📍 Event: {pilihan_event}")
            
            # --- FITUR KOMENTAR ---
# --- TAMPILAN KOMENTAR SEJAJAR (TANGGAL | NAMA | KOMENTAR) ---
            st.write("---")
            st.markdown("### 💬 Komentar Alumni")
            
            # Ambil data komentar
            df_komen = pd.read_sql_query("SELECT nama_penulis, isi_komentar, waktu FROM data_komentar WHERE event_deskripsi = ? ORDER BY id DESC", 
                                        conn, params=(pilihan_event,))
            
            if not df_komen.empty:
                # Membuat Header agar sejajar
                h1, h2, h3 = st.columns([1, 1.5, 3])
                h1.markdown("**Waktu**")
                h2.markdown("**Nama**")
                h3.markdown("**Komentar**")
                st.write("---")

                for _, row in df_komen.iterrows():
                    # Membuat baris data yang sejajar
                    col1, col2, col3 = st.columns([1, 1.5, 3])
                    
                    # Kolom 1: Waktu (Ukuran kecil/abu-abu)
                    col1.markdown(f"<small style='color:gray;'>{row['waktu']}</small>", unsafe_allow_html=True)
                    
                    # Kolom 2: Nama
                    col2.markdown(f"**{row['nama_penulis']}**")
                    
                    # Kolom 3: Isi Komentar
                    col3.info(row['isi_komentar'])
            else:
                st.info("Belum ada komentar untuk event ini.")
            
            with st.expander("➕ Tulis Komentar"):
                with st.form(key=f"form_komen_{pilihan_event}", clear_on_submit=True):
                    nama_in = st.text_input("Nama Anda:", placeholder="Kosongkan untuk jadi Tamu")
                    pesan_in = st.text_area("Tulis komentar:")
                    if st.form_submit_button("Kirim Komentar 🚀") and pesan_in:
                        c = conn.cursor()
                        waktu_skrg = datetime.now().strftime("%d/%m/%y %H:%M")
                        nama_final = nama_in if nama_in else "Tamu"
                        check = c.execute("SELECT nama FROM data_anggota WHERE nama = ?", (nama_final,)).fetchone()
                        if not check and nama_final != "Tamu":
                            nama_final = f"{nama_final} (Tamu)"
                        c.execute("INSERT INTO data_komentar (event_deskripsi, nama_penulis, isi_komentar, waktu) VALUES (?,?,?,?)",
                                  (pilihan_event, nama_final, pesan_in, waktu_skrg))
                        conn.commit()
                        st.rerun()
        else:
            st.warning("Foto tidak ditemukan.")
    else:
        st.info("Belum ada foto dokumentasi.")
    
    st.write("---")
    st.subheader("🗓️ Agenda Kegiatan Mendatang")
    df_agenda = pd.read_sql_query("SELECT tanggal, kegiatan, lokasi, status FROM data_agenda", conn)
    if not df_agenda.empty:
        st.table(df_agenda[['tanggal', 'kegiatan', 'lokasi', 'status']])
    conn.close()
# --- AKHIR LOGIKA HOME ---

# --- 7. ADMIN PANEL (UNTUK UPLOAD) ---
elif st.session_state.menu_aktif == "Admin Panel":
    st.title("⚙️ Admin Panel")
    with st.form("upload_event", clear_on_submit=True):
        files = st.file_uploader("Pilih Foto", type=['jpg','png','jpeg'], accept_multiple_files=True)
        ket = st.text_input("Nama Event (Misal: Manado 2022)")
        if st.form_submit_button("Simpan"):
            if files and ket:
                conn = sqlite3.connect('alumni.db')
                for f in files:
                    path = os.path.join("static/img_events", f.name)
                    with open(path, "wb") as save_f:
                        save_f.write(f.getbuffer())
                    conn.execute("INSERT INTO data_events (path_foto, deskripsi) VALUES (?,?)", (path, ket))
                conn.commit(); conn.close()
                st.success("Berhasil! Ingat: Download alumni.db dan upload ke GitHub agar permanen."); st.rerun()
