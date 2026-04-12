import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

with sqlite3.connect('alumni.db') as conn:
    # Perintah untuk menambah kolom jika belum ada
    try:
        conn.execute("ALTER TABLE data_voting ADD COLUMN pilihan TEXT")
        conn.commit()
    except:
        # Jika kolom sudah ada, dia akan lanjut tanpa error
        pass

st.title("📊 Laporan Hasil Pemilihan Ketua")
st.info("Halaman ini terbuka untuk seluruh alumni SEMPAT 86.")

# --- KONEKSI DATABASE ---
with sqlite3.connect('alumni.db') as conn:
    # Mengambil data perolehan suara
    df_hasil = pd.read_sql_query("""
        SELECT pilihan as Nama_Kandidat, COUNT(*) as Total_Suara 
        FROM data_voting 
        GROUP BY pilihan
    """, conn)

if not df_hasil.empty:
    # --- TAMPILAN RINGKASAN ---
    total_pemilih = df_hasil['Total_Suara'].sum()
    st.metric("Total Suara Masuk", f"{total_pemilih} Suara")

    # --- VISUALISASI GRAFIK ---
    fig = px.pie(df_hasil, values='Total_Suara', names='Nama_Kandidat', 
                 title='Persentase Perolehan Suara',
                 color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(fig, use_container_width=True)

    # --- TABEL RINCIAN ---
    st.write("### Rincian Perolehan:")
    st.dataframe(df_hasil, hide_index=True, use_container_width=True)
else:
    st.warning("Belum ada suara yang masuk.")