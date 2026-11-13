# Ćwiczenie 6: gotowa sieć neuronowa szuka obiektów, czyli jak zapytać sieć (20 min)

**Notatnik:** `06_detektor.ipynb`
**Potrzebne:** obiekt do szukania (np. czerwona gumowa kaczka) na podłodze przed robotem, kilka innych przedmiotów (krzesło, plecak, pudełko), miarka, „obiekty-zagadki” od prowadzącego

## Cel

Sprawdzić, co potrafią gotowe sieci rozpoznające obiekty, nauczyć się dobierać zapytanie słowne i wybrać ustawienia do zadania „znajdź obiekt” w ćwiczeniu 7.

## Trochę teorii

Porównamy dwa rodzaje gotowych, wytrenowanych sieci:

- **Sieć z zamkniętą listą klas (YOLO, zbiór COCO).** Nauczona na ponad 100 000 opisanych zdjęć rozpoznaje **80 rodzajów obiektów**: osobę, krzesło, plecak, butelkę, kubek i inne. Czego nie ma na liście, tego nie wykryje. Najwyżej pomyli to z czymś podobnym.
- **Sieć z otwartym słownikiem (YOLOE).** Tej sieci mówisz słowami (po angielsku), czego ma szukać, np. `"rubber duck"`. Nauczyła się łączyć obrazy z opisami słownymi, więc znajduje obiekty, na których **nikt jej specjalnie nie uczył**. Wynik zależy jednak od tego, **jak zapytasz**.

Dla każdego wykrytego obiektu sieć podaje **ramkę** (gdzie on jest) i **pewność** (od 0 do 1). Wykrycia słabsze od **progu pewności** są odrzucane.

Sieci działają na **procesorze** stacji. Jedno zdjęcie analizują przez kilkaset milisekund, czyli ok. 2–10 zdjęć na sekundę.

## Kroki

### Krok 1: sieć z zamkniętą listą (3 min)
Postaw kaczkę ok. 1 m przed robotem, a obok krzesło i plecak. Uruchom komórkę z modelem `"coco"`.

- Co wykryła sieć? ______________________________________________
- Czy wykryła kaczkę? Jeśli tak, to jako co? ______________________

### Krok 2: zapytaj słowami (5 min)
Uruchom komórkę `porownaj_slowa`. Sprawdza ona wiele opisów na tym samym zdjęciu i pokazuje, przy którym sieć jest najpewniejsza. Dopisz do listy **własne pomysły** (co najmniej 4).

| Opis (zapytanie) | Pewność | Uwagi |
|---|---|---|
| `duck` | | |
| `rubber duck` | | |
| `kaczka` (po polsku) | | |
| `bird` | | |
| | | |
| | | |
| | | |
| | | |

Najlepsze zapytanie: ______________________

### Krok 3: słowa konkurują (2 min)
Ustaw w `ustaw_slowa` jednocześnie Twoje najlepsze zapytanie i inne słowa, np. `["rubber duck", "box", "toy"]`. Czy pewność wykrycia kaczki się zmieniła? Czy pojawiły się nowe wykrycia? ______________________

### Krok 4: obiekt-zagadka (4 min)
Prowadzący daje zespołowi przedmiot. Ustawcie go przed robotem i znajdźcie zapytanie, przy którym sieć wykrywa go z pewnością **powyżej 0,5**. Wygrywa zespół, który zrobi to najszybciej.

Przedmiot: ________________ najlepsze zapytanie: ________________ pewność: ______

### Krok 5: odległość, rozdzielczość, szybkość (4 min)
Ustawiaj kaczkę w różnych odległościach. Dla każdej odległości uruchom komórkę, która sprawdza rozdzielczości 320 i 640.

| Odległość [m] | Pewność przy 320 px | Pewność przy 640 px |
|---|---|---|
| 0,5 | | |
| 1,0 | | |
| 2,0 | | |
| 3,0 | | |

Szybkość: 320 px: ______ zdjęć/s, 640 px: ______ zdjęć/s

### Krok 6: decyzja zespołu (2 min)
Wybierzcie ustawienia do ćwiczenia 7, w którym robot ma sam znaleźć obiekt i do niego podjechać.

- Zapytanie: ________________ próg: ______ rozdzielczość: ______
- Uzasadnienie: ______________________________________________

## Pytania do przemyślenia

1. Dlaczego sieć z zamkniętą listą nie może wykryć kaczki, choć „widzi” ją na zdjęciu?
2. Dlaczego zapytanie po polsku działa gorzej niż po angielsku? *(Podpowiedź: na jakich opisach uczono sieć?)*
3. Robot ma szukać obiektu w całym pomieszczeniu. Co jest ważniejsze: duża rozdzielczość (widać daleko) czy szybkość? Czy da się połączyć jedno i drugie, np. szukać dokładnie, a podjeżdżać szybko?
4. Co jest gorsze dla robota szukającego obiektu: **fałszywe wykrycie** (pojedzie do czegoś innego) czy **przeoczenie**? Jak to wpływa na wybór progu?
