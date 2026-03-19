import streamlit as st
import sqlite3
import pandas as pd
import os
import base64
import streamlit.components.v1 as components
from datetime import datetime

# --- 1. SETUP FOLDER ---
for folder in ['static/img_profile', 'static/img_events']:
    if not os.path.exists(folder):
        os.makedirs(folder)

# --- 2. FUNGSI HELPER (Agar Foto & Slideshow Muncul) ---
def get_image_base64(path):
    if not path: return None
    clean_path = path.replace('app/', '')
    if os.path.exists(clean_path):
        with open(clean_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
            return f"data:image/png;base64,{encoded}"
    return None

# --- 3. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('alumni.db')
    c = conn.cursor()
    # Tabel Anggota
    c.execute('''CREATE TABLE IF NOT EXISTS data_anggota (
                    foto_profile TEXT, nama TEXT, alamat TEXT, 
                    kelas_1 TEXT, kelas_2 TEXT, kelas_3 TEXT, 
                    user_id TEXT PRIMARY KEY, password TEXT)''')
    # Tabel Agenda
    c.execute('''CREATE TABLE IF NOT EXISTS data_agenda (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tanggal TEXT, kegiatan TEXT, lokasi TEXT, status TEXT)''')
    # Tabel Dokumentasi Foto
    c.execute('''CREATE TABLE IF NOT EXISTS data_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    path_foto TEXT, deskripsi TEXT)''')
    # Tabel Komentar
    c.execute('''CREATE TABLE IF NOT EXISTS data_komentar (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_deskripsi TEXT, nama_penulis TEXT, isi_komentar TEXT, waktu TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 4. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Alumni SMPN 4 Cirebon 86", page_icon="🏫", layout="wide")

if 'menu_aktif' not in st.session_state:
    st.session_state.menu_aktif = "Home"

def pindah_halaman(nama):
    st.session_state.menu_aktif = nama

# --- 5. STYLE CSS (Banner Biru) ---
st.markdown("""
    <style>
    .main-header { background: #2b5298; padding: 30px; border-radius: 15px; color: white; text-align: center; }
    .stButton > button { border-radius: 10px; }
    </style>
""", unsafe_allow_html=True)

# --- 6. SIDEBAR NAVIGASI ---
with st.sidebar:
    st.markdown("### 📂 Menu Utama")
    list_menu = ["Home", "Database Alumni", "Berita & Kalender Kegiatan", 
                 "In Memoriam Alumni Sempat 86", "Komunitas", "Networking", "Donasi", "Form Pendaftaran", "Admin Panel"]
    
    try:
        idx = list_menu.index(st.session_state.menu_aktif)
    except:
        idx = 0
        
    menu_pilihan = st.radio("Pilih Halaman:", list_menu, index=idx)
    if menu_pilihan != st.session_state.menu_aktif:
        pindah_halaman(menu_pilihan)
        st.rerun()

# --- 7. LOGIKA HALAMAN ---

# --- A. HALAMAN HOME ---
if st.session_state.menu_aktif == "Home":
    st.markdown('<div class="main-header"><h1>Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    
    # Tombol Daftar & Masuk
    c_spacer, c_daftar, c_masuk = st.columns([7, 1.5, 1.5]) 
    with c_daftar:
        if st.button("📝 Daftar", use_container_width=True):
            pindah_halaman("Form Pendaftaran"); st.rerun()
    with c_masuk:
        if st.button("🔑 Masuk", use_container_width=True):
            pindah_halaman("Database Alumni"); st.rerun()

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
            components.html(f"""
                <div class="slideshow-container">{slides}</div>
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

            # --- Komentar ---
            st.write("---")
            st.markdown("### 💬 Komentar")
            df_k = pd.read_sql_query("SELECT nama_penulis, isi_komentar, waktu FROM data_komentar WHERE event_deskripsi = ? ORDER BY id DESC", conn, params=(pilihan_ev,))
            for _, r in df_k.iterrows():
                st.caption(f"{r['waktu']} - **{r['nama_penulis']}**")
                st.info(r['isi_komentar'])
            
            with st.expander("➕ Tulis Komentar"):
                with st.form(f"form_kom_{pilihan_ev}", clear_on_submit=True):
                    n_k = st.text_input("Nama:")
                    i_k = st.text_area("Komentar:")
                    if st.form_submit_button("Kirim 🚀") and i_k:
                        conn.execute("INSERT INTO data_komentar (event_deskripsi, nama_penulis, isi_komentar, waktu) VALUES (?,?,?,?)",
                                     (pilihan_ev, (n_k if n_k else "Alumni"), i_k, datetime.now().strftime("%d/%m/%y %H:%M")))
                        conn.commit(); st.rerun()
    else:
        st.info("Belum ada foto kegiatan. Silakan upload via Admin Panel.")
    conn.close()

# --- B. HALAMAN FORM PENDAFTARAN (FUNGSI PENUH) ---
elif st.session_state.menu_aktif == "Form Pendaftaran":
    st.title("📝 Pendaftaran Anggota Baru")
    with st.form("regis_form", clear_on_submit=True):
        f1, f2 = st.columns(2)
        with f1:
            nama_reg = st.text_input("Nama Lengkap")
            id_reg = st.text_input("ID / Username")
            pwd_reg = st.text_input("Password", type="password")
        with f2:
            almt_reg = st.text_area("Alamat")
            kls_cols = st.columns(3)
            k1 = kls_cols[0].selectbox("Kls 1", ["A","B","C","D","E","F","G","H"])
            k2 = kls_cols[1].selectbox("Kls 2", ["A","B","C","D","E","F","G","H"])
            k3 = kls_cols[2].selectbox("Kls 3", ["A","B","C","D","E","F","G","H"])
        
        foto_reg = st.file_uploader("Unggah Foto Profil", type=['jpg','png','jpeg'])
        submit_reg = st.form_submit_button("✅ Daftar Sekarang")

        if submit_reg:
            if nama_reg and id_reg and pwd_reg and foto_reg:
                fn = f"{id_reg}_{foto_reg.name}"
                ps = os.path.join("static/img_profile", fn)
                with open(ps, "wb") as f_save: f_save.write(foto_reg.getbuffer())
                
                try:
                    conn = sqlite3.connect('alumni.db')
                    conn.execute("INSERT INTO data_anggota VALUES (?,?,?,?,?,?,?,?)", 
                                 (ps, nama_reg, almt_reg, k1, k2, k3, id_reg, pwd_reg))
                    conn.commit(); conn.close()
                    st.success(f"Alhamdulillah, data {nama_reg} berhasil disimpan!"); st.balloons()
                except: st.error("ID Username sudah terdaftar!")
            else: st.warning("Mohon lengkapi data dan unggah foto profil!")

# --- C. HALAMAN DATABASE ALUMNI ---
elif st.session_state.menu_aktif == "Database Alumni":
    st.title("🔍 Database Alumni")
    conn = sqlite3.connect('alumni.db')
    df_db = pd.read_sql_query("SELECT * FROM data_anggota", conn)
    conn.close()
    if not df_db.empty:
        df_display = df_db.copy()
        df_display['foto_profile'] = df_display['foto_profile'].apply(get_image_base64)
        st.data_editor(df_display, column_config={"foto_profile": st.column_config.ImageColumn("Foto")}, use_container_width=True, hide_index=True)
    else: st.info("Belum ada data.")

# --- D. ADMIN PANEL (Untuk Isi Foto Slideshow) ---
elif st.session_state.menu_aktif == "Admin Panel":
    st.title("⚙️ Admin Panel")
    with st.form("admin_upload"):
        up_foto = st.file_uploader("Upload Foto Kegiatan", type=['jpg','png','jpeg'])
        up_desk = st.text_input("Nama Event (Contoh: Reuni 2024)")
        if st.form_submit_button("Simpan Foto Event") and up_foto and up_desk:
            path_ev = f"static/img_events/{up_foto.name}"
            with open(path_ev, "wb") as f: f.write(up_foto.getbuffer())
            conn = sqlite3.connect('alumni.db')
            conn.execute("INSERT INTO data_events (path_foto, deskripsi) VALUES (?,?)", (path_ev, up_desk))
            conn.commit(); conn.close(); st.success("Foto Berhasil diupload!")

else:
    st.title(st.session_state.menu_aktif)
    st.info("Halaman sedang dikembangkan.")
