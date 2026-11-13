# Warsztat „Autonomiczne pojazdy sterowane AI”: materiały

Moduł 180 min (2 × 90). Plan i efekty uczenia się opisuje `../Opis_modulu_propozycja.md`.

## Zawartość

```
warsztat/
├── instrukcje/            ← DLA UCZESTNIKÓW: opisy ćwiczeń z tabelami do wypełnienia (do druku)
│   ├── 00_wprowadzenie.md     role w zespole, lista ćwiczeń, ćw. 0 (Jupyter)
│   ├── 01_lidar.md            ćw. 1  LiDAR: dokładność, materiały, kąt         (12 min)
│   ├── 02_kamera.md           ćw. 2  piksele, RGB, PNG/JPEG, rozdzielczość     (8 min)
│   ├── 03_odometria.md        ćw. 3  kwadrat 1×1 m, narastanie błędu           (15 min)
│   ├── 04_slam.md             ćw. 4  gmapping, eksperymenty A–F, zapis mapy    (40 min)
│   ├── 05_perceptron.md       ćw. 5  suwaki „hamuj/jedź”, uczenie              (10 min)
│   ├── 06_detektor.md         ćw. 6  COCO vs otwarty słownik, zapytania, zagadka (20 min)
│   ├── 07_nawigacja.md        ćw. 7  AMCL, cele A/B, przeszkoda, znajdź kaczkę (35 min)
│   ├── 08_karta_wynikow.md    karta do podsumowania i prezentacji              (20 min)
│   └── latex/                 zeszyt ćwiczeń do druku: zeszyt_cwiczen.tex + cw00–cw08.tex
│                              (cwNN.tex generuje _md_do_latex.py z plików .md; kompilacja pdflatex lub xelatex)
├── notatniki/             ← kod uruchamiany przez uczestników (stacja robocza zespołu)
│   ├── 00_start.ipynb … 07_nawigacja.ipynb   (GENEROWANE z _zbuduj_notatniki.py)
│   ├── _zbuduj_notatniki.py   generator notatników: poprawki wprowadzać tutaj
│   ├── konfiguracja.py        JEDYNE miejsce na IP robotów (`ROBOTY_IP`: numer z naklejki → IP), tematy ROS, polecenia launch (wszystko „SPRAWDZIĆ”)
│   ├── jetbot_warsztat.py     funkcje PL (LiDAR, kamera, ruch, SLAM, nawigacja, szukanie obiektu) + tryb demo
│   ├── detektor.py            YOLOv8n (COCO) i YOLOE (otwarty słownik, zapytania słowne) — na CPU
│   └── perceptron.py          ćw. 5, działa bez robota
├── prowadzacy/            ← DLA PROWADZĄCYCH
│   ├── scenariusz/            scenariusz_prowadzacego.tex → .pdf (harmonogram minuta po minucie, przygotowanie,
│   │                          odpowiedzi do pytań, plany awaryjne); budowa: ./zbuduj.sh (pdflatex, xelatex lub tectonic)
│   ├── prezentacja/           prezentacja.tex → .pdf (Beamer 16:9): mini-wykłady przed każdym ćwiczeniem + slajdy „Ćwiczenie N”;
│   │                          budowa: ./zbuduj.sh; obrazy/ z _przygotuj_obrazy.py (zdjęcia z Jetbota i wyniki detekcji)
│   ├── podglad_kamery.ipynb   podgląd na żywo z kamery robota + zapis zdjęć testowych (PNG + zdjecia.csv)
│   ├── podglad_kamery.py      kod podglądu; źródła: ROS / CSI (GStreamer na Jetbocie) / USB / demo; Python ≥3.6
│   ├── _zbuduj_podglad.py     generator notatnika
│   └── test_detektora.py      test gotowych detektorów na zdjęciach (CSV + obrazy z ramkami)
└── docker/                ← środowisko stacji: Dockerfile, docker-compose.yml, start.sh (bez parametrów),
                               jupyter_server_config.py (uczniowie widzą w Jupyterze tylko notatniki; pliki .py ukryte)
```

Notatniki mają tę samą numerację kroków co instrukcje. Uczestnicy zmieniają tylko linie `# ZMIEŃ TUTAJ`.

## Architektura (założenie)

- **Jetbot** (obraz Waveshare, ROS 1 Melodic): roscore, napęd, LiDAR, kamera, gmapping, move_base + AMCL. Każdy robot ma **własny roscore**.
- **Stacja robocza zespołu**: host z Dockerem (słabe GPU nie jest używane, detekcja na procesorze). Uczestnicy pracują w **kontenerze** `docker/` (Ubuntu 20.04, ROS Noetic bez GUI, Python 3.8): Jupyter i detektor YOLO. ROS na stacji jest potrzebny, bo notatnik łączy się z robotem przez `rospy`. **RViz nie jest używany**: mapę na żywo (mapa, robot, skan, cząstki AMCL, zaplanowana trasa, cel) rysuje notatnik (`panel_sterowania(podglad=True)`, `jedz_do()`, `podglad_mapy()`). Dzięki temu kontener nie potrzebuje X11 ani OpenGL. Wersję środowiska stacji wybieramy sami; robot zostaje na Melodic. Noetic i Melodic komunikują się bez problemu. Kontener działa w zwykłej sieci Dockera (bez `network_mode: host`), więc tak samo na Linuksie i na **Docker Desktop for Windows** (szczegóły niżej). Startuje **bez parametrów** (`./docker/start.sh` albo `docker\start.bat`). Robota wybiera się w notatniku: `wybierz_robota(N)` (numer z naklejki), adres IP albo `"demo"`. Wybór zapisuje się w `notatniki/.wybrany_robot` (na dysku stacji, przeżywa odtworzenie kontenera) i obowiązuje we wszystkich notatnikach stacji. Zmiana robota (np. zapasowy): `wybierz_robota(4)` i *Kernel → Restart*. `ROS_MASTER_URI` (robot) i `ROS_IP` (adres stacji w sieci robotów) notatnik ustawia sam przy `polacz()`. `ROS_IP` odczytuje z robota przez ssh (`$SSH_CLIENT`), bo kontener za NAT-em Dockera nie zna adresu hosta. Ręcznie: zmienna `WARSZTAT_ROS_IP`. Programy na robocie notatnik uruchamia przez **ssh** (login i hasło z `konfiguracja.py`, opcjonalnie klucz). Logi trafiają do `~/.warsztat_logi/`.
- Detektor działa w Pythonie 3 w procesie notatnika (omija problem Pythona 2.7 w Melodic). Robot dostaje tylko polecenia ruchu (`/cmd_vel`, cele `move_base`).
- **Obiekt do znalezienia** (ćw. 6–7): domyślnie czerwona gumowa kaczka. Jest za niska dla LiDAR-u, więc szukanie i dojazd odbywają się kamerą: obroty co `krok`°, potem dojazd z korektą kierunku do progu `dol_stop` (dolna krawędź ramki). Test 4 zdjęć z Jetbota: YOLOE-11s z zapytaniem „rubber duck” daje pewność 0,70–0,82 do ok. 1,5 m, z daleka (ponad 2 m) słabo; COCO-YOLO kaczki nie zna. Szczegóły: `../zdjecia_testowe/wyniki_testu/PODSUMOWANIE.md`.

## Logowanie na roboty (ssh)

Notatnik uruchamia programy na robotach przez ssh, domyślnie **loginem i hasłem** z `konfiguracja.py`
(`ROBOT_UZYTKOWNIK = "jetbot"`, `ROBOT_HASLO = "jetbot"`). Nic nie trzeba przygotowywać ani kopiować na stacje.
Hasło podaje ssh sam (`SSH_ASKPASS`, funkcja `_ssh_srodowisko()` w `jetbot_warsztat.py`), bez `sshpass` i bez pytania w terminalu.
Komunikat „Permission denied” w notatniku znaczy, że sieć działa, ale login lub hasło się nie zgadzają.

Opcjonalnie klucz ssh: jeśli w `docker/klucze_ssh/` leży klucz dopisany na robocie (`ssh-copy-id`), ssh użyje go przed hasłem.

## Stacje z Windowsem (Docker Desktop)

Kontener jest ten sam co na Linuksie. Raz na każdej stacji (z uprawnieniami administratora):

1. **Docker Desktop** z backendem WSL 2, kontenery linuksowe (domyślne ustawienia).
2. **Obraz**: zamiast budować go na każdej stacji (kilka GB, internet), zbudować raz i przenieść:
   `docker compose -f docker/docker-compose.yml build`, potem `docker save -o warsztat-jetbot.tar warsztat-jetbot:noetic`,
   a na stacji `docker load -i warsztat-jetbot.tar`.
3. **Zapora Windows**: robot musi móc połączyć się z notatnikiem na portach 11411–11430 (PowerShell jako administrator):
   `New-NetFirewallRule -DisplayName "Warsztat ROS" -Direction Inbound -Protocol TCP -LocalPort 11411-11430 -Action Allow -Profile Any`
   Bez tego notatnik **odbiera** dane z robota (skan, obraz), ale robot **nie reaguje** na polecenia ruchu i nawigacji.
   Jeśli przy pierwszym starcie Windows zapyta o dostęp dla Dockera, zezwolić także dla sieci publicznych.
4. Start: dwuklik `docker\start.bat` (uruchamia kontener i otwiera http://127.0.0.1:8888).

Szybki test łączności w notatniku: `wybierz_robota(N)`, `uruchom_robota()`, `status()` (odbiór), potem krótki `jedz()` (robot → stacja, czyli zapora).

## Tryb demonstracyjny (bez robota)

```
cd warsztat/notatniki && WARSZTAT_DEMO=1 jupyter lab
```
Symuluje LiDAR (pokój 3 × 2 m z przeszkodami), kamerę i odometrię z błędem kół. Notatniki **00, 01, 02, 03, 05, 06** wykonują się w nim w całości (sprawdzone automatycznie; 06 na obrazie syntetycznym). Ćwiczenia 04 i 07 wymagają robota. Logikę szukania i dojazdu sprawdzono na prawdziwych zdjęciach z symulowanymi ruchami. Tryb przydaje się do przećwiczenia zajęć i jako plan awaryjny, gdy robot zespołu nie działa.

## Do sprawdzenia na sprzęcie przed warsztatem

Wszystkie miejsca są oznaczone w `konfiguracja.py` komentarzem `SPRAWDZIĆ`:

1. Nazwy pakietu i plików launch Waveshare (`jetbot_pro jetbot.launch / lidar.launch / csi_camera.launch / navigation.launch`) i to, czy `navigation.launch` przyjmuje argument `map_file`.
2. Tematy: `/scan`, `/odom`, `/cmd_vel`, temat kamery i jego kodowanie (rgb8/bgr8).
3. Ramki TF: `base_footprint` czy `base_link`. Orientacja LiDAR-u (`LIDAR_KAT_PRZOD`, bywa 180°).
4. Czy na obrazie są `gmapping`, `map_server`, `amcl`, `move_base`, a także planer lokalny (DWA/TEB) i nazwy serwerów `dynamic_reconfigure`.
4a. Poziomy kąt widzenia kamery (`KAMERA_KAT_POZIOMY`, przyjęto 120°) i domyślne `dol_stop=0.90` (przy jakiej odległości robot staje przed kaczką).
5. Stacje: zbudować obraz `docker compose -f docker/docker-compose.yml build` (**z internetem, przed zajęciami**; wagi YOLO trafiają do obrazu), sprawdzić, czy `ultralytics==8.4.211` instaluje się na Pythonie 3.8, czy podgląd mapy odświeża się w trakcie `jedz_do()` (widżet aktualizowany z wątku), tematy `TEMAT_PLAN`/`TEMAT_CZASTKI` i ramka `RAMKA_ROBOTA` w `konfiguracja.py`, szybkość detekcji na procesorze stacji (`detektor.test_szybkosci`), logowanie ssh na roboty (`ROBOT_HASLO`), czy robot dociera do portów 11411–11430 stacji (zapora), synchronizacja czasu robot↔stacja (chrony) jest zalecana, ale nie krytyczna: notatnik wysyła wiadomości ze znacznikiem czasu 0 („najnowsze dane”).
6. Wi-Fi: przepustowość dla 3–5 strumieni kamery jednocześnie (ćw. 6–7).

## Przygotowanie sali (skrót; pełna wersja w `prowadzacy/scenariusz/scenariusz_prowadzacego.pdf`)

- **Przed zajęciami** uruchomić roboty (`uruchom_robota()`, ok. 1 min na robota), żeby nie tracić czasu na zajęciach.
- Tory z przeszkodami (zalecany jeden tor na dwa zespoły, które jeżdżą na zmianę). Na każdym torze punkt **S** (taśma, krzyżyk + linia kierunku), czyli początek układu współrzędnych map zespołów z tego toru, oraz punkty **A, B** z wypisanymi na tablicy współrzędnymi względem S. Przeszkody wyższe od płaszczyzny LiDAR-u.
- Gotowa mapa `tor_prowadzacy` na każdym robocie (plan awaryjny dla ćw. 7).
- Materiały do ćw. 1: miarka, karton, biała kartka, czarna matowa tkanina, plexi, lusterko, puszka, szablon kątów. Do ćw. 3: taśma malarska. Do ćw. 6–7: czerwona gumowa kaczka (po jednej na zespół + jedna do ukrycia), „obiekty-zagadki” do zapytań słownych (różne przedmioty, po jednym na zespół; warto je wcześniej sprawdzić notatnikiem `prowadzacy/podglad_kamery.ipynb` i `test_detektora.py`), krzesło, plecak, pudełka.
