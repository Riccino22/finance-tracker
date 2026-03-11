import fitz  # pymupdf
import re
import json


doc = fitz.open("6495121 (1) copy.pdf")
RAW = ""
for pagina in doc:
    RAW += pagina.get_text()

texto = RAW.replace(r'\n', '\n')  # decodificar \n literales

def parse_monto(s):
    return float(s.strip().replace('.', '').replace(',', '.'))

def es_fecha(s):
    return bool(re.match(r'^\d{2}[A-Z]{3}$', s.strip()))

def es_monto(s):
    return bool(re.match(r'^[\d.,]+$', s.strip()))

MARCADORES_INICIO = {'SDO.APERTURA', 'TRANSPORTE'}
MARCADORES_FIN    = {'SDO. CIERRE', 'No paga intereses.', 'SALDO PROMEDIO:',
                     'Total de Reduccion'}
TIPOS_CREDITO     = {'REDIVA', 'CRE. CAMBIOS', 'CRED.DIRECTO', 'CRE.CAMBIOS', 'DEVOLUCION'}

def es_credito(tipo):
    return any(tipo.strip().upper().startswith(t) for t in TIPOS_CREDITO)

RUIDO_RE = [
    r'^AG\. CIUDAD VIEJA$', r'^Zabala', r'^MONTEVIDEO$', r'^ÑI/',
    r'^SR\. ', r'^TREINTA Y TRES', r'^\d{5}$', r'^URUGUAY$',
    r'^\d{7}$', r'^URGP$', r'^US\.D$', r'^\d{2}FEB\d{4}$',
    r'^[A-Z0-9]{5,8}c$', r'^\d+/ \d+$',
    r'^A PARTIR', r'^EL PRECIO', r'^ACTUALIZ', r'^POR MAS',
    r'^DE TARIFAS', r'^WWW\.ITAU', r'^N$', r'^1L$', r'^\d{2}/ \d+ - S$',
    r'^Los movimientos', r'^00$', r'^\d{11}$',
    r'^CANTIDAD', r'^POR CAJA', r'^64951',
]

def es_ruido(s):
    return any(re.match(p, s) for p in RUIDO_RE)

lineas = [l.strip() for l in texto.split('\n')
          if l.strip() and l.strip() != ' ' and not es_ruido(l.strip())]

# Encontrar saldo apertura (primer marcador de inicio)
saldo_apertura = None
idx_inicio = 0
for i, l in enumerate(lineas):
    if l in MARCADORES_INICIO:
        for j in range(i+1, min(i+6, len(lineas))):
            if es_monto(lineas[j]):
                saldo_apertura = parse_monto(lineas[j])
                idx_inicio = j + 1
                break
        break

movimientos = []
i = idx_inicio
while i < len(lineas):
    l = lineas[i]

    # Saltar marcador TRANSPORTE (encabezado de página 2)
    if l in MARCADORES_INICIO:
        i += 1
        while i < len(lineas) and es_monto(lineas[i]):
            i += 1
        continue

    # Fin de sección solo si NO viene TRANSPORTE después (otra página)
    if any(l.startswith(m) for m in MARCADORES_FIN):
        # Buscar si hay un TRANSPORTE más adelante (hay más páginas)
        hay_mas = any(lineas[j] == 'TRANSPORTE' for j in range(i, min(i+10, len(lineas))))
        if not hay_mas:
            break
        else:
            i += 1
            continue

    if not es_fecha(l):
        i += 1
        continue

    fecha = l; i += 1
    tipo = lineas[i].strip(); i += 1
    descripcion = lineas[i].strip(); i += 1

    montos = []
    while i < len(lineas) \
          and not es_fecha(lineas[i]) \
          and lineas[i] not in MARCADORES_INICIO \
          and not any(lineas[i].startswith(m) for m in MARCADORES_FIN):
        if es_monto(lineas[i]):
            montos.append(lineas[i].strip())
        i += 1

    debito = credito = saldo = None
    if len(montos) == 1:
        saldo = parse_monto(montos[0])
    elif len(montos) >= 2:
        saldo = parse_monto(montos[-1])
        monto_op = parse_monto(montos[0])
        if es_credito(tipo): credito = monto_op
        else: debito = monto_op

    movimientos.append({'fecha': fecha, 'tipo': tipo, 'descripcion': descripcion,
                        'debito': debito, 'credito': credito, 'saldo': saldo})

resultado = {
    'cuenta': 'RICCARDO RAINIER INOJOSA MED',
    'fecha_estado': '27FEB2026',
    'saldo_apertura': saldo_apertura,
    'saldo_cierre': movimientos[-1]['saldo'] if movimientos else None,
    'total_movimientos': len(movimientos),
    'movimientos': movimientos,
}

print(json.dumps(resultado, indent=2, ensure_ascii=False))