# Guion de la presentacion en video

Duracion prevista: 15 a 20 minutos, con pantalla compartida.

**Preparacion previa a la grabacion.** Dejar ejecutados los comandos de calibracion y evaluacion, la interfaz levantada en el navegador, y el editor abierto en `oncobridge/components/scoring.py` y en la seccion de resultados del README.

```bash
pip install -r requirements.txt
python scripts/split_dataset.py
python scripts/calibrar_umbrales.py
streamlit run interfaces/app_streamlit.py
```

---

## Seccion 1. Problema (0:00 - 2:00)

OncoBridge dispone de una base de conocimiento oncologico curada que ningun profesional puede revisar de forma exhaustiva durante una consulta. El conocimiento existe pero no llega al momento en que se toma la decision: el oncologo tiene minutos por paciente, y el radiologo recibe el estudio sin la pregunta clinica que motivo la derivacion.

El costo de esa brecha es medible. El estadio al momento del diagnostico es el predictor mas fuerte de sobrevida en la mayoria de los tumores solidos, y cada mes de demora en iniciar tratamiento se asocia a un incremento del riesgo de mortalidad.

El sistema no intenta diagnosticar. Intenta que la informacion correcta este disponible en el momento en que se decide si un paciente necesita un estudio por imagenes.

*En pantalla:* encabezado del README.

---

## Seccion 2. Valor del aprendizaje (2:00 - 4:00)

Construir el sistema de punta a punta obligo a resolver tres problemas que un ejercicio acotado no plantea.

El primero es donde ubicar el modelo generativo. La conclusion fue que no debe intervenir en ninguna decision con consecuencia clinica, sino unicamente en la redaccion.

El segundo es como evaluar. La accuracy global oculta el comportamiento sobre los subgrupos que importan, y en oncologia sensibilidad y especificidad no son intercambiables porque los dos errores tienen consecuencias distintas.

El tercero es la separacion entre calibracion y medicion. Ajustar los umbrales sobre los mismos casos con los que despues se reporta el desempeno produce numeros mejores y sin valor predictivo.

Los tres son transferibles a cualquier sistema de apoyo a la decision, dentro y fuera del dominio medico.

---

## Seccion 3. Demostracion funcional (4:00 - 9:30)

*Vista del Componente 1, caso positivo.* Cargar el caso de ejemplo: hematuria macroscopica, dolor lumbar y masa palpable en flanco, en un paciente de 63 anios con tabaquismo e hipertension. Ejecutar el analisis.

Antes de que aparezca el resultado, senalar el orden de ejecucion: el sistema recupera las hipotesis contra la base y calcula la probabilidad con una formula explicita, y recien despues el modelo de lenguaje redacta el texto. Ninguna de las decisiones proviene del modelo.

Al mostrarse el resultado, abrir las hipotesis. Las tres son renales, ordenadas por evidencia, y cada una enumera lo que la sostiene: sintomas compatibles, hallazgos, compromiso del organo, factores de riesgo. Ese listado es la respuesta a por que el sistema propuso cada hipotesis.

*Caso negativo.* Reemplazar por un paciente sin sintomas relevantes. El sistema devuelve que no hay elementos para evaluar. Es una respuesta clinicamente valida y no una falla: significa que los datos no orientan a ninguna condicion cubierta por la base.

*Vista del Componente 2.* Con la hipotesis renal activa, generar la guia de lectura. El componente devuelve la modalidad sugerida, las proyecciones recomendadas, las zonas prioritarias y los hallazgos esperados, junto con una referencia visual sintetica del patron.

Aclarar el alcance: el dataset no incluye estudios de los pacientes, de modo que el componente no analiza imagenes reales. Resuelve el problema inverso, que si es abordable con los datos disponibles: dejar formulada la pregunta clinica antes de que el estudio se lea.

---

## Seccion 4. Metodologia y resultados (9:30 - 12:30)

El dataset tiene 30 entradas de ground truth y 110 casos clinicos distribuidos en positivos, negativos, borderline, sutiles y complejos.

Explicar la particion: 70 por ciento para calibrar y 30 por ciento reservado para la medicion final, estratificado por categoria y con semilla fija. Los umbrales se ajustaron por busqueda en grilla unicamente sobre entrenamiento, con una restriccion de sensibilidad minima que responde a criterio clinico: no derivar a un paciente con lesion es un error mas costoso que derivar a uno sin ella.

*En pantalla:* ejecutar la evaluacion sobre test y mostrar la tabla del README.

Sobre los 34 casos no vistos: accuracy de derivacion 0.765, sensibilidad 0.800, especificidad 0.778, precision de la hipotesis principal 0.852.

Senalar los dos extremos. El sistema resuelve la totalidad de los casos sutiles y de los complejos con historial extenso. Cae a 0.400 en los borderline, que son los casos donde la presentacion es compatible con una hipotesis oncologica pero el contexto indica no derivar.

Mencionar la brecha de generalizacion: la sensibilidad baja de 0.925 en entrenamiento a 0.800 en prueba. Sin la particion, el numero reportado habria sido el primero, mas favorable y no representativo.

---

## Seccion 5. Arquitectura (12:30 - 15:30)

*En pantalla:* diagrama del README y `scoring.py`.

La decision central es la separacion entre logica clinica y generacion de texto. Hipotesis, probabilidades y recomendacion se resuelven con codigo deterministico; el modelo de lenguaje solo redacta sobre valores ya cerrados.

La recuperacion puntua seis senales clinicas por separado, ponderadas por la especificidad de cada termino dentro de la base. Un termino presente en casi todas las entradas no discrimina y pesa poco; uno que aparece en dos entradas es el que separa diagnosticos.

Detenerse en dos piezas. La especificidad anatomica corrige la confusion entre organos vecinos, que era el error mas frecuente de la primera version. Y la regla de que una hipotesis sin evidencia enumerable no se propone, aunque supere el umbral numerico.

Mostrar la formula. El peso de malignidad por capitulo ICD-10 se incorporo despues de medir una especificidad de 0.156 en la primera evaluacion: el sistema derivaba practicamente todo. El factor reproduce una asimetria real, que el umbral para pedir un estudio es mas bajo ante sospecha de malignidad, y se aplica por capitulo de la clasificacion y no por entrada individual.

---

## Seccion 6. Aprendizajes (15:30 - 17:30)

Los errores relevantes fueron de calibracion y no de implementacion.

El primero: la recuperacion original dividia por la union de vocabularios, lo que penalizaba a las entradas con descripciones mas extensas aunque compartieran mas terminos especificos con el paciente. Se corrigio midiendo cobertura del vocabulario del paciente.

El segundo: los biomarcadores sumaban evidencia completa ante cualquier laboratorio cargado, sin verificar el valor contra un umbral. Marcadores inespecificos como LDH inflaban decenas de hipotesis a la vez.

El tercero: la probabilidad de coincidencia se normalizaba contra el mejor candidato del propio caso. En pacientes sin patologia, el candidato menos malo quedaba con probabilidad alta porque siempre existe un maximo.

El cuarto: un caso descripto con dos palabras producia cobertura total con una sola coincidencia. Se agrego un factor de suficiencia de informacion.

La limitacion principal que permanece es el desempeno sobre casos borderline. Una recuperacion basada en terminos no distingue una presentacion compatible que si requiere estudio de una que no.

---

## Seccion 7. Experiencia de usuario y produccion (17:30 - 20:00)

*En pantalla:* ambas vistas de la interfaz.

Cada componente presenta la informacion con el vocabulario de su perfil y sin exponer estructuras JSON. El oncologo recibe recomendacion, urgencia e hipotesis con su evidencia. El radiologo recibe la guia de lectura junto a la referencia visual. La ejecucion exige confirmar que los datos ingresados no contienen informacion identificable.

Sobre privacidad: los datos del trabajo son sinteticos, pero en un despliegue real solo deberian enviarse variables clinicas asociadas a un identificador interno no reversible. El marco aplicable seria la Ley 26.529 en Argentina, y HIPAA o GDPR segun la jurisdiccion de los pacientes.

Sobre produccion: los componentes escalan distinto, ya que el segundo requiere GPU cuando genera imagen y el primero no, lo que justifica servicios separados. El indicador de monitoreo mas util es la tasa de derivacion, cuya desviacion respecto del historico senala que la recuperacion dejo de funcionar, tipicamente tras actualizar la base.

Antes de cualquier uso clinico harian falta una validacion retrospectiva sobre casos reales revisada por especialistas y un periodo de operacion en sombra, con el sistema emitiendo recomendaciones que no se muestran al profesional, para medir concordancia sin exponer pacientes.
