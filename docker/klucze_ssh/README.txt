Tu wstaw klucz prywatny ssh do Jetbotów (np. id_ed25519; logowanie stacja -> robot bez hasła).
Katalog jest montowany do kontenera tylko do odczytu; przy starcie klucze są kopiowane do ~/.ssh
z uprawnieniami 600. Inny katalog: zmienna WARSZTAT_SSH przed `docker compose up`.
NIE commituj kluczy — katalog jest w .gitignore (poza tym plikiem).
