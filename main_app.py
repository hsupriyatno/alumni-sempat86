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
    if os.path.exists(path):
        with open(path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            return f"data:image/png;base64,{encoded}"
    return None

# --- 3. DATABASE SETUP ---
def init_db():
    conn = sqlite3.connect('alumni.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS data_anggota (
                    foto_profile TEXT, nama TEXT, alamat TEXT, 
                    kelas_1 TEXT, kelas_2 TEXT, kelas_3 TEXT, 
                    user_id TEXT PRIMARY KEY, password TEXT)''')
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
                 "In Memoriam Alumni Sempat 86", "Komunitas", "Networking", "Donasi", "Form Pendaftaran"]
    
    try:
        idx_sekarang = list_menu.index(st.session_state.menu_aktif)
    except:
        idx_sekarang = 0
        
    menu_pilihan = st.radio("Pilih Halaman:", list_menu, index=idx_sekarang)
    
    if menu_pilihan != st.session_state.menu_aktif:
        st.session_state.menu_aktif = menu_pilihan
        st.rerun()

# --- 7. LOGIKA HALAMAN ---

# --- A. HALAMAN HOME ---
if st.session_state.menu_aktif == "Home":
    st.markdown('<div class="main-header"><h1>Welcome Home, SEMPAT 86! 🏫</h1></div>', unsafe_allow_html=True)
    
    c_spacer, c_daftar, c_masuk = st.columns([7, 1.5, 1.5]) 
    
    with c_daftar:
        if st.button("📝 Daftar", use_container_width=True):
            pindah_halaman("Form Pendaftaran")
            st.rerun()
            
    with c_masuk:
        if st.button("🔑 Masuk", use_container_width=True):
            pindah_halaman("Database Alumni") 
            st.rerun()

    st.write("---")
    st.info("Selamat datang di aplikasi silaturahmi Alumni SMPN 4 Cirebon Angkatan 1986.")

# --- B. HALAMAN FORM PENDAFTARAN (INI YANG KITA HIDUPKAN) ---
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
                with open(ps, "wb") as f_save:
                    f_save.write(foto_reg.getbuffer())
                
                try:
                    conn = sqlite3.connect('alumni.db')
                    c = conn.cursor()
                    c.execute("INSERT INTO data_anggota VALUES (?,?,?,?,?,?,?,?)", 
                              (ps, nama_reg, almt_reg, k1, k2, k3, id_reg, pwd_reg))
                    conn.commit()
                    conn.close()
                    st.success(f"Berhasil! Selamat bergabung {nama_reg}")
                    st.balloons()
                except:
                    st.error("ID/Username sudah terdaftar!")
            else:
                st.warning("Mohon lengkapi data dan unggah foto!")

# --- C. HALAMAN DATABASE ALUMNI ---
elif st.session_state.menu_aktif == "Database Alumni":
    st.title("🔍 Database Alumni")
    conn = sqlite3.connect('alumni.db')
    df_db = pd.read_sql_query("SELECT * FROM data_anggota", conn)
    conn.close()
    
    if not df_db.empty:
        df_display = df_db.copy()
        df_display['foto_profile'] = df_display['foto_profile'].apply(get_image_base64)
        st.data_editor(
            df_display,
            column_config={"foto_profile": st.column_config.ImageColumn("Foto")},
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Belum ada data.")

# --- D. HALAMAN LAINNYA ---
else:
    st.title(st.session_state.menu_aktif)
    st.info("Halaman sedang dalam tahap pengembangan.")
    if st.button("⬅️ Kembali ke Home"):
        pindah_halaman("Home")
        st.rerun()
