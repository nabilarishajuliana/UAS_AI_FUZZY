# test_data_fetcher.py
# Jalankan dari folder fuzzystock/:
#   python test_data_fetcher.py
# =====================================================

import sys
sys.path.insert(0, "backend")  # supaya bisa import dari folder backend

from data_fetcher import (
    get_stock_data,
    get_harga_sekarang,
    get_data_chart,
    DAFTAR_SAHAM
)

print("=" * 55)
print("TEST DATA FETCHER")
print("=" * 55)

# ─────────────────────────────────────────────────────
# TEST 1: Download data 1 saham
# ─────────────────────────────────────────────────────
print("\n[TEST 1] Download data BBCA...")
result = get_stock_data("BBCA")

if result is None:
    print("GAGAL: Data tidak bisa diambil. Cek koneksi internet.")
    sys.exit(1)

df = result["df"]
print(f"  Ticker  : {result['ticker_bersih']}")
print(f"  Nama    : {result['nama']}")
print(f"  Jumlah baris data: {len(df)}")
print(f"  Kolom   : {list(df.columns)}")
print(f"  Rentang : {df['Date'].iloc[0]} s/d {df['Date'].iloc[-1]}")
print(f"\n  5 baris terakhir:")
print(df[["Date", "Open", "High", "Low", "Close", "Volume"]].tail())

# ─────────────────────────────────────────────────────
# TEST 2: Harga dan perubahan
# ─────────────────────────────────────────────────────
print("\n[TEST 2] Harga sekarang dan perubahan...")
harga_info = get_harga_sekarang(result)
arah = "▲" if harga_info["naik"] else "▼"
print(f"  Harga   : Rp {harga_info['harga_sekarang']:,.2f}")
print(f"  Perubahan: {arah} {harga_info['perubahan_persen']:+.2f}%")

# ─────────────────────────────────────────────────────
# TEST 3: Data chart (5 hari saja untuk preview)
# ─────────────────────────────────────────────────────
print("\n[TEST 3] Data chart (5 hari terakhir)...")
chart = get_data_chart(result, n_hari=5)
for baris in chart:
    print(f"  {baris['tanggal']} | Close: {baris['close']:>10,.2f} | Vol: {baris['volume']:>12,}")

# ─────────────────────────────────────────────────────
# TEST 4: Download semua 8 saham sekaligus
# ─────────────────────────────────────────────────────
print("\n[TEST 4] Download semua 8 saham...")
print("-" * 55)

berhasil = 0
gagal    = 0

for ticker, nama in DAFTAR_SAHAM.items():
    r = get_stock_data(ticker)
    if r is not None:
        h = get_harga_sekarang(r)
        arah = "▲" if h["naik"] else "▼"
        print(f"  {ticker:<6} | {nama:<30} | "
              f"Rp {h['harga_sekarang']:>10,.2f} {arah} {h['perubahan_persen']:>+6.2f}%")
        berhasil += 1
    else:
        print(f"  {ticker:<6} | GAGAL")
        gagal += 1

print("-" * 55)
print(f"  Berhasil: {berhasil}/8  |  Gagal: {gagal}/8")

# ─────────────────────────────────────────────────────
# HASIL AKHIR
# ─────────────────────────────────────────────────────
print("\n" + "=" * 55)
if gagal == 0:
    print("SEMUA TEST LULUS! Part 1 selesai, lanjut ke Part 2.")
else:
    print(f"ADA {gagal} SAHAM GAGAL. Cek koneksi internet.")
print("=" * 55)