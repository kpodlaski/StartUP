"""
detektor — gotowe sieci neuronowe do wykrywania obiektów, uruchamiane na procesorze stacji (bez douczania).

Dwa rodzaje modeli:
  * "coco"  — YOLOv8n wytrenowany na zbiorze COCO: ZAMKNIĘTA lista 80 klas (osoba, krzesło, plecak, butelka…).
              Czego nie ma na liście (np. gumowej kaczki), tego nie wykryje — najwyżej pomyli z czymś podobnym.
  * "maly" / "sredni" / "duzy" — YOLOE-11 s/m/l: OTWARTY SŁOWNIK. Klasy podaje się słowami (po angielsku),
              np. ["rubber duck"]. Sieć nie była douczana na tych obiektach — porównuje obraz z opisem słownym.
              Wynik zależy od sformułowania i od całej listy słów (słowa „konkurują” ze sobą).

Funkcje dla notatników:
  ustaw_slowa(lista)                                  — czego szukać (modele słowne)
  wykryj(img, prog, rozdzielczosc, wielkosc)          — (wykrycia, obraz_z_ramkami, czas_ms)
  pokaz_wykrycia(img, ...)                            — rysuje ramki i wypisuje tabelę
  porownaj_slowa(img, warianty, cel_xy=None)          — który opis słowny daje najpewniejsze wykrycie
  test_szybkosci(wielkosc, rozdzielczosc)             — czas klatki i klatki/s
  podglad_na_zywo(sekundy, ...)                       — obraz z robota z ramkami, odświeżany w notatniku

Format wykrycia (słownik): klasa, pewnosc, srodek_x, dol, wysokosc — trzy ostatnie względne (0–1) wobec
szerokości / wysokości obrazu; `dol` = dolna krawędź ramki (dla obiektu na podłodze: im większa, tym bliżej robota).

Wagi pobiera Dockerfile przy budowie obrazu (katalog konfiguracja.DETEKTOR_KATALOG_WAG).
"""
import os
import time

import numpy as np
import matplotlib.pyplot as plt

import konfiguracja as K
import jetbot_warsztat as J

_modele = {}            # wielkosc -> model
_slowa_modelu = {}      # wielkosc -> krotka słów aktualnie ustawionych w modelu
_slowa = list(K.DETEKTOR_SLOWA)

NAZWY_PL = {"person": "osoba", "chair": "krzesło", "bottle": "butelka", "cup": "kubek", "backpack": "plecak",
            "bird": "ptak", "apple": "jabłko", "fire hydrant": "hydrant", "sports ball": "piłka", "vase": "wazon",
            "bowl": "miska", "teddy bear": "miś", "laptop": "laptop", "book": "książka"}


def _plik_wag(plik):
    lokalny = os.path.join(K.DETEKTOR_KATALOG_WAG, plik)
    return lokalny if os.path.exists(lokalny) else plik


def _model(wielkosc):
    if wielkosc not in _modele:
        plik = K.DETEKTOR_MODELE[wielkosc]
        if wielkosc == "coco":
            from ultralytics import YOLO
            _modele[wielkosc] = YOLO(_plik_wag(plik))
        else:
            from ultralytics import YOLOE
            _modele[wielkosc] = YOLOE(_plik_wag(plik))
        m = _modele[wielkosc]
        liczba = sum(p.numel() for p in m.model.parameters())
        opis = "80 stałych klas COCO" if wielkosc == "coco" else "otwarty słownik (klasy podajesz słowami)"
        print(f"Model „{wielkosc}” ({plik}): {liczba / 1e6:.1f} mln wag, {opis}.")
    m = _modele[wielkosc]
    if wielkosc != "coco" and _slowa_modelu.get(wielkosc) != tuple(_slowa):
        m.set_classes(list(_slowa), m.get_text_pe(list(_slowa)))
        _slowa_modelu[wielkosc] = tuple(_slowa)
    return m


def zaladuj_model(wielkosc="maly"):
    """Wczytuje model: "coco" (zamknięta lista klas) albo "maly" / "sredni" / "duzy" (otwarty słownik)."""
    _model(wielkosc)


def ustaw_slowa(slowa):
    """Ustala, czego szukają modele słowne, np. ["rubber duck"] albo ["toy duck", "box"]. Słowa po angielsku."""
    global _slowa
    if isinstance(slowa, str):
        slowa = [slowa]
    _slowa = [s.strip() for s in slowa if s.strip()]
    print("Szukam:", ", ".join(f"„{s}”" for s in _slowa))


def wykryj(img, prog=0.25, rozdzielczosc=640, wielkosc="maly"):
    """Zwraca (lista_wykryc, obraz_z_ramkami, czas_ms). img: tablica RGB."""
    m = _model(wielkosc)
    t0 = time.time()
    r = m.predict(img[..., ::-1], conf=prog, imgsz=rozdzielczosc, verbose=False)[0]   # YOLO oczekuje BGR
    czas_ms = (time.time() - t0) * 1000
    h, w = img.shape[:2]
    wykrycia = []
    for b in r.boxes:
        x1, y1, x2, y2 = b.xyxy[0].tolist()
        wykrycia.append({"klasa": r.names[int(b.cls)], "pewnosc": round(float(b.conf), 3),
                         "srodek_x": round((x1 + x2) / 2 / w, 3), "dol": round(y2 / h, 3),
                         "wysokosc": round((y2 - y1) / h, 3), "ramka": (int(x1), int(y1), int(x2), int(y2))})
    return wykrycia, r.plot()[..., ::-1], czas_ms


def _nazwa(k):
    return NAZWY_PL.get(k, k)


def pokaz_wykrycia(img, prog=0.25, rozdzielczosc=640, wielkosc="maly"):
    """Wykrywa obiekty na zdjęciu, rysuje ramki i wypisuje tabelę."""
    wykrycia, obraz, czas_ms = wykryj(img, prog, rozdzielczosc, wielkosc)
    szukane = "lista COCO" if wielkosc == "coco" else ", ".join(_slowa)
    J.pokaz(obraz, tytuly=[f"model {wielkosc} [{szukane}], {rozdzielczosc} px, próg {prog}: {czas_ms:.0f} ms"],
            rozmiar=8)
    if not wykrycia:
        print("Nic nie wykryto.")
    for w in sorted(wykrycia, key=lambda w: -w["pewnosc"]):
        print(f"  {_nazwa(w['klasa']):18s} pewność {w['pewnosc']:.2f}   "
              f"środek w poziomie {w['srodek_x'] * 100:3.0f}%   dolna krawędź {w['dol'] * 100:3.0f}%")
    return wykrycia


def porownaj_slowa(img, warianty, rozdzielczosc=640, wielkosc="maly", cel_xy=None):
    """Sprawdza kilka opisów słownych na tym samym zdjęciu. Wypisuje najwyższą pewność dla każdego.

    warianty — lista opisów, np. ["duck", "rubber duck", "toy duck", "kaczka"]
    cel_xy   — (x, y) w pikselach punktu na szukanym obiekcie; liczą się tylko ramki, które go zawierają
               (żeby nie liczyć pomyłek na innych przedmiotach). Bez tego — najlepsze wykrycie gdziekolwiek.
    Zwraca listę (opis, pewność).
    """
    global _slowa
    zapamietane = list(_slowa)
    wyniki = []
    try:
        for opis in warianty:
            _slowa = [opis]
            wykrycia, _, _ = wykryj(img, 0.01, rozdzielczosc, wielkosc)
            if cel_xy is not None:
                x, y = cel_xy
                wykrycia = [w for w in wykrycia if w["ramka"][0] <= x <= w["ramka"][2]
                            and w["ramka"][1] <= y <= w["ramka"][3]]
            wyniki.append((opis, max((w["pewnosc"] for w in wykrycia), default=0.0)))
    finally:
        _slowa = zapamietane
    for opis, p in sorted(wyniki, key=lambda t: -t[1]):
        print(f"  {opis:28s} {p:5.2f}  {'█' * int(p * 40)}")
    return wyniki


def test_szybkosci(wielkosc="maly", rozdzielczosc=640, ile=10, img=None):
    """Mierzy szybkość modelu: średni czas jednej klatki i liczbę klatek na sekundę."""
    img = J.zdjecie() if img is None else img
    wykryj(img, 0.25, rozdzielczosc, wielkosc)                    # rozgrzewka (pierwsze wywołanie jest wolne)
    czasy = [wykryj(img, 0.25, rozdzielczosc, wielkosc)[2] for _ in range(ile)]
    sr = float(np.mean(czasy))
    print(f"model {wielkosc:6s} rozdzielczość {rozdzielczosc:4d}:  {sr:6.0f} ms/klatkę  →  {1000 / sr:5.1f} kl./s")
    return 1000 / sr


def podglad_na_zywo(sekundy=20, prog=0.25, rozdzielczosc=640, wielkosc="maly"):
    """Pokazuje obraz z kamery robota z ramkami wykryć przez `sekundy` sekund."""
    from IPython.display import display, clear_output
    t0, n = time.time(), 0
    while time.time() - t0 < sekundy:
        img = J.zdjecie()
        wykrycia, obraz, _ = wykryj(img, prog, rozdzielczosc, wielkosc)
        n += 1
        clear_output(wait=True)
        fig, ax = plt.subplots(figsize=(8, 6))
        ax.imshow(obraz); ax.axis("off")
        opis = ", ".join(f"{_nazwa(w['klasa'])} {w['pewnosc']:.2f}" for w in wykrycia) or "nic"
        ax.set_title(f"{n / (time.time() - t0):.1f} kl./s   wykryto: {opis}")
        display(fig); plt.close(fig)
    print("Koniec podglądu.")


def najlepsze(img, klasa=None, prog=0.25, rozdzielczosc=640, wielkosc="maly"):
    """Najpewniejsze wykrycie (opcjonalnie tylko danej klasy) albo None. Używane przy szukaniu obiektu."""
    wykrycia, _, _ = wykryj(img, prog, rozdzielczosc, wielkosc)
    if klasa is not None:
        wykrycia = [w for w in wykrycia if w["klasa"] == klasa]
    return max(wykrycia, key=lambda w: w["pewnosc"]) if wykrycia else None
