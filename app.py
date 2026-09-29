import streamlit as st
import pandas as pd

# Setting halaman web
st.set_page_config(page_title="Stok Conwood", layout="wide")

# --- INITIALIZE SESSION STATE (DATABASE SEMENTARA) ---
if "df_stok" not in st.session_state:
    data_stok = [
        {"ID_Produk": "CW-001", "Nama_Produk": "Conwood Decking 12\"", "Tebal_mm": 25, "Lebar_mm": 300, "Panjang_mm": 3050, "Harga_Asli": 220000, "Diskon_Persen": 10, "Stok": 45},
        {"ID_Produk": "CW-002", "Nama_Produk": "Conwood Sunshade 3\"", "Tebal_mm": 14, "Lebar_mm": 75, "Panjang_mm": 3050, "Harga_Asli": 95000, "Diskon_Persen": 0, "Stok": 5},
        {"ID_Produk": "CW-003", "Nama_Produk": "Conwood Plank 2\"", "Tebal_mm": 8, "Lebar_mm": 50, "Panjang_mm": 3000, "Harga_Asli": 75000, "Diskon_Persen": 5, "Stok": 120}
    ]
    st.session_state.df_stok = pd.DataFrame(data_stok)

if "df_histori" not in st.session_state:
    st.session_state.df_histori = pd.DataFrame(columns=[
        "ID_Transaksi", "Tgl_Beli", "Tgl_Kirim", "Nama_Pembeli", "No_Telp", "Alamat", "Nama_Produk", "Qty", "Total_Harga", "Status_Kirim"
    ])

# --- SIDEBAR MENU ---
st.sidebar.title("📌 Menu Utama")
menu = st.sidebar.radio("Pilih Menu:", [
    "🔍 Katalog & Cari Stok",
    "🛒 Transaksi & Restock",
    "📋 Histori & Status Kirim",
    "🖼️ Projek Referensi"
])

# ==========================================
# MENU 1: KATALOG & CARI STOK
# ==========================================
if menu == "🔍 Katalog & Cari Stok":
    st.title("📦 Katalog & Pencarian Stok Conwood")
    
    df = st.session_state.df_stok.copy()
    df["Harga_Akhir"] = df["Harga_Asli"] - (df["Harga_Asli"] * df["Diskon_Persen"] / 100)
    
    keyword = st.text_input("🔍 Ketik nama produk, tebal, lebar, dll...", "")
    
    if keyword.strip():
        search_matrix = df.astype(str).apply(lambda row: ' '.join(row), axis=1)
        df_filtered = df[search_matrix.str.contains(keyword.strip(), case=False, na=False)]
    else:
        df_filtered = df
        
    st.dataframe(
        df_filtered,
        use_container_width=True,
        column_config={
            "Harga_Asli": st.column_config.NumberColumn("Harga Asli", format="Rp %d"),
            "Harga_Akhir": st.column_config.NumberColumn("Harga Akhir", format="Rp %d"),
            "Tebal_mm": "Tebal (mm)",
            "Lebar_mm": "Lebar (mm)",
            "Panjang_mm": "Panjang (mm)",
            "Diskon_Persen": "Diskon (%)"
        }
    )

# ==========================================
# MENU 2: TRANSAKSI & RESTOCK
# ==========================================
elif menu == "🛒 Transaksi & Restock":
    st.title("🛒 Transaksi & Restock Barang")
    
    tab1, tab2 = st.tabs(["📝 Input Penjualan Baru", "📦 Restock Barang Masuk"])
    
    # --- TAB 1: INPUT PENJUALAN ---
    with tab1:
        st.subheader("Input Data Pembeli & Transaksi")
        
        list_produk = st.session_state.df_stok["Nama_Produk"].tolist()
        
        # Selectbox otomatis bisa diketik untuk mencari produk
        produk_dipilih = st.selectbox("Pilih / Ketik Nama Produk Conwood:", list_produk, help="Ketik nama produk untuk mencari cepat")
        
        detail_p = st.session_state.df_stok[st.session_state.df_stok["Nama_Produk"] == produk_dipilih].iloc[0]
        stok_sekarang = detail_p["Stok"]
        harga_asli = detail_p["Harga_Asli"]
        diskon = detail_p["Diskon_Persen"]
        harga_akhir = harga_asli - (harga_asli * diskon / 100)
        
        st.info(f"💡 **Sisa Stok:** {stok_sekarang} Pcs | **Harga Final per Pcs:** Rp {harga_akhir:,.0f}")
        
        col1, col2 = st.columns(2)
        with col1:
            qty = st.number_input("Jumlah (Qty Pcs):", min_value=1, max_value=int(stok_sekarang) if stok_sekarang > 0 else 1, value=1)
            tgl_beli = st.date_input("Tanggal Beli:")
            tgl_kirim = st.date_input("Rencana Tanggal Kirim:")
            
        with col2:
            nama_pembeli = st.text_input("Nama Pembeli:")
            no_telp = st.text_input("No. Telepon HP:")
            alamat = st.text_area("Alamat Pengiriman:")
            
        total_bayar = qty * harga_akhir
        st.write(f"### 💵 Total Bayar: **Rp {total_bayar:,.0f}**")
        
        if st.button("💾 Simpan Transaksi", type="primary"):
            if not nama_pembeli or not no_telp or not alamat:
                st.error("⚠️ Mohon lengkapi Nama, No Telp, dan Alamat pembeli!")
            elif qty > stok_sekarang:
                st.error("⚠️ Stok tidak cukup!")
            else:
                st.session_state.df_stok.loc[st.session_state.df_stok["Nama_Produk"] == produk_dipilih, "Stok"] -= qty
                
                id_trx = f"TRX-{len(st.session_state.df_histori) + 1:03d}"
                trx_baru = {
                    "ID_Transaksi": id_trx,
                    "Tgl_Beli": str(tgl_beli),
                    "Tgl_Kirim": str(tgl_kirim),
                    "Nama_Pembeli": nama_pembeli,
                    "No_Telp": no_telp,
                    "Alamat": alamat,
                    "Nama_Produk": produk_dipilih,
                    "Qty": qty,
                    "Total_Harga": total_bayar,
                    "Status_Kirim": "Belum Terkirim"
                }
                st.session_state.df_histori = pd.concat([st.session_state.df_histori, pd.DataFrame([trx_baru])], ignore_index=True)
                st.success(f"✅ Transaksi **{id_trx}** berhasil disimpan & stok dipotong {qty} Pcs!")

    # --- TAB 2: RESTOCK BARANG ---
    with tab2:
        st.subheader("Tambah Stok Barang Masuk")
        produk_restock = st.selectbox("Pilih / Ketik Produk yang Datang:", list_produk, key="restock")
        qty_masuk = st.number_input("Jumlah Barang Masuk (Pcs):", min_value=1, value=10)
        
        if st.button("➕ Tambah Stok"):
            st.session_state.df_stok.loc[st.session_state.df_stok["Nama_Produk"] == produk_restock, "Stok"] += qty_masuk
            st.success(f"✅ Stok **{produk_restock}** berhasil ditambah {qty_masuk} Pcs!")

# ==========================================
# MENU 3: HISTORI & STATUS KIRIM
# ==========================================
elif menu == "📋 Histori & Status Kirim":
    st.title("📋 Histori Penjualan & Status Pengiriman")
    
    if st.session_state.df_histori.empty:
        st.warning("Belum ada histori transaksi. Silakan input penjualan di menu Transaksi.")
    else:
        # Fitur Update Status Pengiriman
        st.subheader("🔄 Update Status Pengiriman")
        list_trx = st.session_state.df_histori["ID_Transaksi"].tolist()
        selected_trx = st.selectbox("Pilih ID Transaksi untuk diubah statusnya:", list_trx)
        
        idx = st.session_state.df_histori[st.session_state.df_histori["ID_Transaksi"] == selected_trx].index[0]
        status_sekarang = st.session_state.df_histori.loc[idx, "Status_Kirim"]
        
        col_status1, col_status2 = st.columns([2, 1])
        with col_status1:
            status_baru = st.selectbox("Status Pengiriman:", ["Belum Terkirim", "Proses Kirim", "Selesai / Terkirim"], index=["Belum Terkirim", "Proses Kirim", "Selesai / Terkirim"].index(status_sekarang))
        with col_status2:
            st.write(" ")
            st.write(" ")
            if st.button("Update Status"):
                st.session_state.df_histori.loc[idx, "Status_Kirim"] = status_baru
                st.success(f"Status {selected_trx} diubah jadi: {status_baru}")
                st.rerun()

        st.divider()
        st.subheader("Data Histori Lengkap")
        st.dataframe(
            st.session_state.df_histori,
            use_container_width=True,
            column_config={
                "Total_Harga": st.column_config.NumberColumn("Total Bayar", format="Rp %d")
            }
        )

# ==========================================
# MENU 4: PROJEK REFERENSI
# ==========================================
elif menu == "🖼️ Projek Referensi":
    st.title("🖼️ Galeri & Dokumentasi Projek Conwood")
    st.write("Akses cepat ke folder dokumentasi dan contoh hasil pemasangan Conwood di Google Drive.")
    
    # Masukkan link folder Google Drive lu di sini nanti
    link_gdrive = "https://drive.google.com" 
    
    st.link_button("📁 Buka Folder Foto Projek (Google Drive)", link_gdrive, type="primary")
    st.caption("Klik tombol di atas untuk membuka folder galeri projek di Google Drive.")