import streamlit as st
import sqlite3
import pandas as pd
import os
import base64
import streamlit.components.v1 as components
from datetime import datetime
from PIL import Image, ExifTags # <-- TAMBAHKAN BARIS INI
db_path = os.path.join(os.path.dirname(__file__), 'data_anggota.db')
conn = sqlite3.connect(db_path)
# --- 1. SETUP FOLDER & DATABASE ---
for folder in ['static/img_profile', 'static/img_events', 'static/img_memoriam']:
    if not os.path.exists(folder):
        os.makedirs(folder)

conn = sqlite3.connect('alumni.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS marketplace (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nama_produk TEXT,
        harga TEXT,
        whatsapp TEXT,
        deskripsi TEXT,
        foto_produk TEXT, -- Ini untuk menyimpan string base64
        nama_alumni TEXT
    )
''')
conn.commit()
conn.close()
def init_db():
    import sqlite3

# Menghubungkan ke database
    conn = sqlite3.connect('alumni.db')
    c = conn.cursor()

    try:
        conn.execute("ALTER TABLE data_keuangan ADD COLUMN event TEXT")
        conn.commit()
    except:
        # Jika kolom sudah ada, abaikan errornya
        pass

# Perintah membuat tabel marketplace jika belum ada
    c.execute('''CREATE TABLE IF NOT EXISTS marketplace 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, 
              nama_alumni TEXT, 
              nama_produk TEXT, 
              harga TEXT, 
              deskripsi TEXT, 
              foto_produk TEXT, 
              no_wa TEXT)''')

    conn.commit()
    conn.close()
    conn = sqlite3.connect('data_anggota.db') # Pastikan nama file ini yang Anda inginkan
    c = conn.cursor()
    # 1. Tabel Anggota
    c.execute('''CREATE TABLE IF NOT EXISTS data_anggota (
                    foto_profile TEXT, 
                    nama TEXT, 
                    user_id TEXT PRIMARY KEY,
                    password TEXT, 
                    pekerjaan TEXT,  -- Tambahkan kolom ini di sini
                    kelas_1 TEXT, 
                    kelas_2 TEXT, 
                    kelas_3 TEXT, 
                    alamat TEXT)''')
    
    # 2. Tabel Event
    c.execute('''CREATE TABLE IF NOT EXISTS data_events (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 path_foto TEXT, 
                 deskripsi TEXT, 
                 bulan_tahun TEXT)''')
    
    # 3. Tabel Komentar
    c.execute('''CREATE TABLE IF NOT EXISTS data_komentar (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 event_deskripsi TEXT, 
                 nama_penulis TEXT, 
                 isi_komentar TEXT, 
                 waktu TEXT)''')
    
    # 4. Tabel Agenda
    c.execute('''CREATE TABLE IF NOT EXISTS data_agenda (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 tanggal TEXT, 
                 kegiatan TEXT, 
                 lokasi TEXT)''')
    
    # 5. Tabel Memoriam
    c.execute('''CREATE TABLE IF NOT EXISTS data_memoriam (
                 id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 foto TEXT, 
                 nama TEXT, 
                 tanggal_wafat TEXT, 
                 keterangan TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS marketplace 
                (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                nama_alumni TEXT, 
                nama_produk TEXT, 
                harga TEXT, 
                deskripsi TEXT, 
                foto_produk TEXT, 
                no_wa TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS data_keuangan 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  tanggal TEXT, 
                  keterangan TEXT, 
                  event TEXT, 
                  jumlah REAL, 
                  kategori TEXT, 
                  tipe TEXT)''')            

    # --- PENGAMAN: Jika database sudah ada, tambahkan kolom pekerjaan secara manual ---
    try:
        c.execute("ALTER TABLE data_anggota ADD COLUMN pekerjaan TEXT")
    except sqlite3.OperationalError:
        pass # Jika sudah ada kolomnya, abaikan errornya
    try:
        # Menambahkan kolom event ke tabel data_keuangan
        c.execute("ALTER TABLE data_keuangan ADD COLUMN event TEXT")
        conn.commit()
    except:
        # Jika sudah ada, kode ini akan dilewati otomatis
        pass
        conn.close() 

# Panggil fungsi untuk memastikan tabel terbuat
    conn = sqlite3.connect('alumni.db')
    c = conn.cursor()
init_db()

def get_image_base64(path):
    if not path or not os.path.exists(path): return None
    try:
        # --- FIX OTOMATIS: Deteksi & Perbaiki Orientasi Foto ---
        image = Image.open(path)
        
        # Coba ambil data orientasi EXIF
        try:
            for orientation in ExifTags.TAGS.keys():
                if ExifTags.TAGS[orientation] == 'Orientation': break
            
            exif = dict(image._getexif().items())
            
            if exif[orientation] == 3:   image = image.rotate(180, expand=True)
            elif exif[orientation] == 6: image = image.rotate(270, expand=True)
            elif exif[orientation] == 8: image = image.rotate(90, expand=True)
        except (AttributeError, KeyError, IndexError):
            # Jika tidak ada data EXIF, biarkan fotonya apa adanya
            pass
        
        # Simpan sementara ke memory untuk diconvert ke base64
        import io
        img_buffer = io.BytesIO()
        # Simpan dengan format aslinya agar transparan tetap transparan
        image.save(img_buffer, format=image.format if image.format else 'PNG')
        byte_data = img_buffer.getvalue()
        
        # Convert ke base64
        return f"data:image/png;base64,{base64.b64encode(byte_data).decode()}"
    except Exception as e:
        # st.error(f"Error memproses foto {path}: {e}") # Aktifkan ini jika ingin debugging
        return None

# List Pilihan Kelas untuk Dropdown
LIST_KELAS = ["", "A", "B", "C", "D", "E", "F", "G"]

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
    .stat-card { background: white; padding: 10px; border-radius: 8px; border: 1px solid #e0e0e0; text-align: center; box-shadow: 1px 1px 5px rgba(0,0,0,0.05); }
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
    if st.button("🤝 Networking", use_container_width=True): pindah("Networking")
    if st.button("💰 Donasi & Kas", use_container_width=True): pindah("Donasi")
    st.write("---")
    if st.button("⚙️ Admin Panel", use_container_width=True): pindah("Admin Panel")

# --- 3. LOGIKA HALAMAN ---

if st.session_state.menu_aktif == "Home":
    st.markdown('<div style="background:#2b5298;padding:20px;border-radius:10px;color:white;text-align:center;"><h1>Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    st.markdown('<p class="quote-text">"Menyambung Kisah, Mempererat Persaudaraan. Jarak boleh membentang, waktu boleh berlalu, namun ikatan kita tetap satu."</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-quote">Mari jadikan kenangan masa sekolah sebagai energi untuk terus bergerak, berdampak, dan berkarya di bidang masing-masing.</p>', unsafe_allow_html=True)
    st.markdown('<h3 style="text-align:center; color:#b8860b; margin-top:-10px;">Satu almamater, sejuta karya, selamanya saudara</h3>', unsafe_allow_html=True)
    st.write("---")
    
# --- NAVIGASI TOMBOL (Update dengan 3 Tombol) ---
    col_nav1, col_nav2 = st.columns(2)
    with col_nav1:
        if st.button("🔍 Lihat Database Alumni", use_container_width=True, type="primary"): 
            pindah("Database Alumni")
    with col_nav2:
        if st.button("🌹 In Memoriam", use_container_width=True, type="primary"): 
            pindah("In Memoriam")
    
    # Tambahkan tombol baru di tengah bawah
    _, col_tengah, _ = st.columns([1, 2, 1]) # Membuat layout agar tombol di tengah
    with col_tengah:
        if st.button("📝 Input Data Alumni", use_container_width=True, type="primary"):
            st.session_state.menu_aktif = "Admin Panel"
            # Baris di bawah ini memastikan saat masuk Admin Panel, tab yang terbuka adalah tab pertama (Input Alumni)
            st.rerun()
            
    st.write("---")
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

# --- 4. HALAMAN ADMIN PANEL ---
elif st.session_state.menu_aktif == "Admin Panel":
    st.title("⚙️ Admin Panel")
    
    # KUNCI UTAMA: Harus ada 6 nama di dalam kurung ini
    t1, t2, t3, t4, t5, t6 = st.tabs([
        "👥 Alumni", 
        "📸 Dokumentasi", 
        "🗓️ Agenda", 
        "🌹 In Memoriam", 
        "💰 Input Keuangan", 
        "🛠️ Kelola & Edit Data"
    ])
    
    with t1:
        st.subheader("Registrasi Anggota Baru")
        with st.form("input_alumni", clear_on_submit=True):
            f_p = st.file_uploader("Foto Profil", type=['png', 'jpg', 'jpeg'])
            n_a = st.text_input("Nama Lengkap")
            u_i = st.text_input("Username/ID")
            p_w = st.text_input("Password", type="password")
            
            # --- BARIS BARU UNTUK PEKERJAAN ---
            p_k = st.text_input("Aktivitas""  (Opsional, bisa diisi atau dikosongkan)") 
            # ----------------------------------

            k1, k2, k3 = st.columns(3)
            kl1 = k1.selectbox("Kelas 1", options=LIST_KELAS)
            kl2 = k2.selectbox("Kelas 2", options=LIST_KELAS)
            kl3 = k3.selectbox("Kelas 3", options=LIST_KELAS)
            almt = st.text_area("Alamat")
            
            if st.form_submit_button("Simpan Data Alumni"):
                if n_a and u_i:
                    path_p = f"static/img_profile/{f_p.name}" if f_p else ""
                    if f_p:
                        # Pastikan folder static/img_profile sudah dibuat ya Pak
                        with open(path_p, "wb") as f: f.write(f_p.getbuffer())
                    
                    conn = sqlite3.connect('alumni.db')
                    # Perhatikan tanda tanya (?) ditambah satu menjadi 9 buah
                    # Urutan: foto, nama, user_id, password, kelas1, kelas2, kelas3, alamat, pekerjaan
                    conn.execute("""
                        INSERT OR REPLACE INTO data_anggota 
                        VALUES (?,?,?,?,?,?,?,?,?)
                    """, (path_p, n_a, u_i, p_w, kl1, kl2, kl3, almt, p_k))
                    
                    conn.commit()
                    conn.close()
                    st.success(f"Data {n_a} Berhasil Tersimpan!")

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

    with t5: # Tab Input Keuangan
        st.subheader("💰 Input Mutasi Keuangan")
        with st.form("input_keuangan", clear_on_submit=True):
            col_k1, col_k2 = st.columns(2)
            tgl_k = col_k1.date_input("Tanggal Transaksi")
            kat_k = col_k2.selectbox("Kategori", ["Kas Alumni", "Pendanaan Event", "Bantuan Sosial"])
        
            ket_k = st.text_input("Keterangan (Contoh: Iuran, Sewa Tenda, Santunan)")
            # Input khusus untuk Nama Event
            ev_k = st.text_input("Nama Event (Kosongkan jika bukan Pendanaan Event)")
        
            nom_k = st.number_input("Nominal (Rp)", min_value=0, step=1000)
            tipe_k = st.radio("Tipe Transaksi", ["Masuk (Debit)", "Keluar (Kredit)"], horizontal=True)
        
            if st.form_submit_button("Simpan Data Keuangan"):
                if ket_k and nom_k > 0:
                    conn = sqlite3.connect('alumni.db')
                    # Tambahkan ev_k ke dalam query INSERT
                    conn.execute("INSERT INTO data_keuangan (tanggal, keterangan, event, jumlah, kategori, tipe) VALUES (?,?,?,?,?,?)",
                                (str(tgl_k), ket_k, ev_k, nom_k, kat_k, tipe_k))
                    conn.commit()
                    conn.close()
                    st.success("Data Berhasil Dicatat!")
                    st.rerun()
    with t6:
        st.subheader("🛠️ Pusat Kendali (Edit & Hapus Data)")
        
# 1. Pilihan Kategori Kelola (Posisinya sejajar di bawah judul)
        pilih_kategori = st.radio(
        "Pilih Data yang Ingin Dikelola:",
        ["Alumni", "Agenda", "Dokumentasi", "In Memoriam", "Keuangan", "Marketplace"],
        horizontal=True, key="radio_kelola"
    )

        tabel_map = {
        "Alumni": "data_anggota",
        "Agenda": "data_agenda",
        "Dokumentasi": "data_events",
        "In Memoriam": "data_memoriam",
        "Keuangan": "data_keuangan",
        "Marketplace": "marketplace"
    }

    # 2. Tabel Editor (Untuk Edit & Hapus)
        st.subheader(f"📝 Edit Data {pilih_kategori}")
        with sqlite3.connect('alumni.db') as conn:
            df_edit = pd.read_sql_query(f"SELECT * FROM {tabel_map[pilih_kategori]}", conn)
            df_up = st.data_editor(df_edit, use_container_width=True, num_rows="dynamic", key=f"editor_{pilih_kategori}")

        if st.button(f"Simpan Perubahan {pilih_kategori}", type="primary"):
            with sqlite3.connect('alumni.db') as conn:
                df_up.to_sql(tabel_map[pilih_kategori], conn, if_exists='replace', index=False)
            st.success(f"Data {pilih_kategori} Berhasil Diperbarui!")
            st.rerun()

    # --- BAGIAN PUSAT BACKUP (DATABASE & FOTO) ---
        st.markdown("---")
        st.header("💾 Pusat Backup Data Paguyuban")
        st.info("Unduh data di bawah ini secara rutin!")

        col_bak1, col_bak2 = st.columns(2)

        with col_bak1:
            st.subheader("🗄️ Backup Database (.db)")
            # Mencari semua file database
            files_db = [f for f in os.listdir('.') if f.endswith('.db')]
            if files_db:
                for db_file in files_db:
                    with open(db_file, "rb") as f:
                        st.download_button(
                            label=f"📥 Download {db_file}",
                            data=f,
                            file_name=db_file,
                            mime="application/octet-stream",
                            key=f"dl_{db_file}"
                        )
            else:
                st.warning("Tidak ditemukan file database.")

        with col_bak2:
            st.subheader("📸 Backup Semua Foto (.zip)")
            import zipfile, io
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w") as csv_zip:
                for root, dirs, files in os.walk('static'):
                    for file in files:
                        csv_zip.write(os.path.join(root, file))
        
            st.download_button(
                label="📥 Download Semua Foto (ZIP)",
                data=buf.getvalue(),
                file_name="backup_foto_sempat86.zip",
                mime="application/zip"
            )

        st.success("💡 Tip: Simpan backup di folder laptop sesuai tanggal hari ini.")

elif st.session_state.menu_aktif == "Database Alumni":
    st.title("🔍 Database Alumni")
    # --- 1. INISIALISASI STATE ---
    if 'pilihan_zoom' not in st.session_state:
        st.session_state.pilihan_zoom = None

    conn = sqlite3.connect('alumni.db')
    df_db = pd.read_sql_query("SELECT foto_profile, nama, kelas_1, kelas_2, kelas_3, alamat FROM data_anggota ORDER BY nama ASC", conn)
    conn.close()

    if not df_db.empty:
        # --- 2. STATISTIK (SELALU TAMPIL) ---
        def render_stat_row(label, col_name):
            st.write(f"**{label}**")
            counts = df_db[col_name].value_counts().reindex(LIST_KELAS[1:], fill_value=0)
            cols = st.columns(7)
            for i, (kls, jml) in enumerate(counts.items()):
                with cols[i]:
                    st.markdown(f"""
                        <div style="background: white; padding: 5px; border-radius: 5px; border: 1px solid #e0e0e0; 
                                    text-align: center; box-shadow: 1px 1px 3px rgba(0,0,0,0.05); line-height: 1.2;">
                            <p style="margin: 0; font-size: 11px; color: #666;">Kelas {kls}</p>
                            <b style="font-size: 18px; color: #2b5298;">{jml}</b>
                        </div>
                    """, unsafe_allow_html=True)

        st.subheader("📊 Statistik Alumni")
        render_stat_row("Statistik Kelas 1", "kelas_1")
        st.write("") 
        render_stat_row("Statistik Kelas 2", "kelas_2")
        st.write("")
        render_stat_row("Statistik Kelas 3", "kelas_3")
        
        st.write("---")

        # --- 3. FILTER (SELALU TAMPIL) ---
        st.subheader("🔎 Cari & Filter")
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        search_nama = c1.text_input("Cari Nama Alumni")
        f_k1 = c2.selectbox("Filter Kelas 1", options=["Semua"] + LIST_KELAS[1:])
        f_k2 = c3.selectbox("Filter Kelas 2", options=["Semua"] + LIST_KELAS[1:])
        f_k3 = c4.selectbox("Filter Kelas 3", options=["Semua"] + LIST_KELAS[1:])

        # Proses Filter Data
        df_f = df_db.copy()
        if search_nama:
            df_f = df_f[df_f['nama'].str.contains(search_nama, case=False, na=False)]
        if f_k1 != "Semua": df_f = df_f[df_f['kelas_1'] == f_k1]
        if f_k2 != "Semua": df_f = df_f[df_f['kelas_2'] == f_k2]
        if f_k3 != "Semua": df_f = df_f[df_f['kelas_3'] == f_k3]

        st.write("---")

# --- 4. LOGIKA SWITCHING (TABEL vs DETAIL FOTO DENGAN FIX OTOMATIS ORIENTASI) ---
        
        # JIKA ADA FOTO YANG DIKLIK (ZOOM MODE)
        if st.session_state.pilihan_zoom is not None:
            data_terpilih = st.session_state.pilihan_zoom
            
            with st.container(border=True):
                # Baris Tombol Kembali & Nama
                col_back, col_title = st.columns([1, 4])
                if col_back.button("⬅️ Kembali", use_container_width=True):
                    st.session_state.pilihan_zoom = None
                    st.rerun()
                col_title.markdown(f"### 👤 {data_terpilih['nama']}")

                # Baris Foto & Info
                c1, c2, c3 = st.columns([1, 2, 1])
                with c2:
                    img_path = data_terpilih['foto_profile']
                    # Menggunakan fungsi base64 yang sudah kita perbaiki orientasinya
                    img_modal = get_image_base64(img_path)
                    
                    if img_modal:
                        # --- HAPUS CSS ROTATE TADI ---
                        # Kita gunakan foto base64 yang sudah diputar otomatis orientasinya
                        st.image(img_modal, use_container_width=True)
                    else:
                        st.warning("Foto tidak ditemukan.")
                    
                    # Info Kelas & Alamat (Rapi & Indah)
                    st.markdown(f"""
                        <div style="background-color: #f0f7ff; padding: 10px; border-radius: 5px; margin-top: 15px;">
                            <b>Kelas:</b> {data_terpilih['kelas_1']} | {data_terpilih['kelas_2']} | {data_terpilih['kelas_3']}
                        </div>
                    """, unsafe_allow_html=True)
                    
                    st.write(f"🏠 **Alamat:** {data_terpilih['alamat']}")
        # JIKA TIDAK ADA YANG DIKLIK (TABLE MODE - TETAP STABIL)
        else:
            st.write(f"Menampilkan **{len(df_f)}** alumni.")
            
            # Siapkan data untuk tabel (Tabel tidak perlu dirotasi, agar tetap sesuai aslinya)
            df_tampil = df_f.copy()
            df_tampil['foto_profile'] = df_tampil['foto_profile'].apply(get_image_base64)

            event_klik = st.dataframe(
                df_tampil, 
                column_config={
                    "foto_profile": st.column_config.ImageColumn("Klik untuk Zoom", width="small"),
                }, 
                use_container_width=True, 
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row"
            )

            if len(event_klik.selection.rows) > 0:
                idx_pilih = event_klik.selection.rows[0]
                st.session_state.pilihan_zoom = df_f.iloc[idx_pilih]
                st.rerun()
elif st.session_state.menu_aktif == "In Memoriam":
    st.title("🌹 In Memoriam")
    conn = sqlite3.connect('alumni.db')
    
    # Menambahkan 'ORDER BY tanggal_wafat DESC' agar yang terbaru muncul di atas
    df_mem = pd.read_sql_query("SELECT * FROM data_memoriam ORDER BY tanggal_wafat DESC", conn)
    conn.close()
    
    if not df_mem.empty:
        # Memastikan kolom tanggal_wafat terbaca sebagai tanggal agar pengurutan di Pandas juga akurat
        df_mem['tanggal_wafat_dt'] = pd.to_datetime(df_mem['tanggal_wafat'], errors='coerce')
        df_mem = df_mem.sort_values(by='tanggal_wafat_dt', ascending=False)

        cols = st.columns(3)
        for i, (idx, row) in enumerate(df_mem.iterrows()):
            with cols[i % 3]:
                st.markdown('<div class="mem-card">', unsafe_allow_html=True)
                img = get_image_base64(row['foto'])
                if img: 
                    st.image(img, use_container_width=True)
                
                st.subheader(row['nama'])
                
                # Memformat tampilan tanggal agar lebih rapi (Contoh: 22 March 2026)
                tgl_tampil = row['tanggal_wafat_dt'].strftime('%d %B %Y') if pd.notnull(row['tanggal_wafat_dt']) else row['tanggal_wafat']
                
                st.write(f"**Wafat:** {tgl_tampil}")
                st.write(row['keterangan'])
                st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.info("Data belum tersedia.")
elif st.session_state.menu_aktif == "Donasi":
    st.markdown('<div style="background:#2b5298;padding:20px;border-radius:10px;color:white;text-align:center;"><h1>💰 Laporan Donasi & Kas SEMPAT 86</h1></div>', unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["💵 Kas Alumni", "🎟️ Laporan Pendanaan Event", "🤝 Laporan Pendanaan Bantuan"])
    conn = sqlite3.connect('alumni.db')

    def ambil_data_all_flow(filter_event=False):
        conn = sqlite3.connect('alumni.db')
        if filter_event:            # Hanya ambil yang kategorinya Event
            query = "SELECT tanggal, keterangan, jumlah, tipe, kategori FROM data_keuangan WHERE kategori = 'Pendanaan Event'"
        else:
            # Ambil SEMUA transaksi (Kas Utama)
            query = "SELECT tanggal, keterangan, jumlah, tipe, kategori FROM data_keuangan"
        
        df = pd.read_sql_query(query, conn)
        conn.close()
        return df

    with tab1:
        st.subheader("📖 Buku Kas Besar Alumni (Semua Transaksi)")
        df_all = ambil_data_all_flow(filter_event=False)
        if not df_all.empty:
            masuk = df_all[df_all['tipe'] == "Masuk (Debit)"]['jumlah'].sum()
            keluar = df_all[df_all['tipe'] == "Keluar (Kredit)"]['jumlah'].sum()
            saldo = masuk - keluar
          
            # Ringkasan di atas
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Pemasukan", f"Rp {masuk:,.0f}")
            c2.metric("Total Pengeluaran", f"Rp {keluar:,.0f}", delta=f"-{keluar:,.0f}", delta_color="inverse")
            c3.metric("Saldo Kas Saat Ini", f"Rp {saldo:,.0f}")
            
            st.write("---")
            # Menampilkan kategori agar tahu ini uang iuran atau uang event
            df_display = df_all.sort_values(by='tanggal', ascending=False)
            df_display['jumlah'] = df_display['jumlah'].apply(lambda x: f"Rp {x:,.0f}")
            # Gunakan st.dataframe agar lebih interaktif dan sembunyikan index
            st.dataframe(df_display, use_container_width=True, hide_index=True)
        else:
            st.info("Belum ada mutasi kas.")

    # --- TAB 2: LAPORAN PENDANAAN EVENT ---
    with tab2:
        st.subheader("Laporan Pendanaan Event")
    
        with sqlite3.connect('alumni.db') as conn:
            df_event = pd.read_sql_query("SELECT * FROM data_keuangan WHERE kategori = 'Pendanaan Event'", conn)

        if not df_event.empty:
            # Dropdown Filter
            list_ev = ["Semua Event"] + sorted([x for x in df_event['event'].unique() if x])
            pilih_ev = st.selectbox("Filter per Nama Event:", list_ev)
        
            if pilih_ev == "Semua Event":
                df_fix = df_event
            else:
                df_fix = df_event[df_event['event'] == pilih_ev]
            
            # Summary Atas
            tot_ev = df_fix['jumlah'].sum()
            st.success(f"### Total Biaya {pilih_ev}: **Rp {tot_ev:,.0f}**")
        
            # Tabel (Tanpa kolom kategori karena sudah pasti Pendanaan Event)
            st.dataframe(df_fix[['tanggal', 'event', 'keterangan', 'jumlah', 'tipe']], use_container_width=True, hide_index=True)
        
            # Total Bawah (di luar tabel)
            st.markdown(f"""
                <div style="text-align: right; background-color: #f0f2f6; padding: 10px; border-radius: 5px;">
                    <b style="font-size: 20px;">Grand Total: Rp {tot_ev:,.0f}</b>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Belum ada transaksi untuk pendanaan event sejak 16 Maret 2026.")

    # --- TAB 3: LAPORAN PENDANAAN BANTUAN ---
    with tab3:
        st.subheader("🤝 Laporan Khusus Bantuan Sosial")
        # Panggil fungsi utama dengan filter kategori Bantuan Sosial
        df_sosial = ambil_data_all_flow(filter_event=False) 
        
        # Filter manual agar hanya menampilkan kategori Bantuan Sosial
        df_sosial = df_sosial[df_sosial['kategori'] == "Bantuan Sosial"]
        
        if not df_sosial.empty:
            total_sosial = df_sosial['jumlah'].sum()
            st.info(f"### Total Dana Bantuan Sosial: **Rp {total_sosial:,.0f}**")
            
            # Tampilkan tabel tanpa index agar rapi
            df_sos_display = df_sosial.copy()
            df_sos_display['jumlah'] = df_sos_display['jumlah'].apply(lambda x: f"Rp {x:,.0f}")
            st.dataframe(df_sos_display, use_container_width=True, hide_index=True)
        else:
            st.warning("Belum ada transaksi untuk kategori Bantuan Sosial sejak 16 Maret 2026.")
# --- F. MENU NETWORKING ---
elif st.session_state.menu_aktif == "Networking":
    st.markdown('<div style="background:#2b5298;padding:20px;border-radius:10px;color:white;text-align:center;"><h1>🛍️ Marketplace Alumni SEMPAT 86</h1></div>', unsafe_allow_html=True)
    
    # --- 1. FORM INPUT USAHA (Di dalam Expander) ---
    with st.expander("➕ Pasang Iklan Usaha Anda"):
        # Pastikan tabel marketplace sudah ada (Pengaman jika belum terbuat)
        conn = sqlite3.connect('alumni.db')
        conn.execute('''CREATE TABLE IF NOT EXISTS marketplace 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      nama_alumni TEXT, nama_produk TEXT, harga TEXT, 
                      deskripsi TEXT, foto_produk TEXT, no_wa TEXT)''')
        conn.close()

        with st.form("form_usaha", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                nama_p = st.text_input("Nama Produk/Usaha:")
                harga_p = st.text_input("Harga (Contoh: Rp 15.000):")
            with col2:
                wa_p = st.text_input("Nomor WhatsApp (Gunakan kode negara, misal: 62812...):")
                nama_pengiklan = st.text_input("Nama Pengiklan (Alumni):")
                uploaded_files = st.file_uploader("Upload Foto Produk (Maks 5)", type=['jpg','png','jpeg'], accept_multiple_files=True)
            
            desc_p = st.text_area("Deskripsi Singkat:")
            
            if st.form_submit_button("Tayangkan Iklan"):
                if nama_p and wa_p and uploaded_files:
                    if len(uploaded_files) > 5:
                        st.error("Waduh, maksimal 5 foto saja ya Pak!")
                    else:
                        import base64
                        list_foto = []
                        for f in uploaded_files:
                            encoded = base64.b64encode(f.read()).decode()
                            list_foto.append(encoded)
                        
                        foto_gabungan = "||".join(list_foto)
                        
                        conn = sqlite3.connect('alumni.db')
                        conn.execute("INSERT INTO marketplace (nama_alumni, nama_produk, harga, deskripsi, foto_produk, no_wa) VALUES (?, ?, ?, ?, ?, ?)", 
                                     (st.session_state.get('nama', 'Alumni'), nama_p, harga_p, desc_p, foto_gabungan, wa_p))
                        conn.commit()
                        conn.close()
                        st.success("Iklan berhasil ditayangkan!")
                        st.rerun()
                else:
                    st.error("Nama Produk, WA, dan Foto wajib diisi!")

    st.markdown("---")

    # --- 2. TAMPILAN KATALOG PRODUK ---
    conn = sqlite3.connect('alumni.db')
    try:
        # Ambil data terbaru
        df_mkt = pd.read_sql_query("SELECT * FROM marketplace ORDER BY id DESC", conn)
    except Exception as e:
        df_mkt = pd.DataFrame()
    finally:
        conn.close()

    if not df_mkt.empty:
        st.subheader("🛒 Katalog Usaha Alumni")
        cols = st.columns(3)
        for i, (idx, row) in enumerate(df_mkt.iterrows()):
            with cols[i % 3]:
                # Pecah string foto
                list_img = row['foto_produk'].split("||")
                foto_sampul = list_img[0]
                
                # Tampilan Card HTML
                st.markdown(f"""
                <div style="border: 1px solid #ddd; border-radius: 15px; padding: 10px; background: white; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); margin-bottom: 10px;">
                    <img src="data:image/png;base64,{foto_sampul}" style="width: 100%; height: 160px; object-fit: cover; border-radius: 10px;">
                    <h4 style="margin: 10px 0 5px 0; color: #2b5298;">{row['nama_produk']}</h4>
                    <p style="color: #e67e22; font-weight: bold; margin-bottom: 5px;">{row['harga']}</p>
                    <p style="font-size: 0.8em; color: #666; margin-bottom: 10px;">Oleh: {row['nama_alumni']}</p>
                </div>
                """, unsafe_allow_html=True)

                # FUNGSI DIALOG (Popup Slideshow)
                @st.dialog(f"Detail: {row['nama_produk']}")
                def detail_produk(data, images):
                    st.image([f"data:image/png;base64,{img}" for img in images], 
                             caption=[f"Foto {j+1}" for j in range(len(images))],
                             use_container_width=True)
                    
                    st.write(f"**💰 Harga:** {data['harga']}")
                    st.write(f"**📝 Deskripsi:**")
                    st.info(data['deskripsi'])
                    
                    # Bersihkan nomor WA jika ada karakter non-angka
                    wa_clean = ''.join(filter(str.isdigit, str(data['no_wa'])))
                    wa_link = f"https://wa.me/{wa_clean}"
                    st.link_button("🛒 Hubungi via WhatsApp", wa_link, use_container_width=True)

                # Tombol Lihat Detail
                if st.button(f"🔍 Detail ({len(list_img)} Foto)", key=f"btn_mkt_{row['id']}", use_container_width=True):
                    detail_produk(row, list_img)
    else:
        st.info("Belum ada iklan usaha yang ditayangkan. Yuk, jadi yang pertama!")
