#!/usr/bin/env bash
# Start środowiska stacji (Linux).  Użycie:  ./docker/start.sh      (Windows: docker\start.bat)
# Uruchamia JupyterLab (http://127.0.0.1:8888) w tle. Bez parametrów: robota wybiera się w notatniku
# (`wybierz_robota(N)`, numer z naklejki; albo `wybierz_robota("demo")`), a adres stacji (ROS_IP)
# notatnik ustala sam przy połączeniu. Stacji nie trzeba więc „sprzęgać” z robotem przed startem kontenera.
# RViz nie jest używany: mapę na żywo rysuje notatnik (bez okien X11 i OpenGL).
set -euo pipefail
cd "$(dirname "$0")"
docker compose up -d
echo "Jupyter: http://127.0.0.1:8888"
