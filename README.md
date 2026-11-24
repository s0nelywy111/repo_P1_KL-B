# LBK – P1 „Czy to napisało AI?” (PsychoPy)

Projekt zespołu Yevhen Rohozhynskyi/Vladyslav Uharov. Dokumentacja odtworzeniowa: `BUILD_BOOK.md`.
Nagranie z symulatora: `dane/nagranie.jsonl` (opis pól: `python narzedzia/opisz_nagranie.py dane/nagranie.jsonl`).

## KL-B – szkielet badania + LSL
- Eksperyment: `eksperyment/P1_szkielet.psyexp` (PsychoPy 2026.2.5, MouseGaze, 1920×1080 pix)
- Most symulator → LSL: `narzedzia/sim_to_lsl.py` (test: `--plik narzedzia/linie_testowe.jsonl --tylko-wypisz`)
- Kod Code Components: `eksperyment/kod_code_components/`
- Nagranie XDF i wykres: `dane/xdf/`, `analiza/wykres_xdf.py`
- Przykładowe dane wyjściowe PsychoPy (ten sam przebieg co XDF): `eksperyment/data/`
- Uruchomienie symulatora i mostu: `start_lsl.bat`, test mostu: `test_most.bat` (ścieżka do Pythona PsychoPy w pliku)
- Schemat pętli: `dokumentacja/schemat_petli.md` · Karta źródeł: `dokumentacja/karta_zrodel.md`
- Instrukcja odtworzenia: `BUILD_BOOK.md`, rozdz. 3, 4, 6

