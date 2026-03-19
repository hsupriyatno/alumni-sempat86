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

# --- 2. FUNGSI KONVERSI GAMBAR (DIPERBAIKI UNTUK CLOUD) ---
def get_image_base64(path):
    if not path: return None
    
    # Menghapus path lokal laptop jika terbawa di database
    # Misal: 'C:/DATA/...' atau 'app/static/...' akan menjadi 'static/...'
    clean_path = path.replace('\\', '/')
    if 'static/' in clean_path:
        clean_path = 'static/' + clean_path.split('static/')[-1]
    
    if os.path.exists(clean_path):
        with open(clean_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{encoded}"
    return None

# --- 3. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('alumni.db')
    c = conn.cursor()
    # ... (kode tabel lainnya tetap ada)
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

def pindah_halaman(nama_halaman):
    st.session_state.menu_aktif = nama_halaman

# --- 5. STYLE CSS ---
st.markdown("""
    <style>
    .main-header { background: #2b5298; padding: 40px; border-radius: 20px; color: white; text-align: center; margin-bottom: 10px; }
    .stButton > button { border-radius: 10px; height: 45px; }
    </style>
""", unsafe_allow_html=True)

# --- 6. SIDEBAR NAVIGASI ---
with st.sidebar:
    st.markdown("### 📂 Menu Utama")
    list_menu = ["Home", "Database Alumni", "Berita & Kalender Kegiatan", 
                 "In Memoriam Alumni Sempat 86", "Komunitas", "Networking", "Donasi", "Admin Panel"]
    
    # Pastikan index selalu valid
    current_idx = 0
    if st.session_state.menu_aktif in list_menu:
        current_idx = list_menu.index(st.session_state.menu_aktif)
        
    menu_pilihan = st.radio("Pilih Halaman:", list_menu, index=current_idx)
    if menu_pilihan != st.session_state.menu_aktif:
        st.session_state.menu_aktif = menu_pilihan
        st.rerun()

# --- 7. LOGIKA HALAMAN ---

if st.session_state.menu_aktif == "Home":
    st.markdown('<div class="main-header"><h1>Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    
    # Tombol Akses Cepat
    c_spacer, c_daftar, c_masuk = st.columns([7, 1.5, 1.5]) 
    with c_daftar:
        if st.button("📝 Daftar", use_container_width=True):
            pindah_halaman("Form Pendaftaran"); st.rerun()
    with c_masuk:
        if st.button("🔑 Masuk", use_container_width=True):
            pindah_halaman("Database Alumni"); st.rerun()

    st.write("---")

# --- BAGIAN SLIDESHOW & KOMENTAR (GANTI DI SINI) ---
    st.subheader("📸 Dokumentasi Kegiatan")
    conn = sqlite3.connect('alumni.db')
    df_list_event = pd.read_sql_query("SELECT DISTINCT deskripsi FROM data_events WHERE deskripsi != ''", conn)
    
    if not df_list_event.empty:
        pilihan_event = st.selectbox("Pilih Event untuk Dilihat:", df_list_event['deskripsi'])
        
        # Tampilkan Foto (Slideshow)
        df_foto = pd.read_sql_query("SELECT path_foto FROM data_events WHERE deskripsi = ?", conn, params=(pilihan_event,))
        list_foto = [get_image_base64(p) for p in df_foto['path_foto'] if get_image_base64(p)]
        
        if list_foto:
            # (Gunakan komponen HTML slideshow yang sudah Bapak punya di sini)
            st.image(list_foto[0], use_container_width=True, caption=f"📍 Event: {pilihan_event}") # Contoh sederhana
            
            st.write("---")
            st.markdown("### 💬 Komentar Alumni")
            
            # Tampilkan Komentar yang Sudah Ada
            df_komen = pd.read_sql_query("SELECT nama_penulis, isi_komentar, waktu FROM data_komentar WHERE event_deskripsi = ? ORDER BY id DESC", 
                                        conn, params=(pilihan_event,))
            
            for index, row in df_komen.iterrows():
                st.markdown(f"**{row['nama_penulis']}** <small>({row['waktu']})</small>", unsafe_allow_html=True)
                st.info(row['isi_komentar'])
            
            # Form Tambah Komentar
            with st.expander("➕ Tulis Komentar"):
                with st.form(key=f"form_komen_{pilihan_event}", clear_on_submit=True):
                    nama_km = st.text_input("Nama Bapak/Ibu:")
                    pesan_km = st.text_area("Tulis sapaan atau komentar:")
                    submit_km = st.form_submit_button("Kirim Komentar 🚀")
                    
                    if submit_km and nama_km and pesan_km:
                        c = conn.cursor()
                        waktu_sekarang = datetime.now().strftime("%d/%m/%y %H:%M")
                        c.execute("INSERT INTO data_komentar (event_deskripsi, nama_penulis, isi_komentar, waktu) VALUES (?,?,?,?)",
                                  (pilihan_event, nama_km, pesan_km, waktu_sekarang))
                        conn.commit()
                        st.success("Komentar terkirim!")
                        st.rerun()
        else:
            st.warning("Foto tidak ditemukan.")
    else:
        st.info("Belum ada foto dokumentasi.")
    conn.close()

    st.write("---")

    # 2. Agenda Kegiatan (Urut Tanggal)
    st.subheader("🗓️ Agenda Kegiatan Mendatang")
    conn = sqlite3.connect('alumni.db')
    df_agenda = pd.read_sql_query("SELECT tanggal, kegiatan, lokasi, status FROM data_agenda", conn)
    conn.close()
    
    if not df_agenda.empty:
        df_agenda['tanggal_dt'] = pd.to_datetime(df_agenda['tanggal'], format='%d %B %Y')
        df_agenda = df_agenda.sort_values(by='tanggal_dt', ascending=True)
        st.table(df_agenda[['tanggal', 'kegiatan', 'lokasi', 'status']])
    else:
        st.info("Belum ada agenda kegiatan.")

elif st.session_state.menu_aktif == "Database Alumni":
    st.title("🔍 Database Alumni")
    st.info("Halaman ini sedang dalam pengembangan.")

elif st.session_state.menu_aktif == "Admin Panel":
    st.title("⚙️ Admin Panel - Data Entry")
    tab1, tab2 = st.tabs(["📸 Upload Foto Event", "🗓️ Input Agenda"])
    
    with tab1:
        st.subheader("Tambah Dokumentasi Foto")
        with st.form("form_foto", clear_on_submit=True):
            files_foto = st.file_uploader("Pilih Foto-foto Event", type=['jpg','png','jpeg'], accept_multiple_files=True)
            deskripsi = st.text_input("Deskripsi Event (Misal: Bukber 2026)")
            if st.form_submit_button("🚀 Simpan Semua Foto") and files_foto:
                conn = sqlite3.connect('alumni.db')
                c = conn.cursor()
                for f_upload in files_foto:
                    nama_file = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{f_upload.name}"
                    path_simpan = os.path.join("static/img_events", nama_file)
                    with open(path_simpan, "wb") as f:
                        f.write(f_upload.getbuffer())
                    c.execute("INSERT INTO data_events (path_foto, deskripsi) VALUES (?,?)", (path_simpan, deskripsi))
                conn.commit(); conn.close()
                st.success("Foto berhasil disimpan!"); st.rerun()

    with tab2:
        st.subheader("Tambah Agenda Baru")
        with st.form("form_agenda", clear_on_submit=True):
            tgl = st.date_input("Tanggal Kegiatan")
            keg = st.text_input("Nama Kegiatan")
            lok = st.text_input("Lokasi")
            stat = st.selectbox("Status", ["Terencana", "Persiapan", "Selesai"])
            if st.form_submit_button("Simpan Agenda") and keg:
                conn = sqlite3.connect('alumni.db')
                c = conn.cursor()
                c.execute("INSERT INTO data_agenda (tanggal, kegiatan, lokasi, status) VALUES (?,?,?,?)", 
                          (tgl.strftime("%d %B %Y"), keg, lok, stat))
                conn.commit(); conn.close()
                st.success("Agenda berhasil disimpan!"); st.rerun()

else:
    st.title(f"📂 {st.session_state.menu_aktif}")
    st.info("Halaman ini akan segera hadir.")
