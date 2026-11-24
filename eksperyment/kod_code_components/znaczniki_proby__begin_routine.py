# Code Component "znaczniki_proby" (rutyna: proba) – Begin Routine
# Komponent musi być OSTATNI w rutynie (pod karta), żeby stim:onset trafił na flip karty.
stim_wyslany = False
if trials.thisN == 0:
    # początek części głównej = start eksperymentu w zapisie (LabRecorder już nagrywa)
    znacznik_na_flip('exp:start', uczestnik=expInfo['participant'], lista='L1')
znacznik_na_flip('trial:start', trial=trial, blok=blok, temat=temat,
                 sprawca=sprawca, weryfikacja=weryfikacja, wersja=wersja)
