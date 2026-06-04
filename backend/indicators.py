# backend/indicators.py
# =====================================================
# Modul untuk menghitung indikator teknikal saham:
#   - RSI  (Relative Strength Index)
#   - MACD (Moving Average Convergence Divergence)
#   - Volume Ratio
# =====================================================

import numpy as np
import pandas as pd


# ─────────────────────────────────────────────────────
# FUNGSI 1: HITUNG RSI
# ─────────────────────────────────────────────────────

def calculate_rsi(df, period=14):
    """
    Hitung RSI (Relative Strength Index).

    CARA KERJA SINGKAT:
      1. Hitung perubahan harga tiap hari (naik/turun)
      2. Pisahkan: hari naik (gain) dan hari turun (loss)
      3. Hitung rata-rata gain dan rata-rata loss selama 14 hari
      4. RS  = rata_gain / rata_loss
      5. RSI = 100 - (100 / (1 + RS))

    Parameter:
      df     : DataFrame hasil dari data_fetcher.py
      period : periode RSI, default 14 hari

    Return:
      rsi_sekarang (float) : nilai RSI hari ini (0-100)
      rsi_semua   (Series) : nilai RSI semua hari (untuk grafik)
    """

    close = df["Close"].astype(float)

    # Hitung perubahan harga dari hari ke hari
    # Contoh: harga kemarin 9000, hari ini 9300 → delta = +300
    delta = close.diff()

    # Pisahkan kenaikan dan penurunan
    # gain: ambil nilai positif saja, turun → 0
    # loss: ambil nilai negatif saja (dijadikan positif), naik → 0
    gain = delta.clip(lower=0)   # clip bawah = 0 → yang negatif jadi 0
    loss = delta.clip(upper=0).abs()  # clip atas = 0 → yang positif jadi 0, abs biar positif

    # Hitung rata-rata gain dan loss menggunakan EMA (Exponential Moving Average)
    # ewm(com=period-1) adalah cara pandas menghitung Wilder's smoothing
    # Ini menghasilkan rata-rata yang memberikan bobot lebih besar ke data terbaru
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()

    # Hitung RS (Relative Strength)
    # Hindari pembagian dengan nol: kalau avg_loss = 0, RS = 100 (semua naik terus)
    rs = avg_gain / avg_loss.replace(0, np.nan)

    # Hitung RSI
    rsi_semua = 100 - (100 / (1 + rs))

    # Isi NaN dengan 50 (neutral) supaya tidak error
    rsi_semua = rsi_semua.fillna(50)

    # Ambil nilai RSI terbaru (hari ini)
    rsi_sekarang = round(float(rsi_semua.iloc[-1]), 2)

    return rsi_sekarang, rsi_semua


# ─────────────────────────────────────────────────────
# FUNGSI 2: HITUNG MACD
# ─────────────────────────────────────────────────────

def calculate_macd(df, fast=12, slow=26, signal=9):
    """
    Hitung MACD (Moving Average Convergence Divergence).

    CARA KERJA SINGKAT:
      1. Hitung EMA 12 hari (rata-rata bergerak cepat)
      2. Hitung EMA 26 hari (rata-rata bergerak lambat)
      3. MACD Line  = EMA12 - EMA26
      4. Signal Line = EMA 9 dari MACD Line
      5. Histogram  = MACD Line - Signal Line  ← ini yang kita pakai!

    Yang kita pakai sebagai INPUT fuzzy adalah nilai HISTOGRAM terbaru.
    Positif = bullish, Negatif = bearish, Mendekati 0 = sideways.

    Parameter:
      df     : DataFrame hasil dari data_fetcher.py
      fast   : periode EMA cepat, default 12
      slow   : periode EMA lambat, default 26
      signal : periode signal line, default 9

    Return:
      histogram_sekarang (float) : nilai histogram MACD hari ini
      macd_data (dict)           : semua komponen MACD untuk grafik
    """

    close = df["Close"].astype(float)

    # Hitung EMA (Exponential Moving Average)
    # span=12 artinya periode 12 hari
    # adjust=False artinya pakai rumus EMA standar (recursive)
    ema_fast = close.ewm(span=fast, adjust=False).mean()
    ema_slow = close.ewm(span=slow, adjust=False).mean()

    # MACD Line = selisih dua EMA
    macd_line = ema_fast - ema_slow

    # Signal Line = EMA dari MACD Line (dihaluskan lagi)
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()

    # Histogram = selisih MACD Line dan Signal Line
    # Positif  → MACD di atas Signal → momentum naik (bullish)
    # Negatif  → MACD di bawah Signal → momentum turun (bearish)
    histogram = macd_line - signal_line

    # Ambil nilai terbaru
    histogram_sekarang = round(float(histogram.iloc[-1]), 4)

    # Kumpulkan semua data untuk grafik
    macd_data = {
        "macd_line"    : macd_line,
        "signal_line"  : signal_line,
        "histogram"    : histogram,
        "histogram_now": histogram_sekarang,
    }

    return histogram_sekarang, macd_data


# ─────────────────────────────────────────────────────
# FUNGSI 3: HITUNG VOLUME RATIO
# ─────────────────────────────────────────────────────

def calculate_volume_ratio(df, period=20):
    """
    Hitung Volume Ratio.

    CARA KERJA SINGKAT:
      Volume Ratio = Volume Hari Ini / Rata-rata Volume 20 Hari

      Contoh:
        Volume hari ini  = 80 juta
        Rata-rata 20 hr  = 50 juta
        Volume Ratio     = 80/50 = 1.6x  → kategori HIGH

    Kenapa pakai Ratio, bukan nilai absolut?
      Supaya bisa dibandingkan antar saham yang berbeda.
      BBCA volume 50 juta bisa "biasa aja", tapi GOTO 50 juta
      mungkin sudah sangat ramai. Ratio menormalisasi ini.

    Parameter:
      df     : DataFrame hasil dari data_fetcher.py
      period : periode rata-rata, default 20 hari

    Return:
      ratio_sekarang (float) : volume ratio hari ini
      avg_volume     (float) : rata-rata volume 20 hari (untuk info)
    """

    volume = df["Volume"].astype(float)

    # Hapus hari dengan volume = 0 (hari libur / data kosong)
    # supaya tidak merusak perhitungan rata-rata
    volume_bersih = volume.replace(0, np.nan)

    # Hitung rata-rata volume 20 hari terakhir (rolling mean)
    # min_periods=1 artinya kalau data kurang dari 20, tetap hitung
    avg_volume_series = volume_bersih.rolling(window=period, min_periods=1).mean()

    # Ambil nilai terbaru
    volume_sekarang = float(volume_bersih.iloc[-1])
    avg_volume      = float(avg_volume_series.iloc[-1])

    # Kalau volume hari ini = 0 (hari libur), pakai hari sebelumnya
    if np.isnan(volume_sekarang) or volume_sekarang == 0:
        # Cari hari terakhir yang ada volume-nya
        volume_valid = volume_bersih.dropna()
        if len(volume_valid) > 0:
            volume_sekarang = float(volume_valid.iloc[-1])
        else:
            volume_sekarang = avg_volume  # fallback

    # Hitung ratio
    if avg_volume == 0 or np.isnan(avg_volume):
        ratio_sekarang = 1.0  # fallback ke average
    else:
        ratio_sekarang = volume_sekarang / avg_volume

    # Batasi maksimal 3.0 (supaya tidak melewati universe fuzzy)
    ratio_sekarang = min(round(ratio_sekarang, 4), 3.0)

    return ratio_sekarang, round(avg_volume, 0)


# ─────────────────────────────────────────────────────
# FUNGSI 4: HITUNG SEMUA SEKALIGUS (HELPER)
# ─────────────────────────────────────────────────────

def hitung_semua_indikator(df):
    """
    Fungsi helper yang menghitung RSI, MACD, dan Volume Ratio sekaligus.
    Ini yang nanti dipanggil oleh Flask app.py.

    Parameter:
      df : DataFrame hasil dari data_fetcher.py

    Return:
      dict berisi semua nilai indikator + data grafik
    """

    # Hitung semua indikator
    rsi_now, rsi_series         = calculate_rsi(df)
    macd_now, macd_data         = calculate_macd(df)
    vol_ratio, avg_vol          = calculate_volume_ratio(df)

    # Tentukan label kategori untuk tampilan
    rsi_label  = _label_rsi(rsi_now)
    macd_label = _label_macd(macd_now)
    vol_label  = _label_volume(vol_ratio)

    return {
        # Nilai indikator (untuk input fuzzy)
        "rsi"          : rsi_now,
        "macd"         : macd_now,
        "volume_ratio" : vol_ratio,

        # Label kategori (untuk tampilan web)
        "rsi_label"    : rsi_label,
        "macd_label"   : macd_label,
        "vol_label"    : vol_label,

        # Data series untuk grafik
        "rsi_series"   : rsi_series.tolist(),
        "macd_series"  : macd_data["histogram"].tolist(),
        "avg_volume"   : avg_vol,
    }


# ─────────────────────────────────────────────────────
# FUNGSI HELPER: LABEL KATEGORI
# ─────────────────────────────────────────────────────

def _label_rsi(rsi):
    """
    Konversi nilai RSI ke label kategori.
    Sesuai dengan membership function yang kita define.
    """
    if rsi < 30:
        return "Oversold"
    elif rsi > 70:
        return "Overbought"
    else:
        return "Neutral"


def _label_macd(macd):
    """
    Konversi nilai MACD histogram ke label kategori.
    Sesuai dengan membership function yang kita define.
    """
    if macd > 0.1:
        return "Bullish"
    elif macd < -0.1:
        return "Bearish"
    else:
        return "Sideways"


def _label_volume(ratio):
    """
    Konversi volume ratio ke label kategori.
    Sesuai dengan membership function yang kita define.
    """
    if ratio > 1.3:
        return "High"
    elif ratio < 0.7:
        return "Low"
    else:
        return "Average"