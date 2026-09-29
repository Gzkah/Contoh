import streamlit as st
import pandas as pd
import datetime
import random
import gspread
from google.oauth2.service_account import Credentials

# ==========================================
# KONFIGURASI HALAMAN
# ==========================================
st.set_page_config(
    page_title="Stok & Penjualan Conwood",
    page_icon="🪵",
    layout="wide"
)

# ID Google Sheets Anda
SHEET_ID = "1SeTXDnQqcvqhuZ6rtX137tH_rd21OHYP76--bWyfUIk"

# Scope untuk Google Sheets API
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# ==========================================
# KONEKSI GOOGLE SHEETS
# ==========================================
@st.cache_resource
def get_gspread_client():
    try:
        if "gcp_service_account" in st.secrets:
            creds_dict = dict(st.secrets["gcp_service_account"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
            client = gspread.authorize(creds)
            return client
        else:
            return None
    except Exception as e:
        st.error(f"Error Koneksi Google Sheets: {e}")
        return None

# Fungsi membaca data dari sheet
@st.cache_data(ttl=10)
def load_data(sheet_name):
    client = get_gspread_client()
    if client:
        try:
            sh = client.open_by_key(SHEET_ID)
            ws = sh.worksheet(sheet_name)
            data = ws.get_all_records()
            return pd.DataFrame(data)
        except Exception as e:
            st.error(f"Gagal mengambil data dari {sheet_name}: {e}")
            return pd.DataFrame()
    return pd.DataFrame()

# Load Data Awal
df_stok = load_data("Stok_Barang")
df_histori = load_data("Histori_Penjualan")

# ==========================================
# NAVIGATION / SIDEBAR
# ==========================================
st.sidebar.title("📌 Menu Utama")
menu = st.sidebar.radio(
    "Pilih Halaman:",
    ["📊 Dashboard & Stok", "🛒 Transaksi & Restock", "📜 Histori Penjualan"]
)

# ==========================================
# MENU 1: DASHBOARD & STOK
# ==========================================
if menu == "📊 Dashboard & Stok":
    st.title("📊 Dashboard & Stok Conwood")
    
    if not df_stok.empty:
        # Ringkasan Matriks
        col1, col2, col3 = st.columns(3)
        total_item = len(df_stok)
        total_stok = df_stok["Stok"].sum() if "Stok" in df_stok.columns else 0
        
        col1.metric("Total Jenis Produk", f"{total_item} Item")
        col2.metric("Total Sisa Stok", f"{total_stok} Pcs")
        col3.metric("Status Sistem", "🟢 Terkoneksi GSheets")
        
        st.divider()
        st.subheader("📋 Daftar Stok Produk")
        
        # Search Box
        search = st.text_input("🔍 Cari Produk Conwood:", "")
        if search:
            df_filtered = df_stok[df_stok["Nama_Produk"].str.contains(search, case=False, na=False)]
        else:
            df_filtered = df_stok
            
        st.dataframe(df_filtered, use_container_width=True)
    else:
        st.warning("⚠️ Data stok kosong atau gagal terhubung ke Google Sheets.")

# ==========================================
# MENU 2: TRANSAKSI & RESTOCK
# ==========================================
elif menu == "🛒 Transaksi & Restock":
    st.title("🛒 Transaksi & Restock Barang")
    
    if not df_stok.empty:
        # Pilihan Mode (Jual vs Restok)
        mode = st.radio("Pilih Jenis Aksi:", ["🛒 Transaksi Penjualan", "📦 Restok / Tambah Stok Baru"], horizontal=True)
        st.divider()
        
        list_produk = df_stok["Nama_Produk"].dropna().tolist()
        produk_dipilih = st.selectbox("Pilih / Ketik Nama Produk Conwood:", list_produk)
        
        idx_produk = df_stok[df_stok["Nama_Produk"] == produk_dipilih].index[0]
        detail_p = df_stok.loc[idx_produk]
        stok_sekarang = int(detail_p["Stok"])
        
        # ------------------------------------------
        # MODE 1: TRANSAKSI PENJUALAN
        # ------------------------------------------
        if mode == "🛒 Transaksi Penjualan":
            harga_asli_str = str(detail_p["Harga_Asli"]).replace('.', '')
            harga_asli = float(harga_asli_str)
            diskon = float(detail_p["Diskon_Persen"])
            harga_akhir = harga_asli - (harga_asli * diskon / 100)
            
            st.info(f"💡 **Sisa Stok:** {stok_sekarang} Pcs | **Harga Final per Pcs:** Rp {harga_akhir:,.0f}")
            
            col1, col2 = st.columns(2)
            with col1:
                qty = st.number_input("Jumlah (Qty Pcs):", min_value=1, max_value=stok_sekarang if stok_sekarang > 0 else 1, value=1)
                tgl_beli = st.date_input("Tanggal Beli:", datetime.date.today())
                tgl_kirim = st.date_input("Rencana Tanggal Kirim:", datetime.date.today())
                
            with col2:
                nama_pembeli = st.text_input("Nama Pembeli:")
                no_telp = st.text_input("No. Telepon HP:")
                alamat = st.text_area("Alamat Pengiriman:")
                
            total_bayar = qty * harga_akhir
            st.write(f"### 💵 Total Bayar: **Rp {total_bayar:,.0f}**")
            
            if st.button("💾 Simpan Transaksi", type="primary"):
                if not nama_pembeli or not no_telp or not alamat:
                    st.error("⚠️ Mohon lengkapi Nama Pembeli, No. HP, dan Alamat!")
                elif qty > stok_sekarang:
                    st.error("⚠️ Stok barang tidak mencukupi!")
                else:
                    client = get_gspread_client()
                    if client:
                        try:
                            sh = client.open_by_key(SHEET_ID)
                            ws_stok = sh.worksheet("Stok_Barang")
                            ws_histori = sh.worksheet("Histori_Penjualan")
                            
                            stgl_beli = tgl_beli.strftime("%Y-%m-%d")
                            stgl_kirim = tgl_kirim.strftime("%Y-%m-%d")
                            
                            trx_id = f"TRX-{tgl_beli.strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
                            
                            # SUSUNAN BERDASARKAN HEADER GOOGLE SHEETS ANDA:
                            new_row = [
                                trx_id,          # 1. ID_Transaksi
                                stgl_beli,       # 2. Tgl_Beli
                                stgl_kirim,      # 3. Tgl_Kirim
                                nama_pembeli,    # 4. Nama_Pembeli
                                no_telp,         # 5. No_Telp
                                alamat,          # 6. Alamat
                                produk_dipilih,  # 7. Nama_Produk
                                qty,             # 8. Qty
                                total_bayar,     # 9. Total_Harga
                                "Pending"        # 10. Status_Kirim
                            ]
                            
                            ws_histori.append_row(new_row)
                            
                            # Update Stok di Google Sheets (Kolom H = Stok)
                            row_number = idx_produk + 2
                            sisa_stok_baru = stok_sekarang - qty
                            ws_stok.update_cell(row_number, 8, sisa_stok_baru)
                            
                            st.cache_data.clear()
                            st.success("✅ Transaksi berhasil disimpan! Data tersusun rapi di Google Sheets.")
                            st.balloons()
                        except Exception as e:
                            st.error(f"Gagal menyimpan ke Google Sheets: {e}")
                    else:
                        st.error("⚠️ Kredensial Service Account belum terpasang.")

        # ------------------------------------------
        # MODE 2: RESTOK / TAMBAH STOK
        # ------------------------------------------
        else:
            st.info(f"📦 **Stok Saat Ini:** {stok_sekarang} Pcs")
            
            jumlah_masuk = st.number_input("Jumlah Barang Masuk / Restok (Pcs):", min_value=1, value=10)
            stok_total_baru = stok_sekarang + jumlah_masuk
            
            st.write(f"### 📊 Stok Setelah Restok: **{stok_total_baru} Pcs**")
            
            if st.button("➕ Update Restok Barang", type="primary"):
                client = get_gspread_client()
                if client:
                    try:
                        sh = client.open_by_key(SHEET_ID)
                        ws_stok = sh.worksheet("Stok_Barang")
                        
                        row_number = idx_produk + 2
                        ws_stok.update_cell(row_number, 8, stok_total_baru)
                        
                        st.cache_data.clear()
                        st.success(f"✅ Restok berhasil! Stok **{produk_dipilih}** bertambah jadi {stok_total_baru} Pcs.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Gagal mengupdate stok ke Google Sheets: {e}")
                else:
                    st.error("⚠️ Kredensial Service Account belum terpasang.")
    else:
        st.warning("⚠️ Data stok tidak tersedia.")

# ==========================================
# MENU 3: HISTORI PENJUALAN
# ==========================================
elif menu == "📜 Histori Penjualan":
    st.title("📜 Histori Transaksi Penjualan")
    
    if not df_histori.empty:
        st.dataframe(df_histori, use_container_width=True)
    else:
        st.info("ℹ️ Belum ada histori transaksi penjualan.")
