import streamlit as st
import sqlite3
import pandas as pd
import os
import base64

# --- 1. SETUP FOLDER ---
if not os.path.exists('static/img_profile'):
    os.makedirs('static/img_profile')

# --- 2. FUNGSI KONVERSI GAMBAR KE BASE64 ---
def get_image_base64(path):
    if not path:
        return None
    # Menghapus 'app/' jika ada agar path valid di sistem lokal
    clean_path = path.replace('app/', '')
    if os.path.exists(clean_path):
        with open(clean_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{encoded}"
    return None

# --- 3. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('alumni.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS data_anggota (
                    foto_profile TEXT, 
                    nama TEXT, 
                    alamat TEXT, 
                    kelas_1 TEXT, 
                    kelas_2 TEXT, 
                    kelas_3 TEXT, 
                    user_id TEXT PRIMARY KEY, 
                    password TEXT)''')
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
    .main-header { background: #2b5298; padding: 40px; border-radius: 20px; color: white; text-align: center; margin-bottom: 30px; }
    .stButton > button { border-radius: 10px; height: 50px; }
    </style>
""", unsafe_allow_html=True)

# --- 6. SIDEBAR NAVIGASI ---
with st.sidebar:
    st.markdown("### 📂 Menu Utama")
    list_menu = ["Home", "Database Alumni", "Berita & Kalender Kegiatan", 
                 "In Memoriam Alumni Sempat 86", "Komunitas", "Networking", "Donasi", "Form Pendaftaran"]
    
    # Mencari index menu yang aktif agar radio button sinkron
    try:
        idx_sekarang = list_menu.index(st.session_state.menu_aktif)
    except:
        idx_sekarang = 0
        
    menu_pilihan = st.radio("Pilih Halaman:", list_menu, index=idx_sekarang)
    
    if menu_pilihan != st.session_state.menu_aktif:
        st.session_state.menu_aktif = menu_pilihan
        st.rerun()

# --- 7. LOGIKA HALAMAN (Hati-hati Indentasi di Sini) ---

if st.session_state.menu_aktif == "Home":
    st.markdown('<div class="main-header"><h1>Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    c_h1, c_h2 = st.columns(2)
    with c_h1:
        if st.button("🔍 Lihat Database Alumni", use_container_width=True):
            pindah_halaman("Database Alumni")
            st.rerun()
    with c_h2:
        if st.button("📝 Daftar Anggota Baru", use_container_width=True):
            pindah_halaman("Form Pendaftaran")
            st.rerun()

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
                ext = foto_reg.name.split('.')[-1]
                fn = f"{id_reg}.{ext}"
                ps = os.path.join("static/img_profile", fn)
                pdb = f"static/img_profile/{fn}"
                with open(ps, "wb") as f_save:
                    f_save.write(foto_reg.getbuffer())
                try:
                    conn = sqlite3.connect('alumni.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO data_anggota VALUES (?,?,?,?,?,?,?,?)", 
                              (pdb, nama_reg, almt_reg, k1, k2, k3, id_reg, pwd_reg))
                    conn.commit()
                    conn.close()
                    st.success("Pendaftaran Berhasil!")
                    st.balloons()
                except:
                    st.error("ID Username sudah terpakai!")
            else:
                st.warning("Mohon lengkapi semua data dan foto!")

elif st.session_state.menu_aktif == "Database Alumni":
    st.title("🔍 Database Alumni")
    try:
        conn = sqlite3.connect('alumni.db')
        df_db = pd.read_sql_query("SELECT * FROM data_anggota", conn)
        conn.close()
        if not df_db.empty:
            df_display = df_db[['foto_profile', 'nama', 'alamat', 'kelas_1', 'kelas_2', 'kelas_3', 'user_id']].copy()
            # Proses foto agar muncul
            df_display['foto_profile'] = df_display['foto_profile'].apply(get_image_base64)
            st.data_editor(
                df_display,
                column_config={
                    "foto_profile": st.column_config.ImageColumn("Foto", width="small"),
                    "nama": "Nama Lengkap", "alamat": "Domisili", "user_id": "ID Anggota"
                },
                use_container_width=True, hide_index=True, disabled=True
            )
        else:
            st.info("Belum ada data alumni yang terdaftar.")
    except Exception as err:
        st.error(f"Terjadi kesalahan data: {err}")
    if st.button("⬅️ Kembali ke Home"):
        pindah_halaman("Home")
        st.rerun()

else:
    st.title(f"Halaman {st.session_state.menu_aktif}")
    st.info("Fitur ini sedang dalam tahap pengembangan.")
    if st.button("⬅️ Balik ke Menu Utama"):
        pindah_halaman("Home")
        st.rerun()
