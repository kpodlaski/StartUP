# Ćwiczenie 1: LiDAR, czyli jak robot mierzy odległość (12 min)

**Notatnik:** `01_lidar.ipynb`
**Potrzebne:** miarka, karton (ok. 30 × 30 cm), zestaw materiałów: biała kartka, czarna matowa tkanina, szyba lub plexi, lusterko, metalowa puszka, kątomierz i linijka (do ustawiania kątów)

## Cel

Sprawdzić, jak dokładnie LiDAR mierzy odległość i w jakich sytuacjach się myli.

## Trochę teorii

LiDAR (*Light Detection and Ranging*) wysyła krótkie impulsy światła laserowego i mierzy, po jakim czasie wracają po odbiciu od przeszkody. Ponieważ światło porusza się ze stałą prędkością, z czasu powrotu można policzyć odległość. Głowica LiDAR-u obraca się kilka razy na sekundę. W ten sposób robot dostaje **kilkaset pomiarów odległości dookoła siebie**. Taki zestaw punktów to **skan** (chmura punktów).

- **LiDAR 2D** (taki jak na Jetbocie) mierzy w jednej płaszczyźnie, na wysokości czujnika. Nie widzi więc przedmiotów niższych lub wyższych od tej płaszczyzny.
- **LiDAR 3D** ma wiele wiązek ustawionych pod różnymi kątami i widzi otoczenie w przestrzeni. Takie czujniki stosuje się w samochodach autonomicznych.

## Kroki

### Krok 1: pierwszy skan (2 min)
Uruchom komórki `polacz()` i `rysuj_skan()`. Widzisz otoczenie robota z góry. Robot to czerwony trójkąt, a jego przód jest skierowany w górę wykresu.

- Gdzie na wykresie są ściany? Gdzie przeszkody na torze?
- Jedna osoba staje przed robotem, a druga ponownie uruchamia `rysuj_skan()`. Jak na skanie wyglądają nogi?

### Krok 2: dokładność pomiaru (4 min)
Ustaw karton **na wprost robota**, prostopadle do niego. Odległość mierz miarką od **środka LiDAR-u** (obrotowej głowicy) do kartonu. Dla każdej odległości uruchom `seria_pomiarow(kat=0)`. Komórka wykona 10 pomiarów i poda średnią oraz rozrzut.

| Odległość z miarki [m] | Średnia z LiDAR-u [m] | Rozrzut (odch. std.) [m] | Błąd = LiDAR − miarka [cm] |
|---|---|---|---|
| 0,30 | | | |
| 0,60 | | | |
| 1,00 | | | |
| 1,50 | | | |

### Krok 3: różne materiały (3 min)
Na kartonie ustawionym w odległości **0,60 m** umieszczaj kolejno różne materiały. **Lusterko** zmierz dwa razy: ustawione na wprost robota i obrócone o ok. 45°. Przy lusterku pod kątem uruchom też `rysuj_skan()`: gdzie jest punkt?

| Materiał | Średnia z LiDAR-u [m] | Ile pomiarów nieudanych (z 10)? | Czy wynik jest wiarygodny? |
|---|---|---|---|
| karton (odniesienie) | | | |
| biała kartka | | | |
| czarna matowa tkanina | | | |
| szyba / plexi | | | |
| lusterko na wprost | | | |
| lusterko pod kątem 45° | | | |
| metalowa puszka | | | |

### Krok 4: przeszkoda pod kątem (2 min)
Karton w odległości **0,60 m**, obracany względem robota. Kąt ustawcie kątomierzem: linijkę przyłóżcie do przedniej ściany kartonu, kątomierz do linijki (0° = karton ustawiony prostopadle do robota).

| Kąt ustawienia kartonu | Średnia z LiDAR-u [m] | Pomiary nieudane (z 10) |
|---|---|---|
| 0° (prostopadle) | | |
| 30° | | |
| 60° | | |
| prawie równolegle (80°) | | |

## Pytania do przemyślenia

1. Czy błąd pomiaru rośnie z odległością? O ile centymetrów może się mylić LiDAR?
2. Przy których materiałach LiDAR zawodzi? Dlaczego? *(Podpowiedź: co dzieje się ze światłem przy szybie, czarnej tkaninie i lustrze? Dlaczego lustro na wprost i pod kątem dało inne wyniki?)*
3. Robot autonomiczny jedzie korytarzem z przeszklonymi drzwiami. Jakie zagrożenie widzisz?
4. Stolik ma blat na wysokości 70 cm i cienkie nogi. Co „zobaczy” LiDAR 2D zamontowany 15 cm nad podłogą?

> **Jeśli coś nie działa.** „Brak poprawnych pomiarów” oznacza, że czujnik nie dostał odbicia. To też wynik, więc wpisz go do tabeli. Jeśli żaden skan się nie pojawia, uruchom `status()` i zawołaj prowadzącego.
