# backend/app.py
# =====================================================
# Flask Backend API — FuzzyStock
#
# Endpoint:
#   GET /api/stocks           → daftar 8 saham
#   GET /api/analyze/<ticker> → analisis lengkap
# =====================================================

import matplotlib
matplotlib.use('Agg')

from flask import Flask, jsonify
from flask_cors import CORS
import sys
import os

# Tambahkan folder backend ke path supaya bisa import modul lain
sys.path.insert(0, os.path.dirname(__file__))

from data_fetcher import get_stock_data, get_harga_sekarang, get_data_chart, DAFTAR_SAHAM
from indicators   import hitung_semua_indikator, calculate_macd
from fuzzy_engine import analyze


# ─────────────────────────────────────────────────────
# SETUP FLASK
# ─────────────────────────────────────────────────────

app = Flask(__name__)

# CORS = izinkan frontend (HTML di browser) akses API ini
# Tanpa ini, browser akan blokir request dari frontend
CORS(app)


# ─────────────────────────────────────────────────────
# HELPER: proses satu saham lengkap
# Dipakai oleh kedua endpoint di bawah
# ─────────────────────────────────────────────────────

def proses_saham(ticker):
    """
    Ambil data, hitung indikator, jalankan fuzzy.
    Return dict hasil lengkap atau None kalau gagal.
    """

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
            # (chart dikirim di endpoint /analyze saja)
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

    Contoh URL: http://localhost:5000/api/analyze/BBCA
    """
    ticker = ticker.upper()
    print(f"\n[API] GET /api/analyze/{ticker}")

    # Validasi: pastikan ticker ada di daftar kita
    if ticker not in DAFTAR_SAHAM:
        return jsonify({
            "status" : "error",
            "pesan"  : f"Ticker {ticker} tidak ada dalam daftar. "
                       f"Pilih dari: {', '.join(DAFTAR_SAHAM.keys())}",
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
# ENDPOINT 3: GET /api/health
# Cek apakah server berjalan (untuk debugging)
# ─────────────────────────────────────────────────────

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status" : "ok",
        "pesan"  : "FuzzyStock API berjalan!",
        "saham"  : list(DAFTAR_SAHAM.keys()),
    })


# ─────────────────────────────────────────────────────
# JALANKAN SERVER
# ─────────────────────────────────────────────────────

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)