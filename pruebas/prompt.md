Quiero un sistema hecho en streamlit que me muestre graficos de mis movimientos bancarios

En el sistema el usuario va a adjuntar un arhivo pdf todos los meses con sus movimientos, es decir sera un archivo cada mes. Este pdf será formateado segun el script en pruebas/prueba.py. Luego de que el usuario cargue. Esta informacion se guardara en una base de datos con postgres

Tambien todos los datos que se puedan categorizar se podran gestionar en una pagina aparte. Por ejemplo, a las referencias (que seria equivalente al nombre del servicio en la mayoria de los casos) se puede clasificar segun alguna categoria (transporte, comida, otros) y estas categorias a su vez pueden modificarse, agregarse o eliminarse.

Los graficos que quiero visualizar son los siguientes

* Primero me gustaria un grafico de lineas para saber como ha evolucionado mi saldo inicial a lo largo de los meses
* Grafico para visualizar el promedio de los creditos por cada año
* Grafico de barras con debitos y creditos por categoria
* Saldo promedio mensual vs saldo cierre
* Heatmap de gastos: día de la semana × categoría (¿gastás más los viernes?)
* Proyección de saldo: regresión simple para estimar cierre del mes si seguís al mismo ritmo

Quiero usar docker compose con 4 servicios:

* El primero la app de streamlit
* El segundo la api que sera el punto medio entre la base de datos y el cliente
* El tercero un mcp si quiero conectar los datos de mis movimientos con un llm que haga consultas select directamente en la base de datos
* El cuarto la base de datos con postgres

Respecto al MCP, puede comunicarse con la api para ciertas operaciones (para evitar redundancia en el codigo), incluso si se puede centralizar en la api y que el mcp sea un cliente de la api tambien sirve. El mcp puede contener:

* Prompts predefinidos como slash commands: /analizar-mes, /comparar-años, /donde-gasto-mas — el LLM ya sabe qué consultar sin que escribas la pregunta desde cero
* Elicitation para consultas ambiguas: si le preguntás "¿cómo estoy este mes?" el MCP te pregunta de vuelta "¿comparado con el mes anterior o con el promedio anual?"
* Uso de resources para mejor contexto para el modelo
* Me gustaria en las tools tener algunas para consultas comunes de promedios, tendencias, etc.

Detalles adicionales:
* Detección de duplicados al subir: si el PDF del mes ya fue procesado, avisarte en vez de insertarlo dos veces
* Export a CSV/Excel desde los gráficos filtrados

Respecto a la UI, toma como referencia los html de la carpeta templates