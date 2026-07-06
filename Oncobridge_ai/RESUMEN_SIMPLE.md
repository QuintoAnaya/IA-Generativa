# Resumen simple — qué es esto y qué hice

Che, leé esto primero. Es la versión corta y en criollo de todo el laburo, para que entiendas de qué va antes de meterte en el código o la monografía.

## Qué había que hacer

El TP pedía construir un sistema de IA para ayudar en diagnóstico de cáncer. La idea del enunciado: un hospital tiene una base de datos gigante con conocimiento oncológico, pero los médicos no la pueden consultar mientras atienden. Entonces hay que armar un sistema que sí la consulte por ellos, en el momento.

El sistema tiene que tener **dos partes**:
1. Una que ayuda al **oncólogo** (el que atiende al paciente primero).
2. Una que ayuda al **radiólogo** (el que después mira la tomografía/resonancia).

Y además: código en GitHub que funcione, un dataset para probarlo, métricas, y un video en Loom explicándolo.

## Qué construí

Un sistema completo en Python que hace exactamente eso. Te lo explico como si fuera una fábrica con dos estaciones:

**Estación 1 — el asistente del oncólogo.** Le pasás los datos del paciente (edad, síntomas, si fuma, etc.) y el sistema:
- Busca en la base de conocimiento a qué tipo de cáncer se parece el cuadro.
- Te dice las hipótesis más probables (rankeadas).
- Decide si el paciente necesita un estudio de imagen o no.
- Le pone una urgencia (alta/media/baja).
- Escribe un resumen para pasarle al radiólogo.

**Estación 2 — el asistente del radiólogo.** Recibe ese resumen y el estudio, y:
- Le dice al radiólogo qué buscar y dónde en la imagen.
- Compara los hallazgos del estudio con lo que se esperaría para ese cáncer.
- Arma un borrador de informe.

## El truco más importante que hice (y por qué está bueno)

Acá está la decisión que más suma en la nota, prestá atención porque la vas a tener que explicar en el video:

La mayoría de la gente le pediría al modelo de IA (Gemini) que "piense" el diagnóstico. **Eso es peligroso**, porque los modelos de IA a veces inventan cosas que suenan bien pero son falsas (se llama "alucinación"). En medicina eso puede matar a alguien.

Entonces yo lo hice al revés: **la parte médica (qué cáncer, si necesita imagen, urgencia) NO la decide la IA**. La decide una búsqueda en la base de conocimiento, que es transparente y siempre se puede auditar. La IA (Gemini) sólo se usa para **redactar bonito** los textos. Así, si Gemini se manda una macana, no afecta la decisión médica.

Cada hipótesis que da el sistema queda "linkeada" a la entrada de la base de donde salió, así siempre se puede rastrear el porqué.

## Sobre tu API key de Gemini (importante)

- La key va en UN solo lugar: un archivo llamado `.env` que tenés que crear.
- Ese archivo está bloqueado para que **nunca se suba a GitHub** (lo bloqueé con `.gitignore`). O sea, tu key no se filtra.
- Hay un archivo `.env.example` que te dice exactamente cómo hacerlo: copiás ese archivo, lo renombrás a `.env`, y pegás tu key adentro.
- **Si no ponés la key, el sistema igual funciona** en "modo simulado". La lógica médica funciona igual porque no dependía de Gemini. La key solo mejora la redacción de los textos.

## Cómo probé que funciona

Armé 18 casos de prueba inventados (13 de gente con cáncer, 5 de gente sana) y corrí el sistema sobre todos. Resultados:
- Acertó en TODOS si había que mandar a hacer una imagen o no (18/18).
- Acertó el tipo de cáncer en los 13 positivos (13/13).
- La urgencia la acertó en 11 de 13.

**Ojo con algo honesto:** esos números son altos porque los casos de prueba los inventé yo con palabras parecidas a las de la base. Con pacientes reales daría bastante peor. Eso lo dejo escrito en la monografía a propósito, porque en estos trabajos valoran que reconozcas las limitaciones en vez de venderte como perfecto. NO hice trampa para que diera bien: al principio daba 3 errores y los arreglé mejorando el sistema de verdad (filtré palabras genéricas como "dolor" que confundían todo).

## Qué archivos son qué (para que no te pierdas)

- **`README.md`** → las instrucciones para correr todo. Es lo que va a leer el que te corrige.
- **`MONOGRAFIA.md`** → el texto largo y formal explicando el proyecto. Para entregar.
- **`RESUMEN_SIMPLE.md`** → esto que estás leyendo.
- **`GUION_LOOM.md`** → el libreto para tu video, minuto a minuto.
- **`oncobridge/`** → acá está TODO el código, ordenado por carpetas.
- **`data/`** → la base de conocimiento y los casos de prueba.
- **`scripts/`** → los comandos para correr cada parte.

## Qué te falta hacer a vos

1. Poner tu API key de Gemini en el `.env` (opcional, funciona sin eso igual).
2. Subir todo a un repo de GitHub tuyo.
3. Grabar el video de Loom siguiendo el `GUION_LOOM.md`.

Nada más. El código, el dataset, las métricas y los textos ya están todos hechos.
