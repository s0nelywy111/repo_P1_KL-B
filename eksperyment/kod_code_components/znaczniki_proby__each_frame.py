# Code Component "znaczniki_proby" – Each Frame
lsl_tick()
if not stim_wyslany and karta.status == STARTED:
    # karta właśnie wystartowała w tej klatce -> znacznik na flip, w którym pojawi się na ekranie
    znacznik_na_flip('stim:onset', trial=trial, obraz=obraz)
    stim_wyslany = True
