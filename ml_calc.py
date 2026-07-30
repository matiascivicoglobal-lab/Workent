import math

# ---- Parametros globales (hoja "Costos") ----
DOLAR_SISTEMA   = 1495.0   # H7
COMISION_ML     = 0.16     # B7 (guardado como -0.16)
IIBB            = 0.05     # B8 (guardado como -0.05)
IMP_CHEQUE      = 0.012    # B9 (guardado como -0.012)
ENVIO           = 8500.0   # B10
CARGO_FIJO = [             # B3/B4/B5/B6
    (15000, 1255.0),
    (25000, 2500.0),
    (33000, 3030.0),
]
UMBRAL_ENVIO_GRATIS = 33000

def rounddown_10(x):  return math.floor(x / 10) * 10
def floor_5(x):       return math.floor(x / 5) * 5

def cargo_fijo(precio):
    if precio <= 15000: return 1255.0
    if precio <= 25000: return 2500.0
    if precio <  33000: return 3030.0
    return 0.0

def calcular_ml(precio_web, pct_ml, iva, costo_usd):
    # 1. Precio publicado en ML  (BM)
    precio_ml = rounddown_10(precio_web * pct_ml) + 9

    # 2. Precio neto de envio  (BN)
    base = precio_ml if precio_ml < UMBRAL_ENVIO_GRATIS else precio_ml - ENVIO
    precio_cobrado = rounddown_10(floor_5(base)) + 9

    # 3. Deducciones -- TODAS sobre precio_ml (BM), no sobre precio_cobrado
    iva_desc   = precio_ml / iva - precio_ml                    # BH  (negativo)
    neto_siva  = precio_ml + iva_desc                           # = precio_ml/iva
    comision   = -(cargo_fijo(precio_ml) + precio_ml * COMISION_ML)  # BI
    iibb       = -(neto_siva * IIBB)                            # BJ
    imp_ch     = -(precio_ml * IMP_CHEQUE)                      # BK

    # 4. Precio neto en USD  (BL)
    neto_ars = precio_cobrado + iva_desc + comision + iibb + imp_ch
    neto_usd = neto_ars / DOLAR_SISTEMA

    # 5. Markup y margen
    markup = neto_usd / costo_usd - 1                           # BG
    margen = 1 - costo_usd / neto_usd                           # BQ

    return dict(precio_ml=precio_ml, precio_cobrado=precio_cobrado,
                iva=iva_desc, comision=comision, iibb=iibb, imp_ch=imp_ch,
                neto_usd=neto_usd, markup=markup, margen=margen)

if __name__ == '__main__':
    casos = [
        ("fila 3   JS10000-3IN1", 87999, 1.2,  1.21,  31.97,
         dict(precio_ml=105599, precio_cobrado=97099, iva=-18327.0992, comision=-16895.84,
              iibb=-4363.595, imp_ch=-1267.188, neto_usd=37.6223, markup=0.1768, margen=0.1502)),
        ("fila 12  ESPATULA-UA02G", 2448, 1.3, 1.21, 0.46,
         dict(precio_ml=3189, precio_cobrado=3189, iva=-553.4628, comision=-1765.24,
              iibb=-131.7769, imp_ch=-38.268, neto_usd=0.4684, markup=0.0183, margen=0.0179)),
        ("fila 100 CIZALLA-130CM", 329999, 1.1, 1.105, 121.09,
         dict(precio_ml=362999, precio_cobrado=354499, iva=-34493.1177, comision=-58079.84,
              iibb=-16425.2941, imp_ch=-4355.988, neto_usd=161.3008, markup=0.3321, margen=0.2493)),
        ("fila 334 PLANCHA-SUB-TAZA", 138692, 1.15, 1.105, 27.73,
         dict(precio_ml=159499, precio_cobrado=150999, iva=-15156.0136, comision=-25519.84,
              iibb=-7217.1493, imp_ch=-1913.988, neto_usd=67.687, markup=1.4409, margen=0.5903)),
    ]
    ok = True
    for nombre, pw, pct, iva, costo, esp in casos:
        got = calcular_ml(pw, pct, iva, costo)
        print(f"\n{nombre}")
        for k, exp in esp.items():
            g = got[k]
            match = abs(g - exp) < 0.001 if isinstance(exp, float) else g == exp
            ok &= match
            print(f"  {k:<15} calc={round(g,4):>14}  excel={exp:>14}  {'OK' if match else 'DIFF'}")
    print("\n" + ("TODO COINCIDE" if ok else "HAY DIFERENCIAS"))
