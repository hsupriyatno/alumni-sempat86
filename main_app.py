st.subheader("🗓️ Agenda Kegiatan")
    conn = sqlite3.connect('alumni.db')
    # Mengambil data dan langsung mengurutkan berdasarkan kolom tanggal asli dari database
    df_ag = pd.read_sql_query("SELECT tanggal, kegiatan, lokasi FROM data_agenda ORDER BY tanggal ASC", conn)
    
    if not df_ag.empty:
        # Perbaikan Error: Menambahkan errors='coerce' agar aplikasi tidak crash jika ada format tanggal salah
        df_ag['tanggal'] = pd.to_datetime(df_ag['tanggal'], errors='coerce').dt.strftime('%d-%m-%Y')
        # Menghapus baris yang gagal dikonversi agar tabel tetap rapi
        df_ag = df_ag.dropna(subset=['tanggal'])
        st.table(df_ag)
    else:
        st.info("Belum ada agenda kegiatan.")
    conn.close()
