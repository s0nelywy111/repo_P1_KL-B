# ===================================================================
# Code Component "lsl_init" (rutyna: instrukcja) – zakładka Begin Experiment
# KL-B / P1: znaczniki LSL (LBK_Markers) + nieblokujący odbiór LBK_Sim
# Wymaga pakietu pylsl w PsychoPy (Tools > Plugin/packages manager > Packages)
# ===================================================================
import math
import statistics
from collections import deque
from pylsl import (StreamInfo, StreamOutlet, StreamInlet, ContinuousResolver,
                   local_clock, cf_string)

# --- 1. Strumień znaczników: LBK_Markers, typ Markers, 1 kanał tekstowy ---
lsl_zn_info = StreamInfo('LBK_Markers', 'Markers', 1, 0, cf_string, 'lbk_markers_p1')
lsl_zn = StreamOutlet(lsl_zn_info)

def znacznik(nazwa, **pola):
    """Wysyła znacznik TERAZ. Format: nazwa|klucz=wartość|...
    [SPRAWDZIĆ] ze słownikiem znaczników na stronie
    'Badania LBK – pakiety, architektura, wspólny format'."""
    tekst = nazwa + ''.join('|%s=%s' % (k, v) for k, v in pola.items())
    lsl_zn.push_sample([tekst])  # znacznik czasu = local_clock() w chwili wysłania
    print('[ZNACZNIK] %.3f %s' % (local_clock(), tekst))
    return tekst

def znacznik_na_flip(nazwa, **pola):
    """Wysyła znacznik w chwili najbliższego odświeżenia ekranu (flip)."""
    win.callOnFlip(znacznik, nazwa, **pola)

# --- 2. Odbiór LBK_Sim bez blokowania ---
OKNO_S = 5.0            # okno kroczące [s]
CO_ILE_WYDRUK = 1.0     # wydruk w konsoli eksperymentatora co 1 s
lsl_resolver = ContinuousResolver(prop='name', value='LBK_Sim')  # szuka w tle
lsl = {
    'wej': None,          # StreamInlet po znalezieniu strumienia
    'idx': {'hr': 2, 'rr_ms': 3, 'eda_us': 4, 'quality': 6},  # nadpisywane z opisu kanałów
    'bufor': deque(),     # (ts, hr, rr_ms, eda_us) tylko próbki quality == ok
    'odebrane': 0,        # wszystkie próbki
    'pominiete': 0,       # quality != ok (noisy, lost, brak)
    't_wydruk': 0.0,
    't_szukaj': -10.0,
}

def _polacz_lsl(teraz):
    if teraz - lsl['t_szukaj'] < 1.0:
        return
    lsl['t_szukaj'] = teraz
    wyniki = lsl_resolver.results()
    if not wyniki:
        return
    wej = StreamInlet(wyniki[0], max_buflen=30)
    try:  # nazwy kanałów z opisu strumienia (most zapisuje je w desc/channels)
        ch = wej.info(timeout=1.0).desc().child('channels').child('channel')
        nazwy = []
        while not ch.empty():
            nazwy.append(ch.child_value('label'))
            ch = ch.next_sibling()
        for k in ('hr', 'rr_ms', 'eda_us', 'quality'):
            if k in nazwy:
                lsl['idx'][k] = nazwy.index(k)
    except Exception as e:
        print('[LSL] brak opisu kanałów, używam domyślnych indeksów:', e)
    lsl['wej'] = wej
    print('[LSL] połączono z LBK_Sim, indeksy kanałów:', lsl['idx'])

def cechy_okna():
    """Średnie HR [bpm], RMSSD z rr_ms [ms], mediana EDA [µS] z ostatnich OKNO_S s."""
    b = lsl['bufor']
    hr = [x[1] for x in b if not math.isnan(x[1])]
    rr = [x[2] for x in b if not math.isnan(x[2])]
    eda = [x[3] for x in b if not math.isnan(x[3])]
    roznice = [r2 - r1 for r1, r2 in zip(rr, rr[1:])]
    return {
        'n': len(b),
        'hr_sr': sum(hr) / len(hr) if hr else float('nan'),
        'rmssd': math.sqrt(sum(d * d for d in roznice) / len(roznice)) if roznice else float('nan'),
        'eda_med': statistics.median(eda) if eda else float('nan'),
    }

def lsl_tick():
    """Wołać w KAŻDEJ klatce (Each Frame) każdej rutyny. Nigdy nie blokuje."""
    teraz = local_clock()
    if lsl['wej'] is None:
        _polacz_lsl(teraz)
        return
    dane, czasy = lsl['wej'].pull_chunk(timeout=0.0)
    I = lsl['idx']
    for x, t in zip(dane, czasy):
        lsl['odebrane'] += 1
        if x[I['quality']] != 0.0:        # 0 = ok; noisy=1, lost=2, NaN != 0 -> pomijamy
            lsl['pominiete'] += 1
            continue
        lsl['bufor'].append((t, x[I['hr']], x[I['rr_ms']], x[I['eda_us']]))
    b = lsl['bufor']
    while b and b[0][0] < b[-1][0] - OKNO_S:   # okno kroczące wg czasu LSL próbek
        b.popleft()
    if teraz - lsl['t_wydruk'] >= CO_ILE_WYDRUK:
        lsl['t_wydruk'] = teraz
        c = cechy_okna()
        print('[LSL %8.1f] okno %.0f s: n=%d | HR_sr=%.1f bpm | RMSSD=%.1f ms | '
              'EDA_med=%.2f uS | pominiete (quality!=ok): %d z %d'
              % (teraz, OKNO_S, c['n'], c['hr_sr'], c['rmssd'], c['eda_med'],
                 lsl['pominiete'], lsl['odebrane']))
