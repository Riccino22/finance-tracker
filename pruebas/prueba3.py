import pandas as pd

xl = pd.ExcelFile('pruebas/prueba3.xls')
df = xl.parse(xl.sheet_names[0], header=6)  # header=6 porque es 0-indexed
print(df)