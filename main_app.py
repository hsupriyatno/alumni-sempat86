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
    
    # Proteksi Kolom untuk Cloud
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
    # Banner Welcome
st.markdown("""
    <div style="background-color: #fff3cd; padding: 10px; border-radius: 5px; text-align: center; border: 1px solid #ffeeba; margin-bottom: 20px;">
        👈 <b>Tips:</b> Klik ikon <b>">"</b> di pojok kiri atas untuk menu lengkap!
    </div>
""", unsafe_allow_html=True)    
    # ... (bagian quote tetap sama) ...

    st.write("---")
    st.subheader("📍 Menu Navigasi Utama")
    st.info("Gunakan tombol di bawah ini atau klik ikon panah (>) di pojok kiri atas untuk menu lainnya.")

    # Membuat grid tombol yang ramah tampilan HP
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("🔍 Cari Data Alumni", use_container_width=True, type="primary"):
            pindah("Database Alumni")
        if st.button("🗓️ Jadwal Agenda", use_container_width=True):
            # Jika ingin langsung scroll ke bawah, bisa gunakan st.markdown anchors
            pass 
            
    with col_nav2:
        if st.button("🌹 In Memoriam", use_container_width=True, type="primary"):
            pindah("In Memoriam")
        if st.button("⚙️ Admin Panel", use_container_width=True):
            pindah("Admin Panel")

    st.write("---")
    # ... (lanjut ke bagian Agenda dan Dokumentasi) ...
    st.subheader("🗓️ Agenda Kegiatan (Mendatang)")
    conn = sqlite3.connect('alumni.db')
    df_ag = pd.read_sql_query("SELECT tanggal, kegiatan, lokasi FROM data_agenda", conn)
    if not df_ag.empty:
        df_ag['tanggal_dt'] = pd.to_datetime(df_ag['tanggal'], errors='coerce')
        df_ag = df_ag.sort_values(by='tanggal_dt', ascending=True)
        st.table(df_ag[['tanggal', 'kegiatan', 'lokasi']].reset_index(drop=True))
    
    st.write("---")
    st.subheader("📸 Dokumentasi Kegiatan")
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
    conn.close()

elif st.session_state.menu_aktif == "Admin Panel":
    st.title("⚙️ Admin Panel")
    t1, t2, t3, t4, t5 = st.tabs(["👥 Input Alumni", "📸 Dokumentasi", "🗓️ Agenda", "🌹 In Memoriam", "🗑️ Hapus Data"])
    
    with t1:
        st.subheader("Registrasi Anggota Baru")
        with st.form("input_alumni", clear_on_submit=True):
            f_p = st.file_uploader("Foto Profil", type=['png', 'jpg', 'jpeg'])
            n_a = st.text_input("Nama Lengkap")
            u_i = st.text_input("Username/ID")
            p_w = st.text_input("Password", type="password")
            k1, k2, k3 = st.columns(3)
            kl1 = k1.text_input("Kelas 1")
            kl2 = k2.text_input("Kelas 2")
            kl3 = k3.text_input("Kelas 3")
            almt = st.text_area("Alamat")
            if st.form_submit_button("Simpan Data Alumni"):
                if n_a and u_i:
                    path_p = f"static/img_profile/{f_p.name}" if f_p else ""
                    if f_p:
                        with open(path_p, "wb") as f: f.write(f_p.getbuffer())
                    conn = sqlite3.connect('alumni.db')
                    conn.execute("INSERT OR REPLACE INTO data_anggota VALUES (?,?,?,?,?,?,?,?)", (path_p, n_a, u_i, p_w, kl1, kl2, kl3, almt))
                    conn.commit(); conn.close(); st.success("Data Tersimpan!")

    with t2:
        with st.form("up_doc", clear_on_submit=True):
            f, e = st.file_uploader("Upload Foto", accept_multiple_files=True), st.text_input("Nama Event")
            c1, c2 = st.columns(2)
            bulan = c1.selectbox("Bulan", ['Januari','Februari','Maret','April','Mei','Juni','Juli','Agustus','September','Oktober','November','Desember'])
            tahun = c2.selectbox("Tahun", [str(y) for y in range(2020, 2031)])
            if st.form_submit_button("Simpan Dokumentasi"):
                if f and e:
                    conn = sqlite3.connect('alumni.db')
                    for pic in f:
                        p = f"static/img_events/{pic.name}"
                        with open(p, "wb") as s: s.write(pic.getbuffer())
                        conn.execute("INSERT INTO data_events (path_foto, deskripsi, bulan_tahun) VALUES (?,?,?)", (p, e, f"{bulan} {tahun}"))
                    conn.commit(); conn.close(); st.success("Berhasil!"); st.rerun()

    with t3:
        with st.form("up_age", clear_on_submit=True):
            tgl, keg, lok = st.date_input("Tanggal"), st.text_input("Kegiatan"), st.text_input("Lokasi")
            if st.form_submit_button("Simpan Agenda"):
                conn = sqlite3.connect('alumni.db')
                conn.execute("INSERT INTO data_agenda (tanggal, kegiatan, lokasi) VALUES (?,?,?)", (str(tgl), keg, lok))
                conn.commit(); conn.close(); st.success("Agenda Disimpan!"); st.rerun()

    with t4:
        with st.form("up_mem", clear_on_submit=True):
            m_n, m_t, m_k, m_f = st.text_input("Nama"), st.date_input("Tanggal Wafat"), st.text_area("Keterangan"), st.file_uploader("Foto")
            if st.form_submit_button("Simpan"):
                if m_n and m_f:
                    p = f"static/img_memoriam/{m_f.name}"
                    with open(p, "wb") as f: f.write(m_f.getbuffer())
                    conn = sqlite3.connect('alumni.db')
                    conn.execute("INSERT INTO data_memoriam (foto, nama, tanggal_wafat, keterangan) VALUES (?,?,?,?)", (p, m_n, str(m_t), m_k))
                    conn.commit(); conn.close(); st.success("Data Memoriam Disimpan!"); st.rerun()

    with t5:
        st.subheader("Hapus Data")
        kat = st.radio("Pilih Kategori:", ["Agenda", "Dokumentasi", "In Memoriam"])
        conn = sqlite3.connect('alumni.db')
        if kat == "Agenda":
            df_del = pd.read_sql_query("SELECT id, tanggal, kegiatan FROM data_agenda", conn)
            for idx, row in df_del.iterrows():
                c1, c2 = st.columns([4, 1])
                c1.write(f"{row['tanggal']} - {row['kegiatan']}")
                if c2.button("Hapus", key=f"d_a_{row['id']}"):
                    conn.execute("DELETE FROM data_agenda WHERE id=?", (row['id'],))
                    conn.commit(); conn.close(); st.rerun()
        elif kat == "Dokumentasi":
            df_del = pd.read_sql_query("SELECT DISTINCT deskripsi FROM data_events", conn)
            for idx, row in df_del.iterrows():
                c1, c2 = st.columns([4, 1])
                c1.write(row['deskripsi'])
                if c2.button("Hapus", key=f"d_e_{idx}"):
                    conn.execute("DELETE FROM data_events WHERE deskripsi=?", (row['deskripsi'],))
                    conn.commit(); conn.close(); st.rerun()
        conn.close()

elif st.session_state.menu_aktif == "Database Alumni":
    st.title("🔍 Database Alumni")
    conn = sqlite3.connect('alumni.db')
    df_db = pd.read_sql_query("SELECT foto_profile, nama, kelas_1, kelas_2, kelas_3, alamat FROM data_anggota", conn)
    conn.close()
    if not df_db.empty:
        df_db['foto_profile'] = df_db['foto_profile'].apply(get_image_base64)
        st.data_editor(df_db, column_config={"foto_profile": st.column_config.ImageColumn("Foto")}, use_container_width=True, hide_index=True)

elif st.session_state.menu_aktif == "In Memoriam":
    st.title("🌹 In Memoriam")
    conn = sqlite3.connect('alumni.db')
    df_mem = pd.read_sql_query("SELECT * FROM data_memoriam", conn)
    conn.close()
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
