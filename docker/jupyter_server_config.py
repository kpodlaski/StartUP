# Konfiguracja serwera Jupyter dla uczniów (wczytywana w docker-compose.yml: --config=…).
# Przeglądarka plików pokazuje tylko notatniki ćwiczeń. Pliki .py (jetbot_warsztat, konfiguracja z hasłem robota,
# generatory) i pliki techniczne są ukryte, ale notatniki nadal je importują. Pliki z kropką (.wybrany_robot,
# .ipynb_checkpoints) Jupyter ukrywa domyślnie.
ukryte = ["*.py", "__pycache__", "*.pyc", "*.pyo", "*~", "wagi"]
c.ContentsManager.hide_globs = ukryte
c.FileContentsManager.hide_globs = ukryte
