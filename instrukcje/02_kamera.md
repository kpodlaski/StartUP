# Ćwiczenie 2: kamera, czyli jak zapisany jest obraz (8 min)

**Notatnik:** `02_kamera.ipynb`
**Potrzebne:** kolorowe przedmioty przed kamerą robota (np. czerwona gumowa kaczka, zielona i niebieska kartka, kartka z napisem drukowanymi literami)

## Cel

Zrozumieć, z czego składa się obraz cyfrowy i dlaczego sposób jego zapisu ma znaczenie dla robota.

## Trochę teorii

- Obraz cyfrowy to prostokątna siatka **pikseli**. **Rozdzielczość** to liczba pikseli w poziomie × w pionie, np. 640 × 480.
- W modelu **RGB** kolor każdego piksela jest zapisany jako trzy liczby od 0 do 255: ilość światła **czerwonego (R)**, **zielonego (G)** i **niebieskiego (B)**. (0, 0, 0) to czerń, a (255, 255, 255) to biel.
- Jeden piksel zajmuje 3 bajty. Obraz 640 × 480 zajmuje więc 640 · 480 · 3 = **921 600 bajtów (900 kB)**. Kamera wysyła ok. 30 takich obrazów na sekundę.
- **Kompresja bezstratna** (np. **PNG**) zmniejsza plik bez utraty informacji: po odczycie obraz jest identyczny.
- **Kompresja stratna** (np. **JPEG**) usuwa szczegóły, których oko prawie nie zauważa. Pliki są dużo mniejsze, ale obraz już nie jest identyczny z oryginałem.

## Kroki

### Krok 1: zdjęcie i rozdzielczość (1 min)
Ustaw przedmioty przed kamerą i uruchom komórkę ze zdjęciem.

- Rozdzielczość obrazu: ______ × ______ pikseli; liczba pikseli: ____________
- Rozmiar bez kompresji: ______ kB

### Krok 2: piksele i kolory (2 min)
W komórce `piksele(img, x, y)` zmień `x` i `y` tak, żeby oglądać fragment **kaczki**, a potem **białej ściany lub kartki**. Wartości odczytasz z powiększenia.

| Miejsce | R | G | B |
|---|---|---|---|
| kaczka (czerwona) | | | |
| biała ściana / kartka | | | |
| ciemny fragment | | | |

Uruchom `kanaly_rgb(img)`. W którym kanale kaczka jest najjaśniejsza? ____________

### Krok 3: kompresja (3 min)
Uruchom `porownaj_kompresje(img)`. Potem uruchom ją jeszcze raz, podając `wycinek`, czyli powiększony fragment z krawędzią kaczki.

| Format | Rozmiar [kB] | Średni błąd piksela | Czy widać różnicę na powiększeniu? |
|---|---|---|---|
| bez kompresji | | 0 | — |
| PNG | | | |
| JPEG jakość 95 | | | |
| JPEG jakość 50 | | | |
| JPEG jakość 10 | | | |

### Krok 4: mniejsza rozdzielczość (2 min)
W komórce `zmien_rozdzielczosc` sprawdź szerokości 320, 160, 80 i 40 pikseli.

- Przy jakiej szerokości napis na kartce przestaje być czytelny? ______ px  A kaczka przestaje być rozpoznawalna? ______ px

## Pytania do przemyślenia

1. Robot wysyła obraz z kamery przez Wi-Fi do komputera stacji, na którym działa sieć neuronowa. Który format wybierzesz do przesyłania na żywo, a który do zapisania zdjęć dokumentujących wypadek? Dlaczego?
2. Ile danych na sekundę wysyłałaby kamera 640 × 480 nadająca 30 klatek/s bez kompresji?
3. Mniejszy obraz to szybsze przetwarzanie. Co tracimy? *(Wrócimy do tego w ćwiczeniu 6.)*
