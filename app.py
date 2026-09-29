import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# Setting halaman web
st.set_page_config(page_title="Stok Conwood", layout="wide")

# --- KONEKSI GOOGLE SHEETS ---
conn = st.connection("gsheets", type=GSheetsConnection)

# Fungsi membaca data dari Google Sheets
def load_data():
    try:
        df_stok = conn.read(worksheet="Stok_Barang", ttl="0")
        df_histori = conn.read(worksheet="Histori_Penjualan", ttl="0")
        return df_stok, df_histori
    except Exception as e:
        st.error(f"Gagal terhubung ke Google Sheets: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_stok, df_histori = load_data()

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
    
    if not df_stok.empty:
        df = df_stok.copy()
        
        # Format kolom numerik
        df["Harga_Asli"] = pd.to_numeric(df["Harga_Asli"], errors='coerce').fillna(0)
        df["Diskon_Persen"] = pd.to_numeric(df["Diskon_Persen"], errors='coerce').fillna(0)
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
                "Lebar_cm": "Lebar (cm)",
                "Panjang_m": "Panjang (m)",
                "Diskon_Persen": "Diskon (%)"
            }
        )
    else:
        st.warning("Data stok di Google Sheets masih kosong atau belum terbaca.")

# ==========================================
# MENU 2: TRANSAKSI & RESTOCK
# ==========================================
elif menu == "🛒 Transaksi & Restock":
    st.title("🛒 Transaksi & Restock Barang")
    
    tab1, tab2 = st.tabs(["📝 Input Penjualan Baru", "📦 Restock Barang Masuk"])
    
    # --- TAB 1: INPUT PENJUALAN ---
    with tab1:
        st.subheader("Input Data Pembeli & Transaksi")
        
        if not df_stok.empty:
            list_produk = df_stok["Nama_Produk"].dropna().tolist()
            produk_dipilih = st.selectbox("Pilih / Ketik Nama Produk Conwood:", list_produk)
            
            detail_p = df_stok[df_stok["Nama_Produk"] == produk_dipilih].iloc[0]
            stok_sekarang = int(detail_p["Stok"])
            harga_asli = float(detail_p["Harga_Asli"])
            diskon = float(detail_p["Diskon_Persen"])
            harga_akhir = harga_asli - (harga_asli * diskon / 100)
            
            st.info(f"💡 **Sisa Stok:** {stok_sekarang} Pcs | **Harga Final per Pcs:** Rp {harga_akhir:,.0f}")
            
            col1, col2 = st.columns(2)
            with col1:
                qty = st.number_input("Jumlah (Qty Pcs):", min_value=1, max_value=stok_sekarang if stok_sekarang > 0 else 1, value=1)
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
                    df_stok.loc[df_stok["Nama_Produk"] == produk_dipilih, "Stok"] = stok_sekarang - qty
                    
                    id_trx = f"TRX-{len(df_histori) + 1:03d}"
                    trx_baru = pd.DataFrame([{
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
                    }])
                    
                    df_histori_updated = pd.concat([df_histori, trx_baru], ignore_index=True)
                    
                    conn.update(worksheet="Stok_Barang", data=df_stok)
                    conn.update(worksheet="Histori_Penjualan", data=df_histori_updated)
                    
                    st.success(f"✅ Transaksi **{id_trx}** berhasil tersimpan di Google Sheets!")
                    st.rerun()

    # --- TAB 2: RESTOCK BARANG ---
    with tab2:
        st.subheader("Tambah Stok Barang Masuk")
        if not df_stok.empty:
            produk_restock = st.selectbox("Pilih / Ketik Produk yang Datang:", list_produk, key="restock")
            qty_masuk = st.number_input("Jumlah Barang Masuk (Pcs):", min_value=1, value=10)
            
            if st.button("➕ Tambah Stok"):
                stok_lama = int(df_stok.loc[df_stok["Nama_Produk"] == produk_restock, "Stok"].values[0])
                df_stok.loc[df_stok["Nama_Produk"] == produk_restock, "Stok"] = stok_lama + qty_masuk
                
                conn.update(worksheet="Stok_Barang", data=df_stok)
                st.success(f"✅ Stok **{produk_restock}** berhasil diperbarui di Google Sheets!")
                st.rerun()

# ==========================================
# MENU 3: HISTORI & STATUS KIRIM
# ==========================================
elif menu == "📋 Histori & Status Kirim":
    st.title("📋 Histori Penjualan & Status Pengiriman")
    
    if df_histori.empty or df_histori.dropna(how='all').empty:
        st.warning("Belum ada histori transaksi di Google Sheets.")
    else:
        st.subheader("🔄 Update Status Pengiriman")
        list_trx = df_histori["ID_Transaksi"].dropna().tolist()
        selected_trx = st.selectbox("Pilih ID Transaksi:", list_trx)
        
        idx = df_histori[df_histori["ID_Transaksi"] == selected_trx].index[0]
        status_sekarang = str(df_histori.loc[idx, "Status_Kirim"])
        
        options_status = ["Belum Terkirim", "Proses Kirim", "Selesai / Terkirim"]
        default_idx = options_status.index(status_sekarang) if status_sekarang in options_status else 0
        
        status_baru = st.selectbox("Status Pengiriman Baru:", options_status, index=default_idx)
        
        if st.button("Update Status ke Google Sheets"):
            df_histori.loc[idx, "Status_Kirim"] = status_baru
            conn.update(worksheet="Histori_Penjualan", data=df_histori)
            st.success(f"Status {selected_trx} diperbarui jadi: {status_baru}")
            st.rerun()

        st.divider()
        st.subheader("Data Histori Lengkap")
        st.dataframe(df_histori, use_container_width=True)

# ==========================================
# MENU 4: PROJEK REFERENSI
# ==========================================
elif menu == "🖼️ Projek Referensi":
    st.title("🖼️ Galeri & Dokumentasi Projek Conwood")
    st.write("Akses cepat ke folder foto hasil projek Conwood di Google Drive.")
    
    link_gdrive = "https://drive.google.com"
    st.link_button("📁 Buka Folder Foto Projek (Google Drive)", link_gdrive, type="primary")
