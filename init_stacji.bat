@echo off
setlocal EnableExtensions
rem ===========================================================================================
rem  Przygotowanie stacji do warsztatu (Windows + Docker Desktop) - jeden dwuklik, bez parametrow.
rem
rem  1. Materialy: pierwszy raz "git clone", na kolejnych warsztatach aktualizacja do wersji z repo.
rem     Zmiany uczniow z poprzednich zajec (notatniki itp.) trafiaja do "git stash" - nie gina,
rem     da sie je odzyskac (git stash list / git stash show -p). Pliki lokalne stacji wpisane
rem     w .gitignore (wybor robota notatniki\.wybrany_robot, klucze ssh) zostaja bez zmian.
rem  2. Obraz Dockera: budowany tylko, gdy go nie ma albo gdy zmienil sie katalog docker\.
rem  3. Start kontenera z JupyterLab (stary kontener jest zastepowany) i otwarcie przegladarki.
rem
rem  Git: jesli nie ma go w Windowsie, skrypt uzywa gita z obrazu alpine/git (przez Dockera).
rem  Bez internetu: aktualizacja jest pomijana, startuje wersja juz pobrana.
rem  Zapore Windows (porty 11411-11430) ustawia sie osobno, raz - patrz README.
rem
rem  Skrypt mozna trzymac gdziekolwiek (pulpit, pendrive). Plik jest tez w repozytorium -
rem  dlatego najpierw kopiuje sie do %TEMP% i dziala z kopii (aktualizacja moze go podmienic).
rem ===========================================================================================

rem ---- USTAWIENIA ---------------------------------------------------------------------------
set "REPO_URL=https://github.com/kpodlaski/StartUP.git"
set "GALAZ=main"
set "KATALOG=%USERPROFILE%\warsztat_jetbot"
set "OBRAZ=warsztat-jetbot:noetic"
rem -------------------------------------------------------------------------------------------

if /i not "%~1"=="--z-kopii" (
  copy /y "%~f0" "%TEMP%\warsztat_init_stacji.bat" >nul
  "%TEMP%\warsztat_init_stacji.bat" --z-kopii
)

echo.
echo === Przygotowanie stacji: %KATALOG%
echo.

docker info >nul 2>&1
if errorlevel 1 (
  echo [BLAD] Docker nie odpowiada. Uruchom Docker Desktop, poczekaj az wystartuje i sprobuj ponownie.
  goto blad
)

set "GIT_HOST="
where git >nul 2>&1
if not errorlevel 1 set "GIT_HOST=1"
if defined GIT_HOST (echo Git: zainstalowany w Windows) else (echo Git: brak w Windows - uzywam obrazu alpine/git)

set "BUDUJ="
set "PRZED=%TEMP%\warsztat_docker_przed.txt"
set "PO=%TEMP%\warsztat_docker_po.txt"
set "STAN=%TEMP%\warsztat_stan.txt"

if exist "%KATALOG%\.git" goto aktualizuj

rem ---- pierwszy raz: clone ----
if exist "%KATALOG%" (
  dir /b /a "%KATALOG%" | findstr . >nul
  if not errorlevel 1 (
    echo [BLAD] Katalog %KATALOG% istnieje, ale nie jest repozytorium git.
    echo        Zmien jego nazwe ^(np. na warsztat_stary^) albo ustaw inny KATALOG w tym pliku.
    goto blad
  )
)
mkdir "%KATALOG%" 2>nul
echo Pobieram materialy: %REPO_URL%
call :git clone -c core.autocrlf=false -b %GALAZ% %REPO_URL% .
if errorlevel 1 (
  echo [BLAD] git clone nie powiodl sie. Sprawdz internet i adres REPO_URL w tym pliku.
  goto blad
)
call :git config --replace-all core.fileMode false
set "BUDUJ=1"
goto docker

rem ---- kolejne warsztaty: aktualizacja ----
:aktualizuj
echo Aktualizuje materialy...
call :git config --replace-all core.autocrlf false
call :git config --replace-all core.fileMode false
call :git remote set-url origin %REPO_URL%
call :git fetch origin %GALAZ%
if errorlevel 1 (
  echo [UWAGA] Nie udalo sie pobrac zmian ^(brak internetu?^). Uruchamiam wersje juz pobrana.
  goto docker
)
call :git rev-parse HEAD:docker > "%PRZED%" 2>nul
call :git status --porcelain > "%STAN%"
for %%A in ("%STAN%") do if %%~zA GTR 0 (
  echo Zmiany z poprzednich zajec odkladam do "git stash" ^(do odzyskania^).
  call :git stash push --include-untracked -m "init_stacji %DATE% %TIME%"
)
call :git reset --hard origin/%GALAZ%
if errorlevel 1 (
  echo [BLAD] Nie udalo sie ustawic wersji z repozytorium.
  goto blad
)
call :git rev-parse HEAD:docker > "%PO%" 2>nul
fc "%PRZED%" "%PO%" >nul 2>&1
if errorlevel 1 (
  echo Katalog docker\ sie zmienil - obraz zostanie przebudowany.
  set "BUDUJ=1"
)

rem ---- obraz i kontener ----
:docker
docker image inspect %OBRAZ% >nul 2>&1
if errorlevel 1 set "BUDUJ=1"
if defined BUDUJ (
  echo Buduje obraz Dockera %OBRAZ% - za pierwszym razem to potrwa kilkanascie minut...
  docker compose -f "%KATALOG%\docker\docker-compose.yml" build
  if errorlevel 1 (
    echo [BLAD] Budowa obrazu nie powiodla sie.
    goto blad
  )
)
echo Uruchamiam kontener...
docker compose -f "%KATALOG%\docker\docker-compose.yml" up -d --force-recreate
if errorlevel 1 (
  echo [BLAD] Nie udalo sie uruchomic kontenera.
  goto blad
)
echo.
echo === Gotowe. Jupyter: http://127.0.0.1:8888
echo     Robota wybiera prowadzacy w notatniku 00: wybierz_robota(N)
timeout /t 5 >nul
start "" http://127.0.0.1:8888
timeout /t 10
exit /b

:blad
echo.
pause
exit /b

rem ---- git: z Windows albo z obrazu alpine/git; zawsze w katalogu KATALOG ----
rem Tozsamosc podana tylko dla "git stash" (stacja nie ma skonfigurowanego user.name/email).
:git
if defined GIT_HOST (
  git -C "%KATALOG%" -c safe.directory=* -c user.name=stacja -c user.email=stacja@warsztat %*
) else (
  docker run --rm -v "%KATALOG%:/repo" -w /repo alpine/git -c safe.directory=* -c user.name=stacja -c user.email=stacja@warsztat %*
)
exit /b %errorlevel%
