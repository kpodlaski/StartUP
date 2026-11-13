"""
jetbot_warsztat — proste funkcje do sterowania Jetbotem z notatników Jupyter.

Uczestnicy warsztatu NIE muszą czytać tego pliku. Notatniki wywołują tylko funkcje o polskich nazwach,
np. `pobierz_skan()`, `jedz_prosto(1.0)`, `uruchom_slam()`, `jedz_do(1.2, 0.5)`.

Co tu jest:
  * połączenie z ROS-em i zdalne uruchamianie programów na robocie (ssh),
  * LiDAR: pobieranie skanu, pomiar odległości w zadanym kierunku, wykres,
  * kamera: zdjęcie, kanały RGB, piksele, porównanie kompresji JPEG/PNG,
  * ruch: jazda, obroty, odometria, panel sterowania przyciskami,
  * SLAM (gmapping): start z parametrami, podgląd i zapis mapy,
  * podgląd mapy na żywo w notatniku (zamiast RViz): mapa, robot, skan, cząstki AMCL, trasa,
  * nawigacja (move_base + AMCL): pozycja startowa, jazda do celu, parametry,
  * szukanie obiektu kamerą + detektorem: rozglądanie się, dojazd sterowany obrazem, patrol po punktach mapy.

Wybór robota: `wybierz_robota(N)` w notatniku (zapamiętywany w konfiguracja.PLIK_WYBORU), bez parametrów kontenera.

Tryb demonstracyjny (`wybierz_robota("demo")` lub WARSZTAT_DEMO=1) symuluje LiDAR, kamerę i odometrię
w prostokątnym pokoju z przeszkodami — bez robota i bez ROS-a. SLAM, nawigacja i detektor wymagają robota.
Wszystkie ustawienia sprzętowe są w `konfiguracja.py`.
"""
import io
import math
import os
import shlex
import socket
import subprocess
import threading
import time
from collections import namedtuple

import numpy as np
import matplotlib.pyplot as plt

import konfiguracja as K

Skan = namedtuple("Skan", ["katy", "odleglosci"])   # katy w stopniach (0 = na wprost, + = w lewo), odległości w m

_rospy = None
_wydawca_predkosci = None
_procesy = {}
_KATALOG_LOGOW = os.path.expanduser("~/.warsztat_logi")


# =============================================================================================
# Pomocnicze
# =============================================================================================
def _ogranicz(wartosc, limit):
    return max(-limit, min(limit, wartosc))


def _info(tekst):
    print(f"[{_nazwa_robota()}] {tekst}")


# =============================================================================================
# Wybór robota (w notatniku, nie przy starcie kontenera)
# =============================================================================================
def _nazwa_robota():
    if K.TRYB_DEMO:
        return "demo"
    numer = next((n for n, ip in K.ROBOTY_IP.items() if ip == K.ROBOT_IP), None)
    return f"robot {numer}" if numer else (f"robot {K.ROBOT_IP}" if K.ROBOT_IP else "robot ?")


def _rozpoznaj(robot):
    """Numer z naklejki, adres IP albo „demo” → („demo” | IP)."""
    if str(robot).strip().lower() == "demo":
        return "demo"
    if isinstance(robot, int) or str(robot).isdigit():
        if int(robot) not in K.ROBOTY_IP:
            raise ValueError(f"Nie ma robota nr {robot}. Dostępne: {sorted(K.ROBOTY_IP)} albo podaj adres IP.")
        return K.ROBOTY_IP[int(robot)]
    return str(robot).strip()


def _ustaw(wybor):
    global _sym
    if wybor == "demo":
        K.TRYB_DEMO = True
        if _sym is None:
            _sym = _Symulator()
    else:
        K.TRYB_DEMO = False
        K.ROBOT_IP = wybor


def _wczytaj_wybor():
    """Przy imporcie: zmienna WARSZTAT_DEMO / WARSZTAT_ROBOT_IP albo zapisany wcześniej wybór."""
    if K.TRYB_DEMO:
        return _ustaw("demo")
    wybor = os.environ.get("WARSZTAT_ROBOT_IP")
    if not wybor and os.path.exists(K.PLIK_WYBORU):
        wybor = open(K.PLIK_WYBORU).read().strip()
    if wybor:
        _ustaw(wybor)


def wybierz_robota(robot):
    """Wybiera robota dla WSZYSTKICH notatników tej stacji: numer z naklejki (np. 3), adres IP albo "demo".

    Wybór zostaje zapamiętany. Zmiana robota w trakcie pracy: wybierz_robota(...), potem Kernel → Restart.
    """
    wybor = _rozpoznaj(robot)
    poprzedni = "demo" if K.TRYB_DEMO else K.ROBOT_IP
    try:
        with open(K.PLIK_WYBORU, "w") as f:
            f.write(wybor + "\n")
    except OSError as e:
        _info(f"Nie mogę zapisać wyboru w {K.PLIK_WYBORU} ({e}) — wybór obowiązuje tylko do restartu kernela.")
    if _rospy is not None and wybor != poprzedni:
        _info(f"Zapisano wybór: {wybor}. Ten notatnik jest już połączony z innym robotem — "
              "zrób Kernel → Restart i uruchom komórki od początku.")
        return
    _ustaw(wybor)
    _info("Wybrano tryb demonstracyjny." if wybor == "demo" else f"Wybrano robota {wybor}.")


def _ip_stacji():
    """Adres stacji widziany przez robota: pytamy robota przez ssh, skąd przyszło połączenie (SSH_CLIENT).

    Kontener jest za NAT-em Dockera (Linux i Docker Desktop na Windows), więc sam nie zna adresu hosta
    w sieci robotów. Robot widzi właśnie ten adres — i pod nim będzie łączył się z notatnikiem.
    Ręczne ustawienie: zmienna środowiskowa WARSZTAT_ROS_IP.
    """
    if os.environ.get("WARSZTAT_ROS_IP"):
        return os.environ["WARSZTAT_ROS_IP"]
    w = subprocess.run(["ssh", *_SSH_OPCJE, f"{K.ROBOT_UZYTKOWNIK}@{K.ROBOT_IP}", "echo $SSH_CLIENT"],
                       capture_output=True, text=True, timeout=15, **_ssh_srodowisko())
    if w.returncode != 0 or not w.stdout.split():
        raise OSError(w.stderr.strip() or "brak odpowiedzi")
    return w.stdout.split()[0]


def _srodowisko_ros():
    """Ustawia ROS_MASTER_URI (robot) i ROS_IP (stacja). Zwraca False, gdy robot nie jest wybrany."""
    if not K.ROBOT_IP:
        print("Najpierw wybierz robota: wybierz_robota(N), gdzie N to numer z naklejki na robocie.")
        return False
    os.environ["ROS_MASTER_URI"] = f"http://{K.ROBOT_IP}:11311"
    if "ROS_IP" not in os.environ:
        try:
            os.environ["ROS_IP"] = _ip_stacji()
        except (OSError, subprocess.TimeoutExpired) as e:
            _info(f"Nie mogę zalogować się na robota {K.ROBOT_IP} przez ssh: {e}")
            if "Permission denied" in str(e):
                klucze = [f for f in os.listdir(os.path.expanduser("~/.ssh")) if f.startswith("id_") and not f.endswith(".pub")] \
                    if os.path.isdir(os.path.expanduser("~/.ssh")) else []
                print("Robot odpowiada, ale odrzuca logowanie. Sprawdź login i hasło "
                      f"(ROBOT_UZYTKOWNIK={K.ROBOT_UZYTKOWNIK!r}, ROBOT_HASLO w konfiguracja.py)"
                      + (f" albo klucz {klucze}." if klucze else "."))
            else:
                print("Czy robot jest włączony, a stacja jest w sieci robotów?")
            return False
    return True


def _wymaga_robota(co):
    if K.TRYB_DEMO:
        raise RuntimeError(f"„{co}” wymaga prawdziwego robota — w trybie demonstracyjnym jest niedostępne. "
                           "Poproś prowadzącego o gotowe wyniki / mapę.")


# =============================================================================================
# Symulator (tryb demonstracyjny)
# =============================================================================================
class _Symulator:
    """Prostokątny pokój 3 × 2 m z dwiema przeszkodami. Odometria ma błąd systematyczny kół (jak prawdziwy robot)."""

    def __init__(self):
        self.prawdziwa = np.array([0.5, 0.5, 0.0])        # x, y, kąt [rad] — tego robot „nie zna”
        self.odom = np.array([0.0, 0.0, 0.0])             # to, co liczy z obrotów kół
        self.start = self.prawdziwa.copy()
        self.rng = np.random.default_rng(7)
        # błąd kół: lewe koło 3% słabsze, poślizg przy obrotach
        self.skala_lewe, self.skala_prawe, self.poslizg_obrotu = 0.97, 1.0, 0.95
        sciany = [((0, 0), (3, 0)), ((3, 0), (3, 2)), ((3, 2), (0, 2)), ((0, 2), (0, 0))]
        def pudlo(x, y, a, b):
            return [((x, y), (x + a, y)), ((x + a, y), (x + a, y + b)), ((x + a, y + b), (x, y + b)), ((x, y + b), (x, y))]
        self.odcinki = np.array(sciany + pudlo(1.8, 0.8, 0.4, 0.3) + pudlo(0.9, 1.4, 0.25, 0.25), dtype=float)

    def krok(self, v, w, dt):
        # odometria liczy idealnie z zadanych prędkości...
        th = self.odom[2]
        self.odom += np.array([v * math.cos(th) * dt, v * math.sin(th) * dt, w * dt])
        # ...a prawdziwy ruch jest trochę inny (różne silniki, poślizg)
        szer = 0.12
        vl, vp = (v - w * szer / 2) * self.skala_lewe, (v + w * szer / 2) * self.skala_prawe
        v_r, w_r = (vl + vp) / 2, (vp - vl) / szer * self.poslizg_obrotu
        th = self.prawdziwa[2]
        self.prawdziwa += np.array([v_r * math.cos(th) * dt, v_r * math.sin(th) * dt, w_r * dt])

    def skan(self):
        katy = np.arange(-180, 180, 1.0)
        x, y, th = self.prawdziwa
        kier = np.radians(katy) + th
        d = np.stack([np.cos(kier), np.sin(kier)], 1)                       # (N,2)
        a, b = self.odcinki[:, 0], self.odcinki[:, 1]                       # (M,2)
        e = b - a
        p = np.array([x, y])
        # rozwiązanie p + t d = a + s e
        mian = d[:, None, 0] * e[None, :, 1] - d[:, None, 1] * e[None, :, 0]
        ap = a[None] - p
        with np.errstate(divide="ignore", invalid="ignore"):
            t = (ap[..., 0] * e[None, :, 1] - ap[..., 1] * e[None, :, 0]) / mian
            s = (ap[..., 0] * d[:, None, 1] - ap[..., 1] * d[:, None, 0]) / mian
        t = np.where((t > 0) & (s >= 0) & (s <= 1), t, np.inf)
        odl = t.min(1) + self.rng.normal(0, 0.01, len(katy))
        odl[self.rng.random(len(katy)) < 0.02] = np.inf                    # pojedyncze zgubione wiązki
        return Skan(katy, odl)

    def zdjecie(self):
        from PIL import Image, ImageDraw
        img = Image.new("RGB", (640, 480), (200, 210, 225))
        r = ImageDraw.Draw(img)
        r.rectangle([0, 300, 640, 480], fill=(120, 110, 100))
        r.rectangle([80, 180, 230, 330], fill=(180, 140, 90), outline=(90, 60, 30), width=4)
        r.ellipse([400, 360, 480, 420], fill=(215, 40, 50))              # „kaczka” na podłodze
        r.ellipse([450, 330, 490, 370], fill=(215, 40, 50))
        r.polygon([(488, 345), (505, 352), (488, 358)], fill=(250, 170, 20))
        r.text((300, 250), "WARSZTAT", fill=(20, 20, 20))
        for i in range(0, 640, 4):
            r.line([(i, 0), (i, 40)], fill=(i % 256, 255 - i % 256, 128))
        a = np.asarray(img).astype(float)
        a *= np.linspace(0.75, 1.1, 640)[None, :, None]                   # nierównomierne oświetlenie
        a += self.rng.normal(0, 6, a.shape)                                 # szum matrycy jak w prawdziwej kamerze
        return np.clip(a, 0, 255).astype(np.uint8)


_sym = None
_wczytaj_wybor()                     # ustawia K.ROBOT_IP albo tryb demo (tworzy _sym)


# =============================================================================================
# Połączenie i programy na robocie
# =============================================================================================
def polacz():
    """Łączy notatnik z robotem (ROS). Wywołaj raz na początku notatnika."""
    global _rospy, _wydawca_predkosci
    if K.TRYB_DEMO:
        if not getattr(_sym, "polaczono", False):
            _info("TRYB DEMONSTRACYJNY — robot jest symulowany.")
            _sym.polaczono = True
        return True
    if _rospy is not None:
        return True
    if _zakonczony:
        _info("Ten notatnik został zakończony komórką koniec(). Żeby pracować w nim dalej: Kernel → Restart.")
        return False
    if not _srodowisko_ros():
        return False
    import rospy
    from geometry_msgs.msg import Twist
    import rosgraph
    if not rosgraph.is_master_online():
        _info(f"Logowanie na robota {K.ROBOT_IP} działa, ale ROS na robocie nie odpowiada (roscore nie działa). "
              "Uruchom `uruchom_robota()`. Jeśli to nie pomoże: `diagnoza()`.")
        return False
    global _porty
    _porty = _wolne_porty()
    if _porty is None:
        _info(f"Wszystkie porty ROS {K.PORTY_ROS.start}–{K.PORTY_ROS.stop - 1} są zajęte — za dużo otwartych notatników. "
              "Zamknij nieużywane (File → Close and Shut Down Notebook) i zrób Kernel → Restart.")
        return False
    try:
        rospy.init_node("warsztat_notatnik", anonymous=True, disable_signals=True,
                        xmlrpc_port=_porty[0], tcpros_port=_porty[1])
    except rospy.exceptions.ROSException as e:
        _info(f"Nie udało się uruchomić węzła ROS w notatniku ({e}). Zrób Kernel → Restart i uruchom komórki od początku; "
              "jeśli się powtórzy — zamknij inne notatniki (File → Close and Shut Down Notebook).")
        return False
    _rospy = rospy
    _wycisz_puste_polaczenia()
    _wydawca_predkosci = rospy.Publisher(K.TEMAT_PREDKOSC, Twist, queue_size=1)
    _info(f"Połączono z robotem {K.ROBOT_IP}.")
    return True


_porty = None


class _FiltrPustychPolaczen:
    """Ukrywa ostrzeżenie rospy „Inbound TCP/IP connection failed: … before handshake header received.
    0 bytes were received”.

    Pojawia się, gdy ktoś otworzy połączenie TCP z portem węzła i zamknie je bez nagłówka ROS:
    robi to diagnoza() (test portów z robota przez /dev/tcp), a także skanery portów i sondy sieci.
    Dla notatnika jest nieszkodliwe. Inne błędy połączeń (np. z niezerową liczbą bajtów) zostają widoczne.
    """
    def filter(self, rekord):
        try:
            tekst = rekord.getMessage()
        except Exception:
            return True
        return not ("before handshake header received" in tekst and "0 bytes were received" in tekst)


def _wycisz_puste_polaczenia():
    import logging
    for nazwa in ("rosout", "rospy.tcpros", "rospy"):
        lg = logging.getLogger(nazwa)
        if not any(isinstance(f, _FiltrPustychPolaczen) for f in lg.filters):
            lg.addFilter(_FiltrPustychPolaczen())


def _wolne_porty():
    """Pierwsza wolna para portów (XML-RPC, TCPROS) z konfiguracja.PORTY_ROS — każdy notatnik ma własną."""
    porty = list(K.PORTY_ROS)
    for xml, tcp in zip(porty[::2], porty[1::2]):
        gniazda = []
        try:
            for port in (xml, tcp):
                g = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                g.bind(("0.0.0.0", port))
                gniazda.append(g)
            return xml, tcp
        except OSError:
            continue
        finally:
            for g in gniazda:
                g.close()
    return None


# known_hosts w /tmp (świeży przy każdym starcie kontenera); nowy robot akceptowany automatycznie.
# Logowanie: najpierw klucz (jeśli jest w ~/.ssh), potem hasło z konfiguracja.ROBOT_HASLO.
_SSH_OPCJE = ["-o", "ConnectTimeout=5", "-o", "StrictHostKeyChecking=accept-new", "-o", "LogLevel=ERROR",
              "-o", "PreferredAuthentications=publickey,password,keyboard-interactive",
              "-o", "NumberOfPasswordPrompts=1",
              "-o", "UserKnownHostsFile=/tmp/warsztat_known_hosts"]
_ASKPASS = "/tmp/warsztat_askpass.sh"


def _ssh_srodowisko():
    """Argumenty subprocess, dzięki którym ssh poda hasło sam, bez pytania w terminalu.

    OpenSSH bierze hasło z programu SSH_ASKPASS, gdy proces nie ma terminala (start_new_session=True,
    stdin=DEVNULL) i ustawiona jest zmienna DISPLAY (dowolna). Skrypt wypisuje hasło ze zmiennej środowiskowej,
    więc hasło nie trafia do pliku ani na listę procesów. Działa bez sshpass, na OpenSSH 8.2 (Ubuntu 20.04).
    """
    if not os.path.exists(_ASKPASS):
        with open(_ASKPASS, "w") as f:
            f.write('#!/bin/sh\nprintf "%s\\n" "$WARSZTAT_HASLO"\n')
        os.chmod(_ASKPASS, 0o700)
    env = dict(os.environ, SSH_ASKPASS=_ASKPASS, DISPLAY=os.environ.get("DISPLAY", ":0"),
               SSH_ASKPASS_REQUIRE="force", WARSZTAT_HASLO=K.ROBOT_HASLO)
    return dict(env=env, stdin=subprocess.DEVNULL, start_new_session=True)


def _na_robocie(polecenie, nazwa=None):
    """Uruchamia polecenie na robocie przez ssh. Z `nazwa` — w tle (log w ~/.warsztat_logi/<nazwa>.log)."""
    pelne = f"{K.ROBOT_SRODOWISKO.format(ip=K.ROBOT_IP)} && {polecenie}"
    cel = f"{K.ROBOT_UZYTKOWNIK}@{K.ROBOT_IP}"
    if nazwa is None:
        wynik = subprocess.run(["ssh", *_SSH_OPCJE, cel, f"bash -lc {shlex.quote(pelne)}"],
                               capture_output=True, text=True, timeout=120, **_ssh_srodowisko())
        return wynik
    os.makedirs(_KATALOG_LOGOW, exist_ok=True)
    log = open(os.path.join(_KATALOG_LOGOW, f"{nazwa}.log"), "w")
    # -tt: zamknięcie ssh wysyła SIGHUP i zatrzymuje program na robocie
    p = subprocess.Popen(["ssh", "-tt", *_SSH_OPCJE, cel, f"bash -lc {shlex.quote(pelne)}"],
                         stdout=log, stderr=subprocess.STDOUT, **_ssh_srodowisko())
    _procesy[nazwa] = p
    return p


def _zatrzymaj(nazwa):
    p = _procesy.pop(nazwa, None)
    if p is not None and p.poll() is None:
        p.terminate()
        try:
            p.wait(5)
        except subprocess.TimeoutExpired:
            p.kill()
    if nazwa in K.WZORCE_PROCESOW:
        # „[s]lam” zamiast „slam”: wzorzec nie pasuje do własnego wiersza polecenia powłoki ssh,
        # więc pkill nie zabija powłoki, która go uruchomiła.
        wzorzec = "|".join(f"[{w[0]}]{w[1:]}" for w in K.WZORCE_PROCESOW[nazwa].split("|"))
        _na_robocie(f"pkill -f '{wzorzec}'; sleep 2; pkill -9 -f '{wzorzec}'; true")


def _dane_plyna(temat, limit_s=3.0):
    """True, jeśli w ciągu limit_s przyjdzie choć jedna wiadomość z tematu.

    Sama obecność tematu na liście nie wystarcza: węzeł uruchomiony przy wyłączonym LiDAR-ze
    ogłasza /scan, ale nic nie wysyła.
    """
    try:
        _rospy.wait_for_message(temat, _rospy.AnyMsg, timeout=limit_s)
        return True
    except Exception:
        return False


def _czekaj_na_dane(temat, limit_s=60):
    t0 = time.time()
    while time.time() - t0 < limit_s:
        if _dane_plyna(temat, 3.0):
            return True
        time.sleep(1)
    return False


def _czekaj_na_temat(temat, limit_s=30):
    t0 = time.time()
    while time.time() - t0 < limit_s:
        try:
            tematy = [t for t, _ in _rospy.get_published_topics()]
            if temat in tematy:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False


def uruchom_robota():
    """Uruchamia na robocie: roscore, napęd, LiDAR i kamerę (ok. 30–60 s)."""
    if K.TRYB_DEMO:
        return polacz()
    import rosgraph
    if not _srodowisko_ros():
        return False
    if not rosgraph.is_master_online():
        _info("Uruchamiam roscore…")
        _na_robocie(K.POLECENIA_ROBOTA["roscore"], "roscore")
        for _ in range(30):
            time.sleep(1)
            if rosgraph.is_master_online():
                break
        else:
            _info("roscore nie wystartował — sprawdź log ~/.warsztat_logi/roscore.log")
            return False
    polacz()
    _uruchom_tf_lidaru()
    try:
        dzialajace = {t for t, _ in _rospy.get_published_topics()}
    except Exception:
        dzialajace = set()
    for nazwa, temat in [("naped", K.TEMAT_ODOMETRIA), ("lidar", K.TEMAT_SKAN), ("kamera", K.TEMAT_KAMERA)]:
        if temat in dzialajace:
            if _dane_plyna(temat, 3.0):
                continue                  # działa i daje dane — nie ruszamy
            # Temat jest, ale danych brak (np. LiDAR włączony dopiero po starcie robota) → restart programu.
            _info(f"{nazwa}: temat {temat} jest, ale brak danych — uruchamiam ponownie…")
            _zatrzymaj(nazwa)
            time.sleep(1)
        elif nazwa in _procesy:           # był uruchomiony, ale nie ogłosił tematu → restart
            _info(f"{nazwa}: brak danych — uruchamiam ponownie…")
            _zatrzymaj(nazwa)
            time.sleep(1)
        else:
            _info(f"Uruchamiam: {nazwa}…")
        _na_robocie(K.POLECENIA_ROBOTA[nazwa], nazwa)
    ok = True
    for nazwa, temat in [("naped", K.TEMAT_ODOMETRIA), ("lidar", K.TEMAT_SKAN), ("kamera", K.TEMAT_KAMERA)]:
        jest = _czekaj_na_temat(temat, 60) and _czekaj_na_dane(temat, 60)
        _info(f"{nazwa:7s} {temat:28s} {'OK' if jest else 'BRAK DANYCH — zawołaj prowadzącego'}")
        if not jest:
            print(f"    log: ~/.warsztat_logi/{nazwa}.log  (podgląd: !tail -20 ~/.warsztat_logi/{nazwa}.log); "
                  "po usunięciu przyczyny uruchom_robota() jeszcze raz")
        ok &= jest
    return ok


def diagnoza():
    """Sprawdza krok po kroku połączenie stacja ↔ robot i mówi, na którym kroku jest problem (dla prowadzącego)."""
    def krok(nazwa, ok, rada=""):
        print(f"{'✔' if ok else '✘'} {nazwa}" + ("" if ok or not rada else f"\n    → {rada}"))
        return ok

    def port_otwarty(port, limit_s=3):
        try:
            socket.create_connection((K.ROBOT_IP, port), limit_s).close()
            return True
        except OSError:
            return False

    if K.TRYB_DEMO:
        return krok("tryb demonstracyjny — robot nie jest potrzebny", True)
    if not krok(f"wybrany robot: {_nazwa_robota()} ({K.ROBOT_IP})", bool(K.ROBOT_IP), "wybierz_robota(N)"):
        return
    if not krok("robot osiągalny w sieci (port ssh 22)", port_otwarty(22),
                "robot wyłączony, inna sieć Wi-Fi albo zły adres IP w ROBOTY_IP"):
        return
    try:
        ip = _ip_stacji()
        ssh_ok = True
    except (OSError, subprocess.TimeoutExpired) as e:
        ip, ssh_ok = str(e), False
    if not krok("logowanie ssh na robota", ssh_ok, f"{ip}\n    → login/hasło: ROBOT_UZYTKOWNIK, ROBOT_HASLO w konfiguracja.py"):
        return
    krok(f"adres stacji widziany przez robota: {ip}   (ROS_IP w notatniku: {os.environ.get('ROS_IP', 'jeszcze nie ustawiony')})", True)
    w = _na_robocie("rosversion -d; ps -eo args | grep -E '[r]osmaster|[r]oscore' | head -1")
    linie = w.stdout.strip().splitlines()
    krok(f"ROS na robocie: {linie[0] if linie else '?'}", w.returncode == 0 and bool(linie),
         "nie udało się wczytać środowiska ROS na robocie — sprawdź ROBOT_SRODOWISKO w konfiguracja.py\n    " + w.stderr.strip()[-300:])
    if not krok("roscore uruchomiony na robocie", len(linie) > 1, "uruchom_robota()"):
        return
    if not krok("port roscore 11311 osiągalny ze stacji", port_otwarty(11311),
                "roscore słucha tylko lokalnie albo blokuje zapora robota (ROS_IP/ROS_HOSTNAME na robocie)"):
        return
    if _rospy is None:
        print("  (połączenie ROS jeszcze nie nawiązane — uruchom polacz(), potem diagnoza() ponownie)")
        return
    tematy = {t for t, _ in _rospy.get_published_topics()}
    for temat in (K.TEMAT_ODOMETRIA, K.TEMAT_SKAN, K.TEMAT_KAMERA):
        krok(f"temat {temat}", temat in tematy, "uruchom_robota()")
    w = _na_robocie(f"timeout 4 rosrun tf tf_echo {K.RAMKA_ROBOTA} {K.RAMKA_LIDARU} 2>&1 | grep -m1 RPY")
    krok(f"TF {K.RAMKA_ROBOTA} → {K.RAMKA_LIDARU}: {w.stdout.strip() or 'brak'}", "RPY" in w.stdout,
         "uruchom_robota() (publikuje położenie LiDAR-u); bez tego SLAM i skan na mapie nie działają")

    # Ruch: robot sam łączy się z notatnikiem (porty węzła), żeby odebrać /cmd_vel. Sprawdzamy to Z ROBOTA.
    ros_ip = os.environ.get("ROS_IP", ip)
    if _porty is None:
        print("  (porty węzła nieznane — najpierw polacz())")
        return
    w = _na_robocie(f"for p in {_porty[0]} {_porty[1]}; do "
                    f"timeout 3 bash -c \"</dev/tcp/{ros_ip}/$p\" 2>/dev/null && echo $p:ok || echo $p:BRAK; done")
    wyniki = dict(x.split(":") for x in w.stdout.split() if ":" in x)
    krok(f"robot łączy się ze stacją {ros_ip} na portach {_porty[0]}, {_porty[1]}: {wyniki or w.stderr.strip()[-200:]}",
         bool(wyniki) and all(v == "ok" for v in wyniki.values()),
         "zapora na stacji blokuje te porty albo Docker ich nie przekierowuje (docker compose ps → 0.0.0.0:11411-11430->11411-11430/tcp)."
         " Bez tego robot nie dostaje poleceń ruchu. Linux: sprawdź ufw/firewalld; Windows: reguła zapory z README")
    w = _na_robocie(f"rostopic info {K.TEMAT_PREDKOSC}")
    sub = w.stdout.split("Subscribers:")[-1].strip() if "Subscribers:" in w.stdout else ""
    krok(f"ktoś na robocie słucha {K.TEMAT_PREDKOSC} (sterownik napędu): {sub.splitlines()[0] if sub else 'nikt'}",
         bool(sub) and "None" not in sub,
         f"sterownik napędu nie słucha {K.TEMAT_PREDKOSC} — sprawdź nazwę tematu (TEMAT_PREDKOSC) i launch napędu; "
         f"rostopic list na robocie")
    pub = w.stdout.split("Publishers:")[-1].split("Subscribers:")[0].strip() if "Publishers:" in w.stdout else ""
    krok(f"robot widzi notatnik jako nadawcę {K.TEMAT_PREDKOSC}: {pub.splitlines()[0] if pub else 'nie'}",
         "warsztat_notatnik" in pub, "notatnik nie ogłosił /cmd_vel — uruchom polacz() / jedz() i diagnoza() ponownie")


def _uruchom_tf_lidaru():
    """Publikuje na robocie położenie LiDAR-u względem robota (statyczna transformacja TF).

    Obrót (yaw) wynika z LIDAR_KAT_PRZOD: kierunek „na wprost robota” to kąt LIDAR_KAT_PRZOD w ramce LiDAR-u,
    więc ramka LiDAR-u jest obrócona o −LIDAR_KAT_PRZOD względem robota. Węzeł ma stałą nazwę, więc ponowne
    uruchomienie zastępuje poprzedni (ROS zamyka węzeł o tej samej nazwie) — duplikatów nie ma.
    """
    x, y, z = K.LIDAR_POLOZENIE
    yaw = math.radians((-K.LIDAR_KAT_PRZOD) % 360)   # 0…2π: ujemna liczba w argumentach mogłaby udawać opcję
    _zatrzymaj("tf_lidar")
    _na_robocie(K.POLECENIA_ROBOTA["tf_lidar"].format(x=x, y=y, z=z, yaw=f"{yaw:.4f}",
                                                       rodzic=K.RAMKA_ROBOTA, dziecko=K.RAMKA_LIDARU), "tf_lidar")


def status():
    """Pokazuje, które części robota działają."""
    if K.TRYB_DEMO:
        _info("demo: LiDAR, kamera, odometria symulowane")
        return
    polacz()
    tematy = {t for t, _ in _rospy.get_published_topics()}
    for opis, temat in [("napęd/odometria", K.TEMAT_ODOMETRIA), ("LiDAR", K.TEMAT_SKAN), ("kamera", K.TEMAT_KAMERA)]:
        if temat not in tematy:
            print(f"  {opis:24s} ✘ BRAK — uruchom_robota()")
        elif not _dane_plyna(temat, 3.0):
            print(f"  {opis:24s} ✘ temat jest, ale brak danych (np. LiDAR włączony po starcie) — uruchom_robota()")
        else:
            print(f"  {opis:24s} ✔")
    # SLAM i nawigację uruchamiają dopiero ćwiczenia 4 i 7 — ich brak wcześniej to NIE błąd.
    for opis, temat, kiedy in [("mapa (SLAM/nawigacja)", "/map", "uruchom_slam() w ćw. 4 albo nawigacja w ćw. 7"),
                               ("nawigacja", "/move_base/status", "uruchom_nawigacje(...) w ćw. 7")]:
        print(f"  {opis:24s} {'✔' if temat in tematy else '· jeszcze nieuruchomione (' + kiedy + ')'}")


def wezly_i_tematy():
    """Wypisuje programy (węzły) działające w systemie ROS robota i tematy, przez które się komunikują."""
    if K.TRYB_DEMO:
        print("[demo] niedostępne bez robota")
        return
    polacz()
    import rosnode
    print("WĘZŁY (osobne programy):")
    for n in sorted(rosnode.get_node_names()):
        print("  ", n)
    print("\nTEMATY (kanały wiadomości) i typ wiadomości:")
    for t, typ in sorted(_rospy.get_published_topics()):
        print(f"   {t:40s} {typ}")


# =============================================================================================
# LiDAR
# =============================================================================================
def pobierz_skan():
    """Zwraca jeden obrót LiDAR-u: Skan(katy [°], odleglosci [m]). Kąt 0 = na wprost, dodatnie = w lewo."""
    if K.TRYB_DEMO:
        return _sym.skan()
    polacz()
    from sensor_msgs.msg import LaserScan
    m = _rospy.wait_for_message(K.TEMAT_SKAN, LaserScan, timeout=5)
    odl = np.array(m.ranges, dtype=float)
    katy = np.degrees(m.angle_min + np.arange(len(odl)) * m.angle_increment) - K.LIDAR_KAT_PRZOD
    katy = (katy + 180) % 360 - 180
    odl[(odl < m.range_min) | (odl > m.range_max) | ~np.isfinite(odl)] = np.inf
    kol = np.argsort(katy)
    return Skan(katy[kol], odl[kol])


def odleglosc(kat=0.0, szerokosc=2.0, skan=None):
    """Odległość [m] do przeszkody w kierunku `kat` (°) — mediana wiązek z zakresu ± `szerokosc` stopni."""
    skan = skan or pobierz_skan()
    roznica = (skan.katy - kat + 180) % 360 - 180
    wybrane = skan.odleglosci[np.abs(roznica) <= szerokosc]
    wybrane = wybrane[np.isfinite(wybrane)]
    return float(np.median(wybrane)) if len(wybrane) else float("nan")


def seria_pomiarow(kat=0.0, ile=10, odstep_s=0.2):
    """`ile` pomiarów w kierunku `kat`. Zwraca (średnia, odchylenie standardowe, lista) — w metrach."""
    wyniki = []
    for _ in range(ile):
        wyniki.append(odleglosc(kat))
        if not K.TRYB_DEMO:
            time.sleep(odstep_s)
    w = np.array(wyniki)
    ok = w[np.isfinite(w)]
    if len(ok) == 0:
        print("Brak poprawnych pomiarów — czujnik nie widzi przeszkody w tym kierunku!")
        return float("nan"), float("nan"), wyniki
    if len(ok) < len(w):
        print(f"Uwaga: {len(w) - len(ok)} z {len(w)} pomiarów nieudanych (brak odbicia).")
    return float(ok.mean()), float(ok.std()), wyniki


def _rysuj_robota(ax, zasieg):
    """Robot na wykresie „z góry”: prostokąt + strzałka do przodu z podpisem (przód = w górę wykresu)."""
    from matplotlib.patches import Rectangle
    k = zasieg / 4                                 # skala rysunku robota względem wykresu
    ax.add_patch(Rectangle((-0.12 * k, -0.15 * k), 0.24 * k, 0.30 * k, color="red", alpha=0.35, zorder=3))
    ax.annotate("", xy=(0, 0.45 * k), xytext=(0, 0), zorder=4,
                arrowprops=dict(arrowstyle="-|>", color="red", lw=2.5, mutation_scale=18))
    ax.text(0, 0.5 * k, "przód (kamera)", color="red", ha="center", va="bottom", fontsize=9, zorder=4)
    ax.text(0, -0.2 * k, "tył", color="red", ha="center", va="top", fontsize=8, zorder=4)


def rysuj_skan(skan=None, zaznacz_kat=None, zasieg=4.0, tytul="Skan LiDAR — widok z góry"):
    """Rysuje skan jako chmurę punktów widzianą z góry (robot w środku, przód = w górę)."""
    skan = skan or pobierz_skan()
    ok = np.isfinite(skan.odleglosci)
    a = np.radians(skan.katy[ok] + 90)          # obrót: przód robota w górę wykresu
    x, y = skan.odleglosci[ok] * np.cos(a), skan.odleglosci[ok] * np.sin(a)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(x, y, s=4, c=skan.odleglosci[ok], cmap="viridis")
    _rysuj_robota(ax, zasieg)
    if zaznacz_kat is not None:
        d = odleglosc(zaznacz_kat, skan=skan)
        aa = math.radians(zaznacz_kat + 90)
        ax.plot([0, zasieg * math.cos(aa)], [0, zasieg * math.sin(aa)], "r--", lw=1)
        ax.set_title(f"{tytul}\nkierunek {zaznacz_kat}°: {d:.3f} m")
    else:
        ax.set_title(tytul)
    for r in range(1, int(zasieg) + 1):
        ax.add_patch(plt.Circle((0, 0), r, fill=False, ls=":", color="gray"))
    ax.set_xlim(-zasieg, zasieg); ax.set_ylim(-zasieg, zasieg); ax.set_aspect("equal")
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m] (przód robota)")
    plt.show()


# =============================================================================================
# Kamera i obraz cyfrowy
# =============================================================================================
def zdjecie():
    """Zwraca zdjęcie z kamery robota jako tablicę wysokość × szerokość × 3 (R, G, B; wartości 0–255)."""
    if K.TRYB_DEMO:
        return _sym.zdjecie()
    polacz()
    from sensor_msgs.msg import Image
    m = _rospy.wait_for_message(K.TEMAT_KAMERA, Image, timeout=5)
    return _obraz_z_wiadomosci(m)


def _obraz_z_wiadomosci(m):
    dane = np.frombuffer(m.data, dtype=np.uint8)
    if m.encoding in ("rgb8", "bgr8"):
        img = dane.reshape(m.height, m.step)[:, : m.width * 3].reshape(m.height, m.width, 3)
        return img[..., ::-1].copy() if m.encoding == "bgr8" else img.copy()
    if m.encoding == "mono8":
        img = dane.reshape(m.height, m.step)[:, : m.width]
        return np.stack([img] * 3, -1)
    raise ValueError(f"Nieobsługiwane kodowanie obrazu: {m.encoding}")


def pokaz(*obrazy, tytuly=None, rozmiar=5):
    """Wyświetla jeden lub kilka obrazów obok siebie."""
    fig, osie = plt.subplots(1, len(obrazy), figsize=(rozmiar * len(obrazy), rozmiar * 0.8))
    osie = np.atleast_1d(osie)
    for i, (ax, img) in enumerate(zip(osie, obrazy)):
        ax.imshow(img, cmap="gray" if np.ndim(img) == 2 else None, vmin=0, vmax=255, interpolation="nearest")
        if tytuly:
            ax.set_title(tytuly[i])
        ax.axis("off")
    plt.show()


def kanaly_rgb(img):
    """Pokazuje osobno kanał czerwony, zielony i niebieski."""
    r, g, b = (np.zeros_like(img) for _ in range(3))
    r[..., 0], g[..., 1], b[..., 2] = img[..., 0], img[..., 1], img[..., 2]
    pokaz(img, r, g, b, tytuly=["oryginał", "R (czerwony)", "G (zielony)", "B (niebieski)"], rozmiar=4)


def piksele(img, x, y, rozmiar=8):
    """Powiększa fragment rozmiar × rozmiar pikseli zaczynający się w (x, y) i wypisuje wartości RGB."""
    fragment = img[y:y + rozmiar, x:x + rozmiar]
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(fragment, interpolation="nearest")
    if rozmiar <= 8:
        for j in range(fragment.shape[0]):
            for i in range(fragment.shape[1]):
                R, G, B = fragment[j, i]
                ax.text(i, j, f"{R}\n{G}\n{B}", ha="center", va="center", fontsize=7,
                        color="white" if int(R) + int(G) + int(B) < 380 else "black")
    ax.set_title(f"Piksele od (x={x}, y={y}) — w każdym polu R, G, B")
    ax.set_xticks([]); ax.set_yticks([])
    plt.show()


def zmien_rozdzielczosc(img, szerokosc):
    """Zmniejsza obraz do zadanej szerokości (wysokość proporcjonalnie)."""
    from PIL import Image
    p = Image.fromarray(img)
    wys = max(1, round(p.height * szerokosc / p.width))
    return np.asarray(p.resize((szerokosc, wys), Image.BILINEAR))


def porownaj_kompresje(img, jakosci=(95, 50, 10), wycinek=None):
    """Zapisuje obraz jako PNG (bezstratnie) i JPEG o różnych jakościach. Pokazuje rozmiary plików i wygląd.

    wycinek=(x, y, szer, wys) — pokazuje powiększony fragment, gdzie łatwiej zobaczyć artefakty JPEG.
    Zwraca tabelę (lista słowników): format, rozmiar_kB, sredni_blad.
    """
    from PIL import Image
    p = Image.fromarray(img)
    wyniki, obrazy, tytuly = [], [], []
    surowy_kB = img.nbytes / 1024
    wyniki.append({"format": "surowe dane (bez kompresji)", "rozmiar_kB": round(surowy_kB, 1), "sredni_blad": 0.0})
    for fmt, q in [("PNG", None)] + [("JPEG", q) for q in jakosci]:
        bufor = io.BytesIO()
        p.save(bufor, fmt, **({"quality": q} if q else {}))
        odczyt = np.asarray(Image.open(io.BytesIO(bufor.getvalue())).convert("RGB"))
        blad = float(np.abs(odczyt.astype(int) - img.astype(int)).mean())
        nazwa = fmt if q is None else f"JPEG jakość {q}"
        wyniki.append({"format": nazwa, "rozmiar_kB": round(len(bufor.getvalue()) / 1024, 1),
                       "sredni_blad": round(blad, 2)})
        obrazy.append(odczyt); tytuly.append(f"{nazwa}\n{wyniki[-1]['rozmiar_kB']} kB")
    if wycinek:
        x, y, s, w = wycinek
        obrazy = [o[y:y + w, x:x + s] for o in obrazy]
    pokaz(*obrazy, tytuly=tytuly, rozmiar=4)
    print(f"{'format':32s} {'rozmiar [kB]':>12s} {'średni błąd piksela':>20s}")
    for w in wyniki:
        print(f"{w['format']:32s} {w['rozmiar_kB']:12.1f} {w['sredni_blad']:20.2f}")
    return wyniki


# =============================================================================================
# Ruch i odometria
# =============================================================================================
def _wyslij_predkosc(v, w):
    v, w = _ogranicz(v, K.MAKS_PREDKOSC_LINIOWA), _ogranicz(w, K.MAKS_PREDKOSC_KATOWA)
    if K.TRYB_DEMO:
        return v, w
    from geometry_msgs.msg import Twist
    _czekaj_na_naped()
    t = Twist()
    t.linear.x, t.angular.z = v, w
    _wydawca_predkosci.publish(t)
    return v, w


def _czekaj_na_naped(limit_s=3.0):
    """Czeka, aż sterownik napędu połączy się z nadawcą /cmd_vel w notatniku.

    Po polacz() robot potrzebuje ok. 1 s, żeby się połączyć — polecenia wysłane wcześniej przepadają
    (krótkie jedz() tuż po starcie nic nie robiło). Czekamy tylko, gdy połączenia jeszcze nie ma.
    """
    global _naped_ostrzezenie
    if _wydawca_predkosci.get_num_connections() > 0:
        _naped_ostrzezenie = False
        return True
    if _naped_ostrzezenie:                # już czekaliśmy i ostrzegliśmy — nie blokujemy pętli sterowania
        return False
    t0 = time.time()
    while time.time() - t0 < limit_s:
        time.sleep(0.1)
        if _wydawca_predkosci.get_num_connections() > 0:
            return True
    _naped_ostrzezenie = True
    _info(f"Sterownik napędu nie odbiera {K.TEMAT_PREDKOSC} — robot nie pojedzie. Uruchom diagnoza().")
    return False


_naped_ostrzezenie = False


def stop():
    """Natychmiast zatrzymuje robota."""
    if not K.TRYB_DEMO:
        polacz()
        for _ in range(3):
            _wyslij_predkosc(0, 0)
            time.sleep(0.05)


def jedz(predkosc=0.1, obrot=0.0, czas=1.0):
    """Jedzie z prędkością [m/s] i obrotem [rad/s] przez `czas` sekund, potem staje."""
    polacz()
    dt = 0.05
    try:
        for _ in range(int(czas / dt)):
            v, w = _wyslij_predkosc(predkosc, obrot)
            if K.TRYB_DEMO:
                _sym.krok(v, w, dt)
            else:
                time.sleep(dt)
    finally:
        stop()


def pozycja_odometrii():
    """Zwraca (x [m], y [m], kąt [°]) — gdzie robot SĄDZI, że jest, licząc obroty kół."""
    if K.TRYB_DEMO:
        x, y, th = _sym.odom
        return float(x), float(y), float(_roznica_katow(math.degrees(th), 0))
    polacz()
    from nav_msgs.msg import Odometry
    m = _rospy.wait_for_message(K.TEMAT_ODOMETRIA, Odometry, timeout=5)
    q = m.pose.pose.orientation
    kat = math.degrees(math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y ** 2 + q.z ** 2)))
    return m.pose.pose.position.x, m.pose.pose.position.y, kat


def _roznica_katow(a, b):
    return (a - b + 180) % 360 - 180


def jedz_prosto(metry=1.0, predkosc=0.15, trasa=None):
    """Jedzie prosto, aż odometria pokaże przejechane `metry`."""
    polacz()
    x0, y0, _ = pozycja_odometrii()
    kierunek = 1 if metry >= 0 else -1
    dt = 0.05
    try:
        while True:
            x, y, k = pozycja_odometrii()
            if trasa is not None:
                trasa.append((x, y))
            if math.hypot(x - x0, y - y0) >= abs(metry):
                break
            v, w = _wyslij_predkosc(kierunek * abs(predkosc), 0)
            if K.TRYB_DEMO:
                _sym.krok(v, w, dt)
            else:
                time.sleep(dt)
    finally:
        stop()


def obroc(stopnie=90, predkosc_obrotu=0.8, trasa=None):
    """Obraca w miejscu o `stopnie` (dodatnie = w lewo), aż odometria pokaże zadany kąt."""
    polacz()
    _, _, k0 = pozycja_odometrii()
    znak = 1 if stopnie >= 0 else -1
    dt = 0.05
    try:
        while True:
            x, y, k = pozycja_odometrii()
            if trasa is not None:
                trasa.append((x, y))
            if abs(_roznica_katow(k, k0)) >= abs(stopnie) - 1:
                break
            v, w = _wyslij_predkosc(0, znak * abs(predkosc_obrotu))
            if K.TRYB_DEMO:
                _sym.krok(v, w, dt)
            else:
                time.sleep(dt)
    finally:
        stop()


def przejazd_po_kwadracie(bok=1.0, predkosc=0.15, okrazenia=1):
    """Przejazd po kwadracie wyłącznie na podstawie odometrii. Zwraca trasę [(x, y), …] wg odometrii."""
    trasa = [pozycja_odometrii()[:2]]
    for _ in range(4 * okrazenia):
        jedz_prosto(bok, predkosc, trasa)
        time.sleep(0 if K.TRYB_DEMO else 0.3)
        obroc(90, trasa=trasa)
        time.sleep(0 if K.TRYB_DEMO else 0.3)
    x, y, k = pozycja_odometrii()
    x0, y0 = trasa[0]
    print(f"Wg odometrii robot jest {100 * math.hypot(x - x0, y - y0):.1f} cm od startu (kąt {k:.1f}°).")
    print("Teraz zmierz miarką, gdzie jest NAPRAWDĘ!")
    if K.TRYB_DEMO:
        p, s = _sym.prawdziwa, _sym.start
        print(f"[demo] W rzeczywistości: {100 * math.hypot(*(p[:2] - s[:2])):.1f} cm od startu.")
    return trasa


def rysuj_trase(*trasy, podpisy=None):
    """Rysuje trasę (lub kilka) z odometrii — widok z góry."""
    fig, ax = plt.subplots(figsize=(6, 6))
    for i, t in enumerate(trasy):
        t = np.array(t)
        ax.plot(t[:, 0], t[:, 1], "-", label=podpisy[i] if podpisy else f"przejazd {i + 1}")
        ax.plot(t[0, 0], t[0, 1], "go"); ax.plot(t[-1, 0], t[-1, 1], "rx", markersize=10)
    ax.set_aspect("equal"); ax.grid(True); ax.legend()
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
    ax.set_title("Trasa według odometrii (zielony = start, czerwony = koniec)")
    plt.show()


_panele = []          # stany otwartych paneli sterowania w tym notatniku (do zamknięcia przez koniec())
_zakonczony = False


def koniec():
    """Ostatnia komórka każdego notatnika: zatrzymuje robota i odłącza TEN notatnik od robota.

    Kończy panele sterowania i podgląd mapy, zwalnia porty ROS notatnika. Programy na robocie
    (napęd, LiDAR, kamera) działają dalej — następny notatnik połączy się z nimi w pierwszej komórce.
    Po koniec() ten notatnik nie steruje już robotem (żeby wrócić do pracy w nim: Kernel → Restart).
    """
    global _rospy, _zakonczony
    for stan in list(_panele):
        stan["dziala"] = False
    _Podglad.zatrzymaj_aktywny()
    if K.TRYB_DEMO:
        _info("Koniec ćwiczenia. Możesz otworzyć następny notatnik.")
        return
    if _rospy is not None:
        time.sleep(0.3)
        stop()
        _rospy.signal_shutdown("koniec notatnika")
        _rospy = None
    _zakonczony = True
    _info("Koniec ćwiczenia: robot zatrzymany, notatnik odłączony. Robot działa dalej — otwórz następny notatnik.")


def panel_sterowania(predkosc=0.15, predkosc_obrotu=1.0, podglad=False):
    """Wyświetla przyciski do ręcznego sterowania robotem. Robot jedzie, dopóki nie klikniesz STOP.

    podglad=True — obok przycisków mapa na żywo (SLAM, nawigacja; wymaga robota).
    """
    import ipywidgets as W
    from IPython.display import display
    polacz()
    stan = {"v": 0.0, "w": 0.0, "dziala": True}
    _panele.append(stan)
    s_v = W.FloatSlider(value=predkosc, min=0.05, max=K.MAKS_PREDKOSC_LINIOWA, step=0.05, description="prędkość")
    s_w = W.FloatSlider(value=predkosc_obrotu, min=0.2, max=K.MAKS_PREDKOSC_KATOWA, step=0.1, description="obrót")
    info = W.Label("STOP")

    def ustaw(v, w, opis):
        def f(_):
            stan["v"], stan["w"] = v * s_v.value, w * s_w.value
            info.value = opis
        return f

    przyciski = {
        "↑": ustaw(1, 0, "do przodu"), "↓": ustaw(-1, 0, "do tyłu"),
        "←": ustaw(0, 1, "obrót w lewo"), "→": ustaw(0, -1, "obrót w prawo"),
        "↖": ustaw(1, 1, "łuk w lewo"), "↗": ustaw(1, -1, "łuk w prawo"),
        "■ STOP": ustaw(0, 0, "STOP"),
    }
    b = {k: W.Button(description=k, layout=W.Layout(width="80px", height="50px")) for k in przyciski}
    for k, f in przyciski.items():
        b[k].on_click(f)
    b["■ STOP"].button_style = "danger"
    koniec = W.Button(description="Zakończ sterowanie", button_style="warning")

    widok = _Podglad() if podglad and not K.TRYB_DEMO else None

    def zakoncz(_):
        stan["dziala"] = False
        info.value = "sterowanie zakończone"
        if widok:
            widok.zatrzymaj()
    koniec.on_click(zakoncz)

    def petla():
        # Polecenia wysyłamy tylko w ruchu (+ jedno „stój” po STOP). Bezczynny panel milczy, więc panel
        # zostawiony w innym notatniku nie zagłusza poleceń z notatnika, w którym właśnie pracujemy.
        jechal = False
        while stan["dziala"]:
            if stan["v"] or stan["w"]:
                v, w = _wyslij_predkosc(stan["v"], stan["w"])
                jechal = True
            else:
                v = w = 0.0
                if jechal:
                    stop()
                    jechal = False
            if K.TRYB_DEMO:
                _sym.krok(v, w, 0.1)
            time.sleep(0.1)
        if jechal:
            stop()
        if stan in _panele:
            _panele.remove(stan)
    threading.Thread(target=petla, daemon=True).start()
    siatka = W.VBox([W.HBox([b["↖"], b["↑"], b["↗"]]), W.HBox([b["←"], b["■ STOP"], b["→"]]),
                     W.HBox([W.Label(layout=W.Layout(width="80px")), b["↓"]])])
    sterowanie = W.VBox([siatka, s_v, s_w, info, koniec])
    display(W.HBox([sterowanie, widok.start()]) if widok else sterowanie)


# =============================================================================================
# SLAM i mapy
# =============================================================================================
def uruchom_slam(rozdzielczosc=0.05, zasieg=6.0, aktualizacja=2.0, czastki=30):
    """Uruchamia SLAM (gmapping) na robocie.

    rozdzielczosc — wielkość jednej kratki mapy [m]
    zasieg        — z jakiej odległości [m] LiDAR dopisuje przeszkody do mapy
    aktualizacja  — co ile sekund mapa jest przeliczana
    czastki       — ile hipotez położenia robota śledzi algorytm (więcej = dokładniej, ale wolniej)
    """
    _wymaga_robota("SLAM")
    polacz()
    zatrzymaj_slam(cicho=True)
    pol = K.POLECENIA_ROBOTA["slam"].format(rozdzielczosc=rozdzielczosc, zasieg=zasieg, zasieg_max=zasieg + 2,
                                             aktualizacja=aktualizacja, czastki=czastki)
    _na_robocie(pol, "slam")
    if _czekaj_na_temat("/map", 30):
        _info(f"SLAM działa (kratka {rozdzielczosc * 100:.0f} cm, zasięg {zasieg} m, co {aktualizacja} s, "
              f"{czastki} cząstek). Teraz jedź robotem (panel sterowania z podglądem mapy).")
        return True
    _info("SLAM nie wystartował — sprawdź ~/.warsztat_logi/slam.log albo zawołaj prowadzącego.")
    return False


def zatrzymaj_slam(cicho=False):
    """Zatrzymuje SLAM (niezapisana mapa przepada!)."""
    if K.TRYB_DEMO:
        return
    _zatrzymaj("slam")
    if not cicho:
        _info("SLAM zatrzymany.")


def zapisz_mape(nazwa):
    """Zapisuje bieżącą mapę na robocie (pliki <nazwa>.pgm i <nazwa>.yaml)."""
    _wymaga_robota("Zapis mapy")
    nazwa = nazwa.replace(" ", "_")
    w = _na_robocie(K.POLECENIA_ROBOTA["zapisz_mape"].format(katalog=K.ROBOT_KATALOG_MAP, nazwa=nazwa))
    if w.returncode == 0:
        _info(f"Mapa zapisana: {K.ROBOT_KATALOG_MAP}/{nazwa}.yaml")
    else:
        _info("Nie udało się zapisać mapy:\n" + w.stdout[-500:] + w.stderr[-500:])
    return w.returncode == 0


def lista_map():
    """Pokazuje mapy zapisane na robocie."""
    _wymaga_robota("Lista map")
    w = _na_robocie(f"ls -1 {K.ROBOT_KATALOG_MAP}/*.yaml 2>/dev/null | xargs -n1 basename | sed 's/.yaml$//'")
    mapy = [m for m in w.stdout.split() if m]
    print("Zapisane mapy:", ", ".join(mapy) if mapy else "(brak)")
    return mapy


def pokaz_mape(tytul="Mapa"):
    """Pobiera aktualną mapę (/map), rysuje ją i podaje statystyki."""
    _wymaga_robota("Podgląd mapy")
    polacz()
    from nav_msgs.msg import OccupancyGrid
    m = _rospy.wait_for_message("/map", OccupancyGrid, timeout=10)
    s = np.array(m.data, dtype=np.int16).reshape(m.info.height, m.info.width)
    obraz = np.full(s.shape, 160, np.uint8)
    obraz[s == 0], obraz[s >= 65] = 255, 0
    obraz[(s > 0) & (s < 65)] = 200
    znane = s >= 0
    ys, xs = np.where(znane)
    if len(xs):
        obraz = obraz[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    pole = m.info.resolution ** 2
    plt.figure(figsize=(7, 7))
    plt.imshow(obraz[::-1], cmap="gray", vmin=0, vmax=255, interpolation="nearest")
    plt.title(f"{tytul} — kratka {m.info.resolution * 100:.0f} cm")
    plt.axis("off"); plt.show()
    print(f"Zbadany obszar: {znane.sum() * pole:.2f} m²  (wolne: {(s == 0).sum() * pole:.2f} m², "
          f"zajęte: {(s >= 65).sum() * pole:.2f} m²)")


# =============================================================================================
# Podgląd mapy na żywo (zastępuje RViz — wszystko w notatniku, bez okna X11 i bez OpenGL)
# =============================================================================================
_tf_bufor = None


def _poza(rama, limit_s=0.2):
    """(x, y, kąt_rad) ramki `rama` w układzie mapy według TF; None, gdy brak transformacji."""
    global _tf_bufor
    import tf2_ros
    if _tf_bufor is None:
        _tf_bufor = tf2_ros.Buffer()
        _tf_bufor._sluchacz = tf2_ros.TransformListener(_tf_bufor)
        time.sleep(0.5)
    try:
        t = _tf_bufor.lookup_transform("map", rama.lstrip("/"), _rospy.Time(0), _rospy.Duration(limit_s))
    except Exception:
        return None
    return t.transform.translation.x, t.transform.translation.y, _kat_z_kwaternionu(t.transform.rotation)


def _kat_z_kwaternionu(q):
    """Kąt obrotu wokół osi z [rad] z kwaternionu ROS."""
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y ** 2 + q.z ** 2))


class _Podglad:
    """Mapa na żywo jako obrazek w notatniku: mapa (/map), robot, skan LiDAR-u, cząstki AMCL, trasa i cel.

    Subskrybuje tematy tylko na czas działania. Obraz odświeżany w osobnym wątku co `odswiezanie_s`.
    Rysuje to, co akurat jest dostępne: w SLAM-ie mapę, robota i skan, w nawigacji dodatkowo cząstki i trasę.
    """
    _aktywny = None

    def __init__(self, odswiezanie_s=1.0):
        self.odswiezanie_s = odswiezanie_s
        self.dane = {}
        self.dziala = False
        self.subskrypcje = []

    @classmethod
    def zatrzymaj_aktywny(cls):
        if cls._aktywny is not None:
            cls._aktywny.zatrzymaj()

    def start(self):
        import ipywidgets as W
        from nav_msgs.msg import OccupancyGrid, Path
        from sensor_msgs.msg import LaserScan
        from geometry_msgs.msg import PoseArray, PoseStamped
        polacz()
        _Podglad.zatrzymaj_aktywny()
        _Podglad._aktywny = self
        for temat, typ, klucz in [("/map", OccupancyGrid, "mapa"), (K.TEMAT_SKAN, LaserScan, "skan"),
                                  (K.TEMAT_CZASTKI, PoseArray, "czastki"), (K.TEMAT_PLAN, Path, "plan"),
                                  (K.TEMAT_CEL, PoseStamped, "cel")]:
            self.subskrypcje.append(_rospy.Subscriber(temat, typ, self._zapamietaj(klucz), queue_size=1))
        self.obraz = W.Image(format="png", layout=W.Layout(width="440px"))
        self.opis = W.Label("podgląd mapy: czekam na dane…")
        self.dziala = True
        threading.Thread(target=self._petla, daemon=True).start()
        return W.VBox([self.obraz, self.opis])

    def zatrzymaj(self):
        self.dziala = False
        for s in self.subskrypcje:
            s.unregister()
        self.subskrypcje = []
        if _Podglad._aktywny is self:
            _Podglad._aktywny = None

    def _zapamietaj(self, klucz):
        def f(wiadomosc):
            self.dane[klucz] = wiadomosc
        return f

    def _petla(self):
        while self.dziala:
            try:
                self.obraz.value = self._rysuj()
            except Exception as e:      # podgląd nie może przerwać jazdy — tylko informuje
                self.opis.value = f"podgląd mapy: {type(e).__name__}: {e}"
            time.sleep(self.odswiezanie_s)
        self.opis.value = "podgląd zatrzymany (ostatni obraz)"

    def _rysuj(self):
        from matplotlib.figure import Figure
        from matplotlib.backends.backend_agg import FigureCanvasAgg
        fig = Figure(figsize=(5.5, 6.3), dpi=80)
        ax = fig.add_subplot(111)
        widoczne = []                               # punkty, które muszą zmieścić się w kadrze
        m = self.dane.get("mapa")
        if m is not None:
            r, (w, h) = m.info.resolution, (m.info.width, m.info.height)
            ox, oy = m.info.origin.position.x, m.info.origin.position.y
            s = np.array(m.data, dtype=np.int16).reshape(h, w)
            obraz = np.full(s.shape, 160, np.uint8)
            obraz[s == 0], obraz[s >= 65] = 255, 0
            obraz[(s > 0) & (s < 65)] = 200
            ax.imshow(obraz, cmap="gray", vmin=0, vmax=255, origin="lower", interpolation="nearest",
                      extent=[ox, ox + w * r, oy, oy + h * r])
            ys, xs = np.where(s >= 0)
            if len(xs):
                widoczne += [(ox + xs.min() * r, oy + ys.min() * r), (ox + (xs.max() + 1) * r, oy + (ys.max() + 1) * r)]
        skan = self.dane.get("skan")
        if skan is not None:
            p = _poza(skan.header.frame_id)
            if p is not None:
                zakresy = np.array(skan.ranges, dtype=float)
                katy = skan.angle_min + skan.angle_increment * np.arange(len(zakresy))
                ok = np.isfinite(zakresy) & (zakresy > skan.range_min) & (zakresy < skan.range_max)
                ax.scatter(p[0] + zakresy[ok] * np.cos(p[2] + katy[ok]), p[1] + zakresy[ok] * np.sin(p[2] + katy[ok]),
                           s=3, c="tab:red", label="skan LiDAR-u")
        cz = self.dane.get("czastki")
        if cz is not None and cz.poses:
            px = np.array([q.position.x for q in cz.poses]); py = np.array([q.position.y for q in cz.poses])
            pk = np.array([_kat_z_kwaternionu(q.orientation) for q in cz.poses])
            ax.quiver(px, py, np.cos(pk), np.sin(pk), color="tab:blue", alpha=0.5, scale=40, width=0.004,
                      label="cząstki (hipotezy położenia)")
        plan = self.dane.get("plan")
        if plan is not None and plan.poses:
            ax.plot([q.pose.position.x for q in plan.poses], [q.pose.position.y for q in plan.poses],
                    "-", color="tab:green", lw=2, label="zaplanowana trasa")
        cel = self.dane.get("cel")
        if cel is not None:
            ax.plot(cel.pose.position.x, cel.pose.position.y, "*", color="tab:orange", ms=16, label="cel")
            widoczne.append((cel.pose.position.x, cel.pose.position.y))
        robot = _poza(K.RAMKA_ROBOTA)
        if robot is not None:
            x, y, k = robot
            ax.plot(x, y, "o", color="tab:purple", ms=10, label="robot", zorder=5)
            ax.arrow(x, y, 0.25 * math.cos(k), 0.25 * math.sin(k), width=0.025, color="tab:purple", zorder=5)
            widoczne.append((x, y))
        if widoczne:
            xs, ys = zip(*widoczne)
            ax.set_xlim(min(xs) - 0.4, max(xs) + 0.4); ax.set_ylim(min(ys) - 0.4, max(ys) + 0.4)
        ax.set_aspect("equal"); ax.grid(True, alpha=0.3)
        ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
        if ax.get_legend_handles_labels()[0]:
            ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, fontsize=8, frameon=False)
        fig.tight_layout()
        brak = [n for n, jest in [("mapy", m is not None), ("położenia robota", robot is not None)] if not jest]
        self.opis.value = "podgląd mapy: " + (f"brak {', '.join(brak)}" if brak else f"odświeżono {time.strftime('%H:%M:%S')}")
        bufor = io.BytesIO()
        FigureCanvasAgg(fig).print_png(bufor)
        return bufor.getvalue()


def podglad_mapy(odswiezanie_s=1.0):
    """Wyświetla mapę na żywo (do zatrzymania przyciskiem). Zwykle niepotrzebne: panel sterowania
    z `podglad=True` i `jedz_do()` pokazują podgląd same."""
    _wymaga_robota("Podgląd mapy")
    import ipywidgets as W
    from IPython.display import display
    widok = _Podglad(odswiezanie_s)
    przycisk = W.Button(description="Zatrzymaj podgląd", button_style="warning")
    przycisk.on_click(lambda _: widok.zatrzymaj())
    display(W.VBox([widok.start(), przycisk]))


# =============================================================================================
# Nawigacja autonomiczna
# =============================================================================================
_klient_nawigacji = None


def uruchom_nawigacje(mapa):
    """Uruchamia nawigację (map_server + AMCL + move_base) na zapisanej mapie."""
    _wymaga_robota("Nawigacja")
    polacz()
    zatrzymaj_slam(cicho=True)
    zatrzymaj_nawigacje(cicho=True)
    _na_robocie(K.POLECENIA_ROBOTA["nawigacja"].format(katalog=K.ROBOT_KATALOG_MAP, nazwa=mapa), "nawigacja")
    _info("Uruchamiam nawigację (do 60 s)…")
    if _czekaj_na_temat("/move_base/status", 60):
        _info(f"Nawigacja działa na mapie „{mapa}”. Teraz ustaw pozycję startową robota.")
        return True
    _info("Nawigacja nie wystartowała — sprawdź ~/.warsztat_logi/nawigacja.log albo zawołaj prowadzącego.")
    return False


def zatrzymaj_nawigacje(cicho=False):
    if K.TRYB_DEMO:
        return
    global _klient_nawigacji
    _klient_nawigacji = None
    _zatrzymaj("nawigacja")
    if not cicho:
        _info("Nawigacja zatrzymana.")


def _kwaternion(kat_deg):
    k = math.radians(kat_deg) / 2
    return 0.0, 0.0, math.sin(k), math.cos(k)


def ustaw_pozycje_startowa(x, y, kat=0.0):
    """Mówi robotowi, gdzie mniej więcej stoi na mapie (x, y w metrach, kąt w stopniach)."""
    _wymaga_robota("Pozycja startowa")
    polacz()
    from geometry_msgs.msg import PoseWithCovarianceStamped
    p = PoseWithCovarianceStamped()
    p.header.frame_id = "map"
    p.header.stamp = _rospy.Time(0)   # 0 = „najnowsze dane” — nie zależy od zegara stacji
    p.pose.pose.position.x, p.pose.pose.position.y = x, y
    o = p.pose.pose.orientation
    o.x, o.y, o.z, o.w = _kwaternion(kat)
    cov = [0.0] * 36
    cov[0] = cov[7] = 0.25 ** 2
    cov[35] = math.radians(15) ** 2
    p.pose.covariance = cov
    pub = _rospy.Publisher(K.TEMAT_POZYCJA_STARTOWA, PoseWithCovarianceStamped, queue_size=1, latch=True)
    time.sleep(0.5)
    pub.publish(p)
    _info(f"Pozycja startowa: x={x} m, y={y} m, kąt={kat}°. Chmurę cząstek zobaczysz w podglądzie mapy.")


def gdzie_jestem():
    """Zwraca (x, y, kąt°, niepewność_m) — położenie robota na mapie według lokalizacji AMCL."""
    _wymaga_robota("Lokalizacja")
    polacz()
    from geometry_msgs.msg import PoseWithCovarianceStamped
    m = _rospy.wait_for_message("/amcl_pose", PoseWithCovarianceStamped, timeout=10)
    p, q = m.pose.pose.position, m.pose.pose.orientation
    kat = math.degrees(math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y ** 2 + q.z ** 2)))
    niepewnosc = math.sqrt(m.pose.covariance[0] + m.pose.covariance[7])
    print(f"x = {p.x:.2f} m, y = {p.y:.2f} m, kąt = {kat:.0f}°, niepewność ≈ {100 * niepewnosc:.0f} cm")
    return p.x, p.y, kat, niepewnosc


def _klient():
    global _klient_nawigacji
    if _klient_nawigacji is None:
        import actionlib
        from move_base_msgs.msg import MoveBaseAction
        _klient_nawigacji = actionlib.SimpleActionClient(K.AKCJA_NAWIGACJI, MoveBaseAction)
        if not _klient_nawigacji.wait_for_server(_rospy.Duration(10)):
            _klient_nawigacji = None
            raise RuntimeError("Brak serwera nawigacji (move_base). Czy uruchomiono `uruchom_nawigacje(...)`?")
    return _klient_nawigacji


def _cel(x, y, kat):
    from move_base_msgs.msg import MoveBaseGoal
    g = MoveBaseGoal()
    g.target_pose.header.frame_id = "map"
    g.target_pose.header.stamp = _rospy.Time(0)
    g.target_pose.pose.position.x, g.target_pose.pose.position.y = x, y
    o = g.target_pose.pose.orientation
    o.x, o.y, o.z, o.w = _kwaternion(kat)
    return g


_STANY = {0: "oczekuje", 1: "w drodze", 2: "anulowano", 3: "DOTARŁ DO CELU", 4: "PRZERWANO — nie da się dojechać",
          5: "odrzucono cel", 6: "anulowanie…", 7: "anulowanie…", 8: "anulowano", 9: "cel utracony"}


def jedz_do(x, y, kat=0.0, limit_s=120, podglad=True):
    """Wysyła robota do punktu (x, y) na mapie i czeka na wynik. Zwraca True, gdy dotarł.

    podglad=True — w trakcie jazdy mapa na żywo (cząstki, zaplanowana trasa, cel).
    """
    _wymaga_robota("Nawigacja")
    polacz()
    k = _klient()
    widok = None
    if podglad:
        from IPython.display import display
        widok = _Podglad()
        display(widok.start())
    t0 = time.time()
    k.send_goal(_cel(x, y, kat))
    _info(f"Cel: x={x}, y={y}, kąt={kat}°. Jadę…")
    try:
        dojechal_w_limicie = k.wait_for_result(_rospy.Duration(limit_s))
    finally:
        if widok:
            widok.zatrzymaj()
    if not dojechal_w_limicie:
        k.cancel_goal()
        _info(f"Przekroczono limit {limit_s} s — anulowano cel.")
        return False
    stan = k.get_state()
    _info(f"Wynik: {_STANY.get(stan, stan)} (czas {time.time() - t0:.1f} s)")
    return stan == 3


def anuluj():
    """Anuluje bieżący cel nawigacji (robot staje)."""
    if _klient_nawigacji is not None:
        _klient_nawigacji.cancel_all_goals()
    stop()


def ustaw_parametry_nawigacji(maks_predkosc=None, odleglosc_bezpieczenstwa=None):
    """Zmienia parametry nawigacji w trakcie działania.

    maks_predkosc            — największa prędkość jazdy [m/s]
    odleglosc_bezpieczenstwa — o ile [m] trasa ma omijać przeszkody (promień „pompowania” przeszkód)
    """
    _wymaga_robota("Parametry nawigacji")
    polacz()
    from dynamic_reconfigure.client import Client
    if maks_predkosc is not None:
        maks_predkosc = min(maks_predkosc, K.MAKS_PREDKOSC_LINIOWA)
        c = Client(K.DR_PLANER_LOKALNY, timeout=5)
        teraz = c.get_configuration()
        zmiany = {p: maks_predkosc for p in ("max_vel_x", "max_vel_trans", "max_trans_vel") if p in teraz}
        c.update_configuration(zmiany)
        _info(f"Maksymalna prędkość: {maks_predkosc} m/s")
    if odleglosc_bezpieczenstwa is not None:
        for serwer in K.DR_INFLACJA:
            Client(serwer, timeout=5).update_configuration({"inflation_radius": odleglosc_bezpieczenstwa})
        _info(f"Odległość bezpieczeństwa: {odleglosc_bezpieczenstwa} m")


# =============================================================================================
# Szukanie obiektu (kamera + detektor słowny) — obiekt na podłodze jest za niski dla LiDAR-u,
# więc kierunek i bliskość ocenia się z obrazu: środek ramki (lewo/prawo) i dolna krawędź (blisko/daleko).
# =============================================================================================
def _detektor():
    import detektor      # import tutaj — detektor importuje ten moduł
    return detektor


def _swieze_zdjecie(pauza_s=0.4):
    """Zdjęcie zrobione po zatrzymaniu robota (bez rozmazania i bez starej klatki z bufora)."""
    if not K.TRYB_DEMO:
        time.sleep(pauza_s)
    return zdjecie()


def rozejrzyj_sie(krok=30, prog=0.3, rozdzielczosc=640, wielkosc="maly", pokazuj=True):
    """Obraca się co `krok` stopni, robi zdjęcie i szuka obiektu (słowa: detektor.ustaw_slowa).

    Gdy znajdzie — obraca się przodem do obiektu i zwraca wykrycie (słownik), inaczej None.
    """
    _wymaga_robota("Szukanie obiektu")
    D = _detektor()
    obrocono = 0
    while obrocono < 360:
        img = _swieze_zdjecie()
        w = D.najlepsze(img, prog=prog, rozdzielczosc=rozdzielczosc, wielkosc=wielkosc)
        if w:
            _info(f"kąt {obrocono:3d}°: WIDZĘ „{w['klasa']}” (pewność {w['pewnosc']:.2f})")
            if pokazuj:
                pokaz(D.wykryj(img, prog, rozdzielczosc, wielkosc)[1], tytuly=[f"znaleziono po obrocie o {obrocono}°"])
            poprawka = (0.5 - w["srodek_x"]) * K.KAMERA_KAT_POZIOMY
            if abs(poprawka) > 5:
                obroc(poprawka, predkosc_obrotu=0.5)
            return w
        _info(f"kąt {obrocono:3d}°: nic")
        obroc(krok, predkosc_obrotu=0.6)
        obrocono += krok
    _info("Pełny obrót — obiektu nie widać.")
    return None


def podjedz_do_obiektu(prog=0.3, dol_stop=0.90, predkosc=0.10, krok_jazdy_s=0.8, rozdzielczosc=640,
                       wielkosc="maly", limit_s=120, min_odleglosc_lidar=0.15):
    """Podjeżdża do widocznego obiektu, poprawiając kierunek po każdym kroku.

    dol_stop     — zatrzymaj, gdy dolna krawędź ramki zejdzie tak nisko w obrazie (0–1); większa = bliżej obiektu
    predkosc     — prędkość jazdy [m/s];  krok_jazdy_s — jak długo jechać między kolejnymi zdjęciami
    min_odleglosc_lidar — awaryjne zatrzymanie, gdy LiDAR widzi coś (np. pudło) bliżej niż tyle metrów
    Zwraca True, gdy dojechał.
    """
    _wymaga_robota("Dojazd do obiektu")
    D = _detektor()
    t0, zgubiony, kroki = time.time(), 0, 0
    try:
        while time.time() - t0 < limit_s:
            img = _swieze_zdjecie(0.2)
            w = D.najlepsze(img, prog=prog, rozdzielczosc=rozdzielczosc, wielkosc=wielkosc)
            if w is None:
                zgubiony += 1
                _info(f"nie widzę obiektu ({zgubiony}/3)")
                if zgubiony >= 3:
                    _info("Zgubiłem obiekt — przerwano dojazd.")
                    return False
                continue
            zgubiony = 0
            if w["dol"] >= dol_stop:
                _info(f"JESTEM PRZY OBIEKCIE (dolna krawędź {w['dol']:.2f}, {kroki} kroków, "
                      f"{time.time() - t0:.0f} s)")
                pokaz(D.wykryj(img, prog, rozdzielczosc, wielkosc)[1], tytuly=["koniec dojazdu"])
                return True
            przod = odleglosc(0, szerokosc=10)
            if przod == przod and przod < min_odleglosc_lidar:
                _info(f"LiDAR: przeszkoda {przod:.2f} m przed robotem — stoję.")
                return False
            blad = w["srodek_x"] - 0.5                      # >0: obiekt na prawo od środka obrazu
            if abs(blad) > 0.12:
                obroc(-blad * K.KAMERA_KAT_POZIOMY * 0.8, predkosc_obrotu=0.5)
            else:
                jedz(predkosc, obrot=-blad * 1.5, czas=krok_jazdy_s)
            kroki += 1
        _info(f"Przekroczono limit {limit_s} s.")
        return False
    finally:
        stop()


def szukaj_obiektu(punkty, rozgladaj_na_starcie=True, krok=30, prog=0.3, rozdzielczosc=640, wielkosc="maly",
                   dol_stop=0.90):
    """Patrol: rozgląda się na miejscu, potem jedzie po kolei do punktów mapy [(x, y), …] i tam się rozgląda.

    Po znalezieniu obiektu podjeżdża do niego. Zwraca dziennik (lista napisów); czas jest liczony od startu.
    """
    _wymaga_robota("Szukanie obiektu")
    t0, dziennik = time.time(), []

    def zapisz(t):
        wpis = f"{time.time() - t0:6.1f} s  {t}"
        dziennik.append(wpis); print(wpis)

    miejsca = ([None] if rozgladaj_na_starcie else []) + list(punkty)
    for p in miejsca:
        if p is not None:
            zapisz(f"jadę do punktu obserwacyjnego ({p[0]}, {p[1]})")
            if not jedz_do(p[0], p[1], podglad=False):
                zapisz("nie dojechałem — następny punkt")
                continue
        zapisz("rozglądam się")
        w = rozejrzyj_sie(krok, prog, rozdzielczosc, wielkosc, pokazuj=False)
        if w:
            zapisz(f"ZNALEZIONO „{w['klasa']}” (pewność {w['pewnosc']:.2f}) — podjeżdżam")
            ok = podjedz_do_obiektu(prog, dol_stop, rozdzielczosc=rozdzielczosc, wielkosc=wielkosc)
            try:
                x, y, _, _ = gdzie_jestem()
                zapisz(f"{'DOJECHAŁEM' if ok else 'dojazd przerwany'} — robot na mapie: x={x:.2f}, y={y:.2f}")
            except Exception:
                zapisz("DOJECHAŁEM" if ok else "dojazd przerwany")
            return dziennik
    zapisz("obiektu nie znaleziono w żadnym punkcie")
    return dziennik


def zatrzymaj_wszystko():
    """Awaryjnie: zatrzymuje robota, nawigację i SLAM."""
    try:
        anuluj()
    except Exception:
        pass
    _Podglad.zatrzymaj_aktywny()
    zatrzymaj_nawigacje(cicho=True)
    zatrzymaj_slam(cicho=True)
    stop()
    _info("Wszystko zatrzymane.")
