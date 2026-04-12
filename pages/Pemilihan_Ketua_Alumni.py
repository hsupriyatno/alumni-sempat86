import streamlit as st
import sqlite3
from datetime import datetime
import socket

# --- 1. DEFINISIKAN SEMUA FUNGSI DI ATAS ---

def init_db():
    """Fungsi ini memastikan tabel USER dan VOTING sudah siap"""
    with sqlite3.connect('alumni.db') as conn:
        # Tabel User (ditambah kolom WA)
        conn.execute('''CREATE TABLE IF NOT EXISTS data_users 
                     (username TEXT PRIMARY KEY, password TEXT, nama_lengkap TEXT, nomor_wa_aktif TEXT, role TEXT)''')
        
        # Tabel Voting
        conn.execute('''CREATE TABLE IF NOT EXISTS data_voting 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      user_id TEXT, ip_address TEXT, pilihan TEXT, waktu TEXT)''')
        
        # Tambahan: Perbaikan otomatis jika kolom nomor_wa_aktif belum ada di database lama
        try:
            conn.execute("ALTER TABLE data_users ADD COLUMN nomor_wa_aktif TEXT")
        except:
            pass

def show_auth_form():
    st.warning("🔒 Khusus Alumni: Silakan Daftar dan Masuk untuk memberikan suara.")
    tab1, tab2 = st.tabs(["Masuk", "Daftar Akun"])
    
    with tab1:
        with st.form("form_login"):
            user = st.text_input("Username")
            pwd = st.text_input("Password", type="password")
            if st.form_submit_button("Masuk"):
                with sqlite3.connect('alumni.db') as conn:
                    res = conn.execute("SELECT * FROM data_users WHERE username = ? AND password = ?", (user, pwd)).fetchone()
                if res:
                    st.session_state.logged_in = True
                    st.session_state.user_nama = user
                    st.rerun()
                else:
                    st.error("Gagal masuk, cek kembali data Bapak.")

    with tab2:
        st.info("Buat akun alumni baru di sini.")
        with st.form("form_daftar"):
            new_user = st.text_input("Username (Tanpa Spasi)")
            new_nama = st.text_input("Nama Lengkap")
            new_wa = st.text_input("Nomor WA Aktif")
            new_pwd = st.text_input("Password", type="password")
            if st.form_submit_button("Daftar Sekarang"):
                try:
                    with sqlite3.connect('alumni.db') as conn:
                        conn.execute("INSERT INTO data_users VALUES (?,?,?,?,?)", 
                                     (new_user, new_pwd, new_nama, new_wa, 'alumni'))
                    st.success("Berhasil! Silakan klik tab 'Masuk'.")
                except:
                    st.error("Username sudah ada.")

# --- 2. JALANKAN LOGIKA APLIKASI ---

# Jalankan inisialisasi database dulu
init_db()

# Cek Login
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    show_auth_form()
    st.stop()

# Jika sudah login, tampilkan Form Voting
st.title("🗳️ Pemilihan Ketua Alumni")
st.write(f"Halo, **{st.session_state.user_nama}**! Silakan berikan suara Bapak.")

# Logika cek apakah sudah pernah memilih (menggunakan IP atau Username)
hostname = socket.gethostname()
ip_client = socket.gethostbyname(hostname)

with sqlite3.connect('alumni.db') as conn:
    cek = conn.execute("SELECT * FROM data_voting WHERE user_id = ? OR ip_address = ?", 
                       (st.session_state.user_nama, ip_client)).fetchone()

if cek:
    st.success(f"Terima kasih, suara Bapak sudah masuk!")
else:
    with st.form("form_voting"):
        pilihan = st.radio("Pilih Calon:", ["Kandidat A", "Kandidat B", "Kandidat C"])
        if st.form_submit_button("Kirim Suara Sah"):
            waktu = datetime.now().strftime("%d/%m/%Y %H:%M")
            with sqlite3.connect('alumni.db') as conn:
                conn.execute("INSERT INTO data_voting (user_id, ip_address, pilihan, waktu) VALUES (?,?,?,?)",
                             (st.session_state.user_nama, ip_client, pilihan, waktu))
            st.balloons()
            st.rerun()