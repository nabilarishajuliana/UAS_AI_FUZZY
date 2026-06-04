import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# backend/fuzzy_engine.py
# =====================================================
# INTI SISTEM: Fuzzy Logic Engine - Metode Mamdani
#
# Alur:
#   1. Setup membership function (sekali saat import)
#   2. normalize_macd()  → normalisasi nilai MACD
#   3. analyze()         → proses fuzzy & return hasil
#   4. get_label()       → konversi score ke label
#   5. get_rules_aktif() → cari rules yang aktif
# =====================================================

import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl


# ═══════════════════════════════════════════════════════
# BAGIAN 1: SETUP UNIVERSE OF DISCOURSE
# ═══════════════════════════════════════════════════════

rsi_universe    = np.arange(0, 100.5, 0.5)
macd_universe   = np.arange(-2, 2.01, 0.01)
volume_universe = np.arange(0, 3.01, 0.01)
output_universe = np.arange(0, 100.5, 0.5)


# ═══════════════════════════════════════════════════════
# BAGIAN 2: BUAT ANTECEDENT & CONSEQUENT
# ═══════════════════════════════════════════════════════

rsi_var    = ctrl.Antecedent(rsi_universe,    'rsi')
macd_var   = ctrl.Antecedent(macd_universe,   'macd')
volume_var = ctrl.Antecedent(volume_universe, 'volume')
output_var = ctrl.Consequent(output_universe, 'output')


# ═══════════════════════════════════════════════════════
# BAGIAN 3: MEMBERSHIP FUNCTIONS
# ═══════════════════════════════════════════════════════

# ── RSI ──────────────────────────────────────────────
rsi_var['oversold']   = fuzz.trapmf(rsi_universe, [0, 0, 20, 35])
rsi_var['neutral']    = fuzz.trimf(rsi_universe,  [20, 50, 80])
rsi_var['overbought'] = fuzz.trapmf(rsi_universe, [65, 80, 100, 100])

# ── MACD ─────────────────────────────────────────────
macd_var['bearish']  = fuzz.trapmf(macd_universe, [-2, -2, -0.2, 0.1])
macd_var['sideways'] = fuzz.trimf(macd_universe,  [-0.3, 0, 0.3])
macd_var['bullish']  = fuzz.trapmf(macd_universe, [-0.1, 0.2, 2, 2])

# ── Volume ───────────────────────────────────────────
volume_var['low']     = fuzz.trapmf(volume_universe, [0, 0, 0.5, 0.8])
volume_var['average'] = fuzz.trimf(volume_universe,  [0.6, 1.0, 1.4])
volume_var['high']    = fuzz.trapmf(volume_universe, [1.2, 1.5, 3, 3])

# ── Output ───────────────────────────────────────────
output_var['strong_sell'] = fuzz.trapmf(output_universe, [0, 0, 15, 30])
output_var['sell']        = fuzz.trimf(output_universe,  [20, 32, 45])
output_var['hold']        = fuzz.trimf(output_universe,  [38, 50, 62])
output_var['buy']         = fuzz.trimf(output_universe,  [55, 68, 80])
output_var['strong_buy']  = fuzz.trapmf(output_universe, [70, 85, 100, 100])


# ═══════════════════════════════════════════════════════
# BAGIAN 4: 27 FUZZY RULES (LENGKAP)
# 3 RSI × 3 MACD × 3 Volume = 27 kombinasi
# ═══════════════════════════════════════════════════════

rules = [

    # ── OVERSOLD + BULLISH ────────────────────────────
    ctrl.Rule(rsi_var['oversold'] & macd_var['bullish'] & volume_var['high'],
              output_var['strong_buy']),      # 1

    ctrl.Rule(rsi_var['oversold'] & macd_var['bullish'] & volume_var['average'],
              output_var['buy']),             # 2

    ctrl.Rule(rsi_var['oversold'] & macd_var['bullish'] & volume_var['low'],
              output_var['buy']),             # 3

    # ── OVERSOLD + SIDEWAYS ───────────────────────────
    ctrl.Rule(rsi_var['oversold'] & macd_var['sideways'] & volume_var['high'],
              output_var['buy']),             # 4

    ctrl.Rule(rsi_var['oversold'] & macd_var['sideways'] & volume_var['average'],
              output_var['hold']),            # 5

    ctrl.Rule(rsi_var['oversold'] & macd_var['sideways'] & volume_var['low'],
              output_var['hold']),            # 6

    # ── OVERSOLD + BEARISH ────────────────────────────
    # RSI oversold tapi MACD bearish = sinyal konflik → Hold
    ctrl.Rule(rsi_var['oversold'] & macd_var['bearish'] & volume_var['high'],
              output_var['hold']),            # 7

    ctrl.Rule(rsi_var['oversold'] & macd_var['bearish'] & volume_var['average'],
              output_var['hold']),            # 8

    ctrl.Rule(rsi_var['oversold'] & macd_var['bearish'] & volume_var['low'],
              output_var['hold']),            # 9

    # ── NEUTRAL + BULLISH ─────────────────────────────
    ctrl.Rule(rsi_var['neutral'] & macd_var['bullish'] & volume_var['high'],
              output_var['buy']),             # 10

    ctrl.Rule(rsi_var['neutral'] & macd_var['bullish'] & volume_var['average'],
              output_var['buy']),             # 11

    ctrl.Rule(rsi_var['neutral'] & macd_var['bullish'] & volume_var['low'],
              output_var['hold']),            # 12

    # ── NEUTRAL + SIDEWAYS ────────────────────────────
    ctrl.Rule(rsi_var['neutral'] & macd_var['sideways'] & volume_var['high'],
              output_var['hold']),            # 13

    ctrl.Rule(rsi_var['neutral'] & macd_var['sideways'] & volume_var['average'],
              output_var['hold']),            # 14

    ctrl.Rule(rsi_var['neutral'] & macd_var['sideways'] & volume_var['low'],
              output_var['hold']),            # 15

    # ── NEUTRAL + BEARISH ─────────────────────────────
    ctrl.Rule(rsi_var['neutral'] & macd_var['bearish'] & volume_var['high'],
              output_var['sell']),            # 16

    ctrl.Rule(rsi_var['neutral'] & macd_var['bearish'] & volume_var['average'],
              output_var['sell']),            # 17

    ctrl.Rule(rsi_var['neutral'] & macd_var['bearish'] & volume_var['low'],
              output_var['sell']),            # 18

    # ── OVERBOUGHT + BULLISH ──────────────────────────
    # RSI overbought tapi MACD bullish = sinyal konflik → Hold
    ctrl.Rule(rsi_var['overbought'] & macd_var['bullish'] & volume_var['high'],
              output_var['hold']),            # 19

    ctrl.Rule(rsi_var['overbought'] & macd_var['bullish'] & volume_var['average'],
              output_var['hold']),            # 20

    ctrl.Rule(rsi_var['overbought'] & macd_var['bullish'] & volume_var['low'],
              output_var['hold']),            # 21

    # ── OVERBOUGHT + SIDEWAYS ─────────────────────────
    ctrl.Rule(rsi_var['overbought'] & macd_var['sideways'] & volume_var['high'],
              output_var['sell']),            # 22

    ctrl.Rule(rsi_var['overbought'] & macd_var['sideways'] & volume_var['average'],
              output_var['sell']),            # 23

    ctrl.Rule(rsi_var['overbought'] & macd_var['sideways'] & volume_var['low'],
              output_var['sell']),            # 24

    # ── OVERBOUGHT + BEARISH ──────────────────────────
    ctrl.Rule(rsi_var['overbought'] & macd_var['bearish'] & volume_var['high'],
              output_var['strong_sell']),     # 25

    ctrl.Rule(rsi_var['overbought'] & macd_var['bearish'] & volume_var['average'],
              output_var['strong_sell']),     # 26

    ctrl.Rule(rsi_var['overbought'] & macd_var['bearish'] & volume_var['low'],
              output_var['sell']),            # 27
]


# ═══════════════════════════════════════════════════════
# BAGIAN 5: BUAT CONTROL SYSTEM
# ═══════════════════════════════════════════════════════

fuzzy_ctrl = ctrl.ControlSystem(rules)


# ═══════════════════════════════════════════════════════
# BAGIAN 6: FUNGSI NORMALIZE MACD
# ═══════════════════════════════════════════════════════

def normalize_macd(macd_raw, macd_series):
    abs_values = macd_series.abs().dropna()

    if len(abs_values) == 0 or abs_values.max() == 0:
        return 0.0

    normalizer = abs_values.quantile(0.95)

    if normalizer == 0:
        normalizer = abs_values.max()

    if normalizer == 0:
        return 0.0

    macd_norm = (macd_raw / normalizer) * 2
    macd_norm = float(np.clip(macd_norm, -2.0, 2.0))

    return round(macd_norm, 4)


# ═══════════════════════════════════════════════════════
# BAGIAN 7: FUNGSI ANALYZE (FUNGSI UTAMA)
# ═══════════════════════════════════════════════════════

def analyze(rsi_val, macd_raw, macd_series, volume_ratio):

    # Step 1: Normalisasi input
    rsi_input    = float(np.clip(rsi_val, 0, 100))
    macd_input   = normalize_macd(macd_raw, macd_series)
    volume_input = float(np.clip(volume_ratio, 0, 3))

    # Step 2: Buat simulasi baru
    simulasi = ctrl.ControlSystemSimulation(fuzzy_ctrl)

    # Step 3: Masukkan nilai input
    simulasi.input['rsi']    = rsi_input
    simulasi.input['macd']   = macd_input
    simulasi.input['volume'] = volume_input

    # Step 4: Jalankan fuzzy engine
    try:
        simulasi.compute()
        score = float(simulasi.output['output'])
        score = round(score, 2)
    except Exception as e:
        print(f"  WARNING fuzzy compute error: {e}")
        score = 50.0

    # Step 5: Petakan ke label
    rekomendasi = get_label(score)

    # Step 6: Hitung fuzzifikasi
    fuzzifikasi = hitung_fuzzifikasi(rsi_input, macd_input, volume_input)

    # Step 7: Cari rules aktif
    rules_aktif = get_rules_aktif(fuzzifikasi)

    return {
        "score"          : score,
        "rekomendasi"    : rekomendasi,
        "rsi_input"      : rsi_input,
        "macd_raw"       : macd_raw,
        "macd_normalized": macd_input,
        "volume_input"   : volume_input,
        "fuzzifikasi"    : fuzzifikasi,
        "rules_aktif"    : rules_aktif,
    }


# ═══════════════════════════════════════════════════════
# BAGIAN 8: FUNGSI GET_LABEL
# ═══════════════════════════════════════════════════════

def get_label(score):
    if score <= 30:
        return "Strong Sell"
    elif score <= 45:
        return "Sell"
    elif score <= 55:
        return "Hold"
    elif score <= 75:
        return "Buy"
    else:
        return "Strong Buy"


# ═══════════════════════════════════════════════════════
# BAGIAN 9: FUNGSI HITUNG FUZZIFIKASI
# ═══════════════════════════════════════════════════════

def hitung_fuzzifikasi(rsi_input, macd_input, volume_input):

    # RSI
    rsi_idx        = np.argmin(np.abs(rsi_universe - rsi_input))
    rsi_oversold   = round(float(fuzz.trapmf(rsi_universe, [0, 0, 20, 35])[rsi_idx]), 3)
    rsi_neutral    = round(float(fuzz.trimf(rsi_universe,  [20, 50, 80])[rsi_idx]), 3)
    rsi_overbought = round(float(fuzz.trapmf(rsi_universe, [65, 80, 100, 100])[rsi_idx]), 3)

    # MACD
    macd_idx      = np.argmin(np.abs(macd_universe - macd_input))
    macd_bearish  = round(float(fuzz.trapmf(macd_universe, [-2, -2, -0.2, 0.1])[macd_idx]), 3)
    macd_sideways = round(float(fuzz.trimf(macd_universe,  [-0.3, 0, 0.3])[macd_idx]), 3)
    macd_bullish  = round(float(fuzz.trapmf(macd_universe, [-0.1, 0.2, 2, 2])[macd_idx]), 3)

    # Volume
    vol_idx     = np.argmin(np.abs(volume_universe - volume_input))
    vol_low     = round(float(fuzz.trapmf(volume_universe, [0, 0, 0.5, 0.8])[vol_idx]), 3)
    vol_average = round(float(fuzz.trimf(volume_universe,  [0.6, 1.0, 1.4])[vol_idx]), 3)
    vol_high    = round(float(fuzz.trapmf(volume_universe, [1.2, 1.5, 3, 3])[vol_idx]), 3)

    return {
        "rsi"   : {"oversold": rsi_oversold, "neutral": rsi_neutral, "overbought": rsi_overbought},
        "macd"  : {"bearish": macd_bearish, "sideways": macd_sideways, "bullish": macd_bullish},
        "volume": {"low": vol_low, "average": vol_average, "high": vol_high},
    }


# ═══════════════════════════════════════════════════════
# BAGIAN 10: FUNGSI GET_RULES_AKTIF (27 RULES LENGKAP)
# ═══════════════════════════════════════════════════════

def get_rules_aktif(fuzzifikasi):

    rsi  = fuzzifikasi["rsi"]
    macd = fuzzifikasi["macd"]
    vol  = fuzzifikasi["volume"]

    # 27 rules — sama persis urutan dengan BAGIAN 4
    semua_rules = [
        # OVERSOLD + BULLISH
        ("RSI=Oversold AND MACD=Bullish AND Vol=High",
         [rsi["oversold"], macd["bullish"],  vol["high"]],    "Strong Buy"),   # 1
        ("RSI=Oversold AND MACD=Bullish AND Vol=Average",
         [rsi["oversold"], macd["bullish"],  vol["average"]], "Buy"),           # 2
        ("RSI=Oversold AND MACD=Bullish AND Vol=Low",
         [rsi["oversold"], macd["bullish"],  vol["low"]],     "Buy"),           # 3

        # OVERSOLD + SIDEWAYS
        ("RSI=Oversold AND MACD=Sideways AND Vol=High",
         [rsi["oversold"], macd["sideways"], vol["high"]],    "Buy"),           # 4
        ("RSI=Oversold AND MACD=Sideways AND Vol=Average",
         [rsi["oversold"], macd["sideways"], vol["average"]], "Hold"),          # 5
        ("RSI=Oversold AND MACD=Sideways AND Vol=Low",
         [rsi["oversold"], macd["sideways"], vol["low"]],     "Hold"),          # 6

        # OVERSOLD + BEARISH
        ("RSI=Oversold AND MACD=Bearish AND Vol=High",
         [rsi["oversold"], macd["bearish"],  vol["high"]],    "Hold"),          # 7
        ("RSI=Oversold AND MACD=Bearish AND Vol=Average",
         [rsi["oversold"], macd["bearish"],  vol["average"]], "Hold"),          # 8
        ("RSI=Oversold AND MACD=Bearish AND Vol=Low",
         [rsi["oversold"], macd["bearish"],  vol["low"]],     "Hold"),          # 9

        # NEUTRAL + BULLISH
        ("RSI=Neutral AND MACD=Bullish AND Vol=High",
         [rsi["neutral"],  macd["bullish"],  vol["high"]],    "Buy"),           # 10
        ("RSI=Neutral AND MACD=Bullish AND Vol=Average",
         [rsi["neutral"],  macd["bullish"],  vol["average"]], "Buy"),           # 11
        ("RSI=Neutral AND MACD=Bullish AND Vol=Low",
         [rsi["neutral"],  macd["bullish"],  vol["low"]],     "Hold"),          # 12

        # NEUTRAL + SIDEWAYS
        ("RSI=Neutral AND MACD=Sideways AND Vol=High",
         [rsi["neutral"],  macd["sideways"], vol["high"]],    "Hold"),          # 13
        ("RSI=Neutral AND MACD=Sideways AND Vol=Average",
         [rsi["neutral"],  macd["sideways"], vol["average"]], "Hold"),          # 14
        ("RSI=Neutral AND MACD=Sideways AND Vol=Low",
         [rsi["neutral"],  macd["sideways"], vol["low"]],     "Hold"),          # 15

        # NEUTRAL + BEARISH
        ("RSI=Neutral AND MACD=Bearish AND Vol=High",
         [rsi["neutral"],  macd["bearish"],  vol["high"]],    "Sell"),          # 16
        ("RSI=Neutral AND MACD=Bearish AND Vol=Average",
         [rsi["neutral"],  macd["bearish"],  vol["average"]], "Sell"),          # 17
        ("RSI=Neutral AND MACD=Bearish AND Vol=Low",
         [rsi["neutral"],  macd["bearish"],  vol["low"]],     "Sell"),          # 18

        # OVERBOUGHT + BULLISH
        ("RSI=Overbought AND MACD=Bullish AND Vol=High",
         [rsi["overbought"], macd["bullish"],  vol["high"]],    "Hold"),        # 19
        ("RSI=Overbought AND MACD=Bullish AND Vol=Average",
         [rsi["overbought"], macd["bullish"],  vol["average"]], "Hold"),        # 20
        ("RSI=Overbought AND MACD=Bullish AND Vol=Low",
         [rsi["overbought"], macd["bullish"],  vol["low"]],     "Hold"),        # 21

        # OVERBOUGHT + SIDEWAYS
        ("RSI=Overbought AND MACD=Sideways AND Vol=High",
         [rsi["overbought"], macd["sideways"], vol["high"]],    "Sell"),        # 22
        ("RSI=Overbought AND MACD=Sideways AND Vol=Average",
         [rsi["overbought"], macd["sideways"], vol["average"]], "Sell"),        # 23
        ("RSI=Overbought AND MACD=Sideways AND Vol=Low",
         [rsi["overbought"], macd["sideways"], vol["low"]],     "Sell"),        # 24

        # OVERBOUGHT + BEARISH
        ("RSI=Overbought AND MACD=Bearish AND Vol=High",
         [rsi["overbought"], macd["bearish"],  vol["high"]],    "Strong Sell"), # 25
        ("RSI=Overbought AND MACD=Bearish AND Vol=Average",
         [rsi["overbought"], macd["bearish"],  vol["average"]], "Strong Sell"), # 26
        ("RSI=Overbought AND MACD=Bearish AND Vol=Low",
         [rsi["overbought"], macd["bearish"],  vol["low"]],     "Sell"),        # 27
    ]

    # Hitung alpha & filter yang aktif
    aktif = []
    for deskripsi, derajat_list, output_label in semua_rules:
        alpha = round(min(derajat_list), 3)
        if alpha > 0.01:
            aktif.append({
                "rule"  : deskripsi,
                "alpha" : alpha,
                "output": output_label,
            })

    # Urutkan dari alpha terbesar
    aktif.sort(key=lambda x: x["alpha"], reverse=True)

    return aktif