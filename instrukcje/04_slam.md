# Ćwiczenie 4: SLAM, czyli budujemy mapę (40 min)

**Notatnik:** `04_slam.ipynb`
**Potrzebne:** tor z przeszkodami, punkt startowy **S** Waszego toru oznaczony na podłodze (wspólny dla zespołów jeżdżących na tym torze)

## Cel

Zbudować mapę toru metodą SLAM, sprawdzić, jak parametry algorytmu wpływają na jakość mapy, i zapisać najlepszą mapę do części II.

## Trochę teorii

**SLAM** (*Simultaneous Localization and Mapping*) to jednoczesna lokalizacja i budowa mapy. Robot rysuje mapę z kolejnych skanów LiDAR-u. Jednocześnie porównuje każdy nowy skan z tym, co już narysował, i na tej podstawie **poprawia swoje położenie**, czyli koryguje błąd odometrii z ćwiczenia 3.

Mapa to siatka kratek. Każda kratka może być:
- **wolna** (biała): tu nie ma przeszkody,
- **zajęta** (czarna): tu jest przeszkoda,
- **nieznana** (szara): robot jeszcze tu nie „zajrzał”.

**Zamknięcie pętli** (*loop closure*) zachodzi, gdy robot wraca w miejsce, które już zna. Algorytm zauważa, że „to tu już było”, i prostuje całą mapę.

**Jak zbudowany jest robot w ROS (Robot Operating System).** Oprogramowanie robota to wiele osobnych programów, czyli **węzłów**. Jeden obsługuje LiDAR, drugi silniki, trzeci SLAM. Wasz notatnik na stacji też jest węzłem. Węzły wymieniają się wiadomościami przez **tematy**. Na przykład LiDAR publikuje skany w temacie `/scan`, a SLAM je stamtąd odbiera i publikuje mapę w temacie `/map`.

## Zasady jazdy podczas budowy mapy

- Jedź **wolno**, a obracaj się jeszcze wolniej. Szybki obrót „rozmazuje” mapę.
- Objedź cały tor i **wróć do miejsc, które już robot widział**, żeby zamknąć pętlę.
- Nie stawajcie wszyscy wokół robota, bo LiDAR narysuje Wasze nogi jako ściany.

## Kroki

### Krok 1: ROS od środka (3 min)
Uruchom `wezly_i_tematy()`. Znajdź na liście węzeł LiDAR-u i temat `/scan`, a także temat, którym wysyłane są polecenia jazdy (`/cmd_vel`).

### Krok 2: pierwsza mapa z parametrami domyślnymi (12 min)
1. **Ustaw robota na punkcie S**, przodem wzdłuż oznaczonej linii. Punkt S będzie środkiem mapy (x = 0, y = 0), a kierunek linii to oś x.
2. Uruchom `uruchom_slam()`. Komunikat potwierdzi, że SLAM działa.
3. Uruchom `panel_sterowania(podglad=True)` i objedź tor przyciskami. Obok przycisków zobaczysz mapę na żywo: robot (fioletowa strzałka), skan LiDAR-u (czerwone punkty) i rosnącą mapę. Obserwuj, jak mapa rośnie.
4. Obserwuj zamknięcie pętli: co się dzieje z mapą, gdy robot wraca w znane miejsce?
5. Uruchom `pokaz_mape()` i zapisz wynik do tabeli. Uruchom `zapisz_mape("zespolN_mapa1")`, wstawiając zamiast N numer zespołu.

### Krok 3: eksperymenty z parametrami (18 min)
Prowadzący przydzieli Waszemu zespołowi **dwa eksperymenty** z listy poniżej. Przed każdym eksperymentem: robot na punkt S, uruchomić komórkę z nowymi parametrami (SLAM zaczyna od pustej mapy), objechać tor tak samo jak w kroku 2.

| Eksperyment | Co zmieniamy | Parametry w notatniku |
|---|---|---|
| A | grubsza siatka | `rozdzielczosc=0.10` |
| B | drobniejsza siatka | `rozdzielczosc=0.02` |
| C | „krótkowzroczny” LiDAR | `zasieg=1.0` |
| D | rzadkie aktualizacje mapy | `aktualizacja=10.0` |
| E | mało hipotez położenia | `czastki=5` |
| F | szybka jazda i szybkie obroty | domyślne parametry; w panelu prędkość 0,3 i obrót 2,0 |

| Mapa | Parametry | Czas objazdu [min] | Zbadany obszar [m²] | Czy pętla się zamknęła? | Ocena mapy 1–5 | Co jest nie tak? |
|---|---|---|---|---|---|---|
| mapa1 | domyślne (0,05 / 6,0 / 2,0 / 30) | | | | | |
| | | | | | | |
| | | | | | | |

Kryteria oceny mapy: proste ściany (nie „podwójne”), przeszkody w dobrych miejscach, brak dziur, kształt toru zgodny z rzeczywistością.

### Krok 4: najlepsza mapa (7 min)
Ustawcie parametry, które dały najlepszą mapę, zbudujcie ją jeszcze raz starannie i zapiszcie jako **`zespolN_najlepsza`**. Ta mapa posłuży w ćwiczeniu 7. Na koniec uruchom `zatrzymaj_slam()`.

## Pytania do przemyślenia

1. Co się stało z mapą przy szybkiej jeździe i szybkich obrotach? Dlaczego?
2. Drobniejsza siatka daje dokładniejszą mapę. Jaka jest cena? *(Pomyśl o pamięci i czasie obliczeń.)*
3. Dlaczego długi, pusty korytarz bez charakterystycznych punktów jest trudny dla SLAM?
4. *(Jeśli prowadzący pokazał LiDAR 3D)* Co widzi LiDAR 3D, czego nie widzi 2D?

> **Plan awaryjny.** Jeśli mapa wyszła słabo, a czas się kończy, prowadzący ma gotową mapę toru `tor_prowadzacy`. Wystarczy jej użyć w ćwiczeniu 7.
