import streamlit as st
import sqlite3
import pandas as pd
import os
import base64
import streamlit.components.v1 as components
from datetime import datetime

# --- 1. SETUP FOLDER & DATABASE (Step 1 Aman) ---
for folder in ['static/img_profile', 'static/img_events']:
    if not os.path.exists(folder):
        os.makedirs(folder)

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
    # Pastikan tabel dokumentasi foto ada
    c.execute('''CREATE TABLE IF NOT EXISTS data_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path_foto TEXT, deskripsi TEXT)''')
    # Pastikan tabel komentar ada
    c.execute('''CREATE TABLE IF NOT EXISTS data_komentar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_deskripsi TEXT, nama_penulis TEXT, isi_komentar TEXT, waktu TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 2. FUNGSI KONVERSI GAMBAR (Base64) ---
def get_image_base64(path):
    if not path or not os.path.exists(path): return None
    try:
        with open(path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{encoded}"
    except Exception: return None

# --- 3. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Alumni SMPN 4 Cirebon 86", page_icon="🏫", layout="wide")

if 'menu_aktif' not in st.session_state:
    st.session_state.menu_aktif = "Home"

def pindah_halaman(nama_halaman):
    st.session_state.menu_aktif = nama_halaman

# --- 4. STYLE CSS ---
st.markdown("""
    <style>
    .main-header { background: #2b5298; padding: 30px; border-radius: 15px; color: white; text-align: center; margin-bottom: 30px; }
    .stButton > button { border-radius: 10px; height: 50px; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# --- 5. SIDEBAR NAVIGASI ---
with st.sidebar:
    st.markdown("### 📂 Menu Utama")
    list_menu = ["Home", "Database Alumni", "Berita & Kalender Kegiatan", 
                 "In Memoriam Alumni Sempat 86", "Networking", "Donasi", "Form Pendaftaran", "Admin Panel"]
    
    try:
        current_idx = list_menu.index(st.session_state.menu_aktif)
    except:
        current_idx = 0
        
    menu_pilihan = st.radio("Pilih Halaman:", list_menu, index=current_idx)
    if menu_pilihan != st.session_state.menu_aktif and st.session_state.menu_aktif != "Form Pendaftaran":
        st.session_state.menu_aktif = menu_pilihan
        st.rerun()

# --- 6. LOGIKA HALAMAN (Kuncinya di Sini) ---

# --- A. HALAMAN HOME (Fokus Step 2: Perbaikan Slideshow) ---
if st.session_state.menu_aktif == "Home":
    st.markdown('<div class="main-header"><h1>Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    
    # Tombol Utama (Pasti Jalan)
    c_h1, c_h2 = st.columns(2)
    with c_h1:
        if st.button("🔍 Lihat Database Alumni", key="btn_db_home", use_container_width=True):
            st.session_state.menu_aktif = "Database Alumni"
            st.rerun()
    with c_h2:
        if st.button("📝 Daftar Anggota Baru", key="btn_reg_home", use_container_width=True):
            st.session_state.menu_aktif = "Form Pendaftaran"
            st.rerun()

    st.write("---")
    # Perbaikan Slideshow Dokumentasi (FOKUS UTAMA STEP 2)
    st.subheader("📸 Dokumentasi Kegiatan")
    
    conn = sqlite3.connect('alumni.db')
    # Ambil daftar event unik
    df_event = pd.read_sql_query("SELECT DISTINCT deskripsi FROM data_events", conn)
    
    if not df_event.empty:
        pilihan_event = st.selectbox("Pilih Event untuk Dilihat:", df_event['deskripsi'])
        
        # Ambil semua foto dari event yang dipilih
        df_foto = pd.read_sql_query("SELECT path_foto FROM data_events WHERE deskripsi = ?", conn, params=(pilihan_event,))
        list_f = [get_image_base64(p) for p in df_foto['path_foto']]
        
        # Saring foto yang gagal dimuat
        list_foto_oke = [img for img in list_f if img is not None]
        
        if list_foto_oke:
            # Slideshow Utama (Dengan HTML & JavaScript)
            slides_html = "".join([f'<div class="mySlides fade"><img src="{img}" style="width:100%; height:400px; object-fit:cover; border-radius:15px;"></div>' for img in list_foto_oke])
            components.html(f"""
                <div class="slideshow-container">{slides_html}</div>
                <script>
                    let sIdx = 0; function showS() {{
                        let s = document.getElementsByClassName("mySlides");
                        for (let i=0; i<s.length; i++) s[i].style.display="none";
                        sIdx++; if (sIdx > s.length) sIdx=1;
                        if(s[sIdx-1]) s[sIdx-1].style.display="block";
                        setTimeout(showS, 3000);
                    }} showS();
                </script>
            """, height=410)

            # --- Komentar (Hanya Tampil Jika Event Dipilih) ---
            st.write("---")
            st.markdown(f"### 💬 Komentar untuk Event: **{pilihan_event}**")
            df_k = pd.read_sql_query("SELECT nama_penulis, isi_komentar, waktu FROM data_komentar WHERE event_deskripsi = ? ORDER BY id DESC", conn, params=(pilihan_event,))
            
            for _, r in df_k.iterrows():
                st.caption(f"{r['waktu']} - **{r['nama_penulis']}**")
                st.info(r['isi_komentar'])
            
            with st.expander("➕ Tulis Komentar"):
                with st.form(f"form_komen_{pilihan_event}", clear_on_submit=True):
                    nama_in = st.text_input("Nama Bapak/Ibu:")
                    pesan_in = st.text_area("Pesan atau Sapaan:")
                    if st.form_submit_button("Kirim Komentar 🚀"):
                        waktu_s = datetime.now().strftime("%d/%m/%y %H:%M")
                        if pesan_in:
                            conn.execute("INSERT INTO data_komentar (event_deskripsi, nama_penulis, isi_komentar, waktu) VALUES (?,?,?,?)",
                                         (pilihan_event, (nama_in if nama_in else "Alumni"), pesan_in, waktu_s))
                            conn.commit(); st.rerun()
        else:
            st.warning("Foto event ini tidak dapat dimuat. Pastikan folder 'static/img_events' sudah ada.")
    else:
        st.info("Belum ada foto kegiatan. Silakan upload melalui menu 'Admin Panel'.")
    conn.close()

# --- B. FORM PENDAFTARAN LENGKAP (Step 1 Aman) ---
elif st.session_state.menu_aktif == "Form Pendaftaran":
    st.title("📝 Form Pendaftaran Alumni")
    if st.button("⬅️ Kembali ke Home"):
        pindah_halaman("Home"); st.rerun()
    
    with st.form("reg_form_lengkap"):
        f1, f2 = st.columns(2)
        with f1:
            nama_reg = st.text_input("Nama Lengkap")
            alamat_reg = st.text_area("Alamat")
            uid_reg = st.text_input("User ID")
            pwd_reg = st.text_input("Password", type="password")
        with f2:
            kls_1 = st.text_input("Kelas 1 (contoh: 1A)")
            kls_2 = st.text_input("Kelas 2")
            kls_3 = st.text_input("Kelas 3")
            foto_p = st.file_uploader("Upload Foto Profile", type=['jpg','png','jpeg'])
            
        if st.form_submit_button("Daftar Sekarang"):
            if nama_reg and uid_reg and pwd_reg:
                path_prof = ""
                if foto_p:
                    path_prof = f"static/img_profile/{uid_reg}_{foto_p.name}"
                    with open(path_prof, "wb") as f_prof: f_prof.write(foto_p.getbuffer())
                
                try:
                    conn = sqlite3.connect('alumni.db')
                    conn.execute("INSERT INTO data_anggota VALUES (?,?,?,?,?,?,?,?)", (path_prof, nama_reg, alamat_reg, kls_1, kls_2, kls_3, uid_reg, pwd_reg))
                    conn.commit(); conn.close()
                    st.balloons(); st.success("Alhamdulillah, pendaftaran Anda berhasil!"); st.rerun()
                except: st.error("ID Username sudah terdaftar!")
            else: st.warning("Mohon isi Nama, User ID, dan Password.")

elif st.session_state.menu_aktif == "Database Alumni":
    st.title("🔍 Database Alumni")
    conn = sqlite3.connect('alumni.db')
    df_db = pd.read_sql_query("SELECT * FROM data_anggota", conn)
    conn.close()
    if not df_db.empty:
        df_display = df_db[['foto_profile', 'nama', 'kelas_1', 'kelas_2', 'kelas_3', 'alamat']].copy()
        df_display['foto_profile'] = df_display['foto_profile'].apply(get_image_base64)
        st.data_editor(df_display, column_config={"foto_profile": st.column_config.ImageColumn("Foto")}, use_container_width=True, hide_index=True)
    else: st.info("Belum ada data anggota.")

# --- D. ADMIN PANEL (Lengkap untuk upload Foto Event) ---
elif st.session_state.menu_aktif == "Admin Panel":
    st.title("⚙️ Admin Panel")
    with st.form("admin_up_event"):
        f_event_up = st.file_uploader("Upload Foto Dokumentasi", type=['jpg','png','jpeg'])
        d_event_up = st.text_input("Nama Event (Contoh: Kopdar Sempat86 Cirebon)")
        if st.form_submit_button("🚀 Upload Foto") and f_event_up and d_event_up:
            p_save_event = f"static/img_events/{f_event_up.name}"
            with open(p_save_event, "wb") as f_e: f_e.write(f_event_up.getbuffer())
            conn = sqlite3.connect('alumni.db')
            conn.execute("INSERT INTO data_events (path_foto, deskripsi) VALUES (?,?)", (p_save_event, d_event_up))
            conn.commit(); conn.close(); st.success("Foto event berhasil ditambah!"); st.rerun()

else:
    st.title(f"📂 {st.session_state.menu_aktif}")
    st.info("Halaman sedang dikembangkan.")
