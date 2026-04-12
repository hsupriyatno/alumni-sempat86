import streamlit as st
import sqlite3
from datetime import datetime
import socket

st.set_page_config(page_title="Voting Ketua Sempat-86", page_icon="🗳️")

# Inisialisasi Database (Hanya tabel voting)
def init_vote_db():
    with sqlite3.connect('alumni.db') as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS data_voting 
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                      user_id TEXT, ip_address TEXT, pilihan TEXT, waktu TEXT)''')

init_vote_db()

# Cek Login (Penting agar tidak bisa curang)
if 'logged_in' not in st.session_state or not st.session_state.logged_in:
    st.warning("⚠️ Silakan Login terlebih dahulu di halaman utama untuk memberikan suara.")
    st.stop() # Hentikan script jika belum login

# Logika Voting Otomatis
st.title("🗳️ Pemilihan Ketua Alumni")

hostname = socket.gethostname()
ip_client = socket.gethostbyname(hostname)
user_aktif = st.session_state.user_nama 

with sqlite3.connect('alumni.db') as conn:
    cek_voter = conn.execute("SELECT * FROM data_voting WHERE user_id = ? OR ip_address = ?", 
                            (user_aktif, ip_client)).fetchone()

if cek_voter:
    st.success(f"Terima kasih, {user_aktif}. Suara Anda sudah terekam.")
else:
    with st.form("form_voting"):
        pilihan = st.radio("Pilih Calon Ketua:", ["Kandidat A", "Kandidat B", "Kandidat C"])
        if st.form_submit_button("Kirim Suara Sah"):
            waktu_vote = datetime.now().strftime("%d/%m/%Y %H:%M")
            with sqlite3.connect('alumni.db') as conn:
                conn.execute("INSERT INTO data_voting (user_id, ip_address, pilihan, waktu) VALUES (?,?,?,?)",
                             (user_aktif, ip_client, pilihan, waktu_vote))
            st.balloons()
            st.rerun()