#!/usr/bin/env python3
"""
Generuje eksperyment/P1_szkielet.psyexp przez API PsychoPy (psychopy.experiment),
z kodem Code Components z eksperyment/kod_code_components/.
Ten sam wynik można zbudować ręcznie w Builderze – patrz BUILD_BOOK.md, rozdz. 3.

Uruchomienie (z katalogu głównego repo, Python z PsychoPy 2026.2.5):
    python narzedzia/zbuduj_psyexp.py
"""
from pathlib import Path

from psychopy import experiment
from psychopy.experiment.routines import Routine
from psychopy.experiment.loops import TrialHandler
from psychopy.experiment.components.image import ImageComponent
from psychopy.experiment.components.keyboard import KeyboardComponent
from psychopy.experiment.components.code import CodeComponent
from psychopy.experiment.components.text import TextComponent
from psychopy.experiment.components.eyetracker_record import EyetrackerRecordComponent

REPO = Path(__file__).resolve().parents[1]
EKS = REPO / "eksperyment"
KOD = EKS / "kod_code_components"
PELNY = "[1920, 1080]"


def kod(nazwa):
    """Treść pliku z kodem bez linii komentarza nagłówkowego (zostawiamy resztę komentarzy)."""
    return (KOD / nazwa).read_text(encoding="utf-8")


def obraz(exp, rutyna, nazwa, plik, start=0.0, czas="", aktualizacja="constant"):
    c = ImageComponent(exp, rutyna, name=nazwa, image=plik, units="pix",
                       size=PELNY, pos="(0, 0)", startVal=start, stopVal=czas)
    c.params["image"].updates = aktualizacja
    return c


def klawiatura(exp, rutyna, nazwa, klawisze, start=0.0, czas="", poprawna=None):
    c = KeyboardComponent(exp, rutyna, name=nazwa, allowedKeys=klawisze,
                          store="last key", forceEndRoutine=True,
                          startVal=start, stopVal=czas)
    if poprawna:
        c.params["storeCorrect"].val = True
        c.params["correctAns"].val = poprawna
    return c


def kodowy(exp, rutyna, nazwa, begin_exp="", begin_rout="", each="", end_rout="", end_exp=""):
    c = CodeComponent(exp, rutyna, name=nazwa, beginExp=begin_exp, beginRoutine=begin_rout,
                      eachFrame=each, endRoutine=end_rout, endExperiment=end_exp)
    c.params["Code Type"].val = "Py"
    return c


def main():
    exp = experiment.Experiment()
    s = exp.settings.params
    s["expName"].val = "P1_szkielet"
    s["Window size (pixels)"].val = PELNY
    s["Full-screen window"].val = True
    s["Units"].val = "pix"
    s["color"].val = "[233, 236, 240]"          # tło z protokołu (RGB 233,236,240)
    s["colorSpace"].val = "rgb255"
    s["Show mouse"].val = False
    s["Save hdf5 file"].val = True               # zapis danych MouseGaze (ioHub)
    s["Save excel file"].val = False             # unikamy błędu saveAsExcel z KL-A
    s["Experiment info"].val = "{'participant': 'f\"{randint(0, 999999):06.0f}\"', 'session': '001'}"
    s["eyetracker"].val = "eyetracker.hw.mouse.EyeTracker"   # = MouseGaze (klucz backendu, nie etykieta)
    s["mgBlink"].val = "('MIDDLE_BUTTON',)"
    s["keyboardBackend"].val = "ioHub"           # zalecane przy eyetrackingu (alert 4550)

    # --- instrukcja (w pętli instr: 4 ekrany z pliku instrukcje.csv) ---
    r = Routine("instrukcja", exp); exp.addRoutine("instrukcja", r)
    r.addComponent(obraz(exp, "instrukcja", "instr_obraz", "$ekran", aktualizacja="set every repeat"))
    r.addComponent(klawiatura(exp, "instrukcja", "instr_klaw", "'space'"))
    r.addComponent(kodowy(exp, "instrukcja", "lsl_init",
                          begin_exp=kod("lsl_init__begin_experiment.py"),
                          begin_rout=kod("lsl_init__begin_routine.py"),
                          each=kod("lsl_init__each_frame.py"),
                          end_exp=kod("lsl_init__end_experiment.py")))

    # --- proba: krzyż 0,8 s -> karta (SPACJA, maks. 45 s) ---
    r = Routine("proba", exp); exp.addRoutine("proba", r)
    r.addComponent(obraz(exp, "proba", "krzyz", "bodzce/sluzbowe/krzyz_fiksacyjny.png", 0.0, 0.8))
    r.addComponent(obraz(exp, "proba", "karta", "$obraz", 0.8, 45.0, "set every repeat"))
    r.addComponent(klawiatura(exp, "proba", "klaw_karta", "'space'", 0.8, 45.0))
    et = EyetrackerRecordComponent(exp, "proba", name="etRecord", startVal=0.0, stopVal="",
                                   actionType="Start and Stop", stopWithRoutine=True)
    r.addComponent(et)
    r.addComponent(kodowy(exp, "proba", "znaczniki_proby",
                          begin_rout=kod("znaczniki_proby__begin_routine.py"),
                          each=kod("znaczniki_proby__each_frame.py"),
                          end_rout=kod("znaczniki_proby__end_routine.py")))

    # --- werdykt: Q1 F/J ---
    r = Routine("werdykt", exp); exp.addRoutine("werdykt", r)
    r.addComponent(obraz(exp, "werdykt", "q1", "bodzce/sluzbowe/Q1.png"))
    r.addComponent(klawiatura(exp, "werdykt", "werdykt_klaw", "'f','j'", poprawna="$poprawny_klawisz"))
    r.addComponent(kodowy(exp, "werdykt", "znacznik_resp",
                          begin_rout=kod("znacznik_resp__begin_routine.py"),
                          each=kod("znacznik_resp__each_frame.py"),
                          end_rout=kod("znacznik_resp__end_routine.py")))

    # --- przerwa_isi: pusty ekran 600 ms ---
    r = Routine("przerwa_isi", exp); exp.addRoutine("przerwa_isi", r)
    r.settings.params["stopType"].val = "duration (s)"
    r.settings.params["stopVal"].val = 0.6
    # rutyna bez komponentu z czasem trwania kończy się od razu -> pusty tekst 0,6 s trzyma przerwę
    r.addComponent(TextComponent(exp, "przerwa_isi", name="isi_pusty", text="", units="pix",
                                 startVal=0.0, stopVal=0.6))
    r.addComponent(kodowy(exp, "przerwa_isi", "lsl_klatka_isi",
                          each=kod("lsl_klatka__each_frame.py"),
                          end_rout=kod("przerwa_isi__end_routine.py")))

    # --- przerwa_blok: tylko po triale 8 i 16 ---
    r = Routine("przerwa_blok", exp); exp.addRoutine("przerwa_blok", r)
    r.settings.params["skipIf"].val = "trial not in (8, 16)"
    r.addComponent(obraz(exp, "przerwa_blok", "przerwa_obraz", "bodzce/sluzbowe/E07_przerwa.png"))
    r.addComponent(klawiatura(exp, "przerwa_blok", "przerwa_klaw", "'space'"))
    r.addComponent(kodowy(exp, "przerwa_blok", "lsl_klatka_blok", each=kod("lsl_klatka__each_frame.py")))

    # --- koniec ---
    r = Routine("koniec", exp); exp.addRoutine("koniec", r)
    r.addComponent(obraz(exp, "koniec", "koniec_obraz", "bodzce/sluzbowe/E08_koniec_czesci.png", 0.0, 5.0))
    r.addComponent(klawiatura(exp, "koniec", "koniec_klaw", "'space'", 0.0, 5.0))
    r.addComponent(kodowy(exp, "koniec", "lsl_klatka_koniec", each=kod("lsl_klatka__each_frame.py")))

    # --- Flow ---
    f = exp.flow
    for i, nazwa in enumerate(["instrukcja", "proba", "werdykt", "przerwa_isi", "przerwa_blok", "koniec"]):
        f.addRoutine(exp.routines[nazwa], i)
    # najpierw pętla trials (indeksy przed wstawieniem pętli instr), potem instr
    trials = TrialHandler(exp, name="trials", loopType="sequential", nReps=1,
                          conditionsFile="warunki/warunki_L1.csv")
    f.addLoop(trials, 1, 5)                # [trials: proba, werdykt, przerwa_isi, przerwa_blok]
    instr = TrialHandler(exp, name="instr", loopType="sequential", nReps=1,
                         conditionsFile="warunki/instrukcje.csv")
    f.addLoop(instr, 0, 1)                 # [instr: instrukcja]

    out = EKS / "P1_szkielet.psyexp"
    exp.saveToXML(str(out), makeLegacy=False)
    print("Zapisano", out)


if __name__ == "__main__":
    main()
