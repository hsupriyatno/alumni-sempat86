import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import socket

# --- 1. INISIALISASI DATABASE (VERSI BERSIH) ---
def init_db():
    with sqlite3.connect('alumni.db') as conn:
        # 1. Tabel User
        conn.execute('''CREATE TABLE IF NOT EXISTS data_users 
                     (username TEXT PRIMARY KEY, password TEXT, nama_lengkap TEXT, nomor_wa_aktif TEXT, role TEXT)''')
        
        # 2. Tabel Voting (Pastikan kolom 'pilihan' konsisten)
        conn.execute('''CREATE TABLE IF NOT EXISTS data_voting 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      user_id TEXT, ip_address TEXT, pilihan TEXT, waktu TEXT)''')
        
        # 3. Tabel Penjaringan
        conn.execute('''CREATE TABLE IF NOT EXISTS data_penjaringan 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      nama_calon TEXT, pengusul TEXT)''')
        
        # --- PERBAIKAN KOLOM OTOMATIS (Mencegah OperationalError) ---
        cursor = conn.cursor()
        
        # Cek kolom nomor_wa_aktif di data_users
        cursor.execute("PRAGMA table_info(data_users)")
        cols_user = [info[1] for info in cursor.fetchall()]
        if 'nomor_wa_aktif' not in cols_user:
            conn.execute("ALTER TABLE data_users ADD COLUMN nomor_wa_aktif TEXT")

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
                        conn.execute("INSERT INTO data_users (username, password, nama_lengkap, nomor_wa_aktif, role) VALUES (?,?,?,?,?)", 
                                     (new_user, new_pwd, new_nama, new_wa, 'alumni'))
                    st.success("Berhasil! Silakan klik tab 'Masuk'.")
                except:
                    st.error("Username sudah ada.")

# --- 2. LOGIKA UTAMA ---
init_db()
# Cek Login
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    show_auth_form()
    st.stop()
st.write(f"Selamat datang, **{st.session_state.user_nama}**! Silakan gunakan fitur di bawah ini untuk berpartisipasi dalam pemilihan Ketua Alumni.")

# Ambil data calon
with sqlite3.connect('alumni.db') as conn:
    df_calon = pd.read_sql_query("SELECT DISTINCT nama_calon FROM data_penjaringan ORDER BY nama_calon ASC", conn)
    list_calon = df_calon['nama_calon'].tolist()

# --- A. FITUR PENJARINGAN ---
st.subheader("📝 Penjaringan Calon Ketua")
with st.expander("➕ Klik di sini untuk mengusulkan nama calon jika belum ada di daftar", expanded=False):
    with st.form("form_nominasi", clear_on_submit=True):
        nama_usulan = st.text_input("Masukkan Nama Calon yang Diusulkan:")
        
        if st.form_submit_button("Usulkan Nama"):
            nama_cek = nama_usulan.lower().strip() # Ubah ke huruf kecil untuk pengecekan
            
            # --- LOGIKA PENOLAKAN PANITIA ---
            if any(x in nama_cek for x in ["hery", "heri", "cimot"]):
                st.error("🚫 Maaf, nama tersebut terdeteksi sebagai Panitia Pemilihan dan tidak dapat dicalonkan.")
            
            elif nama_usulan.strip():
                with sqlite3.connect('alumni.db') as conn:
                    conn.execute("INSERT INTO data_penjaringan (nama_calon, pengusul) VALUES (?,?)", 
                                 (nama_usulan.title().strip(), st.session_state.user_nama))
                st.success(f"Nama '{nama_usulan.title()}' berhasil diusulkan!")
                st.rerun()
            else:
                st.warning("Silakan masukkan nama calon terlebih dahulu.")

# --- B. FITUR VOTING ---
st.divider()
if not list_calon:
    st.info("💡 **Belum ada kandidat.** Silakan usulkan nama melalui menu 'Penjaringan Calon' di atas terlebih dahulu.")
else:
    hostname = socket.gethostname()
    ip_client = socket.gethostbyname(hostname)
    
    with sqlite3.connect('alumni.db') as conn:
        cek = conn.execute("SELECT * FROM data_voting WHERE user_id = ? OR ip_address = ?", 
                           (st.session_state.user_nama, ip_client)).fetchone()

    if cek:
        st.success("✅ Terima kasih, suara Bapak sudah masuk!")
    else:
        with st.form("form_voting"):
            st.write("Silakan pilih salah satu kandidat:")
            pilihan = st.radio("Daftar Calon:", list_calon) 
            
            if st.form_submit_button("Kirim Suara Sah"):
                waktu_vote = datetime.now().strftime("%d/%m/%Y %H:%M")
                with sqlite3.connect('alumni.db') as conn:
                    conn.execute("INSERT INTO data_voting (user_id, ip_address, pilihan, waktu) VALUES (?,?,?,?)",
                                 (st.session_state.user_nama, ip_client, pilihan, waktu_vote))
                st.balloons()
                st.success("Suara berhasil dikirim!")
                st.rerun()