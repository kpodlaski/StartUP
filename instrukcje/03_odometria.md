# Ćwiczenie 3: odometria, czyli dlaczego robot się gubi (15 min)

**Notatnik:** `03_odometria.ipynb`
**Potrzebne:** taśma malarska, miarka, kawałek wolnej podłogi ok. 1,5 × 1,5 m

## Cel

Sprawdzić, jak dokładnie robot zna swoje położenie, gdy liczy je tylko z obrotów kół.

## Trochę teorii

**Odometria** to obliczanie położenia na podstawie tego, ile obrotów wykonały koła. Robot „wie”, że koło o obwodzie 20 cm obróciło się 5 razy, więc uznaje, że przejechał 1 m. Tak samo liczy obroty. Problem w tym, że koła się **ślizgają**, a dwa silniki **nigdy nie są identyczne**. Każdy mały błąd dokłada się do poprzednich, a robot nie ma jak tego zauważyć.

## Kroki

### Krok 1: oznaczenie startu (2 min)
Przyklej na podłodze taśmą **krzyżyk** (punkt startu) i **linię kierunku**. Ustaw robota tak, żeby środek między kołami był nad krzyżykiem, a przód był skierowany wzdłuż linii. Przyklej też kawałek taśmy przy przednim brzegu robota, żeby potem zmierzyć kąt.

### Krok 2: przejazd po kwadracie (4 min)
Uruchom `przejazd_po_kwadracie(bok=1.0)`. Robot przejedzie kwadrat 1 × 1 m, skręcając w lewo, i zatrzyma się tam, gdzie **według odometrii** jest start.

Gdy robot stanie, zmierzcie miarką, jak daleko środek robota jest od krzyżyka (w cm). Pomiar obrotu robota względem linii kierunku jest szacunkowy.

### Krok 3: kolejne przejazdy (6 min)
Za każdym razem ustaw robota dokładnie na krzyżyku. W komórkach zmieniasz parametry oznaczone `# ZMIEŃ TUTAJ`.

| Przejazd | Bok [m] | Prędkość [m/s] | Okrążenia | Odległość od startu wg odometrii [cm] | Odległość od startu z miarki [cm] | Obrót względem linii [°] |
|---|---|---|---|---|---|---|
| 1 | 1,0 | 0,15 | 1 | | | |
| 2 | 1,0 | 0,15 | 1 (powtórzenie) | | | |
| 3 | 1,0 | 0,30 | 1 | | | |
| 4 | 1,0 | 0,15 | 2 | | | |

### Krok 4: trasa według robota (1 min)
Uruchom `rysuj_trase(...)`. Wykres pokazuje, jak robot **wyobraża sobie** swoją trasę.

## Pytania do przemyślenia

1. Robot „sądzi”, że wrócił do startu. Gdzie jest naprawdę? Czy przy powtórzeniu błąd jest taki sam?
2. Jak zmienia się błąd przy większej prędkości? A przy dwóch okrążeniach?
3. Gdyby robot przejechał tak 100 m, czy nadal wiedziałby, gdzie jest?
4. Czego robot potrzebuje, żeby **poprawić** swoje położenie? *(Podpowiedź: co widzi LiDAR? Zobacz ćwiczenie 4.)*

> **Wniosek do zapamiętania.** Odometria jest dobra na krótkich odcinkach, ale jej błąd **narasta bez końca**. Dlatego robot musi porównywać to, co widzi, z mapą otoczenia. Na tym polega **SLAM**.
