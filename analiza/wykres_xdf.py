#!/usr/bin/env python3
"""
Wykres EDA z pliku XDF (LabRecorder) z pionowymi liniami znaczników – dowód wspólnej osi czasu.

    python analiza/wykres_xdf.py dane/xdf/sesja_KL-B.xdf
    -> dane/xdf/sesja_KL-B_eda_znaczniki.png  + podsumowanie w konsoli

Wymaga: pyxdf, matplotlib, numpy  (pip install pyxdf matplotlib numpy)
Oś X = czas LSL (s) od pierwszej próbki LBK_Sim. pyxdf domyślnie synchronizuje zegary
strumieni (offsety zapisane przez LabRecorder), więc znaczniki i EDA leżą na tej samej osi.
"""
import sys
from pathlib import Path

import numpy as np


def etykiety_kanalow(strumien):
    try:
        kan = strumien["info"]["desc"][0]["channels"][0]["channel"]
        return [k["label"][0] for k in kan]
    except (KeyError, IndexError, TypeError):
        return []


def znajdz(strumienie, nazwa):
    for s in strumienie:
        if s["info"]["name"][0] == nazwa:
            return s
    raise SystemExit(f"Brak strumienia {nazwa} w pliku. Są: "
                     f"{[s['info']['name'][0] for s in strumienie]}")


STYL = {  # typ znacznika -> (kolor, styl linii)
    "exp:start": ("black", "-"), "exp:end": ("black", "-"),
    "trial:start": ("tab:gray", ":"), "trial:end": ("tab:gray", ":"),
    "stim:onset": ("tab:red", "-"), "stim:offset": ("tab:purple", "--"),
    "resp": ("tab:blue", "-"),
}


def rysuj(strumienie, wyjscie, tytul=""):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    sim = znajdz(strumienie, "LBK_Sim")
    zn = znajdz(strumienie, "LBK_Markers")
    et = etykiety_kanalow(sim) or ["t_sim", "seq", "hr", "rr_ms", "eda_us", "focus", "quality"]
    dane = np.asarray(sim["time_series"], dtype=float)
    t = np.asarray(sim["time_stamps"], dtype=float)
    t0 = t[0]
    eda = dane[:, et.index("eda_us")]
    jak = dane[:, et.index("quality")]
    ok = jak == 0

    fig, ax = plt.subplots(figsize=(14, 5))
    eda_ok = np.where(ok, eda, np.nan)               # przerwy w linii tam, gdzie quality != ok
    ax.plot(t - t0, eda_ok, lw=1.2, color="tab:green", label="EDA (quality = ok)")
    zle = ~ok
    if zle.any():
        ax.plot(t[zle] - t0, np.where(np.isnan(eda[zle]), np.nanmin(eda), eda[zle]), "x",
                color="tab:orange", ms=4, label=f"próbki pominięte (quality ≠ ok): {zle.sum()}")

    widziane = set()
    for ts, (tekst,) in zip(zn["time_stamps"], zn["time_series"]):
        typ = tekst.split("|")[0]
        rodzina = typ.split(":")[0]
        kolor, linia = STYL.get(typ, ("tab:olive", "-"))
        ax.axvline(ts - t0, color=kolor, ls=linia, lw=0.9, alpha=0.8,
                   label=typ if typ not in widziane else None)
        widziane.add(typ)
        if rodzina == "exp":
            ax.text(ts - t0, ax.get_ylim()[1], typ, rotation=90, va="top", ha="right",
                    fontsize=7, color=kolor)

    ax.set_xlabel("czas LSL od pierwszej próbki LBK_Sim [s]")
    ax.set_ylabel("EDA [µS]")
    ax.set_title(tytul or "LBK_Sim (EDA) + LBK_Markers na wspólnej osi czasu LSL")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8)
    fig.tight_layout()
    fig.savefig(wyjscie, dpi=150)
    print(f"Zapisano {wyjscie}")

    czas_nagrania = t[-1] - t[0]
    typy = {}
    for (tekst,) in zn["time_series"]:
        typy[tekst.split("|")[0]] = typy.get(tekst.split("|")[0], 0) + 1
    print(f"LBK_Sim: {len(t)} próbek, {czas_nagrania:.1f} s, "
          f"śr. {len(t) / czas_nagrania:.2f} Hz, quality≠ok: {zle.sum()}")
    print(f"LBK_Markers: {len(zn['time_stamps'])} znaczników: {typy}")
    brak = [m for m in ("exp:start", "trial:start", "stim:onset", "resp", "exp:end") if m not in typy]
    if brak:
        print("UWAGA: w nagraniu brakuje znaczników:", brak)
    if czas_nagrania < 120:
        print("UWAGA: nagranie krótsze niż 2 min (wymóg KL-B).")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    import pyxdf
    sciezka = Path(sys.argv[1])
    strumienie, _ = pyxdf.load_xdf(str(sciezka))
    rysuj(strumienie, sciezka.with_name(sciezka.stem + "_eda_znaczniki.png"), sciezka.name)


if __name__ == "__main__":
    main()
