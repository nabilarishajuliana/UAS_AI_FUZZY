# test_indicators.py
# Jalankan dari folder fuzzystock/:
#   python test_indicators.py
# =====================================================

import sys
sys.path.insert(0, "backend")

from data_fetcher import get_stock_data
from indicators import (
    calculate_rsi,
    calculate_macd,
    calculate_volume_ratio,
    hitung_semua_indikator
)

print("=" * 60)
print("TEST INDICATORS")
print("=" * 60)

# ─────────────────────────────────────────────────────
# Download data dulu
# ─────────────────────────────────────────────────────
print("\nMengunduh data BBCA untuk test...")
result = get_stock_data("BBCA")

if result is None:
    print("GAGAL ambil data. Cek koneksi internet.")
    sys.exit(1)

df   = result["df"]
nama = result["nama"]
print(f"Data {nama} berhasil ({len(df)} hari)\n")

# ─────────────────────────────────────────────────────
# TEST 1: RSI
# ─────────────────────────────────────────────────────
print("-" * 60)
print("TEST 1: RSI (Relative Strength Index)")
print("-" * 60)

rsi_now, rsi_series = calculate_rsi(df)

print(f"  RSI sekarang    : {rsi_now}")
print(f"  RSI 5 hari lalu :")
for i, val in enumerate(rsi_series.iloc[-5:]):
    print(f"    hari -{4-i}: {round(val, 2)}")

# Interpretasi
if rsi_now < 30:
    print(f"\n  Interpretasi: OVERSOLD ({rsi_now} < 30)")
    print(f"  → Potensi sinyal BELI")
elif rsi_now > 70:
    print(f"\n  Interpretasi: OVERBOUGHT ({rsi_now} > 70)")
    print(f"  → Potensi sinyal JUAL")
else:
    print(f"\n  Interpretasi: NEUTRAL (30 < {rsi_now} < 70)")
    print(f"  → Tidak ada sinyal ekstrem")

# Validasi nilai RSI
assert 0 <= rsi_now <= 100, "ERROR: RSI di luar range 0-100!"
print(f"\n  ✓ RSI valid: {rsi_now} (dalam range 0-100)")

# ─────────────────────────────────────────────────────
# TEST 2: MACD
# ─────────────────────────────────────────────────────
print("\n" + "-" * 60)
print("TEST 2: MACD Histogram")
print("-" * 60)

macd_now, macd_data = calculate_macd(df)

print(f"  MACD Histogram sekarang : {macd_now}")
print(f"  MACD Line 5 hari lalu   :")
for i, val in enumerate(macd_data["macd_line"].iloc[-5:]):
    print(f"    hari -{4-i}: {round(val, 4)}")

print(f"\n  Signal Line sekarang    : {round(float(macd_data['signal_line'].iloc[-1]), 4)}")
print(f"  Histogram sekarang      : {macd_now}")

if macd_now > 0.1:
    print(f"\n  Interpretasi: BULLISH (histogram {macd_now} > 0.1)")
    print(f"  → Momentum naik")
elif macd_now < -0.1:
    print(f"\n  Interpretasi: BEARISH (histogram {macd_now} < -0.1)")
    print(f"  → Momentum turun")
else:
    print(f"\n  Interpretasi: SIDEWAYS (-0.1 < {macd_now} < 0.1)")
    print(f"  → Momentum tidak jelas")

print(f"\n  ✓ MACD berhasil dihitung")

# ─────────────────────────────────────────────────────
# TEST 3: Volume Ratio
# ─────────────────────────────────────────────────────
print("\n" + "-" * 60)
print("TEST 3: Volume Ratio")
print("-" * 60)

vol_ratio, avg_vol = calculate_volume_ratio(df)

print(f"  Volume hari ini   : {int(df['Volume'].iloc[-1]):,}")
print(f"  Rata-rata 20 hari : {int(avg_vol):,}")
print(f"  Volume Ratio      : {vol_ratio}x")

if vol_ratio > 1.3:
    print(f"\n  Interpretasi: HIGH ({vol_ratio}x > 1.3x)")
    print(f"  → Sinyal lebih meyakinkan")
elif vol_ratio < 0.7:
    print(f"\n  Interpretasi: LOW ({vol_ratio}x < 0.7x)")
    print(f"  → Sinyal kurang meyakinkan")
else:
    print(f"\n  Interpretasi: AVERAGE (0.7x < {vol_ratio}x < 1.3x)")
    print(f"  → Volume normal")

assert 0 <= vol_ratio <= 3.0, "ERROR: Volume Ratio di luar range 0-3!"
print(f"\n  ✓ Volume Ratio valid: {vol_ratio} (dalam range 0-3)")

# ─────────────────────────────────────────────────────
# TEST 4: Hitung semua indikator sekaligus
# ─────────────────────────────────────────────────────
print("\n" + "-" * 60)
print("TEST: Hitung Semua Indikator Sekaligus (hitung_semua_indikator)")
print("-" * 60)

semua = hitung_semua_indikator(df)
print(f"Data {nama}")

print(f"\n  RSI          : {semua['rsi']} → {semua['rsi_label']}")
print(f"  MACD         : {semua['macd']} → {semua['macd_label']}")
print(f"  Volume Ratio : {semua['volume_ratio']}x → {semua['vol_label']}")

# ─────────────────────────────────────────────────────
# TEST 5: Cek semua 8 saham
# ─────────────────────────────────────────────────────
print("\n" + "-" * 60)
print("TEST: Hitung Indikator Semua 8 Saham")
print("-" * 60)

from data_fetcher import DAFTAR_SAHAM

print(f"\n  {'Ticker':<8} {'RSI':>8} {'Kat RSI':<12} {'MACD':>10} {'Kat MACD':<12} {'Vol Ratio':>10} {'Kat Vol'}")
print("  " + "-" * 78)

semua_berhasil = True
for ticker in DAFTAR_SAHAM:
    r = get_stock_data(ticker)
    if r is None:
        print(f"  {ticker:<8} GAGAL")
        semua_berhasil = False
        continue

    ind = hitung_semua_indikator(r["df"])
    print(f"  {ticker:<8} "
          f"{ind['rsi']:>8.2f} "
          f"{ind['rsi_label']:<12} "
          f"{ind['macd']:>10.4f} "
          f"{ind['macd_label']:<12} "
          f"{ind['volume_ratio']:>10.4f}x "
          f"{ind['vol_label']}")

# ─────────────────────────────────────────────────────
# HASIL AKHIR
# ─────────────────────────────────────────────────────
print("\n" + "=" * 60)
if semua_berhasil:
    print("SEMUA TEST LULUS! Part 2 selesai, lanjut ke Part 3.")
else:
    print("ADA YANG GAGAL. Cek koneksi internet.")
print("=" * 60)