@echo off
rem Start srodowiska stacji (Windows, Docker Desktop). Bez parametrow.
rem Robota wybiera sie w notatniku: wybierz_robota(N). Obraz musi byc wczesniej zbudowany albo wczytany
rem (docker load -i warsztat-jetbot.tar), patrz README.
cd /d "%~dp0"
docker compose up -d
if errorlevel 1 (
  echo Nie udalo sie uruchomic kontenera. Czy Docker Desktop jest wlaczony?
  pause
  exit /b 1
)
echo Jupyter: http://127.0.0.1:8888
start "" http://127.0.0.1:8888
