import streamlit as st
import pandas as pd

# Setting halaman web
st.set_page_config(page_title="Stok Conwood", layout="wide")

# ID Google Sheets Lu
SHEET_ID = "1SeTXDnQqcvqhuZ6rtX137tH_rd21OHYP76--bWyfUIk"

# Link Direct CSV ke masing-masing Tab
URL_STOK = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Stok_Barang"
URL_HISTORI = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Histori_Penjualan"

@st.cache_data(ttl=5) # Auto refresh cache data tiap 5 detik
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
    st.info("💡 Untuk mengedit stok / menambah transaksi baru, Anda dapat langsung mengeditnya dari Google Sheets.")

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
