#!/usr/bin/env python3
"""
Most symulator -> LSL (KL-B, pakiet P1).

Łączy się z symulatorem biosygnałów (tryb tcp), czyta linie NDJSON
we wspólnym formacie LBK i publikuje je jako strumień LSL:

    nazwa: LBK_Sim   typ: Physio   format: float32   kanały: KANALY (niżej)

Zasady:
  * każde brakujące pole, wartość null albo nieliczbowa -> NaN
    (most NIGDY się nie zatrzymuje z powodu braku pola);
  * pole "quality" jest kodowane liczbowo: ok=0, noisy=1, lost=2, inne/brak=NaN;
  * niepoprawna linia JSON jest pomijana i liczona (licznik w logu);
  * po zerwaniu połączenia most czeka i łączy się ponownie;
  * znacznik czasu LSL = local_clock() w chwili odebrania linii
    (symulator nie zna zegara LSL; opóźnienie TCP wchodzi w błąd czasu).

Uruchomienie (najpierw symulator):
    python symulator_biosygnalow.py --mode tcp --scenario mix
    python sim_to_lsl.py                       # 127.0.0.1:5555
Test na liniach z pliku (bez symulatora):
    python sim_to_lsl.py --plik linie_testowe.jsonl --tylko-wypisz
    python sim_to_lsl.py --plik linie_testowe.jsonl          # wypycha też do LSL

Wymaga: pylsl (pip install pylsl).
"""
import argparse
import json
import math
import socket
import sys
import time

# Kolejność kanałów strumienia LBK_Sim.
# Pierwsze pola wysyła symulator; pola wzroku i oddechu przewiduje wspólny
# format LBK (aparatura), symulator ich nie wysyła -> w LSL będą NaN.
# [SPRAWDZIĆ] nazwy pól wzroku/oddechu ze stroną
# „Badania LBK – pakiety, architektura, wspólny format” i w razie potrzeby
# poprawić tylko tę listę.
KANALY = [
    ("t_sim", "s"),        # czas symulatora (własny zegar urządzenia)
    ("seq", "count"),
    ("hr", "bpm"),
    ("rr_ms", "ms"),
    ("eda_us", "uS"),
    ("focus", "a.u."),
    ("quality", "code"),   # 0=ok, 1=noisy, 2=lost
    ("gaze_x", "px"),
    ("gaze_y", "px"),
    ("pupil_mm", "mm"),
    ("resp", "a.u."),
]
# nazwa pola w JSON -> nazwa kanału (gdy się różnią)
ALIASY = {"t": "t_sim"}
KOD_JAKOSCI = {"ok": 0.0, "noisy": 1.0, "lost": 2.0}
NAN = float("nan")


def na_liczbe(v):
    """Zamienia wartość z JSON na float; wszystko, czego się nie da -> NaN."""
    if v is None or isinstance(v, bool):
        return NAN
    try:
        x = float(v)
    except (TypeError, ValueError):
        return NAN
    return x if math.isfinite(x) else NAN


def rekord_na_probke(rec):
    """dict z JSON -> lista floatów w kolejności KANALY (brak pola = NaN)."""
    rec = {ALIASY.get(k, k): v for k, v in rec.items()}
    probka = []
    for nazwa, _ in KANALY:
        if nazwa == "quality":
            probka.append(KOD_JAKOSCI.get(rec.get("quality"), NAN))
        else:
            probka.append(na_liczbe(rec.get(nazwa)))
    return probka


def parsuj_linie(linia):
    """Zwraca próbkę albo None, jeśli linia nie jest obiektem JSON."""
    linia = linia.strip()
    if not linia:
        return None
    try:
        rec = json.loads(linia)
    except json.JSONDecodeError:
        return None
    if not isinstance(rec, dict):
        return None
    return rekord_na_probke(rec)


def utworz_outlet(hz):
    from pylsl import StreamInfo, StreamOutlet, cf_float32

    info = StreamInfo("LBK_Sim", "Physio", len(KANALY), hz, cf_float32, "lbk_sim_p1")
    kan = info.desc().append_child("channels")
    for nazwa, jedn in KANALY:
        c = kan.append_child("channel")
        c.append_child_value("label", nazwa)
        c.append_child_value("unit", jedn)
    info.desc().append_child_value("quality_codes", "ok=0;noisy=1;lost=2")
    info.desc().append_child_value("source", "symulator_biosygnalow.py via sim_to_lsl.py")
    return StreamOutlet(info)


class Licznik:
    def __init__(self):
        self.ok = self.zle_linie = self.braki = 0
        self.t_log = time.time()

    def dodaj(self, probka):
        self.ok += 1
        self.braki += sum(1 for x in probka if math.isnan(x))

    def log(self, co_ile=5.0, wymus=False):
        if wymus or time.time() - self.t_log >= co_ile:
            print(f"[most] wysłano {self.ok} próbek, pominięto złych linii: "
                  f"{self.zle_linie}, pól NaN łącznie: {self.braki}", file=sys.stderr)
            self.t_log = time.time()


def obsluz_linie(linia, outlet, licznik, wypisz):
    probka = parsuj_linie(linia)
    if probka is None:
        if linia.strip():
            licznik.zle_linie += 1
        return
    licznik.dodaj(probka)
    if wypisz:
        print(dict(zip([k for k, _ in KANALY], probka)))
    if outlet is not None:
        from pylsl import local_clock
        outlet.push_sample(probka, local_clock())


def z_pliku(args):
    outlet = None if args.tylko_wypisz else utworz_outlet(0.0)
    licznik = Licznik()
    with open(args.plik, encoding="utf-8") as f:
        for linia in f:
            obsluz_linie(linia, outlet, licznik, wypisz=True)
            if outlet is not None:
                time.sleep(0.25)
    licznik.log(wymus=True)


def z_symulatora(args):
    outlet = utworz_outlet(args.hz)
    licznik = Licznik()
    print(f"[most] strumień LBK_Sim gotowy ({len(KANALY)} kanałów). "
          f"Łączę z {args.host}:{args.port} ...", file=sys.stderr)
    while True:
        try:
            with socket.create_connection((args.host, args.port), timeout=5) as s:
                s.settimeout(None)
                print("[most] połączono z symulatorem", file=sys.stderr)
                with s.makefile("r", encoding="utf-8", errors="replace") as f:
                    for linia in f:
                        obsluz_linie(linia, outlet, licznik, wypisz=args.wypisz)
                        licznik.log()
            print("[most] symulator zamknął połączenie", file=sys.stderr)
        except (ConnectionRefusedError, socket.timeout, OSError) as e:
            print(f"[most] brak połączenia ({e.__class__.__name__}); "
                  f"ponowna próba za 2 s", file=sys.stderr)
        time.sleep(2)


def main():
    p = argparse.ArgumentParser(description="Most symulator -> LSL (LBK_Sim)")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=5555)
    p.add_argument("--hz", type=float, default=4.0, help="nominalna częstotliwość strumienia")
    p.add_argument("--plik", help="zamiast TCP: czytaj linie z pliku (test)")
    p.add_argument("--tylko-wypisz", action="store_true", help="z --plik: bez LSL, tylko wydruk")
    p.add_argument("--wypisz", action="store_true", help="wypisuj każdą próbkę")
    args = p.parse_args()
    try:
        z_pliku(args) if args.plik else z_symulatora(args)
    except KeyboardInterrupt:
        print("\n[most] zatrzymano (Ctrl+C)", file=sys.stderr)


if __name__ == "__main__":
    main()
