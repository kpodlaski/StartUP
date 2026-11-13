"""
Konfiguracja warsztatu „Autonomiczne pojazdy sterowane AI”.

JEDYNE miejsce, w którym prowadzący wpisują dane zależne od sprzętu i obrazu systemu.
Notatniki uczestników niczego tu nie zmieniają — importują ten plik przez `jetbot_warsztat.py`.

Architektura (założenie):
  * Jetbot (Jetson Nano, obraz Waveshare, ROS 1 Melodic) — roscore, sterowniki napędu, LiDAR, kamera,
    gmapping, move_base + AMCL + map_server. Polecenia uruchamiane zdalnie przez ssh.
  * Stacja robocza zespołu — dowolny host z Dockerem i GPU; uczestnicy pracują w KONTENERZE
    (docker/Dockerfile: Ubuntu 20.04 + ROS Noetic + Python 3.8) — Jupyter i detektor YOLO (bez RViz: mapa na żywo w notatniku).
    ROS_MASTER_URI kontenera wskazuje na Jetbota danego zespołu (osobny roscore na zespół).
    Noetic (kontener) ↔ Melodic (robot) komunikują się bez problemu (ROS 1, zgodne wiadomości).

Wszystko oznaczone `SPRAWDZIĆ` to założenie do potwierdzenia na prawdziwym sprzęcie przed warsztatem.
"""
import os

# --------------------------------------------------------------------------------------------
# Tryb demonstracyjny — bez robota i bez ROS-a (symulowane: LiDAR, kamera, odometria).
# Służy do przećwiczenia notatników przez prowadzących i jako plan awaryjny, gdy robot nie działa.
# Można też włączyć zmienną środowiskową:  WARSZTAT_DEMO=1 jupyter lab
# --------------------------------------------------------------------------------------------
TRYB_DEMO = os.environ.get("WARSZTAT_DEMO", "0") == "1"

# --------------------------------------------------------------------------------------------
# Połączenie z robotem. Robota wybiera się W NOTATNIKU: `wybierz_robota(3)` (numer z naklejki na robocie)
# albo `wybierz_robota("192.168.1.105")` / `wybierz_robota("demo")`. Wybór zapisuje się w PLIK_WYBORU
# i obowiązuje we wszystkich notatnikach tej stacji, także po restarcie kernela. Kontener startuje bez parametrów.
# --------------------------------------------------------------------------------------------
# Adresy IP Jetbotów: numer na naklejce robota -> IP.                             SPRAWDZIĆ
ROBOTY_IP = {
    1: "192.168.1.101",
    2: "192.168.1.102",
    3: "192.168.1.103",
    4: "192.168.1.104",
    5: "192.168.1.105",
}
# Porty węzła ROS notatnika. Robot łączy się z notatnikiem (np. gdy notatnik publikuje /cmd_vel),
# więc porty są przekierowane z hosta do kontenera (docker-compose.yml) i otwarte w zaporze.
# Każdy otwarty notatnik (osobny kernel = osobny węzeł) bierze pierwszą wolną PARĘ z zakresu
# (XML-RPC, TCPROS) = (11411, 11412), (11413, 11414), … — do 10 notatników naraz na stacji.
# Dzięki temu kontener działa w zwykłej sieci Dockera — tak samo na Linuksie i na Docker Desktop (Windows).
PORTY_ROS = range(11411, 11431)        # 11411–11430; ten sam zakres w docker-compose.yml i w zaporze
# Plik z wyborem robota (IP albo „demo”) leży w katalogu notatników, czyli na dysku stacji (wolumen Dockera),
# więc przeżywa odtworzenie kontenera i restart komputera. Każda stacja ma własną kopię katalogu warsztatu.
PLIK_WYBORU = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".wybrany_robot")
ROBOT_IP = None                        # ustawiane przez jetbot_warsztat.wybierz_robota() / PLIK_WYBORU
ROBOT_UZYTKOWNIK = "jetbot"            # login ssh na Jetbocie                                  SPRAWDZIĆ
# Hasło ssh (domyślne na obrazie Waveshare). Gdy w kontenerze jest klucz ssh dopisany na robocie, używany jest klucz;
# hasło to droga zapasowa i domyślna. Roboty są w zamkniętej sieci warsztatu — hasło jawnie w pliku jest tu akceptowalne.
ROBOT_HASLO = "jetbot"                                                                          # SPRAWDZIĆ
ROBOT_KATALOG_MAP = "~/mapy"           # gdzie na robocie zapisujemy mapy z SLAM

# Polecenie przygotowujące środowisko ROS na robocie (wykonywane przed każdym poleceniem zdalnym).
ROBOT_SRODOWISKO = (
    "source /opt/ros/melodic/setup.bash && "
    "source ~/catkin_ws/devel/setup.bash && "                                     # SPRAWDZIĆ
    "export ROS_MASTER_URI=http://{ip}:11311 && export ROS_IP={ip}"     # {ip} wstawiane w chwili wywołania
)

# --------------------------------------------------------------------------------------------
# Polecenia uruchamiane na robocie (pakiet Waveshare: jetbot_pro — nazwy do potwierdzenia)
# --------------------------------------------------------------------------------------------
POLECENIA_ROBOTA = {
    "roscore":  "roscore",
    "naped":    "roslaunch jetbot_pro jetbot.launch",          # silniki + odometria /odom  SPRAWDZIĆ
    "lidar":    "roslaunch jetbot_pro lidar.launch",           # /scan                      SPRAWDZIĆ
    "kamera":   "roslaunch jetbot_pro csi_camera.launch",      # obraz z kamery CSI         SPRAWDZIĆ
    # Położenie LiDAR-u na robocie (TF base_footprint → laser_frame). Launch LiDAR-u Waveshare go NIE publikuje
    # (sprawdzone 2026-11-12: drzewo TF miało tylko odom → base_footprint → base_imu_link), a bez niego
    # nie działa SLAM ani rysowanie skanu na mapie. Argumenty: x y z yaw pitch roll rodzic dziecko.
    "tf_lidar": ("rosrun tf2_ros static_transform_publisher {x} {y} {z} {yaw} 0 0 {rodzic} {dziecko} "
                 "__name:=warsztat_tf_lidar"),
    # SLAM uruchamiamy bezpośrednio, żeby móc podawać parametry (gmapping nie ma dynamic_reconfigure).
    "slam": (
        "rosrun gmapping slam_gmapping scan:=/scan "
        "_base_frame:=base_footprint _odom_frame:=odom _map_frame:=map "        # SPRAWDZIĆ ramki
        "_delta:={rozdzielczosc} _maxUrange:={zasieg} _maxRange:={zasieg_max} "
        "_map_update_interval:={aktualizacja} _particles:={czastki}"
    ),
    "zapisz_mape": "mkdir -p {katalog} && rosrun map_server map_saver -f {katalog}/{nazwa}",
    "nawigacja": "roslaunch jetbot_pro navigation.launch map_file:={katalog}/{nazwa}.yaml",  # SPRAWDZIĆ
}

# Wzorce procesów do ubicia przy zatrzymywaniu (pkill -f) — działają także z innego kernela/notatnika
# niż ten, który program uruchomił. Ubicie roslaunch zamyka też jego węzły.
# naped/lidar/kamera: potrzebne, gdy program działa, ale nie daje danych (np. LiDAR włączony po starcie robota).
WZORCE_PROCESOW = {
    "naped": "jetbot_pro jetbot.launch",                       # SPRAWDZIĆ razem z POLECENIA_ROBOTA
    "lidar": "jetbot_pro lidar.launch",
    "kamera": "jetbot_pro csi_camera.launch",
    "slam": "slam_gmapping",
    "nawigacja": "move_base|amcl|map_server",
}

# --------------------------------------------------------------------------------------------
# Tematy ROS                                                                         SPRAWDZIĆ
# --------------------------------------------------------------------------------------------
TEMAT_SKAN = "/scan"
TEMAT_ODOMETRIA = "/odom"
TEMAT_PREDKOSC = "/cmd_vel"
TEMAT_KAMERA = "/csi_cam_0/image_raw"          # sensor_msgs/Image (rgb8 lub bgr8)
TEMAT_POZYCJA_STARTOWA = "/initialpose"
TEMAT_CZASTKI = "/particlecloud"               # geometry_msgs/PoseArray z AMCL (podgląd mapy)
TEMAT_PLAN = "/move_base/NavfnROS/plan"        # nav_msgs/Path; przy GlobalPlanner: /move_base/GlobalPlanner/plan
TEMAT_CEL = "/move_base/current_goal"          # geometry_msgs/PoseStamped
RAMKA_ROBOTA = "base_footprint"                # ramka TF robota (ta sama co _base_frame w poleceniu "slam")
AKCJA_NAWIGACJI = "move_base"

# Kąt (w stopniach) w ramce LiDAR-u, który odpowiada kierunkowi „na wprost robota”.
# Na części Jetbotów LiDAR jest zamontowany obrócony o 180°.
# Sprawdzone na robocie 2026-11-12: kąt 0 skanu wypada z TYŁU robota (po przeciwnej stronie niż kamera).
LIDAR_KAT_PRZOD = 180.0
RAMKA_LIDARU = "laser_frame"                    # frame_id w wiadomościach /scan (sprawdzone 2026-11-12)
LIDAR_POLOZENIE = (0.0, 0.0, 0.10)              # x (do przodu), y (w lewo), z (w górę) [m] względem base_footprint  SPRAWDZIĆ miarką

# Poziomy kąt widzenia kamery [°] — do zamiany położenia obiektu w obrazie na kąt obrotu.
# Kamera Jetbota jest szerokokątna (rybie oko); zdjęcia testowe sugerują ok. 120°.        SPRAWDZIĆ
KAMERA_KAT_POZIOMY = 120.0

# Serwery dynamic_reconfigure nawigacji (zależą od planera lokalnego w navigation.launch).  SPRAWDZIĆ
DR_PLANER_LOKALNY = "/move_base/DWAPlannerROS"
DR_INFLACJA = ["/move_base/global_costmap/inflation_layer", "/move_base/local_costmap/inflation_layer"]

# --------------------------------------------------------------------------------------------
# Bezpieczeństwo
# --------------------------------------------------------------------------------------------
MAKS_PREDKOSC_LINIOWA = 0.30    # m/s — twardy limit w funkcjach ruchu
MAKS_PREDKOSC_KATOWA = 2.0      # rad/s

# --------------------------------------------------------------------------------------------
# Detektor — działa na PROCESORZE stacji (słabe GPU), w tym samym procesie co notatnik.
# Wagi są wbudowane w obraz Dockera (docker/Dockerfile); poza kontenerem pobiorą się przy pierwszym użyciu.
# --------------------------------------------------------------------------------------------
DETEKTOR_MODELE = {
    "coco": "yolov8n.pt",           # zamknięta lista 80 klas COCO (do porównania)
    "maly": "yoloe-11s-seg.pt",     # otwarty słownik — klasy podawane słowami
    "sredni": "yoloe-11m-seg.pt",
    "duzy": "yoloe-11l-seg.pt",
}
DETEKTOR_SLOWA = ["rubber duck"]    # domyślnie szukany obiekt (test 2026-11-12: kaczka 0.70–0.82 przy 640 px)
DETEKTOR_KATALOG_WAG = os.environ.get("WARSZTAT_WAGI",
                                      os.path.join(os.path.dirname(os.path.abspath(__file__)), "wagi"))
