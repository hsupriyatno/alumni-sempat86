import streamlit as st
import sqlite3
import pandas as pd
import os
import base64
import streamlit.components.v1 as components
from datetime import datetime

# --- 1. SETUP FOLDER & DATABASE (WAJIB UNTUK STREAMLIT CLOUD) ---
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
    
    # Cek kolom bulan_tahun (Proteksi DatabaseError)
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

if st.session_state.menu_aktif == "Home":
    st.markdown('<div style="background:#2b5298;padding:20px;border-radius:10px;color:white;text-align:center;"><h1>Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    st.markdown('<p style="color:#b8860b; font-style:italic; font-size:20px; text-align:center; font-weight:bold;">"Menyambung Kisah, Mempererat Persaudaraan."</p>', unsafe_allow_html=True)
    
    # TOMBOL CEPAT
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 Daftar Anggota Baru", use_container_width=True): pindah("Admin Panel")
    with col2:
        if st.button("🔍 Lihat Database Anggota", use_container_width=True): pindah("Database Alumni")

    st.write("---")
    st.subheader("🗓️ Agenda Kegiatan")
    conn = sqlite3.connect('alumni.db')
    df_ag = pd.read_sql_query("SELECT * FROM data_agenda", conn)
    if not df_ag.empty:
        st.table(df_ag[['tanggal', 'kegiatan', 'lokasi']])
    
    st.write("---")
    st.subheader("📸 Dokumentasi")
    df_ev = pd.read_sql_query("SELECT DISTINCT deskripsi, bulan_tahun FROM data_events", conn)
    if not df_ev.empty:
        # Sortir dropdown agar yang terbaru di atas
        df_ev['label'] = df_ev['deskripsi'] + " (" + df_ev['bulan_tahun'].fillna("-") + ")"
        pilih = st.selectbox("Pilih Event:", df_ev['label'])
        real_desc = df_ev[df_ev['label'] == pilih]['deskripsi'].values[0]
        
        # Tampilkan Foto & Komentar (Logika Slide tetap sama)
        st.info(f"Menampilkan dokumentasi: {real_desc}")
    conn.close()

elif st.session_state.menu_aktif == "Admin Panel":
    st.title("⚙️ Admin Panel")
    t1, t2, t3, t4, t5 = st.tabs(["👥 Input Alumni", "📸 Dokumentasi", "🗓️ Agenda", "🌹 In Memoriam", "🗑️ Hapus Data"])
    
    with t1:
        with st.form("fm_alumni"):
            nama = st.text_input("Nama Lengkap")
            uid = st.text_input("User ID")
            if st.form_submit_button("Simpan"):
                conn = sqlite3.connect('alumni.db')
                conn.execute("INSERT OR REPLACE INTO data_anggota (nama, user_id) VALUES (?,?)", (nama, uid))
                conn.commit(); conn.close(); st.success("Data Tersimpan!")

    with t2:
        with st.form("fm_doc"):
            files = st.file_uploader("Upload Foto", accept_multiple_files=True)
            ev_name = st.text_input("Nama Event")
            bln = st.selectbox("Bulan", ["Januari", "Februari", "Maret", "April", "Mei", "Juni", "Juli", "Agustus", "September", "Oktober", "November", "Desember"])
            thn = st.selectbox("Tahun", [str(y) for y in range(2024, 2027)])
            if st.form_submit_button("Simpan Dokumentasi"):
                if files and ev_name:
                    conn = sqlite3.connect('alumni.db')
                    for f in files:
                        p = f"static/img_events/{f.name}"
                        with open(p, "wb") as s: s.write(f.getbuffer())
                        conn.execute("INSERT INTO data_events (path_foto, deskripsi, bulan_tahun) VALUES (?,?,?)", (p, ev_name, f"{bln} {thn}"))
                    conn.commit(); conn.close(); st.success("Foto Berhasil Diunggah!"); st.rerun()

    with t3:
        with st.form("fm_agenda"):
            tgl = st.date_input("Tanggal")
            keg = st.text_input("Kegiatan")
            lok = st.text_input("Lokasi")
            if st.form_submit_button("Simpan Agenda"):
                conn = sqlite3.connect('alumni.db')
                conn.execute("INSERT INTO data_agenda (tanggal, kegiatan, lokasi) VALUES (?,?,?)", (str(tgl), keg, lok))
                conn.commit(); conn.close(); st.success("Agenda Disimpan!")

    with t4:
        with st.form("fm_mem"):
            n_m = st.text_input("Nama")
            f_m = st.file_uploader("Foto")
            if st.form_submit_button("Simpan In Memoriam"):
                if n_m and f_m:
                    p = f"static/img_memoriam/{f_m.name}"
                    with open(p, "wb") as s: s.write(f_m.getbuffer())
                    conn = sqlite3.connect('alumni.db')
                    conn.execute("INSERT INTO data_memoriam (foto, nama) VALUES (?,?)", (p, n_m))
                    conn.commit(); conn.close(); st.success("Data Tersimpan!")

    with t5:
        st.subheader("Hapus Data")
        # Logika hapus data tetap sama...

elif st.session_state.menu_aktif == "Database Alumni":
    st.title("🔍 Database Alumni")
    conn = sqlite3.connect('alumni.db')
    df = pd.read_sql_query("SELECT * FROM data_anggota", conn)
    st.dataframe(df)
    conn.close()

elif st.session_state.menu_aktif == "In Memoriam":
    st.title("🌹 In Memoriam")
    conn = sqlite3.connect('alumni.db')
    df_m = pd.read_sql_query("SELECT * FROM data_memoriam", conn)
    conn.close()
    if df_m.empty:
        st.info("Belum ada data.")
    else:
        # Tampilkan grid foto memoriam
        for idx, row in df_m.iterrows():
            st.write(row['nama'])import streamlit as st
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
    # Pastikan tabel utama ada
    c.execute('''CREATE TABLE IF NOT EXISTS data_anggota (
                    foto_profile TEXT, nama TEXT, user_id TEXT PRIMARY KEY, 
                    password TEXT, kelas_1 TEXT, kelas_2 TEXT, kelas_3 TEXT, alamat TEXT)''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS data_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, path_foto TEXT, deskripsi TEXT)''')
    
    # TRIK KHUSUS: Cek dan tambah kolom bulan_tahun jika belum ada
    try:
        c.execute("ALTER TABLE data_events ADD COLUMN bulan_tahun TEXT")
    except sqlite3.OperationalError:
        # Jika error berarti kolom sudah ada, abaikan saja
        pass

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

st.markdown("""
    <style>
    .stApp { background: linear-gradient(to bottom, #e3f2fd, #ffffff); }
    [data-testid="stSidebar"] { background-color: #f0f7ff; }
    .slideshow-container { position: relative; max-width: 1000px; margin: auto; }
    .mySlides { display: none; }
    .fade { animation-name: fade; animation-duration: 1.5s; }
    @keyframes fade { from {opacity: .4} to {opacity: 1} }
    .mem-card { border: 1px solid #ddd; border-radius: 10px; padding: 15px; background: white; box-shadow: 2px 2px 8px rgba(0,0,0,0.1); text-align: center; margin-bottom: 20px;}
    .quote-text { color: #b8860b; font-style: italic; font-size: 20px; text-align: center; padding: 10px; font-weight: bold; margin-bottom: 0px; }
    .sub-quote { text-align: center; color: #555; margin-bottom: 20px; }
    .comment-box { background-color: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 5px solid #2b5298; margin-bottom: 10px; }
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
    st.write("---")
    if st.button("⚙️ Admin Panel", use_container_width=True): pindah("Admin Panel")

# --- 3. LOGIKA HALAMAN ---

if st.session_state.menu_aktif == "Home":
    st.markdown('<div style="background:#2b5298;padding:20px;border-radius:10px;color:white;text-align:center;"><h1>Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    st.markdown('<p class="quote-text">"Menyambung Kisah, Mempererat Persaudaraan. Jarak boleh membentang, waktu boleh berlalu, namun ikatan kita tetap satu."</p>', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align:center; color:#b8860b;">Satu almamater, sejuta karya, selamanya saudara</h3>', unsafe_allow_html=True)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("📝 Daftar Anggota Baru", use_container_width=True): pindah("Admin Panel")
    with col_btn2:
        if st.button("🔍 Lihat Database Anggota", use_container_width=True): pindah("Database Alumni")

    st.write("---")
    st.subheader("🗓️ Agenda Kegiatan (Mendatang)")
    conn = sqlite3.connect('alumni.db')
    try:
        df_ag = pd.read_sql_query("SELECT tanggal, kegiatan, lokasi FROM data_agenda", conn)
        if not df_ag.empty:
            df_ag['tanggal_dt'] = pd.to_datetime(df_ag['tanggal'], errors='coerce')
            df_ag = df_ag.sort_values(by='tanggal_dt', ascending=True)
            st.table(df_ag[['tanggal', 'kegiatan', 'lokasi']].reset_index(drop=True))
        else:
            st.info("Belum ada agenda mendatang.")
    except:
        st.error("Gagal memuat agenda.")
    finally:
        conn.close()

    st.write("---")
    st.subheader("📸 Dokumentasi Kegiatan")
    conn = sqlite3.connect('alumni.db')
    try:
        df_ev_list = pd.read_sql_query("SELECT DISTINCT deskripsi, bulan_tahun FROM data_events", conn)
        if not df_ev_list.empty:
            bulan_map = {'Januari': 1, 'Februari': 2, 'Maret': 3, 'April': 4, 'Mei': 5, 'Juni': 6,
                         'Juli': 7, 'Agustus': 8, 'September': 9, 'Oktober': 10, 'November': 11, 'Desember': 12}
            
            def buat_sort_key(row):
                try:
                    parts = str(row['bulan_tahun']).split()
                    return datetime(int(parts[1]), bulan_map.get(parts[0], 1), 1)
                except: return datetime(1900, 1, 1)

            df_ev_list['sort_key'] = df_ev_list.apply(buat_sort_key, axis=1)
            df_ev_list = df_ev_list.sort_values(by='sort_key', ascending=False)
            df_ev_list['label'] = df_ev_list['deskripsi'] + " (" + df_ev_list['bulan_tahun'].fillna("Waktu tdk diketahui") + ")"
            
            pilihan_label = st.selectbox("Pilih Event:", df_ev_list['label'])
            pilihan_ev = df_ev_list[df_ev_list['label'] == pilihan_label]['deskripsi'].values[0]
            
            df_f = pd.read_sql_query("SELECT path_foto FROM data_events WHERE deskripsi = ?", conn, params=(pilihan_ev,))
            imgs = [get_image_base64(p) for p in df_f['path_foto'] if get_image_base64(p)]
            if imgs:
                slides = "".join([f'<div class="mySlides fade"><img src="{i}" style="width:100%; height:450px; object-fit:cover; border-radius:15px;"></div>' for i in imgs])
                js_code = f'<div class="slideshow-container">{slides}</div><script>let slideIndex = 0; function showSlides() {{ let slides = document.getElementsByClassName("mySlides"); for (let i = 0; i < slides.length; i++) {{ slides[i].style.display = "none"; }} slideIndex++; if (slideIndex > slides.length) {{slideIndex = 1}} if (slides[slideIndex-1]) {{ slides[slideIndex-1].style.display = "block"; }} setTimeout(showSlides, 3000); }} showSlides();</script>'
                components.html(js_code, height=460)
            
            # Komentar
            st.write("---")
            st.write(f"💬 **Obrolan Event: {pilihan_ev}**")
            with st.form("form_komentar", clear_on_submit=True):
                c1, c2 = st.columns([1, 3])
                nama_kom = c1.text_input("Nama Anda")
                isi_kom = c2.text_input("Tulis komentar...")
                if st.form_submit_button("Kirim Komentar"):
                    if nama_kom and isi_kom:
                        waktu_skrg = datetime.now().strftime("%d/%m/%Y %H:%M")
                        conn.execute("INSERT INTO data_komentar (event_deskripsi, nama_penulis, isi_komentar, waktu) VALUES (?,?,?,?)", 
                                     (pilihan_ev, nama_kom, isi_kom, waktu_skrg))
                        conn.commit()
                        st.rerun()

            df_kom = pd.read_sql_query("SELECT nama_penulis, isi_komentar, waktu FROM data_komentar WHERE event_deskripsi = ? ORDER BY id DESC", 
                                       conn, params=(pilihan_ev,))
            for _, r in df_kom.iterrows():
                st.markdown(f'<div class="comment-box"><b>{r["nama_penulis"]}</b> <small>({r["waktu"]})</small><br>{r["isi_komentar"]}</div>', unsafe_allow_html=True)
    except:
        st.info("Dokumentasi belum tersedia.")
    finally:
        conn.close()

elif st.session_state.menu_aktif == "Database Alumni":
    st.title("🔍 Database Alumni")
    conn = sqlite3.connect('alumni.db')
    try:
        df_db = pd.read_sql_query("SELECT foto_profile, nama, kelas_1, kelas_2, kelas_3, alamat FROM data_anggota", conn)
        if not df_db.empty:
            df_db['foto_profile'] = df_db['foto_profile'].apply(get_image_base64)
            st.data_editor(df_db, column_config={"foto_profile": st.column_config.ImageColumn("Foto")}, use_container_width=True, hide_index=True)
        else:
            st.info("Database masih kosong.")
    finally:
        conn.close()

elif st.session_state.menu_aktif == "In Memoriam":
    st.title("🌹 In Memoriam")
    conn = sqlite3.connect('alumni.db')
    try:
        df_mem = pd.read_sql_query("SELECT * FROM data_memoriam", conn)
        if not df_mem.empty:
            cols = st.columns(3)
            for i, (idx, row) in enumerate(df_mem.iterrows()):
                with cols[i % 3]:
                    st.markdown('<div class="mem-card">', unsafe_allow_html=True)
                    img = get_image_base64(row['foto'])
                    if img: st.image(img, use_container_width=True)
                    st.subheader(row['nama'])
                    st.write(f"Wafat: {row['tanggal_wafat']}")
                    st.write(row['keterangan'])
                    st.markdown('</div>', unsafe_allow_html=True)
        else:
            st.info("Data belum tersedia.")
    except:
        st.error("Gagal mengambil data memoriam.")
    finally:
        conn.close()

elif st.session_state.menu_aktif == "Admin Panel":
    st.title("⚙️ Admin Panel")
    # ... (Isi Admin Panel tetap seperti sebelumnya)
