"""
Generator notatników Jupyter warsztatu „Autonomiczne pojazdy sterowane AI”.

Wejście:  treść komórek zapisana w tym pliku (listy NOTATNIKI → komórki "md"/"kod").
Wyjście:  pliki 00_start.ipynb … 07_nawigacja.ipynb w tym samym katalogu (nadpisywane, bez wyników).

Notatniki są GENEROWANE — poprawki wprowadzaj tutaj i uruchom:
    python3 _zbuduj_notatniki.py
Numeracja kroków w notatnikach odpowiada instrukcjom w ../instrukcje/*.md.
Kod wywołuje funkcje z jetbot_warsztat.py, detektor.py i perceptron.py (ten sam katalog).
"""
import os
import nbformat as nbf

KATALOG = os.path.dirname(os.path.abspath(__file__))

START = """from jetbot_warsztat import *
polacz()"""

NOTATNIKI = {
# ------------------------------------------------------------------------------------------
"00_start.ipynb": [
("md", """# Ćwiczenie 0: pierwsze kroki
Komórkę uruchamiasz klawiszami **Shift + Enter**. Uruchamiaj komórki **po kolei, od góry**.
Zmieniaj tylko wartości w liniach oznaczonych `# ZMIEŃ TUTAJ`."""),
("md", "**Krok 1.** Połączenie z robotem. Ma się pojawić napis *„Połączono z robotem”*. "
 "**Sprawdź, czy numer w nawiasie kwadratowym, np. `[robot 3]`, zgadza się z naklejką na Waszym robocie.** Jeśli nie, zawołaj prowadzącego."),
("kod", START),
("md", "**Krok 2.** Co działa w robocie? Przy napędzie, LiDAR-ze i kamerze powinien być znak ✔."),
("kod", "status()"),
("md", "**Krok 3.** Krótki przejazd do przodu. Zmień czas na `2.0` i uruchom ponownie. **Pilot trzyma rękę przy robocie!**"),
("kod", """czas = 1.0          # ZMIEŃ TUTAJ  (sekundy)
jedz(predkosc=0.1, obrot=0.0, czas=czas)"""),
("md", "**Krok 4. HAMULEC AWARYJNY**: ta komórka działa w każdym notatniku."),
("kod", "stop()"),
],
# ------------------------------------------------------------------------------------------
"01_lidar.ipynb": [
("md", """# Ćwiczenie 1: LiDAR, czyli jak robot mierzy odległość
Wyniki wpisuj do tabel w instrukcji (`instrukcje/01_lidar.md`)."""),
("kod", START),
("md", "**Krok 1.** Skan otoczenia z góry. Robot to czerwony trójkąt, a przód robota jest skierowany w górę wykresu."),
("kod", "rysuj_skan()"),
("md", "Ten sam skan z zaznaczonym kierunkiem: 0° to na wprost, 90° w lewo, −90° w prawo."),
("kod", """kat = 0            # ZMIEŃ TUTAJ  (stopnie)
rysuj_skan(zaznacz_kat=kat)"""),
("md", """**Krok 2.** Dokładność. Karton na wprost robota, odległość zmierzona miarką od środka LiDAR-u.
Komórka wykonuje 10 pomiarów i podaje średnią oraz rozrzut."""),
("kod", """odleglosc_z_miarki = 0.30     # ZMIEŃ TUTAJ  (metry): 0.30, 0.60, 1.00, 1.50
srednia, rozrzut, pomiary = seria_pomiarow(kat=0, ile=10)
print(f"LiDAR: {srednia:.3f} m  (rozrzut {rozrzut*100:.1f} cm)")
print(f"Błąd: {(srednia - odleglosc_z_miarki)*100:+.1f} cm")"""),
("md", """**Krok 3.** Różne materiały, każdy w odległości 0,60 m. Uruchamiaj komórkę dla każdego materiału.
Lusterko zmierz dwa razy: na wprost robota i obrócone o ok. 45°. Przy lusterku pod kątem uruchom też komórkę poniżej."""),
("kod", """material = "karton"           # ZMIEŃ TUTAJ
srednia, rozrzut, pomiary = seria_pomiarow(kat=0, ile=10)
nieudane = sum(1 for p in pomiary if not np.isfinite(p))
print(f"{material}: {srednia:.3f} m, nieudanych pomiarów: {nieudane}/10")"""),
("kod", "rysuj_skan(zaznacz_kat=0)     # lusterko pod kątem: gdzie jest punkt na wprost robota?"),
("md", "**Krok 4.** Karton pod kątem (0°, 30°, 60°, 80°), w odległości 0,60 m."),
("kod", """kat_kartonu = 0               # ZMIEŃ TUTAJ  (tylko do opisu)
srednia, rozrzut, pomiary = seria_pomiarow(kat=0, ile=10)
nieudane = sum(1 for p in pomiary if not np.isfinite(p))
print(f"karton pod kątem {kat_kartonu}°: {srednia:.3f} m, nieudanych: {nieudane}/10")
rysuj_skan(zaznacz_kat=0, zasieg=1.5)"""),
("md", "Odpowiedz na pytania z instrukcji. Hamulec awaryjny:"),
("kod", "stop()"),
],
# ------------------------------------------------------------------------------------------
"02_kamera.ipynb": [
("md", "# Ćwiczenie 2: kamera, czyli jak zapisany jest obraz"),
("kod", START),
("md", "**Krok 1.** Zdjęcie z kamery robota i jego rozdzielczość."),
("kod", """img = zdjecie()
wysokosc, szerokosc, kanaly = img.shape
print(f"Rozdzielczość: {szerokosc} × {wysokosc} pikseli = {szerokosc*wysokosc} pikseli")
print(f"Każdy piksel ma {kanaly} liczby (R, G, B), więc bez kompresji: {img.nbytes/1024:.0f} kB")
pokaz(img)"""),
("md", "**Krok 2.** Piksele z bliska. Ustaw `x` i `y` (liczone od lewego górnego rogu) tak, żeby trafić w kaczkę, a potem w białą ścianę lub kartkę."),
("kod", """x = 300            # ZMIEŃ TUTAJ
y = 200            # ZMIEŃ TUTAJ
piksele(img, x, y)"""),
("kod", "kanaly_rgb(img)"),
("md", "**Krok 3.** Kompresja: PNG (bezstratna) i JPEG o różnych jakościach."),
("kod", "wyniki = porownaj_kompresje(img)"),
("md", "To samo, ale z powiększonym fragmentem. Ustaw wycinek na krawędzi kaczki: `(x, y, szerokość, wysokość)`."),
("kod", "wyniki = porownaj_kompresje(img, jakosci=(95, 50, 10), wycinek=(250, 150, 120, 120))   # ZMIEŃ TUTAJ"),
("md", "**Krok 4.** Mniejsza rozdzielczość. Od jakiej szerokości napis przestaje być czytelny, a kaczka rozpoznawalna?"),
("kod", """szerokosci = [320, 160, 80, 40]     # ZMIEŃ TUTAJ
male = [zmien_rozdzielczosc(img, s) for s in szerokosci]
pokaz(*male, tytuly=[f"{s} px" for s in szerokosci], rozmiar=4)"""),
],
# ------------------------------------------------------------------------------------------
"03_odometria.ipynb": [
("md", """# Ćwiczenie 3: odometria, czyli dlaczego robot się gubi
Robot musi stać **dokładnie na krzyżyku**, przodem wzdłuż linii. Potrzebne jest ok. 1,5 × 1,5 m wolnego miejsca **na lewo i do przodu** od robota."""),
("kod", START),
("md", "Gdzie robot jest według odometrii (przed jazdą)?"),
("kod", "print(pozycja_odometrii())"),
("md", "**Krok 2. Przejazd 1:** kwadrat 1 × 1 m. Po zatrzymaniu zmierz miarką odległość od krzyżyka."),
("kod", """trasa1 = przejazd_po_kwadracie(bok=1.0, predkosc=0.15, okrazenia=1)"""),
("md", "**Krok 3. Przejazd 2:** powtórzenie (robot ponownie na krzyżyk)."),
("kod", """trasa2 = przejazd_po_kwadracie(bok=1.0, predkosc=0.15, okrazenia=1)"""),
("md", "**Przejazd 3:** większa prędkość."),
("kod", """predkosc = 0.30    # ZMIEŃ TUTAJ
trasa3 = przejazd_po_kwadracie(bok=1.0, predkosc=predkosc, okrazenia=1)"""),
("md", "**Przejazd 4:** dwa okrążenia."),
("kod", """okrazenia = 2      # ZMIEŃ TUTAJ
trasa4 = przejazd_po_kwadracie(bok=1.0, predkosc=0.15, okrazenia=okrazenia)"""),
("md", "**Krok 4.** Tak robot **wyobraża sobie** swoje trasy. Porównaj z tym, co zmierzyłeś miarką."),
("kod", """rysuj_trase(trasa1, trasa2, trasa3, trasa4,
            podpisy=["1: 0,15 m/s", "2: powtórzenie", "3: szybciej", "4: dwa okrążenia"])"""),
("kod", "stop()"),
],
# ------------------------------------------------------------------------------------------
"04_slam.ipynb": [
("md", """# Ćwiczenie 4: SLAM, czyli budujemy mapę
Mapa na żywo pojawi się obok przycisków panelu sterowania. Robot startuje z punktu **S**, przodem wzdłuż linii.
Zamiast `N` w nazwach map wpisz **numer swojego zespołu**."""),
("kod", START),
("md", "**Krok 1.** ROS od środka: jakie programy (węzły) działają i jakimi tematami się komunikują?"),
("kod", "wezly_i_tematy()"),
("md", "**Krok 2.** Pierwsza mapa z parametrami domyślnymi. Robot na punkcie S!"),
("kod", "uruchom_slam(rozdzielczosc=0.05, zasieg=6.0, aktualizacja=2.0, czastki=30)"),
("md", """Uruchom komórkę poniżej: pod nią pojawi się **panel z przyciskami-strzałkami** (↑ ↓ ← →, STOP) i obok mapa na żywo.
Klikaj strzałki; robot jedzie, dopóki nie klikniesz **STOP**. Jedź wolno i wracaj w znane miejsca.
Po objechaniu toru kliknij **Zakończ sterowanie**."""),
("kod", "panel_sterowania(predkosc=0.15, predkosc_obrotu=0.8, podglad=True)"),
("kod", "pokaz_mape(\"mapa 1: parametry domyślne\")"),
("kod", "zapisz_mape(\"zespolN_mapa1\")        # ZMIEŃ TUTAJ (numer zespołu)"),
("md", """**Krok 3.** Eksperymenty z parametrami (przydzielone przez prowadzącego):

| | rozdzielczosc | zasieg | aktualizacja | czastki |
|---|---|---|---|---|
| domyślne | 0.05 | 6.0 | 2.0 | 30 |
| A | **0.10** | 6.0 | 2.0 | 30 |
| B | **0.02** | 6.0 | 2.0 | 30 |
| C | 0.05 | **1.0** | 2.0 | 30 |
| D | 0.05 | 6.0 | **10.0** | 30 |
| E | 0.05 | 6.0 | 2.0 | **5** |
| F | domyślne, ale w panelu prędkość 0.3 i obrót 2.0 | | | |

Przed każdym eksperymentem robot wraca na punkt S. Uruchomienie komórki zaczyna mapę od nowa."""),
("kod", """eksperyment = "A"                  # ZMIEŃ TUTAJ
uruchom_slam(rozdzielczosc=0.10,   # ZMIEŃ TUTAJ
             zasieg=6.0,           # ZMIEŃ TUTAJ
             aktualizacja=2.0,     # ZMIEŃ TUTAJ
             czastki=30)           # ZMIEŃ TUTAJ"""),
("kod", "panel_sterowania(predkosc=0.15, predkosc_obrotu=0.8, podglad=True)     # ZMIEŃ TUTAJ (eksperyment F)"),
("kod", """pokaz_mape(f"eksperyment {eksperyment}")
zapisz_mape(f"zespolN_eksperyment_{eksperyment}")       # ZMIEŃ TUTAJ (numer zespołu)"""),
("md", "**Krok 4.** Najlepsza mapa: wpisz najlepsze parametry, zbuduj mapę starannie i zapisz ją. Posłuży w ćwiczeniu 7."),
("kod", """uruchom_slam(rozdzielczosc=0.05, zasieg=6.0, aktualizacja=2.0, czastki=30)   # ZMIEŃ TUTAJ
panel_sterowania(predkosc=0.15, predkosc_obrotu=0.8, podglad=True)"""),
("kod", """pokaz_mape("najlepsza mapa")
zapisz_mape("zespolN_najlepsza")        # ZMIEŃ TUTAJ (numer zespołu)
lista_map()"""),
("kod", "zatrzymaj_slam()"),
("kod", "stop()"),
],
# ------------------------------------------------------------------------------------------
"05_perceptron.ipynb": [
("md", """# Ćwiczenie 5: neuron, czyli hamuj czy jedź?
Neuron liczy **s = waga · odległość + bias**. Jeśli **s > 0**, odpowiada **HAMUJ**, w przeciwnym razie **JEDŹ**.

**Jak czytać wykresy:** tło = co robi neuron (czerwone HAMUJ, zielone JEDŹ), kropki = co powinien zrobić, ✖ = błąd.
Pod wykresem jest przykład obliczenia s. Ten notatnik nie potrzebuje robota."""),
("kod", "from perceptron import *"),
("md", """**Część A.** Waga jest ustawiona na −1. Przesuwaj **bias** i patrz, jak przesuwa się czarna granica.
Cel: neuron hamuje tylko przy czerwonych kropkach (✔ BRAWO). Potem zmień wagę na +1 i zobacz, co się stanie."""),
("kod", "suwaki_A()"),
("md", """**Część B.** Przy szybkiej jeździe trzeba hamować wcześniej. Waga odległości zostaje −1.
Dobierz **wagę prędkości** i **bias** tak, żeby wszystkie 60 sytuacji było dobrze."""),
("kod", "suwaki_B()"),
("md", """**Część C.** Automatyczne uczenie: komputer zaczyna od wag równych zero i po każdej pomyłce lekko je poprawia.
Ostatnia linia wyniku przelicza wagi komputera tak, żeby dało się je porównać z Waszymi."""),
("kod", "wagi = uczenie_B()"),
],
# ------------------------------------------------------------------------------------------
"06_detektor.ipynb": [
("md", """# Ćwiczenie 6: gotowa sieć neuronowa szuka obiektów, czyli jak zapytać sieć
Porównamy sieć z **zamkniętą listą** 80 klas (COCO) i sieć z **otwartym słownikiem** (YOLOE), której mówimy słowami, czego szukać.
Obie są już wytrenowane i działają na procesorze stacji."""),
("kod", START + "\nimport detektor"),
("md", "**Krok 1.** Sieć z zamkniętą listą (COCO). Kaczka ok. 1 m przed robotem, obok krzesło i plecak."),
("kod", """img = zdjecie()
detektor.pokaz_wykrycia(img, prog=0.25, wielkosc="coco")"""),
("md", """**Krok 2.** Zapytaj słowami. Komórka sprawdza wiele opisów na tym samym zdjęciu.
Dopisz do listy własne pomysły (po angielsku i po polsku). Żeby liczyć tylko ramki na kaczce, podaj w `cel_xy` punkt leżący na kaczce
(x, y w pikselach; odczytasz go z osi obrazu w kroku 1). Z `cel_xy=None` liczy się najlepsze wykrycie w całym obrazie."""),
("kod", """zapytania = ["duck", "rubber duck", "kaczka", "bird",
             "...", "...", "...", "..."]           # ZMIEŃ TUTAJ: dopisz własne pomysły zamiast "..."
cel_xy = None                                     # ZMIEŃ TUTAJ, np. (360, 340)
wyniki = detektor.porownaj_slowa(img, [z for z in zapytania if z != "..."], cel_xy=cel_xy)"""),
("md", """**Krok 3.** Słowa konkurują: kilka słów naraz. Komórka robi **nowe zdjęcie** i pokazuje je dwa razy:
najpierw z jednym słowem, potem z kilkoma. Czy pewność wykrycia kaczki się zmienia?"""),
("kod", """img = zdjecie()                                     # nowe zdjęcie (scena mogła się zmienić)
detektor.ustaw_slowa(["rubber duck"])               # ZMIEŃ TUTAJ: Wasze najlepsze zapytanie
detektor.pokaz_wykrycia(img, prog=0.25)
detektor.ustaw_slowa(["rubber duck", "box", "toy"])  # ZMIEŃ TUTAJ: to samo zapytanie + inne słowa
detektor.pokaz_wykrycia(img, prog=0.25)"""),
("md", "**Krok 4.** Obiekt-zagadka od prowadzącego: znajdź zapytanie, przy którym pewność przekracza 0,5."),
("kod", """img = zdjecie()
detektor.porownaj_slowa(img, ["...", "...", "...", "..."])   # ZMIEŃ TUTAJ"""),
("kod", """detektor.ustaw_slowa(["..."])                  # ZMIEŃ TUTAJ: najlepsze zapytanie
detektor.pokaz_wykrycia(img, prog=0.25)"""),
("md", "**Krok 5.** Odległość i rozdzielczość. Ustaw kaczkę w odległości 0,5 / 1 / 2 / 3 m i uruchamiaj komórkę dla każdej odległości."),
("kod", """detektor.ustaw_slowa(["rubber duck"])          # ZMIEŃ TUTAJ: Wasze najlepsze zapytanie
img = zdjecie()
for rozdzielczosc in (320, 640):
    detektor.pokaz_wykrycia(img, prog=0.1, rozdzielczosc=rozdzielczosc)"""),
("kod", """for rozdzielczosc in (320, 640):
    detektor.test_szybkosci("maly", rozdzielczosc, img=img)"""),
("md", "Podgląd na żywo przez 20 s: przesuwaj kaczkę, zasłaniaj ją, zmieniaj światło."),
("kod", "detektor.podglad_na_zywo(sekundy=20, prog=0.25, rozdzielczosc=640)"),
("md", "**Krok 6.** Decyzja zespołu na ćwiczenie 7 (wpisz też do instrukcji)."),
("kod", """MOJE_ZAPYTANIE = ["rubber duck"]    # ZMIEŃ TUTAJ
MOJ_PROG = 0.3                      # ZMIEŃ TUTAJ
MOJA_ROZDZIELCZOSC = 640            # ZMIEŃ TUTAJ
detektor.ustaw_slowa(MOJE_ZAPYTANIE)
detektor.pokaz_wykrycia(zdjecie(), prog=MOJ_PROG, rozdzielczosc=MOJA_ROZDZIELCZOSC)"""),
],
# ------------------------------------------------------------------------------------------
"07_nawigacja.ipynb": [
("md", """# Ćwiczenie 7: autonomiczna jazda na mapie i poszukiwanie kaczki
Współrzędne: punkt **S** = (0, 0), oś x wzdłuż linii startowej, oś y w lewo, jednostką są metry.
Współrzędne punktów A i B są na tablicy. Mapę na żywo pokazują panel sterowania i `jedz_do()`."""),
("kod", START + "\nimport detektor"),
("md", "**Krok 1.** Start nawigacji na Waszej mapie (lub `\"tor_prowadzacy\"`)."),
("kod", """lista_map()
uruchom_nawigacje("zespolN_najlepsza")      # ZMIEŃ TUTAJ"""),
("md", "Robot stoi na punkcie S, przodem wzdłuż linii. Mówimy mu, gdzie mniej więcej jest:"),
("kod", """ustaw_pozycje_startowa(x=0.0, y=0.0, kat=0)   # ZMIEŃ TUTAJ, jeśli robot stoi gdzie indziej
gdzie_jestem()"""),
("md", "Uruchom komórkę poniżej (pojawi się panel ze strzałkami i mapa). Przejedź kawałek i obserwuj na mapie chmurę cząstek (niebieskie strzałki). Potem kliknij **Zakończ sterowanie** i sprawdź niepewność."),
("kod", "panel_sterowania(predkosc=0.1, predkosc_obrotu=0.6, podglad=True)"),
("kod", "gdzie_jestem()"),
("md", "**Zadanie A.** Dojazd do celu. Po zatrzymaniu zmierz miarką odległość od punktu."),
("kod", """x_celu = 1.5     # ZMIEŃ TUTAJ  (punkt A z tablicy)
y_celu = 0.5     # ZMIEŃ TUTAJ
jedz_do(x_celu, y_celu)
gdzie_jestem()"""),
("md", "**Zadanie B.** Nowa przeszkoda na trasie. Zmieniaj parametry i powtarzaj przejazd."),
("kod", """ustaw_parametry_nawigacji(maks_predkosc=0.15,            # ZMIEŃ TUTAJ  (0.10 … 0.25)
                          odleglosc_bezpieczenstwa=0.20)  # ZMIEŃ TUTAJ  (0.10 … 0.35)"""),
("kod", """x_celu = 0.5     # ZMIEŃ TUTAJ  (punkt B z tablicy)
y_celu = 1.0     # ZMIEŃ TUTAJ
jedz_do(x_celu, y_celu)"""),
("md", """**Zadanie C: znajdź kaczkę.** Najpierw ustawienia sieci z ćwiczenia 6.
LiDAR kaczki nie widzi (jest za niska), więc robot szuka jej kamerą."""),
("kod", """detektor.ustaw_slowa(["rubber duck"])     # ZMIEŃ TUTAJ  (Wasze najlepsze zapytanie)
PROG = 0.3                                # ZMIEŃ TUTAJ
ROZDZIELCZOSC = 640                       # ZMIEŃ TUTAJ"""),
("md", "**C1.** Rozglądanie się z miejsca: robot obraca się co `krok` stopni i sprawdza każde zdjęcie."),
("kod", "wykrycie = rozejrzyj_sie(krok=30, prog=PROG, rozdzielczosc=ROZDZIELCZOSC)     # ZMIEŃ TUTAJ (krok)"),
("md", """**C2.** Dojazd do kaczki. `dol_stop` to próg, przy którym robot staje: jak nisko w obrazie musi być dolna krawędź ramki
(0 = góra obrazu, 1 = dół). Większa wartość oznacza, że robot staje bliżej kaczki."""),
("kod", """podjedz_do_obiektu(prog=PROG, rozdzielczosc=ROZDZIELCZOSC,
                   dol_stop=0.90,       # ZMIEŃ TUTAJ
                   predkosc=0.10)       # ZMIEŃ TUTAJ"""),
("md", """**C3.** Poszukiwania: prowadzący ukrył kaczkę. Wybierzcie punkty obserwacyjne na mapie (x, y) i ich kolejność.
Robot rozejrzy się na miejscu, potem pojedzie po kolei do punktów, aż znajdzie kaczkę i do niej podjedzie."""),
("kod", """punkty = [(1.0, 0.0), (2.0, 1.0), (0.5, 1.5)]      # ZMIEŃ TUTAJ
dziennik = szukaj_obiektu(punkty, krok=30, prog=PROG, rozdzielczosc=ROZDZIELCZOSC, dol_stop=0.90)"""),
("md", "**Hamulec awaryjny** oraz sprzątanie na koniec:"),
("kod", "anuluj()"),
("kod", "zatrzymaj_wszystko()"),
],
}


# Dopisywane na końcu każdego notatnika, który łączy się z robotem.
KONIEC = [
    ("md", """**Koniec ćwiczenia.** Uruchom tę komórkę, zanim przejdziesz do następnego notatnika:
zatrzymuje robota i odłącza ten notatnik. Robot działa dalej, a następny notatnik połączy się z nim sam."""),
    ("kod", "koniec()"),
]


def zbuduj():
    for nazwa, komorki in NOTATNIKI.items():
        nb = nbf.v4.new_notebook()
        nb.metadata["kernelspec"] = {"name": "python3", "display_name": "Python 3", "language": "python"}
        if any(typ == "kod" and "jetbot_warsztat" in t for typ, t in komorki):   # notatniki pracujące z robotem
            komorki = komorki + KONIEC
        nb.cells = [nbf.v4.new_markdown_cell(t) if typ == "md" else nbf.v4.new_code_cell(t) for typ, t in komorki]
        nbf.write(nb, os.path.join(KATALOG, nazwa))
        print("zapisano", nazwa, f"({len(komorki)} komórek)")


if __name__ == "__main__":
    zbuduj()
