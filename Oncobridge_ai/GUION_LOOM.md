# Guion para el video de Loom — OncoBridge AI

**Duración objetivo: 15–20 minutos.** Grabá compartiendo pantalla. Abajo tenés qué decir y qué mostrar en cada tramo. No leas palabra por palabra, usalo de guía. Los tiempos son aproximados.

Antes de grabar: tené abierto el repo en el editor y una terminal lista en la carpeta del proyecto. Corré una vez `python scripts/run_evaluacion.py` para tener el output fresco.

---

## Minuto 0–2 | Presentación y el problema

Qué decir:

"Hola, soy Beto. Este es mi trabajo final de IA Generativa para Biomedicina. El sistema se llama OncoBridge AI y es un sistema de apoyo a la decisión clínica para diagnóstico oncológico.

El problema que ataca es este: los hospitales tienen muchísimo conocimiento oncológico acumulado —patrones de diagnóstico, biomarcadores, guías de imagen— pero ese conocimiento no llega al momento en que se decide. El oncólogo tiene pocos minutos con el paciente y no puede revisar una base gigante; y el radiólogo muchas veces recibe el estudio sin el contexto clínico que motivó la derivación. OncoBridge busca cerrar esa brecha."

Mostrá: el README abierto, arriba de todo.

---

## Minuto 2–4 | Por qué esto tiene valor (lo aprendido)

Qué decir:

"Lo que más me interesó del enfoque es cómo usar un modelo generativo sin caer en su principal riesgo, que son las alucinaciones. En medicina, que el modelo invente algo que suena bien pero es falso es inaceptable.

La decisión de diseño central que tomé fue separar dos cosas: la lógica clínica por un lado y la redacción por el otro. La lógica clínica —qué hipótesis, si requiere imagen, qué urgencia— sale de una búsqueda sobre una base de conocimiento curada, que es determinista y auditable. Al modelo Gemini sólo le pido que redacte los textos en lenguaje natural. Así, si el modelo se equivoca, no afecta la decisión médica."

Mostrá: el diagrama de arquitectura del README (el ASCII con las dos estaciones).

---

## Minuto 4–9 | Demo funcional (la parte más importante)

Qué decir mientras mostrás:

"Vamos a verlo funcionar. Primero un caso positivo: un paciente fumador con tos con sangre y pérdida de peso."

Corré en la terminal:
```bash
python scripts/run_pipeline.py
```

Explicá señalando el output:
- "Miren: el Componente 1, el del oncólogo, recuperó las hipótesis. La primera es cáncer de pulmón, y fíjense que cada hipótesis tiene un `kb_id`, que es el identificador de la entrada de la base de donde salió. Eso es la trazabilidad."
- "Decidió que requiere imagen, urgencia alta, y sugirió una tomografía de tórax."
- "Y después el Componente 2, el del radiólogo, agarra ese contexto, da la guía de lectura —qué buscar y dónde— y evalúa la concordancia de los hallazgos. Acá dice concordancia alta."

Ahora el caso negativo:
```bash
python scripts/run_pipeline.py --ejemplo neg
```

"Este es una persona con cefalea por estrés, sin banderas rojas. El sistema correctamente decide que NO requiere imagen y frena en el Componente 1. No manda a nadie a hacerse una tomografía al pedo. Esto es clave: un buen sistema también tiene que saber cuándo NO actuar."

Mostrá también, opcional, el modo simulado:
"Un detalle: arriba dice 'Modo LLM: SIMULADO'. El sistema funciona aunque no tenga la API key de Gemini configurada, porque la lógica médica no depende del modelo. La key sólo mejora la redacción."

---

## Minuto 9–12 | Dataset y resultados

Qué decir:

"Para evaluarlo armé un dataset de 18 casos sintéticos: 13 positivos de distintos tipos de cáncer y 5 negativos, cuadros benignos. Puse casos negativos a propósito, para medir si el sistema evita las derivaciones innecesarias, no sólo si detecta las necesarias."

Corré:
```bash
python scripts/run_evaluacion.py
```

Explicá el output:
- "En la decisión de derivar a imagen: precisión, recall y F1 en 1.0. La matriz de confusión da 13 verdaderos positivos, 5 verdaderos negativos, cero errores."
- "Diagnóstico principal: acertó los 13 de 13."
- "Urgencia: 11 de 13."

Y ahora lo importante, sé honesto:

"Ahora, estos números son altos y hay que leerlos con cuidado. El dataset es sintético y usa un vocabulario parecido al de la base, así que le facilita la tarea. Con datos reales, con lenguaje libre y ruidoso, daría bastante peor. El valor está en el diseño de la evaluación, no en tomar estos números como desempeño clínico real. Y los dos errores de urgencia los dejé a propósito, sin forzar el sistema para que diera perfecto, porque me parece más honesto mostrar la limitación."

Contá también la anécdota del debugging, suma:

"De hecho, al principio el sistema daba 3 falsos positivos: mandaba a hacer imágenes a pacientes sanos. Lo debuggeé y era porque palabras genéricas como 'dolor' o 'síntomas' matcheaban con todo. Lo arreglé filtrando esas palabras del buscador. No hardcodeé respuestas para que diera bien: mejoré el sistema de verdad."

---

## Minuto 12–15 | Overview de la arquitectura del código

Qué decir mientras navegás las carpetas:

"Rápidamente cómo está organizado el código:
- En `oncobridge/knowledge` está la base de conocimiento y el buscador.
- En `oncobridge/components` están los dos componentes, el del oncólogo y el del radiólogo.
- En `oncobridge/utils` está el contrato de datos y el cliente de Gemini, que es el único lugar donde se maneja la API key.
- `pipeline.py` es el orquestador que encadena todo.
- En `data` está la base de conocimiento con 15 tipos de cáncer y el dataset de evaluación.
- En `scripts` están los comandos para correr cada parte."

Mostrá: abrí `componente1_oncologo.py` y señalá el comentario que explica que la lógica sale del retrieval, no del LLM.

---

## Minuto 15–18 | Aprendizajes y experiencia de usuario

Qué decir:

"Lo que me llevo de este trabajo: primero, que en IA médica la explicabilidad vale tanto como el rendimiento. Un sistema que acierta pero no podés auditar no sirve en este dominio. Segundo, que conviene usar el modelo generativo para lo que es bueno —redactar— y no para lo que es riesgoso —decidir. Tercero, que evaluar bien, con casos negativos y siendo honesto con las limitaciones, es parte del trabajo, no un trámite.

En cuanto a la experiencia de usuario, el sistema está pensado para integrarse en el flujo real: el oncólogo carga el caso como parte de la consulta y el resumen le llega al radiólogo junto con el pedido del estudio. No agrega pasos, ordena los que ya existen."

---

## Minuto 18–20 | Puesta en producción y privacidad

Qué decir:

"Para llevar esto a producción de verdad haría falta bastante más. En cuanto a privacidad, todo el proyecto usa datos sintéticos; un sistema real tendría que anonimizar los datos y cumplir los marcos vigentes: HIPAA en Estados Unidos, GDPR en Europa, y acá en Argentina la Ley 26.529 de derechos del paciente y la de protección de datos personales.

En cuanto a despliegue, el sistema hoy corre local; el siguiente paso sería exponerlo como un servicio con autenticación, registro de auditoría de cada consulta, y validación clínica con datos reales antes de cualquier uso. Y siempre bajo el mismo principio: es una herramienta de apoyo, la decisión final es del médico.

Eso es OncoBridge AI. Gracias."

---

## Checklist antes de subir el video

- [ ] Se ve la demo del caso positivo corriendo.
- [ ] Se ve la demo del caso negativo frenando.
- [ ] Se ven las métricas de la evaluación.
- [ ] Explicaste la separación lógica-clínica / redacción.
- [ ] Fuiste honesto con las limitaciones.
- [ ] Mencionaste privacidad (HIPAA/GDPR/Ley 26.529) y puesta en producción.
- [ ] Duración entre 15 y 20 minutos.
