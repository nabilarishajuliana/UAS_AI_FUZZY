# test_fuzzy_engine.py
# Jalankan dari folder fuzzystock/:
#   python test_fuzzy_engine.py
# =====================================================

import sys
import pandas as pd
sys.path.insert(0, "backend")

from data_fetcher  import get_stock_data, DAFTAR_SAHAM
from indicators    import hitung_semua_indikator, calculate_macd
from fuzzy_engine  import analyze, normalize_macd, get_label

print("=" * 65)
print("TEST FUZZY ENGINE — Metode Mamdani")
print("=" * 65)


# ─────────────────────────────────────────────────────
# TEST 1: Normalisasi MACD
# ─────────────────────────────────────────────────────
print("\n[TEST 1] Normalisasi MACD")
print("-" * 65)

# Simulasi: buat series MACD dummy untuk test
dummy_series = pd.Series([-80, -60, -40, -20, 0, 20, 40, 60, 80, -45])

test_cases = [
    ( 0.0,  "Sideways (nol)"),
    ( 80.0, "Bullish kuat"),
    (-45.0, "Bearish sedang"),
    (-80.0, "Bearish kuat"),
]
for raw, label in test_cases:
    norm = normalize_macd(raw, dummy_series)
    print(f"  MACD raw {raw:>8.2f}  →  normalized {norm:>7.4f}  ({label})")

print("\n  ✓ Normalisasi MACD OK")


# ─────────────────────────────────────────────────────
# TEST 2: Test dengan nilai input manual (tanpa API)
# ─────────────────────────────────────────────────────
print("\n[TEST 2] Analyze dengan nilai manual")
print("-" * 65)

# Buat dummy MACD series (misal range -100 sampai +100)
dummy_macd_series = pd.Series(
    [i * 10 for i in range(-10, 11)] + [-45, 30, -80, 60]
)

scenarios = [
    # (rsi, macd_raw, vol_ratio, deskripsi_yang_diharapkan)
    (25,  60.0, 1.8, "RSI Oversold + MACD Bullish + Vol High → Strong Buy?"),
    (75, -60.0, 1.8, "RSI Overbought + MACD Bearish + Vol High → Strong Sell?"),
    (50,   0.0, 1.0, "RSI Neutral + MACD Sideways + Vol Average → Hold?"),
    (40,  40.0, 1.5, "RSI Neutral + MACD Bullish + Vol High → Buy?"),
    (65, -40.0, 1.2, "RSI Neutral + MACD Bearish + Vol Average → Sell?"),
]

for rsi, macd_raw, vol, deskripsi in scenarios:
    hasil = analyze(rsi, macd_raw, dummy_macd_series, vol)
    score = hasil["score"]
    rek   = hasil["rekomendasi"]
    macd_n = hasil["macd_normalized"]
    print(f"\n  Input: RSI={rsi}, MACD_raw={macd_raw} (norm={macd_n}), Vol={vol}")
    print(f"  Skenario: {deskripsi}")
    print(f"  → Score: {score}  |  Rekomendasi: {rek}")


# ─────────────────────────────────────────────────────
# TEST 3: Test dengan data BBCA real
# ─────────────────────────────────────────────────────
print("\n\n[TEST 3] Analyze BBCA dengan data real")
print("-" * 65)

print("  Mengunduh data BBCA...")
result = get_stock_data("BBCA")

if result is None:
    print("  GAGAL. Cek koneksi internet.")
else:
    df   = result["df"]
    ind  = hitung_semua_indikator(df)
    _, macd_data = calculate_macd(df)
    macd_series = macd_data["histogram"]

    print(f"\n  Nilai Indikator BBCA:")
    print(f"    RSI          = {ind['rsi']} ({ind['rsi_label']})")
    print(f"    MACD raw     = {ind['macd']} ({ind['macd_label']})")
    print(f"    Volume Ratio = {ind['volume_ratio']}x ({ind['vol_label']})")

    hasil = analyze(
        rsi_val      = ind["rsi"],
        macd_raw     = ind["macd"],
        macd_series  = macd_series,
        volume_ratio = ind["volume_ratio"]
    )

    print(f"\n  Hasil Fuzzy Mamdani:")
    print(f"    MACD normalized = {hasil['macd_normalized']}")
    print(f"    Decision Score  = {hasil['score']}")
    print(f"    Rekomendasi     = {hasil['rekomendasi']}")

    print(f"\n  Detail Fuzzifikasi:")
    f = hasil["fuzzifikasi"]
    print(f"    RSI   → Oversold:{f['rsi']['oversold']} | "
          f"Neutral:{f['rsi']['neutral']} | "
          f"Overbought:{f['rsi']['overbought']}")
    print(f"    MACD  → Bearish:{f['macd']['bearish']} | "
          f"Sideways:{f['macd']['sideways']} | "
          f"Bullish:{f['macd']['bullish']}")
    print(f"    Vol   → Low:{f['volume']['low']} | "
          f"Average:{f['volume']['average']} | "
          f"High:{f['volume']['high']}")

    print(f"\n  Rules yang Aktif (alpha > 0.01):")
    if len(hasil["rules_aktif"]) == 0:
        print("    (tidak ada rule aktif yang signifikan)")
    for r in hasil["rules_aktif"]:
        print(f"    α={r['alpha']} | IF {r['rule']} → {r['output']}")


# ─────────────────────────────────────────────────────
# TEST 4: Analisis semua 8 saham
# ─────────────────────────────────────────────────────
print("\n\n[TEST 4] Analisis semua 8 saham")
print("-" * 65)
print(f"\n  {'Ticker':<8} {'RSI':>7} {'MACD_n':>8} {'Vol':>7} {'Score':>7}  Rekomendasi")
print("  " + "-" * 55)

for ticker in DAFTAR_SAHAM:
    r = get_stock_data(ticker)
    if r is None:
        print(f"  {ticker:<8} GAGAL")
        continue

    df  = r["df"]
    ind = hitung_semua_indikator(df)
    _, macd_data  = calculate_macd(df)
    macd_series = macd_data["histogram"]

    hasil = analyze(
        rsi_val      = ind["rsi"],
        macd_raw     = ind["macd"],
        macd_series  = macd_series,
        volume_ratio = ind["volume_ratio"]
    )

    print(f"  {ticker:<8} "
          f"{ind['rsi']:>7.2f} "
          f"{hasil['macd_normalized']:>8.4f} "
          f"{ind['volume_ratio']:>7.4f} "
          f"{hasil['score']:>7.2f}  "
          f"{hasil['rekomendasi']}")


# ─────────────────────────────────────────────────────
# HASIL AKHIR
# ─────────────────────────────────────────────────────
print("\n" + "=" * 65)
print("SEMUA TEST SELESAI! Cek hasil di atas.")
print("Kalau score keluar dan rekomendasi masuk akal →")
print("Part 3 selesai, lanjut ke Part 4: Flask API!")
print("=" * 65)