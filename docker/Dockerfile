# Środowisko uczestnika warsztatu „Autonomiczne pojazdy sterowane AI” (stacja robocza zespołu).
#
# Robot (Jetbot) zostaje na swoim obrazie: Ubuntu 18.04 + ROS Melodic.
# Ten kontener: Ubuntu 20.04 + ROS Noetic (Python 3.8, bez GUI) + JupyterLab + detektory na PROCESORZE
# (stacje mają słabe GPU): YOLOv8n (COCO, 80 klas) i YOLOE-11 s/m/l (otwarty słownik — klasy podawane słowami).
# Noetic ↔ Melodic: wspólny protokół ROS 1, zgodne standardowe wiadomości (sensor_msgs, nav_msgs, move_base_msgs).
#
# Budowa (potrzebny internet — pobiera wagi i koder tekstu, żeby na sali internet NIE był potrzebny):
#   docker compose -f docker/docker-compose.yml build
# Bez RViz i bez okien: mapa na żywo jest rysowana w notatniku (jetbot_warsztat._Podglad),
# więc wystarcza obraz ros-base (rospy, wiadomości, actionlib) — bez X11, OpenGL i sterowników GPU.
FROM ros:noetic-ros-base

ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3-pip git openssh-client iputils-ping libgl1 \
        ros-noetic-move-base-msgs ros-noetic-actionlib ros-noetic-dynamic-reconfigure \
        ros-noetic-tf2-ros \
    && rm -rf /var/lib/apt/lists/*

# PyTorch w wersji CPU (bez CUDA — obraz kilka GB mniejszy). Ostatnia linia wspierająca Pythona 3.8 to 2.4.x.
RUN pip3 install --no-cache-dir torch==2.4.1 torchvision==0.19.1 --index-url https://download.pytorch.org/whl/cpu
# ultralytics 8.4.211 — wersja, na której przetestowano detekcję kaczki (2026-11-12, na Pythonie 3.11).  SPRAWDZIĆ na 3.8
# ROS z apt przynosi python3-dateutil 2.7.3 (zależność catkin_pkg), a jupyter-client wymaga >=2.8.2.
# Stary pip z Ubuntu 20.04 sam tego nie podbija → instalujemy nowszą wersję do /usr/local (--ignore-installed:
# bez odinstalowywania pakietu apt; /usr/local jest wcześniej na sys.path, więc wygrywa nowsza).
RUN pip3 install --no-cache-dir --ignore-installed "python-dateutil>=2.8.2"
# CLIP (tokenizer dla koderów tekstu YOLOE) instalujemy jawnie: ultralytics doinstalowuje go sam przez git
# dopiero przy pierwszym użyciu, a na sali nie ma internetu. Wymaga gita (jest w apt powyżej).
RUN pip3 install --no-cache-dir "ultralytics==8.4.211" opencv-python-headless jupyterlab ipywidgets matplotlib pillow \
        "git+https://github.com/ultralytics/CLIP.git" && \
    python3 -c "import dateutil, jupyter_client, rospkg, catkin_pkg, clip; print('dateutil', dateutil.__version__)"

# Żadnych doinstalowań „w locie”: brakująca zależność ma przerwać budowę obrazu (a na sali — dać jasny błąd),
# zamiast próbować pobierać pakiety z internetu.
ENV YOLO_AUTOINSTALL=false

# Wagi i koder tekstu (mobileclip) wbudowane w obraz; ultralytics szuka ich w weights_dir (ustawienia poniżej).
ENV YOLO_CONFIG_DIR=/opt/ultralytics_cfg WARSZTAT_WAGI=/opt/wagi
RUN mkdir -p /opt/wagi /opt/ultralytics_cfg && cd /opt/wagi && \
    yolo settings weights_dir=/opt/wagi sync=False && \
    python3 -c "from ultralytics import YOLO, YOLOE; YOLO('yolov8n.pt'); \
[ (lambda m: m.set_classes(['rubber duck'], m.get_text_pe(['rubber duck'])))(YOLOE(f)) \
  for f in ('yoloe-11s-seg.pt','yoloe-11m-seg.pt','yoloe-11l-seg.pt') ]" && \
    ls -la /opt/wagi && chmod -R a+rwX /opt/wagi /opt/ultralytics_cfg

# Użytkownik bez uprawnień roota; katalog warsztatu montowany jako wolumen.
RUN useradd -m -s /bin/bash uczestnik && echo "source /opt/ros/noetic/setup.bash" >> /home/uczestnik/.bashrc
USER uczestnik
WORKDIR /home/uczestnik/warsztat/notatniki

# Polecenie startowe (kopiowanie kluczy ssh + JupyterLab) jest w docker-compose.yml (`command:`), a nie tutaj:
# jego zmiana nie wymaga wtedy przebudowy obrazu. Ten CMD to tylko zapas przy `docker run` bez compose.
CMD ["bash", "-lc", "source /opt/ros/noetic/setup.bash && exec jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --ServerApp.token='' --ServerApp.password=''"]
