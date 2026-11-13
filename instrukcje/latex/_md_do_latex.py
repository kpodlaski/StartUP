"""
Konwersja instrukcji dla uczestników (../NN_*.md) do LaTeX-a: pliki cw00.tex … cw08.tex w tym katalogu.

Wejście:  ../00_wprowadzenie.md … ../08_karta_wynikow.md (Markdown).
Wyjście:  cwNN.tex — treść ćwiczeń (bez preambuły); wstawiane do zeszyt_cwiczen.tex przez \\input.
          Pliki cwNN.tex można potem poprawiać ręcznie. UWAGA: ponowne uruchomienie skryptu je NADPISZE.

Wymaga pandoca (np. `pip install pypandoc_binary`).  Uruchom:  python3 _md_do_latex.py  [NN ...]
          (z numerami, np. `python3 _md_do_latex.py 05`, konwertuje tylko te pliki — reszta cwNN.tex zostaje nietknięta)

Co robi oprócz zwykłej konwersji pandoca:
  * tabele składa jako tabular w minipage (nie dzielą się między strony); szerokości kolumn liczy z długości tekstu; puste kolumny (do wypełniania ręcznie) dostają więcej miejsca,
  * ciągi podkreślników „______” zamienia na linię do pisania (\\linia{…}),
  * cytaty Markdown (> …) stają się ramkami (środowisko quote jest przedefiniowane w zeszyt_cwiczen.tex),
  * w 00_wprowadzenie usuwa tytuł główny (jest na stronie tytułowej) i podnosi poziom nagłówków,
  * w 08_karta_wynikow zamienia rysunek ASCII na pustą ramkę na szkic mapy (\\szkicmapy),
  * usuwa emoji (czcionka ich nie ma), zamienia ✔ na \\ding{51}, ✖ na \\ding{54} i indeksy ₁ ₂ na \\textsubscript.
"""
import glob
import os
import re
import subprocess

TU = os.path.dirname(os.path.abspath(__file__))
ZRODLA = os.path.join(TU, "..")


def pandoc():
    try:
        import pypandoc
        return pypandoc.get_pandoc_path()
    except Exception:
        return "pandoc"


def szerokosci_tabel(md):
    """Przepisuje linie separatora tabel (|---|---|) tak, by liczba kresek odpowiadała pożądanej szerokości."""
    linie, wynik, i = md.split("\n"), [], 0
    while i < len(linie):
        if (linie[i].lstrip().startswith("|") and i + 1 < len(linie)
                and re.match(r"^\s*\|(\s*:?-+:?\s*\|)+\s*$", linie[i + 1])):
            blok = [linie[i], linie[i + 1]]
            j = i + 2
            while j < len(linie) and linie[j].lstrip().startswith("|"):
                blok.append(linie[j]); j += 1
            komorki = [[c.strip() for c in l.strip().strip("|").split("|")] for l in blok]
            n = len(komorki[0])
            szer = []
            for k in range(n):
                naglowek = len(komorki[0][k]) if k < len(komorki[0]) else 0
                tresc = [len(r[k]) for r in komorki[2:] if k < len(r)]
                if tresc and max(tresc) == 0:              # kolumna do wypełnienia ręcznie
                    w = max(min(naglowek, 30), 16)
                else:
                    w = max([min(naglowek, 30)] + tresc)
                szer.append(min(max(w, 10), 55))
            blok[1] = "|" + "|".join("-" * w for w in szer) + "|"
            wynik.extend(blok)
            i = j
        else:
            wynik.append(linie[i]); i += 1
    return "\n".join(wynik)


def puste_linie_przed_listami(md):
    """Pandoc wymaga pustej linii przed listą; w źródłach .md bywa jej brak (też w cytatach „> - …”)."""
    wynik, poprzednia = [], ""
    lista = re.compile(r"^\s*(?:>\s*)?(?:[-*]|\d+\.)\s+")
    for linia in md.split("\n"):
        if lista.match(linia) and poprzednia.strip() not in ("", ">") and not lista.match(poprzednia):
            wynik.append(">" if linia.lstrip().startswith(">") else "")
        wynik.append(linia)
        poprzednia = linia
    return "\n".join(wynik)


def tabele_bez_dzielenia(tex):
    """longtable z pandoca → tabular w minipage (krótkie tabele nie rozpadają się między strony)."""
    tex = re.sub(r"\{\\def\\LTcaptype\{none\}[^\n]*\n", "", tex)
    tex = re.sub(r"\\begin\{longtable\}\[\]\{(.*)\}\n",
                 lambda m: "\\par\\noindent\\begin{minipage}{\\linewidth}\n\\begin{tabular}{" + m.group(1) + "}\n", tex)
    tex = tex.replace("\\endhead\n", "").replace("\\bottomrule\\noalign{}\n\\endlastfoot\n", "")
    tex = tex.replace("\\end{longtable}\n}", "\\bottomrule\\noalign{}\n\\end{tabular}\n\\end{minipage}\\par\\medskip")
    return tex


def przygotuj_md(nazwa, md):
    md = md.replace("⚠️ ", "").replace("⚠️", "")
    md = md.replace("\n**Potrzebne:**", "\n\n**Potrzebne:**")           # osobny akapit pod „Notatnik:”
    if nazwa.startswith("00_"):
        md = re.sub(r"^# .*\n", "", md, count=1)                          # tytuł jest na stronie tytułowej
    if nazwa.startswith("08_"):
        md = re.sub(r"- \*\(Szkic naszej najlepszej mapy\)\*\n", "", md)
        md = re.sub(r"```\n┌.*?```", r"\\szkicmapy", md, flags=re.S)
    return szerokosci_tabel(puste_linie_przed_listami(md))


def popraw_latex(tex):
    tex = tabele_bez_dzielenia(tex)
    tex = re.sub(r"(?:\\_){4,}", lambda m: "\\linia{%.1f}" % min(len(m.group(0)) / 2 * 0.42, 14), tex)
    tex = tex.replace("✔", "\\ding{51}").replace("✖", "\\ding{54}").replace("₁", "\\textsubscript{1}").replace("₂", "\\textsubscript{2}")
    return tex


def konwertuj(tylko=None):
    """tylko — lista prefiksów numerów (np. ["05"]); None = wszystkie pliki."""
    for sciezka in sorted(glob.glob(os.path.join(ZRODLA, "0*_*.md"))):
        nazwa = os.path.basename(sciezka)
        if tylko and nazwa[:2] not in tylko:
            continue
        md = przygotuj_md(nazwa, open(sciezka, encoding="utf-8").read())
        opcje = ["-f", "markdown", "-t", "latex", "--columns=1", "--wrap=preserve"]
        if nazwa.startswith("00_"):
            opcje.append("--shift-heading-level-by=-1")
        tex = subprocess.run([pandoc()] + opcje, input=md, capture_output=True, text=True, check=True).stdout
        cel = os.path.join(TU, "cw" + nazwa[:2] + ".tex")
        with open(cel, "w", encoding="utf-8") as f:
            f.write(f"% Wygenerowano z ../{nazwa} skryptem _md_do_latex.py (można edytować ręcznie).\n")
            f.write(popraw_latex(tex))
        print("zapisano", os.path.basename(cel))


if __name__ == "__main__":
    import sys
    konwertuj(sys.argv[1:] or None)
