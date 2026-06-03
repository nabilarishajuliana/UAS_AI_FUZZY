# test_install.py
# Jalankan file ini untuk memastikan semua library berhasil diinstall

print("Testing instalasi library...")

try:
    import flask
    print("✓ Flask:", flask.__version__)
except ImportError:
    print("✗ Flask GAGAL - jalankan: pip install flask")

try:
    import yfinance
    print("✓ yfinance:", yfinance.__version__)
except ImportError:
    print("✗ yfinance GAGAL - jalankan: pip install yfinance")

try:
    import skfuzzy
    print("✓ scikit-fuzzy:", skfuzzy.__version__)
except ImportError:
    print("✗ scikit-fuzzy GAGAL - jalankan: pip install scikit-fuzzy")

try:
    import pandas
    print("✓ pandas:", pandas.__version__)
except ImportError:
    print("✗ pandas GAGAL - jalankan: pip install pandas")

try:
    import numpy
    print("✓ numpy:", numpy.__version__)
except ImportError:
    print("✗ numpy GAGAL - jalankan: pip install numpy")

try:
    import flask_cors
    print("✓ flask-cors: OK")
except ImportError:
    print("✗ flask-cors GAGAL - jalankan: pip install flask-cors")

print("\nSelesai! Kalau semua centang (✓), lanjut ke Part 1.")