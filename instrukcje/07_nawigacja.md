# Ćwiczenie 7: autonomiczna jazda na mapie, czyli zadania na torze (35 min)

**Notatnik:** `07_nawigacja.ipynb`
**Potrzebne:** Wasza mapa `zespolN_najlepsza` (albo mapa prowadzącego `tor_prowadzacy`), punkty **S, A, B** oznaczone na Waszym torze (współrzędne na tablicy), karton jako „nowa przeszkoda”, obiekt do znalezienia (kaczka) ukryty przez prowadzącego

## Cel

Uruchomić nawigację autonomiczną: robot sam ustala, gdzie jest na mapie, planuje trasę do celu, omija przeszkody, a na koniec sam odnajduje obiekt w pomieszczeniu i do niego podjeżdża.

## Trochę teorii

Nawigacja składa się z trzech elementów:
1. **Lokalizacja (AMCL)**: robot ustala, gdzie jest na **gotowej** mapie, porównując skan LiDAR-u z mapą. Używa wielu hipotez położenia, czyli **cząstek** (na podglądzie mapy to chmura niebieskich strzałek). Na początku cząstki są rozrzucone. Gdy robot jedzie, te, które nie pasują do skanu, znikają, a chmura się zawęża.
2. **Planer globalny**: wyznacza trasę od położenia robota do celu po mapie (zielona linia na podglądzie mapy).
3. **Planer lokalny**: prowadzi robota wzdłuż trasy i na bieżąco omija przeszkody, które widzi LiDAR, także te, których nie było na mapie.

Współrzędne mapy: punkt **S** to (0, 0), oś **x** biegnie wzdłuż linii startowej, oś **y** w lewo. Jednostką są metry.

## Kroki

### Krok 1: start nawigacji i lokalizacja (7 min)
1. Uruchom `uruchom_nawigacje("zespolN_najlepsza")`. Start trwa do 1 minuty.
2. Postaw robota na punkcie **S** i uruchom `ustaw_pozycje_startowa(0, 0, 0)`.
3. Uruchom `panel_sterowania(podglad=True)` i obejrzyj na mapie chmurę cząstek. Przejedź kawałek, obracając się powoli. Co się dzieje z chmurą?
4. Uruchom `gdzie_jestem()`. Jaka jest niepewność położenia przed jazdą i po niej?

Niepewność przed jazdą: ______ cm, po jeździe: ______ cm

### Zadanie A: dojazd do celu (7 min)
Ustaw w komórce współrzędne punktu **A** (z tablicy) i uruchom `jedz_do(x, y)`. Gdy robot stanie, zmierzcie miarką odległość środka robota od punktu A. Powtórz dla punktu **B**.

### Zadanie B: nowa przeszkoda (7 min)
1. Postaw karton na trasie z A do B, w miejscu, gdzie na mapie jest pusto.
2. Wyślij robota do celu i obserwuj na podglądzie mapy (pojawia się pod komórką `jedz_do`), jak planer zmienia trasę.
3. Zmień parametry komórką `ustaw_parametry_nawigacji(...)` i powtórz:
   - `odleglosc_bezpieczenstwa`: 0,10 m, potem 0,35 m. Jak blisko przeszkód jedzie robot? Czy zmieści się w wąskim przejeździe?
   - `maks_predkosc`: 0,10 m/s, potem 0,25 m/s.

### Zadanie C: znajdź kaczkę (12 min)
Prowadzący ukrywa kaczkę gdzieś na torze. Robot ma ją **sam** znaleźć i do niej podjechać.

Kaczka jest niższa niż wiązka LiDAR-u, więc LiDAR jej nie widzi, a nawigacja nie traktuje jej jak przeszkody. Robot szuka jej **kamerą i siecią z ćwiczenia 6**: obraca się, robi zdjęcia i sprawdza, czy sieć coś wykrywa. Gdy znajdzie kaczkę, podjeżdża: ustawia się tak, żeby kaczka była na środku obrazu, jedzie kawałek i powtarza. Zatrzymuje się, gdy kaczka jest już nisko w obrazie, czyli blisko robota.

1. **C1: rozglądanie się (3 min).** Ustaw kaczkę ok. 1 m od robota, z boku albo z tyłu. Ustaw zapytanie i próg z ćwiczenia 6, a potem uruchom `rozejrzyj_sie()`. Po ilu obrotach robot ją znalazł? Sprawdź też inny `krok` obrotu (np. 45° zamiast 30°).
2. **C2: dojazd (3 min).** Uruchom `podjedz_do_obiektu()`. Zmierz miarką, jak daleko od kaczki robot się zatrzymał. Zmień `dol_stop`, żeby zatrzymał się ok. 15–20 cm przed kaczką.
3. **C3: poszukiwania (6 min).** Kaczka jest ukryta na torze. Na swojej mapie wybierzcie **punkty obserwacyjne**, z których robot się rozejrzy, i ustalcie ich kolejność. Uruchom `szukaj_obiektu(punkty)`. Robot rozejrzy się na miejscu, a potem będzie jeździł po punktach, aż znajdzie kaczkę i do niej podjedzie. Komórka wypisze dziennik z czasem.

| Próba | Punkty obserwacyjne | krok [°] | Czas znalezienia [s] | Czas do zatrzymania przy kaczce [s] | Odległość od kaczki [cm] |
|---|---|---|---|---|---|
| 1 | | | | | |
| 2 | | | | | |

Wygrywa zespół, którego robot najszybciej dojedzie do kaczki.

### Dziennik prób

Pracujcie w cyklu **test → analiza → korekta parametrów → kolejny test**.

| Próba | Zadanie | Zmienione parametry | Dotarł? (T/N) | Czas [s] | Odległość od celu [cm] | Co się stało? |
|---|---|---|---|---|---|---|
| 1 | A | domyślne | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |
| 6 | | | | | | |

## Pytania do przemyślenia

1. Czym różni się **lokalizacja** (AMCL) od **budowy mapy** (SLAM)? Dlaczego w tym ćwiczeniu nie uruchamialiśmy SLAM?
2. Co się stanie, gdy podasz robotowi **błędną** pozycję startową (np. 1 m obok)? Sprawdźcie, jeśli starczy czasu.
3. Dlaczego robot podjeżdża do kaczki „skokami” (jedzie, staje, patrzy)? Wymieńcie wszystkie źródła opóźnienia (kamera → Wi-Fi → sieć neuronowa → decyzja → silniki).
4. Jak wybraliście punkty obserwacyjne? Co by się stało, gdyby kaczka stała za pudłem?
5. Kto odpowiada za to, gdy autonomiczny pojazd popełni błąd: programista, producent czujnika, właściciel czy ktoś inny?

> **Jeśli coś nie działa.**
> - „PRZERWANO, nie da się dojechać”: cel leży w przeszkodzie albo zbyt blisko ściany. Zmniejsz `odleglosc_bezpieczenstwa` albo wybierz inny punkt.
> - Robot kręci się w miejscu: lokalizacja się zgubiła. Ustaw ponownie pozycję startową.
> - Robot „nie widzi” kaczki, choć stoi ona przed nim: obniż próg, zmień zapytanie albo ustaw rozdzielczość 640.
> - Robot jedzie do czegoś innego: podnieś próg albo zmień zapytanie na dokładniejsze.
> - Awaryjnie: `zatrzymaj_wszystko()`.
