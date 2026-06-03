# backend/data_fetcher.py
# =====================================================
# Modul untuk mengambil data saham dari Yahoo Finance
# =====================================================

import yfinance as yf
import pandas as pd
from datetime import datetime

# ─────────────────────────────────────────────────────
# DAFTAR 8 SAHAM IDX YANG KITA ANALISIS
# ─────────────────────────────────────────────────────
DAFTAR_SAHAM = {
    "BBCA": "Bank Central Asia",
    "BBRI": "Bank Rakyat Indonesia",
    "ASII": "Astra International",
    "TLKM": "Telkom Indonesia",
    "GOTO": "GoTo Gojek Tokopedia",
    "BMRI": "Bank Mandiri",
    "BREN": "Barito Renewables Energy",
    "UNVR": "Unilever Indonesia",
}


def format_ticker(ticker):
    """
    Tambahkan .JK di belakang ticker kalau belum ada.
    Contoh: 'BBCA' -> 'BBCA.JK'
    Yahoo Finance butuh suffix .JK untuk saham Indonesia.
    """
    ticker = ticker.upper().strip()
    if not ticker.endswith(".JK"):
        ticker = ticker + ".JK"
    return ticker


def get_stock_data(ticker):
    """
    Ambil data historis saham dari Yahoo Finance.

    Parameter:
        ticker (str): Kode saham, contoh 'BBCA' atau 'BBCA.JK'

    Return:
        dict berisi:
            - 'df': DataFrame dengan kolom Open, High, Low, Close, Volume
            - 'ticker_bersih': ticker tanpa .JK
            - 'nama': nama perusahaan
        atau None kalau ticker tidak ditemukan / error
    """
    ticker_yf = format_ticker(ticker)
    ticker_bersih = ticker.upper().replace(".JK", "")

    try:
        print(f"  Mengunduh data {ticker_yf}...")

        # Download data 3 bulan terakhir, interval harian
        df = yf.download(
            ticker_yf,
            period="3mo",
            interval="1d",
            progress=False,   # matikan progress bar
            auto_adjust=True  # sesuaikan harga untuk split/dividen
        )

        # Cek apakah data kosong
        if df.empty:
            print(f"  ERROR: Data {ticker_yf} kosong / tidak ditemukan.")
            return None

        # Cek minimal ada 30 baris data
        # (butuh minimal 26 hari untuk MACD, 14 hari untuk RSI)
        if len(df) < 30:
            print(f"  WARNING: Data {ticker_yf} kurang dari 30 hari ({len(df)} baris).")
            return None

        # Bersihkan kolom - pastiin nama kolom konsisten
        df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]

        # Drop baris yang ada NaN di kolom penting
        df = df.dropna(subset=["Close", "Volume"])

        # Reset index supaya Date jadi kolom biasa (bukan index)
        df = df.reset_index()

        # Pastiin kolom Date ada
        if "Date" not in df.columns:
            df = df.rename(columns={"index": "Date"})

        print(f"  OK! {len(df)} hari data berhasil diambil.")

        return {
            "df": df,
            "ticker_bersih": ticker_bersih,
            "nama": DAFTAR_SAHAM.get(ticker_bersih, ticker_bersih),
        }

    except Exception as e:
        print(f"  ERROR saat ambil data {ticker_yf}: {str(e)}")
        return None


def get_harga_sekarang(data_result):
    """
    Ambil harga terkini dan persentase perubahan dari data yang sudah diunduh.

    Parameter:
        data_result (dict): hasil dari get_stock_data()

    Return:
        dict berisi harga_sekarang dan perubahan_persen
    """
    df = data_result["df"]

    harga_sekarang = float(df["Close"].iloc[-1])
    harga_kemarin  = float(df["Close"].iloc[-2])

    perubahan = ((harga_sekarang - harga_kemarin) / harga_kemarin) * 100

    return {
        "harga_sekarang": round(harga_sekarang, 2),
        "perubahan_persen": round(perubahan, 2),
        "naik": perubahan >= 0,
    }


def get_data_chart(data_result, n_hari=60):
    """
    Ambil data untuk ditampilkan di grafik frontend.
    Kembalikan list of dict yang siap di-convert ke JSON.

    Parameter:
        data_result (dict): hasil dari get_stock_data()
        n_hari (int): berapa hari terakhir yang ditampilkan di grafik

    Return:
        list of dict: [{tanggal, open, high, low, close, volume}, ...]
    """
    df = data_result["df"].tail(n_hari).copy()

    chart_data = []
    for _, row in df.iterrows():
        chart_data.append({
            "tanggal": str(row["Date"])[:10],  # format YYYY-MM-DD
            "open":    round(float(row["Open"]), 2),
            "high":    round(float(row["High"]), 2),
            "low":     round(float(row["Low"]), 2),
            "close":   round(float(row["Close"]), 2),
            "volume":  int(row["Volume"]),
        })

    return chart_data