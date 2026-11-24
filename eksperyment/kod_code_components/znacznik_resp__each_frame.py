# Code Component "znacznik_resp" – Each Frame (komponent POD klawiaturą werdykt_klaw)
lsl_tick()
if werdykt_klaw.keys and not resp_wyslany:
    znacznik('resp', trial=trial, klawisz=werdykt_klaw.keys,
             poprawny=int(werdykt_klaw.keys == poprawny_klawisz))
    resp_wyslany = True
