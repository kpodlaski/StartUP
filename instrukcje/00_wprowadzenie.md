# Autonomiczne pojazdy sterowane AI: instrukcje dla zespołów

## Jak pracujemy

Pracujecie w zespołach 2–3-osobowych. Każdy zespół ma **jednego Jetbota**, **stanowisko komputerowe** i **ten zeszyt ćwiczeń**. Wyniki wpisujecie bezpośrednio do tabel w instrukcjach. Przydadzą się w podsumowaniu.

Podział pracy ustalacie sami. Pilnujcie tylko dwóch zasad:

- **przy klawiaturze zmieniajcie się co ćwiczenie**, żeby każdy coś uruchomił i zmienił w notatniku,
- **gdy robot jedzie, jedna osoba stoi przy torze** (w instrukcjach nazywamy ją **pilotem**). Ustawia robota na starcie, a w razie zagrożenia łapie go albo woła „STOP!”.

### Ćwiczenia

| Nr | Ćwiczenie | Notatnik | Czas |
|---|---|---|---|
| 0 | Pierwsze kroki z notatnikiem i robotem | `00_start.ipynb` | 5 min |
| 1 | LiDAR: jak robot mierzy odległość | `01_lidar.ipynb` | 12 min |
| 2 | Kamera: jak zapisany jest obraz | `02_kamera.ipynb` | 8 min |
| 3 | Odometria: dlaczego robot się gubi | `03_odometria.ipynb` | 15 min |
| 4 | SLAM: budujemy mapę | `04_slam.ipynb` | 40 min |
| | *przerwa* | | |
| 5 | Neuron: hamuj czy jedź? | `05_perceptron.ipynb` | 10 min |
| 6 | Gotowa sieć neuronowa szuka obiektów: jak zapytać sieć | `06_detektor.ipynb` | 20 min |
| 7 | Autonomiczna jazda na mapie i poszukiwanie kaczki | `07_nawigacja.ipynb` | 35 min |
| 8 | Karta wyników zespołu | (papier) | 20 min |

## Ćwiczenie 0: pierwsze kroki (5 min)

**Cel:** nauczyć się uruchamiać komórki notatnika i sprawdzić, czy robot jest połączony.

### Jak działa notatnik Jupyter

- Notatnik składa się z **komórek**. Komórki z tekstem to opis, a komórki z kodem to polecenia dla komputera.
- Komórkę uruchamiasz, gdy klikniesz ją i naciśniesz **Shift + Enter** (albo przycisk ▶).
- Gdy komórka pracuje, obok niej widać `[*]`. Po zakończeniu pojawia się numer, np. `[3]`.
- Komórki uruchamiaj **po kolei, od góry**.
- Wolno zmieniać tylko wartości w liniach oznaczonych **`# ZMIEŃ TUTAJ`**. Resztę kodu można czytać, ale nie trzeba go rozumieć.
- Gdy coś „zawiśnie”, wybierz z menu *Kernel → Restart* i uruchom komórki od początku.
- **Ostatnia komórka każdego notatnika to `koniec()`.** Uruchom ją, zanim otworzysz następny notatnik: zatrzymuje robota i odłącza notatnik. Robot działa dalej, a następny notatnik połączy się z nim w pierwszej komórce. Niczego nie trzeba restartować ani zamykać.

### Kroki

1. Otwórz `00_start.ipynb`. Uruchom pierwszą komórkę (połączenie z robotem). Ma pojawić się komunikat *„Połączono z robotem”*. **Sprawdź, czy numer w komunikacie, np. `[robot 3]`, zgadza się z naklejką na Waszym robocie.** Jeśli nie, zawołaj prowadzącego.
2. Uruchom komórkę `status()`. Przy napędzie, LiDAR-ze i kamerze powinien być znak ✔.
3. W komórce z krótkim przejazdem zmień czas jazdy (`czas = 1.0  # ZMIEŃ TUTAJ`) na `2.0` i uruchom ją. **Pilot** trzyma rękę przy robocie.
4. Uruchom komórkę z `stop()`. Zapamiętaj ją, bo to **hamulec awaryjny**, który działa w każdym notatniku.

> ⚠️ **Bezpieczeństwo.** Robot jest mały, ale potrafi spaść ze stołu albo wjechać pod nogi. Gdy robot jedzie, pilot jest zawsze przy torze. W razie problemu: komórka `stop()` albo podnieś robota.
