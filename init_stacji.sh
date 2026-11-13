#!/usr/bin/env bash
# =============================================================================================
#  Przygotowanie stacji do warsztatu (Linux) — odpowiednik init_stacji.bat. Bez parametrów.
#
#  1. Materiały: pierwszy raz `git clone`, na kolejnych warsztatach aktualizacja do wersji z repo.
#     Zmiany uczniów z poprzednich zajęć trafiają do `git stash` (do odzyskania: git stash list),
#     pliki lokalne stacji z .gitignore (notatniki/.wybrany_robot, klucze ssh) zostają.
#  2. Obraz Dockera: budowany tylko, gdy go nie ma albo gdy zmienił się katalog docker/.
#  3. Start kontenera z JupyterLab (stary kontener jest zastępowany).
#
#  Git: jeśli go nie ma, używany jest obraz alpine/git. Bez internetu aktualizacja jest pomijana.
#  Cały skrypt jest w funkcji main: bash wczytuje ją w całości, zanim zacznie wykonywać,
#  więc aktualizacja repozytorium może bezpiecznie podmienić ten plik w trakcie działania.
# =============================================================================================

# ---- USTAWIENIA ------------------------------------------------------------------------------
REPO_URL="https://github.com/kpodlaski/StartUP.git"
GALAZ="main"
KATALOG="${WARSZTAT_KATALOG:-$HOME/warsztat_jetbot}"
OBRAZ="warsztat-jetbot:noetic"
# ----------------------------------------------------------------------------------------------

main() {
    set -uo pipefail
    blad() { echo "[BŁĄD] $*" >&2; exit 1; }

    # git z systemu albo z obrazu alpine/git; zawsze w katalogu KATALOG.
    # Tożsamość podana tylko dla `git stash` (stacja nie ma user.name/email).
    g() {
        local opcje=(-c safe.directory='*' -c user.name=stacja -c user.email=stacja@warsztat)
        if command -v git >/dev/null; then
            git -C "$KATALOG" "${opcje[@]}" "$@"
        else
            docker run --rm --user "$(id -u):$(id -g)" -e HOME=/tmp \
                -v "$KATALOG:/repo" -w /repo alpine/git "${opcje[@]}" "$@"
        fi
    }

    echo "=== Przygotowanie stacji: $KATALOG"
    docker info >/dev/null 2>&1 || blad "Docker nie odpowiada (uruchomiony? użytkownik w grupie docker?)."
    command -v git >/dev/null && echo "Git: systemowy" || echo "Git: brak — używam obrazu alpine/git"

    local buduj=""
    if [[ -d "$KATALOG/.git" ]]; then
        echo "Aktualizuję materiały…"
        g config --replace-all core.autocrlf false; g config --replace-all core.fileMode false
        g remote set-url origin "$REPO_URL"
        if g fetch origin "$GALAZ"; then
            local przed po
            przed=$(g rev-parse HEAD:docker 2>/dev/null || true)
            if [[ -n "$(g status --porcelain)" ]]; then
                echo "Zmiany z poprzednich zajęć odkładam do „git stash” (do odzyskania)."
                g stash push --include-untracked -m "init_stacji $(date '+%F %T')" || blad "git stash nie powiódł się."
            fi
            g reset --hard "origin/$GALAZ" || blad "Nie udało się ustawić wersji z repozytorium."
            po=$(g rev-parse HEAD:docker 2>/dev/null || true)
            if [[ "$przed" != "$po" ]]; then echo "Katalog docker/ się zmienił — obraz zostanie przebudowany."; buduj=1; fi
        else
            echo "[UWAGA] Nie udało się pobrać zmian (brak internetu?). Uruchamiam wersję już pobraną."
        fi
    else
        if [[ -e "$KATALOG" && -n "$(ls -A "$KATALOG" 2>/dev/null)" ]]; then
            blad "Katalog $KATALOG istnieje, ale nie jest repozytorium git. Zmień jego nazwę albo ustaw WARSZTAT_KATALOG."
        fi
        mkdir -p "$KATALOG"
        echo "Pobieram materiały: $REPO_URL"
        g clone -c core.autocrlf=false -b "$GALAZ" "$REPO_URL" . \
            || blad "git clone nie powiódł się. Sprawdź internet i REPO_URL w tym pliku."
        g config --replace-all core.fileMode false
        buduj=1
    fi

    local compose="$KATALOG/docker/docker-compose.yml"
    docker image inspect "$OBRAZ" >/dev/null 2>&1 || buduj=1
    if [[ -n "$buduj" ]]; then
        echo "Buduję obraz $OBRAZ — za pierwszym razem to potrwa kilkanaście minut…"
        docker compose -f "$compose" build || blad "Budowa obrazu nie powiodła się."
    fi
    echo "Uruchamiam kontener…"
    docker compose -f "$compose" up -d --force-recreate || blad "Nie udało się uruchomić kontenera."
    echo
    echo "=== Gotowe. Jupyter: http://127.0.0.1:8888"
    echo "    Robota wybiera prowadzący w notatniku 00: wybierz_robota(N)"
    command -v xdg-open >/dev/null && (sleep 5; xdg-open http://127.0.0.1:8888 >/dev/null 2>&1) &
    exit 0
}

main "$@"
