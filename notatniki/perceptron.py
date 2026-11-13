"""
perceptron — interaktywne ćwiczenie „hamuj / jedź” (bez robota, działa na każdym komputerze).

Neuron liczy sumę ważoną:  s = w1·x1 + w2·x2 + b  i decyduje: s > 0 → HAMUJ, w przeciwnym razie → JEDŹ.

Wersja uproszczona dla uczniów bez programowania (2026-11-12): wykres pokazuje WPROST, gdzie neuron hamuje
(czerwone tło) i gdzie jedzie (zielone tło), a pod wykresem jest jedno konkretne obliczenie s krok po kroku.

Dane (sytuacje drogowe) są generowane z reguły „prawdziwej” (nieznanej uczestnikom):
  * część A (jedno wejście):  HAMUJ, gdy odległość < 0.40 m
  * część B (dwa wejścia):    HAMUJ, gdy odległość < 0.15 m + 1.2 s · prędkość   (droga hamowania rośnie z prędkością)
Punkty leżące bardzo blisko granicy są pomijane, żeby zadanie było rozwiązywalne w 100%.

Funkcje:
  dane_A(), dane_B()      — zbiory sytuacji (stałe ziarno losowania, każdy zespół ma te same)
  suwaki_A()              — 2 suwaki (waga, bias); waga startuje od −1, bias przesuwa granicę hamowania
  suwaki_B()              — 2 suwaki (waga prędkości, bias); waga odległości stała = −1 (jak w części A)
  uczenie_B(epoki)        — automatyczne uczenie regułą perceptronu, z wykresami postępu

Rozwiązania (dla prowadzącego, sprawdzone siatką): A: waga −1, bias 0.35–0.45 (granica = bias).
B: np. waga prędkości 1.2 i bias 0.15; działa szeroki zakres (waga prędkości ok. 0.8–1.5 z biasem 0.0–0.27).
"""
import numpy as np
import matplotlib.pyplot as plt

CZERWONY, ZIELONY = "#d62728", "#2ca02c"


def dane_A(n=24, ziarno=1):
    rng = np.random.default_rng(ziarno)
    d = rng.uniform(0.05, 1.5, 4 * n)
    d = d[np.abs(d - 0.40) > 0.04][:n]
    return d, (d < 0.40).astype(int)


def dane_B(n=60, ziarno=2):
    rng = np.random.default_rng(ziarno)
    d, v = rng.uniform(0.05, 1.2, 4 * n), rng.uniform(0.0, 0.6, 4 * n)
    granica = 0.15 + 1.2 * v
    ok = np.abs(d - granica) > 0.05
    d, v = d[ok][:n], v[ok][:n]
    return np.stack([d, v], 1), (d < 0.15 + 1.2 * v).astype(int)


def _decyzja(s):
    return (s > 0).astype(int)


def _slowo(s):
    return "HAMUJ" if s > 0 else "JEDŹ"


def _liczba(x):
    """Liczba po polsku (przecinek) w nawiasie, jeśli ujemna — do czytelnego zapisu obliczeń."""
    t = f"{x:.2f}".replace(".", ",")
    return f"({t})" if x < 0 else t


def suwaki_A():
    """Jedno wejście: odległość. Przesuń suwaki tak, żeby neuron hamował tylko przy czerwonych kropkach."""
    import ipywidgets as W
    d, y = dane_A()
    przyklad = 0.30                                    # stała sytuacja do pokazania obliczenia

    def rysuj(waga=-1.0, bias=0.0):
        xs = np.linspace(0, 1.6, 801)
        hamuje = _decyzja(waga * xs + bias)
        dec = _decyzja(waga * d + bias)
        poprawne = int((dec == y).sum())

        fig, ax = plt.subplots(figsize=(9, 2.6))
        # tło: decyzja neuronu w każdym miejscu osi
        ax.fill_between(xs, 0, 1, where=hamuje == 1, color=CZERWONY, alpha=0.18, step="mid", lw=0)
        ax.fill_between(xs, 0, 1, where=hamuje == 0, color=ZIELONY, alpha=0.18, step="mid", lw=0)
        for i in range(len(d)):
            kolor = CZERWONY if y[i] else ZIELONY
            ax.scatter(d[i], 0.5, s=110, c=kolor, marker="o" if dec[i] == y[i] else "X", edgecolors="k", zorder=3)
        if abs(waga) > 1e-9 and 0 < -bias / waga < 1.6:
            g = -bias / waga
            ax.axvline(g, color="k", lw=2)
            ax.text(g + 0.01, 0.08, f"granica: {_liczba(g)} m", ha="left", va="bottom", fontsize=10)
        ax.set_xlim(0, 1.6); ax.set_ylim(0, 1); ax.set_yticks([])
        ax.set_xlabel("odległość od przeszkody [m]")
        ax.set_title(f"Poprawne decyzje: {poprawne} / {len(d)}" + ("   ✔ BRAWO!" if poprawne == len(d) else ""),
                     fontsize=11, color="darkgreen" if poprawne == len(d) else "black")
        plt.show()
        s = waga * przyklad + bias
        print(f"Przykład: odległość {_liczba(przyklad)} m  →  s = {_liczba(waga)} · {_liczba(przyklad)} + {_liczba(bias)}"
              f" = {_liczba(s)}  →  {'s > 0' if s > 0 else 's ≤ 0'}  →  {_slowo(s)}")

    W.interact(rysuj,
               waga=W.FloatSlider(value=-1.0, min=-3, max=3, step=0.1, description="waga"),
               bias=W.FloatSlider(value=0.0, min=-1.5, max=1.5, step=0.01, description="bias"))


def _rysuj_B(ax, X, y, wd, wv, b, tytul):
    """Tło = decyzja neuronu w każdym punkcie (odległość, prędkość); kropki = poprawna odpowiedź; X = błąd."""
    gd, gv = np.meshgrid(np.linspace(0, 1.3, 261), np.linspace(-0.02, 0.65, 135))
    tlo = _decyzja(wd * gd + wv * gv + b)
    ax.contourf(gd, gv, tlo, levels=[-0.5, 0.5, 1.5], colors=[ZIELONY, CZERWONY], alpha=0.18)
    if tlo.min() != tlo.max():
        ax.contour(gd, gv, tlo, levels=[0.5], colors="k", linewidths=2)
    dec = _decyzja(X[:, 0] * wd + X[:, 1] * wv + b)
    for klasa, kolor in [(1, CZERWONY), (0, ZIELONY)]:
        for traf, znak in [(True, "o"), (False, "X")]:
            m = (y == klasa) & ((dec == y) == traf)
            ax.scatter(X[m, 0], X[m, 1], c=kolor, marker=znak, s=60 if znak == "o" else 120, edgecolors="k", zorder=3)
    ax.set_xlim(0, 1.3); ax.set_ylim(-0.02, 0.65)
    ax.set_xlabel("odległość od przeszkody [m]"); ax.set_ylabel("prędkość robota [m/s]")
    ok = int((dec == y).sum())
    ax.set_title(f"{tytul}: poprawne {ok} / {len(y)}" + ("  ✔ BRAWO!" if ok == len(y) else ""),
                 fontsize=11, color="darkgreen" if ok == len(y) else "black")
    return ok


def suwaki_B():
    """Dwa wejścia: odległość i prędkość. Waga odległości jest stała (−1, jak w części A); dobierasz 2 suwaki."""
    import ipywidgets as W
    X, y = dane_B()
    WAGA_ODLEGLOSCI = -1.0
    przyklad = (0.50, 0.40)                            # szybka jazda, pół metra od przeszkody → powinien hamować

    def rysuj(waga_predkosci=0.0, bias=0.40):
        fig, ax = plt.subplots(figsize=(7, 5))
        _rysuj_B(ax, X, y, WAGA_ODLEGLOSCI, waga_predkosci, bias, "Neuron")
        plt.show()
        d, v = przyklad
        s = WAGA_ODLEGLOSCI * d + waga_predkosci * v + bias
        print(f"Przykład: odległość {_liczba(d)} m, prędkość {_liczba(v)} m/s  →  "
              f"s = {_liczba(WAGA_ODLEGLOSCI)} · {_liczba(d)} + {_liczba(waga_predkosci)} · {_liczba(v)} + {_liczba(bias)}"
              f" = {_liczba(s)}  →  {_slowo(s)}")

    print(f"waga odległości = {WAGA_ODLEGLOSCI} (stała, jak w części A). Dobierz wagę prędkości i bias.")
    W.interact(rysuj,
               waga_predkosci=W.FloatSlider(value=0.0, min=-1, max=3, step=0.05, description="waga prędk."),
               bias=W.FloatSlider(value=0.40, min=-0.5, max=1.0, step=0.01, description="bias"))


def uczenie_B(epoki=40, tempo=0.1, pokaz_epoki=(0, 1, 5, None)):
    """Uczenie regułą perceptronu: po każdym błędzie wagi przesuwają się trochę w stronę poprawnej odpowiedzi.

    Zwraca nauczone wagi (waga_odleglosci, waga_predkosci, bias).
    """
    X, y = dane_B()
    rng = np.random.default_rng(0)
    w = np.zeros(3)                                    # wd, wv, b — start: same zera
    historia, migawki = [int((_decyzja(X @ w[:2] + w[2]) == y).sum())], {0: w.copy()}   # historia[0] = przed uczeniem
    for e in range(1, epoki + 1):
        for i in rng.permutation(len(y)):
            x = np.array([X[i, 0], X[i, 1], 1.0])
            blad = y[i] - _decyzja(np.array([w @ x]))[0]   # +1, 0 lub −1
            w += tempo * blad * x
        trafione = int((_decyzja(X @ w[:2] + w[2]) == y).sum())
        historia.append(trafione)
        migawki[e] = w.copy()
        if trafione == len(y):
            break
    ostatnia = len(historia) - 1
    epoki_do_pokazania = sorted({ostatnia if p is None else min(p, ostatnia) for p in pokaz_epoki})
    fig, osie = plt.subplots(1, len(epoki_do_pokazania) + 1, figsize=(4.2 * (len(epoki_do_pokazania) + 1), 4))
    for ax, e in zip(osie, epoki_do_pokazania):
        wd, wv, b = migawki[e]
        _rysuj_B(ax, X, y, wd, wv, b, f"po {e} ep.")
    osie[-1].plot(range(0, ostatnia + 1), historia, "o-")
    osie[-1].set_ylim(0, len(y) + 3); osie[-1].xaxis.get_major_locator().set_params(integer=True)
    osie[-1].axhline(len(y), color="green", ls="--")
    osie[-1].set_xlabel("epoka = jedno przejście przez wszystkie przykłady"); osie[-1].set_ylabel("poprawne decyzje")
    osie[-1].set_title("Postęp uczenia")
    plt.tight_layout(); plt.show()
    wd, wv, b = migawki[ostatnia]
    print(f"Nauczone wagi: waga odległości = {wd:.2f}, waga prędkości = {wv:.2f}, bias = {b:.2f}")
    print(f"Poprawne decyzje: {historia[-1]} / {len(y)} po {ostatnia} epokach.")
    if abs(wd) > 1e-9:
        print(f"Po podzieleniu przez {abs(wd):.2f} (żeby waga odległości była −1, jak u Was): "
              f"waga prędkości = {wv / abs(wd):.2f}, bias = {b / abs(wd):.2f}")
    return wd, wv, b
