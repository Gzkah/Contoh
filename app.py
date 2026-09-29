import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import datetime

# Setting halaman web
st.set_page_config(page_title="Stok Conwood", layout="wide")

# ID Google Sheets
SHEET_ID = "1SeTXDnQqcvqhuZ6rtX137tH_rd21OHYP76--bWyfUIk"

# Link Direct CSV (Read-Only)
URL_STOK = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Stok_Barang"
URL_HISTORI = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Histori_Penjualan"

# Fungsi Koneksi Write gspread via Secrets
def get_gspread_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    if "gcp_service_account" in st.secrets:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scopes
        )
        return gspread.authorize(creds)
    return None

@st.cache_data(ttl=2)
def load_data():
    try:
        df_stok = pd.read_csv(URL_STOK)
        df_histori = pd.read_csv(URL_HISTORI)
        return df_stok, df_histori
    except Exception as e:
        st.error(f"Gagal membaca data dari Google Sheets: {e}")
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
        
        df["Harga_Asli"] = df["Harga_Asli"].astype(str).str.replace('.', '', regex=False)
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
    
    if not df_stok.empty:
        list_produk = df_stok["Nama_Produk"].dropna().tolist()
        produk_dipilih = st.selectbox("Pilih / Ketik Nama Produk Conwood:", list_produk)
        
        idx_produk = df_stok[df_stok["Nama_Produk"] == produk_dipilih].index[0]
        detail_p = df_stok.loc[idx_produk]
        stok_sekarang = int(detail_p["Stok"])
        
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
                        
                        # 1. Tambah baris ke Histori_Penjualan
                        stgl_beli = tgl_beli.strftime("%Y-%m-%d")
                        stgl_kirim = tgl_kirim.strftime("%Y-%m-%d")
                        
                        new_row = [
                            stgl_beli,
                            produk_dipilih,
                            qty,
                            harga_akhir,
                            total_bayar,
                            nama_pembeli,
                            no_telp,
                            alamat,
                            stgl_kirim,
                            "Pending"
                        ]
                        ws_histori.append_row(new_row)
                        
                        # 2. Kurangi stok di Stok_Barang
                        # Baris di gspread mulai dari index 1, header ada di baris 1, jadi + 2
                        row_number = idx_produk + 2
                        sisa_stok_baru = stok_sekarang - qty
                        ws_stok.update_cell(row_number, 8, sisa_stok_baru) # Kolom H = Stok
                        
                        st.cache_data.clear()
                        st.success("✅ Transaksi berhasil disimpan! Stok terupdate & data masuk ke Histori.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Gagal menyimpan ke Google Sheets: {e}")
                else:
                    st.error("⚠️ Secrets Google Service Account belum terpasang di Dashboard Streamlit Community Cloud.")

# ==========================================
# MENU 3: HISTORI & STATUS KIRIM
# ==========================================
elif menu == "📋 Histori & Status Kirim":
    st.title("📋 Histori Penjualan & Status Pengiriman")
    if not df_histori.empty:
        st.dataframe(df_histori, use_container_width=True)
    else:
        st.warning("Belum ada histori transaksi di Google Sheets.")

# ==========================================
# MENU 4: PROJEK REFERENSI
# ==========================================
elif menu == "🖼️ Projek Referensi":
    st.title("🖼️ Galeri & Dokumentasi Projek Conwood")
    st.write("Akses cepat ke folder foto hasil projek Conwood di Google Drive.")
    
    link_gdrive = "https://drive.google.com"
    st.link_button("📁 Buka Folder Foto Projek (Google Drive)", link_gdrive, type="primary")
