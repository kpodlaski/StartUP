# Ćwiczenie 5: neuron, czyli hamuj czy jedź? (10 min)

**Notatnik:** `05_perceptron.ipynb` (nie wymaga robota)

## Cel

Zobaczyć, jak pojedynczy sztuczny neuron podejmuje decyzję i co to znaczy, że sieć neuronowa „uczy się”.

## Trochę teorii

Sztuczny neuron (**perceptron**) dostaje liczby, np. odległość od przeszkody. Mnoży je przez **wagi**, dodaje **bias** (przesunięcie) i sprawdza znak wyniku:

> s = waga · odległość + bias  
> s > 0 → **HAMUJ**, w przeciwnym razie → **JEDŹ**

Cała „wiedza” neuronu to te kilka liczb. **Uczenie** to automatyczne szukanie takich liczb, przy których neuron odpowiada dobrze.

**Jak czytać wykresy:** **tło** pokazuje, co robi neuron (czerwone = HAMUJ, zielone = JEDŹ). **Kropki** pokazują, co powinien zrobić. **✖** oznacza błąd neuronu. Pod wykresem jest przykład obliczenia s.

## Kroki

### Część A: jedno wejście, czyli odległość (3 min)
Waga jest ustawiona na −1. Przesuwaj **bias** i patrz, jak przesuwa się czarna granica. Ustaw go tak, żeby neuron hamował tylko przy czerwonych kropkach (✔ BRAWO).

- Przy jakim biasie się udało? ______ Gdzie jest wtedy granica? ______ m
- Zmień wagę na **+1**. Co robi teraz neuron? Dlaczego waga musi być ujemna?

### Część B: dwa wejścia, czyli odległość i prędkość (4 min)
Przy szybkiej jeździe trzeba hamować wcześniej. Waga odległości zostaje −1. Dobierz **wagę prędkości** i **bias** tak, żeby wszystkie 60 sytuacji było dobrze.

| | waga prędkości | bias | Poprawne (z 60) |
|---|---|---|---|
| Nasze ustawienie | | | |
| Komputer (część C, po podzieleniu) | | | |

### Część C: automatyczne uczenie (3 min)
Uruchom komórkę. Komputer zaczyna od wag równych zero i po każdej pomyłce lekko je poprawia. Na wykresach widać, jak granica przesuwa się po kolejnych **epokach** (epoka to jedno przejście przez wszystkie przykłady). Wpisz wynik do tabeli powyżej.

## Pytania do przemyślenia

1. Czy komputer znalazł te same liczby co Wy? Czy to źle, że są inne? *(Porównaj, gdzie przebiega granica.)*
2. Wasz neuron ma **3** liczby do dobrania. Sieci z ćwiczenia 6 mają ich **ok. 3 miliony** (YOLO z listą 80 klas) i **ok. 14 milionów** (YOLOE, której zadajemy pytania słowami). Czy dałoby się je dobrać suwakami?
3. Do nauczenia takiej sieci potrzeba setek tysięcy opisanych zdjęć i wielu dni pracy kart graficznych. Dlaczego w praktyce korzysta się z **gotowych, wytrenowanych modeli**?
