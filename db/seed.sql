-- ============================================================
-- Itaú Dashboard · Datos de prueba para demo
-- Cuenta ficticia: CARLOS RODRIGUEZ
-- Período: Agosto 2025 – Enero 2026 (6 meses)
-- ============================================================

-- Limpiar datos previos (orden por FK)
TRUNCATE transactions, references_catalog, statements RESTART IDENTITY CASCADE;

-- ============================================================
-- STATEMENTS (extractos mensuales)
-- ============================================================
INSERT INTO statements (account_name, year, month, fecha_estado, saldo_apertura, saldo_cierre, saldo_promedio, filename) VALUES
    ('SR. CARLOS RODRIGUEZ',  2025,  8, '31AGO2025', 48200.00,  52340.50,  50100.00, 'estado_ago_2025.pdf'),
    ('SR. CARLOS RODRIGUEZ',  2025,  9, '30SET2025', 52340.50,  47890.75,  49800.00, 'estado_set_2025.pdf'),
    ('SR. CARLOS RODRIGUEZ',  2025, 10, '31OCT2025', 47890.75,  61200.00,  54500.00, 'estado_oct_2025.pdf'),
    ('SR. CARLOS RODRIGUEZ',  2025, 11, '30NOV2025', 61200.00,  55430.20,  58100.00, 'estado_nov_2025.pdf'),
    ('SR. CARLOS RODRIGUEZ',  2025, 12, '31DIC2025', 55430.20,  49870.60,  52600.00, 'estado_dic_2025.pdf'),
    ('SR. CARLOS RODRIGUEZ',  2026,  1, '31ENE2026', 49870.60,  58920.30,  54200.00, 'estado_ene_2026.pdf');

-- ============================================================
-- REFERENCES CATALOG (comercios → categoría)
-- ============================================================
INSERT INTO references_catalog (descripcion, category_id) VALUES
    -- Supermercados (id=1)
    ('DISCO',           1),
    ('TIENDA INGLESA',  1),
    ('DEVOTO',          1),
    ('TA-TA',           1),
    ('GEANT',           1),
    -- Restaurantes (id=2)
    ('BURGER KING',     2),
    ('MC DONALDS',      2),
    ('SUBWAY',          2),
    ('LA PASIVA',       2),
    ('EL FOGON',        2),
    ('SUSHI CLUB',      2),
    -- Transporte (id=3)
    ('UBER',            3),
    ('CUTCSA',          3),
    ('ANCAP',           3),
    ('COPETROL',        3),
    -- Salud (id=4)
    ('FARMACIA URUGUAY', 4),
    ('FARMASHOP',        4),
    ('CASMU',            4),
    ('MEDICA URUGUAYA',  4),
    -- Tecnología (id=5)
    ('NETFLIX',          5),
    ('SPOTIFY',          5),
    ('AMAZON',           5),
    ('MERCADO LIBRE',    5),
    ('APPLE',            5),
    -- Transferencias (id=6)
    ('TRANSFERENCIA',    6),
    -- Ingresos (id=7)
    ('SUELDO',           7),
    ('HONORARIOS',       7),
    -- Servicios (id=8)
    ('UTE',              8),
    ('OSE',              8),
    ('ANTEL',            8),
    ('MOVISTAR',         8),
    ('DIRECTV',          8);

-- ============================================================
-- TRANSACTIONS
-- ============================================================

-- ── AGOSTO 2025 (statement_id=1) ──────────────────────────
INSERT INTO transactions (statement_id, position, fecha, fecha_completa, tipo, descripcion, debito, credito, saldo, reference_id) VALUES
(1,  0, '01AGO', '2025-08-01', 'CRED.DIRECTO',  'SUELDO',            NULL,     85000.00, 133200.00, (SELECT id FROM references_catalog WHERE descripcion='SUELDO')),
(1,  1, '03AGO', '2025-08-03', 'COMPRA',        'TIENDA INGLESA',     3240.50,  NULL,     129959.50, (SELECT id FROM references_catalog WHERE descripcion='TIENDA INGLESA')),
(1,  2, '05AGO', '2025-08-05', 'COMPRA',        'UBER',                890.00,  NULL,     129069.50, (SELECT id FROM references_catalog WHERE descripcion='UBER')),
(1,  3, '07AGO', '2025-08-07', 'COMPRA',        'BURGER KING',         680.00,  NULL,     128389.50, (SELECT id FROM references_catalog WHERE descripcion='BURGER KING')),
(1,  4, '08AGO', '2025-08-08', 'COMPRA',        'NETFLIX',             590.00,  NULL,     127799.50, (SELECT id FROM references_catalog WHERE descripcion='NETFLIX')),
(1,  5, '08AGO', '2025-08-08', 'COMPRA',        'SPOTIFY',             320.00,  NULL,     127479.50, (SELECT id FROM references_catalog WHERE descripcion='SPOTIFY')),
(1,  6, '10AGO', '2025-08-10', 'COMPRA',        'DISCO',              4120.00,  NULL,     123359.50, (SELECT id FROM references_catalog WHERE descripcion='DISCO')),
(1,  7, '12AGO', '2025-08-12', 'COMPRA',        'FARMACIA URUGUAY',    850.00,  NULL,     122509.50, (SELECT id FROM references_catalog WHERE descripcion='FARMACIA URUGUAY')),
(1,  8, '14AGO', '2025-08-14', 'COMPRA',        'UTE',                2100.00,  NULL,     120409.50, (SELECT id FROM references_catalog WHERE descripcion='UTE')),
(1,  9, '14AGO', '2025-08-14', 'COMPRA',        'OSE',                 480.00,  NULL,     119929.50, (SELECT id FROM references_catalog WHERE descripcion='OSE')),
(1, 10, '15AGO', '2025-08-15', 'COMPRA',        'MC DONALDS',          540.00,  NULL,     119389.50, (SELECT id FROM references_catalog WHERE descripcion='MC DONALDS')),
(1, 11, '17AGO', '2025-08-17', 'COMPRA',        'ANCAP',              3800.00,  NULL,     115589.50, (SELECT id FROM references_catalog WHERE descripcion='ANCAP')),
(1, 12, '19AGO', '2025-08-19', 'COMPRA',        'ANTEL',              1650.00,  NULL,     113939.50, (SELECT id FROM references_catalog WHERE descripcion='ANTEL')),
(1, 13, '20AGO', '2025-08-20', 'COMPRA',        'TIENDA INGLESA',     2890.00,  NULL,     111049.50, (SELECT id FROM references_catalog WHERE descripcion='TIENDA INGLESA')),
(1, 14, '22AGO', '2025-08-22', 'COMPRA',        'SUBWAY',              430.00,  NULL,     110619.50, (SELECT id FROM references_catalog WHERE descripcion='SUBWAY')),
(1, 15, '23AGO', '2025-08-23', 'COMPRA',        'MERCADO LIBRE',      5200.00,  NULL,     105419.50, (SELECT id FROM references_catalog WHERE descripcion='MERCADO LIBRE')),
(1, 16, '25AGO', '2025-08-25', 'COMPRA',        'CASMU',              3200.00,  NULL,     102219.50, (SELECT id FROM references_catalog WHERE descripcion='CASMU')),
(1, 17, '27AGO', '2025-08-27', 'COMPRA',        'GEANT',              6100.00,  NULL,      96119.50, (SELECT id FROM references_catalog WHERE descripcion='GEANT')),
(1, 18, '28AGO', '2025-08-28', 'COMPRA',        'UBER',                760.00,  NULL,      95359.50, (SELECT id FROM references_catalog WHERE descripcion='UBER')),
(1, 19, '29AGO', '2025-08-29', 'COMPRA',        'LA PASIVA',           510.00,  NULL,      94849.50, (SELECT id FROM references_catalog WHERE descripcion='LA PASIVA')),
(1, 20, '30AGO', '2025-08-30', 'COMPRA',        'DIRECTV',            1800.00,  NULL,      93049.50, (SELECT id FROM references_catalog WHERE descripcion='DIRECTV')),
(1, 21, '31AGO', '2025-08-31', 'COMPRA',        'DISCO',              3920.00,  NULL,      89129.50, (SELECT id FROM references_catalog WHERE descripcion='DISCO'));

-- ── SETIEMBRE 2025 (statement_id=2) ───────────────────────
INSERT INTO transactions (statement_id, position, fecha, fecha_completa, tipo, descripcion, debito, credito, saldo, reference_id) VALUES
(2,  0, '01SET', '2025-09-01', 'CRED.DIRECTO',  'SUELDO',            NULL,     85000.00, 137340.50, (SELECT id FROM references_catalog WHERE descripcion='SUELDO')),
(2,  1, '02SET', '2025-09-02', 'COMPRA',        'TIENDA INGLESA',     2980.00,  NULL,     134360.50, (SELECT id FROM references_catalog WHERE descripcion='TIENDA INGLESA')),
(2,  2, '04SET', '2025-09-04', 'COMPRA',        'BURGER KING',         720.00,  NULL,     133640.50, (SELECT id FROM references_catalog WHERE descripcion='BURGER KING')),
(2,  3, '05SET', '2025-09-05', 'COMPRA',        'NETFLIX',             590.00,  NULL,     133050.50, (SELECT id FROM references_catalog WHERE descripcion='NETFLIX')),
(2,  4, '05SET', '2025-09-05', 'COMPRA',        'SPOTIFY',             320.00,  NULL,     132730.50, (SELECT id FROM references_catalog WHERE descripcion='SPOTIFY')),
(2,  5, '08SET', '2025-09-08', 'COMPRA',        'DISCO',              5340.00,  NULL,     127390.50, (SELECT id FROM references_catalog WHERE descripcion='DISCO')),
(2,  6, '09SET', '2025-09-09', 'COMPRA',        'UBER',               1200.00,  NULL,     126190.50, (SELECT id FROM references_catalog WHERE descripcion='UBER')),
(2,  7, '10SET', '2025-09-10', 'COMPRA',        'FARMASHOP',           680.00,  NULL,     125510.50, (SELECT id FROM references_catalog WHERE descripcion='FARMASHOP')),
(2,  8, '12SET', '2025-09-12', 'COMPRA',        'UTE',                2100.00,  NULL,     123410.50, (SELECT id FROM references_catalog WHERE descripcion='UTE')),
(2,  9, '12SET', '2025-09-12', 'COMPRA',        'OSE',                 480.00,  NULL,     122930.50, (SELECT id FROM references_catalog WHERE descripcion='OSE')),
(2, 10, '14SET', '2025-09-14', 'COMPRA',        'SUSHI CLUB',         2400.00,  NULL,     120530.50, (SELECT id FROM references_catalog WHERE descripcion='SUSHI CLUB')),
(2, 11, '15SET', '2025-09-15', 'COMPRA',        'ANCAP',              4100.00,  NULL,     116430.50, (SELECT id FROM references_catalog WHERE descripcion='ANCAP')),
(2, 12, '17SET', '2025-09-17', 'COMPRA',        'ANTEL',              1650.00,  NULL,     114780.50, (SELECT id FROM references_catalog WHERE descripcion='ANTEL')),
(2, 13, '18SET', '2025-09-18', 'COMPRA',        'MOVISTAR',            890.00,  NULL,     113890.50, (SELECT id FROM references_catalog WHERE descripcion='MOVISTAR')),
(2, 14, '20SET', '2025-09-20', 'COMPRA',        'GEANT',              7800.00,  NULL,     106090.50, (SELECT id FROM references_catalog WHERE descripcion='GEANT')),
(2, 15, '22SET', '2025-09-22', 'COMPRA',        'MERCADO LIBRE',      8900.00,  NULL,      97190.50, (SELECT id FROM references_catalog WHERE descripcion='MERCADO LIBRE')),
(2, 16, '23SET', '2025-09-23', 'COMPRA',        'MC DONALDS',          480.00,  NULL,      96710.50, (SELECT id FROM references_catalog WHERE descripcion='MC DONALDS')),
(2, 17, '25SET', '2025-09-25', 'COMPRA',        'CASMU',              3200.00,  NULL,      93510.50, (SELECT id FROM references_catalog WHERE descripcion='CASMU')),
(2, 18, '27SET', '2025-09-27', 'COMPRA',        'DIRECTV',            1800.00,  NULL,      91710.50, (SELECT id FROM references_catalog WHERE descripcion='DIRECTV')),
(2, 19, '28SET', '2025-09-28', 'COMPRA',        'EL FOGON',           1850.00,  NULL,      89860.50, (SELECT id FROM references_catalog WHERE descripcion='EL FOGON')),
(2, 20, '29SET', '2025-09-29', 'COMPRA',        'DISCO',              4200.00,  NULL,      85660.50, (SELECT id FROM references_catalog WHERE descripcion='DISCO')),
(2, 21, '30SET', '2025-09-30', 'COMPRA',        'APPLE',              3500.00,  NULL,      82160.50, (SELECT id FROM references_catalog WHERE descripcion='APPLE'));

-- ── OCTUBRE 2025 (statement_id=3) – mes de ingreso extra ──
INSERT INTO transactions (statement_id, position, fecha, fecha_completa, tipo, descripcion, debito, credito, saldo, reference_id) VALUES
(3,  0, '01OCT', '2025-10-01', 'CRED.DIRECTO',  'SUELDO',            NULL,     85000.00, 132890.75, (SELECT id FROM references_catalog WHERE descripcion='SUELDO')),
(3,  1, '03OCT', '2025-10-03', 'CRED.DIRECTO',  'HONORARIOS',        NULL,     35000.00, 167890.75, (SELECT id FROM references_catalog WHERE descripcion='HONORARIOS')),
(3,  2, '04OCT', '2025-10-04', 'COMPRA',        'TIENDA INGLESA',     3450.00,  NULL,     164440.75, (SELECT id FROM references_catalog WHERE descripcion='TIENDA INGLESA')),
(3,  3, '05OCT', '2025-10-05', 'COMPRA',        'NETFLIX',             590.00,  NULL,     163850.75, (SELECT id FROM references_catalog WHERE descripcion='NETFLIX')),
(3,  4, '05OCT', '2025-10-05', 'COMPRA',        'SPOTIFY',             320.00,  NULL,     163530.75, (SELECT id FROM references_catalog WHERE descripcion='SPOTIFY')),
(3,  5, '07OCT', '2025-10-07', 'COMPRA',        'AMAZON',             4200.00,  NULL,     159330.75, (SELECT id FROM references_catalog WHERE descripcion='AMAZON')),
(3,  6, '08OCT', '2025-10-08', 'COMPRA',        'UBER',                650.00,  NULL,     158680.75, (SELECT id FROM references_catalog WHERE descripcion='UBER')),
(3,  7, '10OCT', '2025-10-10', 'COMPRA',        'DISCO',              4890.00,  NULL,     153790.75, (SELECT id FROM references_catalog WHERE descripcion='DISCO')),
(3,  8, '12OCT', '2025-10-12', 'COMPRA',        'UTE',                2100.00,  NULL,     151690.75, (SELECT id FROM references_catalog WHERE descripcion='UTE')),
(3,  9, '12OCT', '2025-10-12', 'COMPRA',        'OSE',                 480.00,  NULL,     151210.75, (SELECT id FROM references_catalog WHERE descripcion='OSE')),
(3, 10, '13OCT', '2025-10-13', 'COMPRA',        'SUSHI CLUB',         3100.00,  NULL,     148110.75, (SELECT id FROM references_catalog WHERE descripcion='SUSHI CLUB')),
(3, 11, '15OCT', '2025-10-15', 'COMPRA',        'ANCAP',              3600.00,  NULL,     144510.75, (SELECT id FROM references_catalog WHERE descripcion='ANCAP')),
(3, 12, '16OCT', '2025-10-16', 'COMPRA',        'FARMACIA URUGUAY',   1200.00,  NULL,     143310.75, (SELECT id FROM references_catalog WHERE descripcion='FARMACIA URUGUAY')),
(3, 13, '18OCT', '2025-10-18', 'COMPRA',        'ANTEL',              1650.00,  NULL,     141660.75, (SELECT id FROM references_catalog WHERE descripcion='ANTEL')),
(3, 14, '20OCT', '2025-10-20', 'COMPRA',        'MERCADO LIBRE',      6700.00,  NULL,     134960.75, (SELECT id FROM references_catalog WHERE descripcion='MERCADO LIBRE')),
(3, 15, '21OCT', '2025-10-21', 'COMPRA',        'BURGER KING',         890.00,  NULL,     134070.75, (SELECT id FROM references_catalog WHERE descripcion='BURGER KING')),
(3, 16, '22OCT', '2025-10-22', 'COMPRA',        'GEANT',              5400.00,  NULL,     128670.75, (SELECT id FROM references_catalog WHERE descripcion='GEANT')),
(3, 17, '24OCT', '2025-10-24', 'COMPRA',        'CASMU',              3200.00,  NULL,     125470.75, (SELECT id FROM references_catalog WHERE descripcion='CASMU')),
(3, 18, '25OCT', '2025-10-25', 'COMPRA',        'DIRECTV',            1800.00,  NULL,     123670.75, (SELECT id FROM references_catalog WHERE descripcion='DIRECTV')),
(3, 19, '27OCT', '2025-10-27', 'COMPRA',        'APPLE',              7500.00,  NULL,     116170.75, (SELECT id FROM references_catalog WHERE descripcion='APPLE')),
(3, 20, '28OCT', '2025-10-28', 'COMPRA',        'LA PASIVA',           620.00,  NULL,     115550.75, (SELECT id FROM references_catalog WHERE descripcion='LA PASIVA')),
(3, 21, '30OCT', '2025-10-30', 'COMPRA',        'TA-TA',              4200.00,  NULL,     111350.75, (SELECT id FROM references_catalog WHERE descripcion='TA-TA')),
(3, 22, '31OCT', '2025-10-31', 'COMPRA',        'UBER',                780.00,  NULL,     110570.75, (SELECT id FROM references_catalog WHERE descripcion='UBER'));

-- ── NOVIEMBRE 2025 (statement_id=4) – Black Friday ────────
INSERT INTO transactions (statement_id, position, fecha, fecha_completa, tipo, descripcion, debito, credito, saldo, reference_id) VALUES
(4,  0, '03NOV', '2025-11-03', 'CRED.DIRECTO',  'SUELDO',            NULL,     85000.00, 196200.00, (SELECT id FROM references_catalog WHERE descripcion='SUELDO')),
(4,  1, '04NOV', '2025-11-04', 'COMPRA',        'NETFLIX',             590.00,  NULL,     195610.00, (SELECT id FROM references_catalog WHERE descripcion='NETFLIX')),
(4,  2, '04NOV', '2025-11-04', 'COMPRA',        'SPOTIFY',             320.00,  NULL,     195290.00, (SELECT id FROM references_catalog WHERE descripcion='SPOTIFY')),
(4,  3, '05NOV', '2025-11-05', 'COMPRA',        'DISCO',              4100.00,  NULL,     191190.00, (SELECT id FROM references_catalog WHERE descripcion='DISCO')),
(4,  4, '07NOV', '2025-11-07', 'COMPRA',        'UBER',                920.00,  NULL,     190270.00, (SELECT id FROM references_catalog WHERE descripcion='UBER')),
(4,  5, '10NOV', '2025-11-10', 'COMPRA',        'UTE',                2100.00,  NULL,     188170.00, (SELECT id FROM references_catalog WHERE descripcion='UTE')),
(4,  6, '10NOV', '2025-11-10', 'COMPRA',        'OSE',                 480.00,  NULL,     187690.00, (SELECT id FROM references_catalog WHERE descripcion='OSE')),
(4,  7, '12NOV', '2025-11-12', 'COMPRA',        'ANTEL',              1650.00,  NULL,     186040.00, (SELECT id FROM references_catalog WHERE descripcion='ANTEL')),
(4,  8, '14NOV', '2025-11-14', 'COMPRA',        'CASMU',              3200.00,  NULL,     182840.00, (SELECT id FROM references_catalog WHERE descripcion='CASMU')),
(4,  9, '15NOV', '2025-11-15', 'COMPRA',        'ANCAP',              4200.00,  NULL,     178640.00, (SELECT id FROM references_catalog WHERE descripcion='ANCAP')),
(4, 10, '18NOV', '2025-11-18', 'COMPRA',        'TIENDA INGLESA',     5100.00,  NULL,     173540.00, (SELECT id FROM references_catalog WHERE descripcion='TIENDA INGLESA')),
(4, 11, '20NOV', '2025-11-20', 'COMPRA',        'FARMASHOP',           940.00,  NULL,     172600.00, (SELECT id FROM references_catalog WHERE descripcion='FARMASHOP')),
(4, 12, '22NOV', '2025-11-22', 'COMPRA',        'BURGER KING',         760.00,  NULL,     171840.00, (SELECT id FROM references_catalog WHERE descripcion='BURGER KING')),
-- Black Friday (28 NOV): pico de gastos en tecnología
(4, 13, '28NOV', '2025-11-28', 'COMPRA',        'AMAZON',            18500.00,  NULL,     153340.00, (SELECT id FROM references_catalog WHERE descripcion='AMAZON')),
(4, 14, '28NOV', '2025-11-28', 'COMPRA',        'MERCADO LIBRE',     12300.00,  NULL,     141040.00, (SELECT id FROM references_catalog WHERE descripcion='MERCADO LIBRE')),
(4, 15, '28NOV', '2025-11-28', 'COMPRA',        'APPLE',              8900.00,  NULL,     132140.00, (SELECT id FROM references_catalog WHERE descripcion='APPLE')),
(4, 16, '29NOV', '2025-11-29', 'COMPRA',        'GEANT',              9800.00,  NULL,     122340.00, (SELECT id FROM references_catalog WHERE descripcion='GEANT')),
(4, 17, '29NOV', '2025-11-29', 'COMPRA',        'DIRECTV',            1800.00,  NULL,     120540.00, (SELECT id FROM references_catalog WHERE descripcion='DIRECTV')),
(4, 18, '30NOV', '2025-11-30', 'COMPRA',        'SUSHI CLUB',         3200.00,  NULL,     117340.00, (SELECT id FROM references_catalog WHERE descripcion='SUSHI CLUB')),
(4, 19, '30NOV', '2025-11-30', 'COMPRA',        'DISCO',              3800.00,  NULL,     113540.00, (SELECT id FROM references_catalog WHERE descripcion='DISCO'));

-- ── DICIEMBRE 2025 (statement_id=5) – Gastos fin de año ───
INSERT INTO transactions (statement_id, position, fecha, fecha_completa, tipo, descripcion, debito, credito, saldo, reference_id) VALUES
(5,  0, '01DIC', '2025-12-01', 'CRED.DIRECTO',  'SUELDO',            NULL,     85000.00, 140430.20, (SELECT id FROM references_catalog WHERE descripcion='SUELDO')),
(5,  1, '01DIC', '2025-12-01', 'COMPRA',        'NETFLIX',             590.00,  NULL,     139840.20, (SELECT id FROM references_catalog WHERE descripcion='NETFLIX')),
(5,  2, '01DIC', '2025-12-01', 'COMPRA',        'SPOTIFY',             320.00,  NULL,     139520.20, (SELECT id FROM references_catalog WHERE descripcion='SPOTIFY')),
(5,  3, '03DIC', '2025-12-03', 'COMPRA',        'ANCAP',              4500.00,  NULL,     135020.20, (SELECT id FROM references_catalog WHERE descripcion='ANCAP')),
(5,  4, '05DIC', '2025-12-05', 'COMPRA',        'TIENDA INGLESA',     6800.00,  NULL,     128220.20, (SELECT id FROM references_catalog WHERE descripcion='TIENDA INGLESA')),
(5,  5, '08DIC', '2025-12-08', 'COMPRA',        'UTE',                2100.00,  NULL,     126120.20, (SELECT id FROM references_catalog WHERE descripcion='UTE')),
(5,  6, '08DIC', '2025-12-08', 'COMPRA',        'OSE',                 480.00,  NULL,     125640.20, (SELECT id FROM references_catalog WHERE descripcion='OSE')),
(5,  7, '10DIC', '2025-12-10', 'COMPRA',        'ANTEL',              1650.00,  NULL,     123990.20, (SELECT id FROM references_catalog WHERE descripcion='ANTEL')),
(5,  8, '12DIC', '2025-12-12', 'COMPRA',        'CASMU',              3200.00,  NULL,     120790.20, (SELECT id FROM references_catalog WHERE descripcion='CASMU')),
(5,  9, '14DIC', '2025-12-14', 'COMPRA',        'FARMACIA URUGUAY',   1100.00,  NULL,     119690.20, (SELECT id FROM references_catalog WHERE descripcion='FARMACIA URUGUAY')),
(5, 10, '15DIC', '2025-12-15', 'COMPRA',        'GEANT',             11200.00,  NULL,     108490.20, (SELECT id FROM references_catalog WHERE descripcion='GEANT')),
(5, 11, '17DIC', '2025-12-17', 'COMPRA',        'MERCADO LIBRE',      4500.00,  NULL,     103990.20, (SELECT id FROM references_catalog WHERE descripcion='MERCADO LIBRE')),
(5, 12, '19DIC', '2025-12-19', 'COMPRA',        'DISCO',              7200.00,  NULL,      96790.20, (SELECT id FROM references_catalog WHERE descripcion='DISCO')),
(5, 13, '20DIC', '2025-12-20', 'COMPRA',        'UBER',               1100.00,  NULL,      95690.20, (SELECT id FROM references_catalog WHERE descripcion='UBER')),
(5, 14, '22DIC', '2025-12-22', 'COMPRA',        'EL FOGON',           4200.00,  NULL,      91490.20, (SELECT id FROM references_catalog WHERE descripcion='EL FOGON')),
(5, 15, '23DIC', '2025-12-23', 'COMPRA',        'DIRECTV',            1800.00,  NULL,      89690.20, (SELECT id FROM references_catalog WHERE descripcion='DIRECTV')),
(5, 16, '24DIC', '2025-12-24', 'COMPRA',        'TIENDA INGLESA',     9400.00,  NULL,      80290.20, (SELECT id FROM references_catalog WHERE descripcion='TIENDA INGLESA')),
(5, 17, '26DIC', '2025-12-26', 'COMPRA',        'SUSHI CLUB',         5100.00,  NULL,      75190.20, (SELECT id FROM references_catalog WHERE descripcion='SUSHI CLUB')),
(5, 18, '28DIC', '2025-12-28', 'COMPRA',        'AMAZON',             6800.00,  NULL,      68390.20, (SELECT id FROM references_catalog WHERE descripcion='AMAZON')),
(5, 19, '30DIC', '2025-12-30', 'COMPRA',        'BURGER KING',         820.00,  NULL,      67570.20, (SELECT id FROM references_catalog WHERE descripcion='BURGER KING')),
(5, 20, '31DIC', '2025-12-31', 'COMPRA',        'LA PASIVA',          1100.00,  NULL,      66470.20, (SELECT id FROM references_catalog WHERE descripcion='LA PASIVA'));

-- ── ENERO 2026 (statement_id=6) – Vuelta a la normalidad ──
INSERT INTO transactions (statement_id, position, fecha, fecha_completa, tipo, descripcion, debito, credito, saldo, reference_id) VALUES
(6,  0, '02ENE', '2026-01-02', 'CRED.DIRECTO',  'SUELDO',            NULL,     85000.00, 134870.60, (SELECT id FROM references_catalog WHERE descripcion='SUELDO')),
(6,  1, '02ENE', '2026-01-02', 'COMPRA',        'NETFLIX',             590.00,  NULL,     134280.60, (SELECT id FROM references_catalog WHERE descripcion='NETFLIX')),
(6,  2, '02ENE', '2026-01-02', 'COMPRA',        'SPOTIFY',             320.00,  NULL,     133960.60, (SELECT id FROM references_catalog WHERE descripcion='SPOTIFY')),
(6,  3, '04ENE', '2026-01-04', 'COMPRA',        'TIENDA INGLESA',     3100.00,  NULL,     130860.60, (SELECT id FROM references_catalog WHERE descripcion='TIENDA INGLESA')),
(6,  4, '06ENE', '2026-01-06', 'COMPRA',        'UBER',                780.00,  NULL,     130080.60, (SELECT id FROM references_catalog WHERE descripcion='UBER')),
(6,  5, '07ENE', '2026-01-07', 'COMPRA',        'FARMASHOP',           540.00,  NULL,     129540.60, (SELECT id FROM references_catalog WHERE descripcion='FARMASHOP')),
(6,  6, '08ENE', '2026-01-08', 'COMPRA',        'ANCAP',              4100.00,  NULL,     125440.60, (SELECT id FROM references_catalog WHERE descripcion='ANCAP')),
(6,  7, '10ENE', '2026-01-10', 'COMPRA',        'UTE',                2100.00,  NULL,     123340.60, (SELECT id FROM references_catalog WHERE descripcion='UTE')),
(6,  8, '10ENE', '2026-01-10', 'COMPRA',        'OSE',                 480.00,  NULL,     122860.60, (SELECT id FROM references_catalog WHERE descripcion='OSE')),
(6,  9, '12ENE', '2026-01-12', 'COMPRA',        'ANTEL',              1650.00,  NULL,     121210.60, (SELECT id FROM references_catalog WHERE descripcion='ANTEL')),
(6, 10, '13ENE', '2026-01-13', 'COMPRA',        'BURGER KING',         650.00,  NULL,     120560.60, (SELECT id FROM references_catalog WHERE descripcion='BURGER KING')),
(6, 11, '14ENE', '2026-01-14', 'COMPRA',        'CASMU',              3200.00,  NULL,     117360.60, (SELECT id FROM references_catalog WHERE descripcion='CASMU')),
(6, 12, '15ENE', '2026-01-15', 'COMPRA',        'DISCO',              4800.00,  NULL,     112560.60, (SELECT id FROM references_catalog WHERE descripcion='DISCO')),
(6, 13, '17ENE', '2026-01-17', 'COMPRA',        'GEANT',              4200.00,  NULL,     108360.60, (SELECT id FROM references_catalog WHERE descripcion='GEANT')),
(6, 14, '19ENE', '2026-01-19', 'COMPRA',        'MC DONALDS',          580.00,  NULL,     107780.60, (SELECT id FROM references_catalog WHERE descripcion='MC DONALDS')),
(6, 15, '20ENE', '2026-01-20', 'COMPRA',        'MERCADO LIBRE',      3400.00,  NULL,     104380.60, (SELECT id FROM references_catalog WHERE descripcion='MERCADO LIBRE')),
(6, 16, '22ENE', '2026-01-22', 'COMPRA',        'DIRECTV',            1800.00,  NULL,     102580.60, (SELECT id FROM references_catalog WHERE descripcion='DIRECTV')),
(6, 17, '23ENE', '2026-01-23', 'COMPRA',        'FARMACIA URUGUAY',    890.00,  NULL,     101690.60, (SELECT id FROM references_catalog WHERE descripcion='FARMACIA URUGUAY')),
(6, 18, '25ENE', '2026-01-25', 'COMPRA',        'SUSHI CLUB',         2800.00,  NULL,      98890.60, (SELECT id FROM references_catalog WHERE descripcion='SUSHI CLUB')),
(6, 19, '27ENE', '2026-01-27', 'COMPRA',        'MOVISTAR',            890.00,  NULL,      98000.60, (SELECT id FROM references_catalog WHERE descripcion='MOVISTAR')),
(6, 20, '28ENE', '2026-01-28', 'COMPRA',        'APPLE',              2400.00,  NULL,      95600.60, (SELECT id FROM references_catalog WHERE descripcion='APPLE')),
(6, 21, '29ENE', '2026-01-29', 'COMPRA',        'TA-TA',              3800.00,  NULL,      91800.60, (SELECT id FROM references_catalog WHERE descripcion='TA-TA')),
(6, 22, '31ENE', '2026-01-31', 'COMPRA',        'UBER',                680.00,  NULL,      91120.60, (SELECT id FROM references_catalog WHERE descripcion='UBER'));

-- ============================================================
-- NOTAS en transacciones puntuales
-- ============================================================
UPDATE transactions SET nota = 'Proyecto freelance · dashboard para cliente'
WHERE statement_id = 3 AND position = 1;  -- HONORARIOS oct-2025

UPDATE transactions SET nota = 'Black Friday · Smart TV Samsung 55"'
WHERE statement_id = 4 AND position = 13; -- AMAZON $18.500 nov-2025

UPDATE transactions SET nota = 'Black Friday · auriculares + teclado mecánico'
WHERE statement_id = 4 AND position = 14; -- MERCADO LIBRE $12.300 nov-2025

UPDATE transactions SET nota = 'Compras Navidad · cena 24 y regalos familia'
WHERE statement_id = 5 AND position = 10; -- GEANT $11.200 dic-2025

UPDATE transactions SET nota = 'Cena fin de año con el equipo'
WHERE statement_id = 5 AND position = 14; -- EL FOGON $4.200 dic-2025

-- ============================================================
-- Verificación rápida
-- ============================================================
SELECT
    s.year,
    s.month,
    s.saldo_apertura,
    s.saldo_cierre,
    COUNT(t.id) AS movimientos,
    SUM(t.debito)  AS total_debitos,
    SUM(t.credito) AS total_creditos
FROM statements s
LEFT JOIN transactions t ON t.statement_id = s.id
GROUP BY s.id, s.year, s.month, s.saldo_apertura, s.saldo_cierre
ORDER BY s.year, s.month;
