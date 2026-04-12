import streamlit as st
import sqlite3
import pandas as pd

st.set_page_config(page_title="Hasil Voting Alumni", page_icon="📊")

st.title("📊 Laporan Hasil Pemilihan Ketua")

# Proteksi Sederhana khusus Admin
pass_admin = st.text_input("Masukkan Password Admin untuk melihat hasil:", type="password")

if pass_admin == "86admin": # Silakan Bapak ganti passwordnya
    with sqlite3.connect('alumni.db') as conn:
        # 1. Ambil Ringkasan Suara
        df_hasil = pd.read_sql_query("""
            SELECT pilihan as 'Kandidat', COUNT(*) as 'Total Suara' 
            FROM data_voting 
            GROUP BY pilihan 
            ORDER BY [Total Suara] DESC
        """, conn)

        # 2. Ambil Detail Pemilih (Untuk audit jika ada kecurangan)
        df_detail = pd.read_sql_query("""
            SELECT user_id as 'Nama Pemilih', ip_address as 'IP Perangkat', waktu as 'Waktu Memilih' 
            FROM data_voting 
            ORDER BY waktu DESC
        """, conn)

    if not df_hasil.empty:
        # Tampilkan Grafik
        st.subheader("📈 Grafik Perolehan Suara")
        st.bar_chart(df_hasil.set_index('Kandidat'))

        # Tampilkan Tabel Ringkasan
        st.subheader("📑 Tabel Perolehan")
        st.dataframe(df_hasil, use_container_width=True)

        # Tampilkan Audit Log (Siapa saja yang sudah pilih)
        with st.expander("Lihat Daftar Pemilih (Audit Log)"):
            st.table(df_detail)
            
        # Tombol Download Hasil
        csv = df_hasil.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Hasil (CSV)", csv, "hasil_voting_86.csv", "text/csv")
    else:
        st.info("Belum ada suara yang masuk.")
else:
    if pass_admin != "":
        st.error("Password Salah!")
    st.warning("Halaman ini hanya untuk Panitia/Admin.")