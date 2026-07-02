# backend/app.py
# =====================================================
# Flask Backend API — FuzzyStock (Production Ready)
#
# Endpoint:
#   GET /api/stocks           → daftar 8 saham
#   GET /api/analyze/<ticker> → analisis lengkap
# =====================================================

import matplotlib
matplotlib.use('Agg')

from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
import sys
import os

# Tambahkan folder backend ke path supaya bisa import modul lain
sys.path.insert(0, os.path.dirname(__file__))

from data_fetcher import (
    get_stock_data,
    get_harga_sekarang,
    get_data_chart,
    DAFTAR_SAHAM,
    DAFTAR_SAHAM_SEMUA,
)
from indicators   import hitung_semua_indikator, calculate_macd
from fuzzy_engine import analyze


# ─────────────────────────────────────────────────────
# SETUP FLASK
# ─────────────────────────────────────────────────────

app = Flask(__name__)

# CORS = izinkan frontend (HTML di browser) akses API ini
CORS(app)

# Menentukan letak folder frontend secara relatif dan aman untuk produksi
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))


@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/detail.html')
def detail_page():
    return send_from_directory(FRONTEND_DIR, 'detail.html')


@app.route('/script.js')
def frontend_script():
    return send_from_directory(FRONTEND_DIR, 'script.js')


# ─────────────────────────────────────────────────────
# HELPER: proses satu saham lengkap
# Dipakai oleh kedua endpoint di bawah
# ─────────────────────────────────────────────────────

def proses_saham(ticker):
    """
    Ambil data, hitung indikator, jalankan fuzzy.
    Return dict hasil lengkap atau None kalau gagal.
    """
    try:
        # 1. Ambil data dari Yahoo Finance
        result = get_stock_data(ticker)
        if result is None:
            return None

        df   = result["df"]
        nama = result["nama"]

        # 2. Hitung harga dan perubahan
        harga_info = get_harga_sekarang(result)

        # 3. Hitung indikator teknikal
        indikator = hitung_semua_indikator(df)

        # 4. Ambil MACD series untuk normalisasi
        _, macd_data = calculate_macd(df)
        macd_series  = macd_data["histogram"]

        # 5. Jalankan fuzzy engine
        hasil_fuzzy = analyze(
            rsi_val      = indikator["rsi"],
            macd_raw     = indikator["macd"],
            macd_series  = macd_series,
            volume_ratio = indikator["volume_ratio"]
        )

        # 6. Ambil data chart
        chart_data = get_data_chart(result, n_hari=60)

        return {
            # Info saham
            "ticker"          : ticker,
            "nama"            : nama,
            "harga"           : harga_info["harga_sekarang"],
            "perubahan_persen": harga_info["perubahan_persen"],
            "naik"            : harga_info["naik"],

            # Indikator teknikal
            "rsi"             : indikator["rsi"],
            "rsi_label"       : indikator["rsi_label"],
            "macd"            : indikator["macd"],
            "macd_normalized" : hasil_fuzzy["macd_normalized"],
            "macd_label"      : indikator["macd_label"],
            "volume_ratio"    : indikator["volume_ratio"],
            "vol_label"       : indikator["vol_label"],

            # Hasil fuzzy
            "score"           : hasil_fuzzy["score"],
            "rekomendasi"     : hasil_fuzzy["rekomendasi"],
            "fuzzifikasi"     : hasil_fuzzy["fuzzifikasi"],
            "rules_aktif"     : hasil_fuzzy["rules_aktif"],

            # Data grafik
            "chart"           : chart_data,
        }
    except Exception as e:
        print(f"Error saat memproses {ticker}: {str(e)}")
        return None


# ─────────────────────────────────────────────────────
# ENDPOINT 1: GET /api/stocks
# Return daftar semua 8 saham + rekomendasi singkat
# Dipakai oleh landing page untuk isi kartu saham
# ─────────────────────────────────────────────────────

@app.route('/api/stocks', methods=['GET'])
def get_stocks():
    """
    Return semua 8 saham sekaligus.
    Frontend pakai ini untuk isi grid kartu di landing page.
    """
    print("\n[API] GET /api/stocks — memproses 8 saham...")

    hasil = []
    gagal = []

    for ticker in DAFTAR_SAHAM:
        print(f"  Memproses {ticker}...")
        data = proses_saham(ticker)

        if data is None:
            gagal.append(ticker)
            # Kalau gagal, masukkan data kosong supaya frontend tidak error
            hasil.append({
                "ticker"          : ticker,
                "nama"            : DAFTAR_SAHAM[ticker],
                "harga"           : 0,
                "perubahan_persen": 0,
                "naik"            : True,
                "rsi"             : 50,
                "rsi_label"       : "Neutral",
                "macd"            : 0,
                "macd_label"      : "Sideways",
                "volume_ratio"    : 1.0,
                "vol_label"       : "Average",
                "score"           : 50,
                "rekomendasi"     : "Hold",
                "error"           : True,
            })
        else:
            # Untuk endpoint /stocks, tidak perlu kirim data chart
            data_ringkas = {k: v for k, v in data.items() if k != "chart"}
            hasil.append(data_ringkas)

    print(f"  Selesai: {len(hasil)-len(gagal)}/8 berhasil")

    return jsonify({
        "status" : "ok",
        "jumlah" : len(hasil),
        "gagal"  : gagal,
        "data"   : hasil,
    })


# ─────────────────────────────────────────────────────
# ENDPOINT 2: GET /api/analyze/<ticker>
# Return analisis LENGKAP satu saham termasuk chart
# Dipakai oleh halaman detail saham
# ─────────────────────────────────────────────────────

@app.route('/api/analyze/<ticker>', methods=['GET'])
def analyze_saham(ticker):
    """
    Return analisis lengkap satu saham.
    Frontend pakai ini untuk halaman detail.
    """
    ticker = ticker.upper()
    print(f"\n[API] GET /api/analyze/{ticker}")

    # Validasi: pastikan ticker ada di daftar kita
    if ticker not in DAFTAR_SAHAM_SEMUA:
        return jsonify({
            "status" : "error",
            "pesan"  : f"Ticker {ticker} tidak ada dalam daftar. "
                       f"Pilih dari: {', '.join(DAFTAR_SAHAM_SEMUA.keys())}",
        }), 404

    # Proses saham
    data = proses_saham(ticker)

    if data is None:
        return jsonify({
            "status": "error",
            "pesan" : f"Gagal mengambil data {ticker}. "
                      f"Cek koneksi internet.",
        }), 500

    return jsonify({
        "status": "ok",
        "data"  : data,
    })


# ─────────────────────────────────────────────────────
# ENDPOINT BONUS & DEBUGGING
# ─────────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status" : "ok",
        "pesan"  : "FuzzyStock API berjalan!",
        "saham"  : list(DAFTAR_SAHAM.keys()),
    })


@app.route('/api/universe', methods=['GET'])
def get_universe():
    return jsonify({
        "status": "ok",
        "jumlah": len(DAFTAR_SAHAM_SEMUA),
        "data": [{"ticker": ticker, "nama": nama} for ticker, nama in DAFTAR_SAHAM_SEMUA.items()],
    })


# ─────────────────────────────────────────────────────
# JALANKAN SERVER
# ─────────────────────────────────────────────────────

if __name__ == '__main__':
    # Membaca port dinamis dari Render (Default ke 5000 jika dijalankan lokal)
    port = int(os.environ.get("PORT", 5000))
    
    print("=" * 50)
    print("  FuzzyStock API Server")
    print(f"  Berjalan pada port: {port}")
    print("=" * 50)
    
    # Matikan debug=True saat di-deploy ke Render agar berjalan stabil
    is_production = os.environ.get("PORT") is not None
    
    app.run(
        host="0.0.0.0",  # Wajib 0.0.0.0 agar bisa diakses secara publik oleh internet/Render
        port=port,
        debug=not is_production,
        use_reloader=not is_production,
    )