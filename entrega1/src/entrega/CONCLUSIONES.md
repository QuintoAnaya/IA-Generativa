# Conclusiones - Práctica LLMs para Biomedicina

**Nombre:** Emerio Quinto Tenreyro Anaya y Fausto Paredes
**Fecha:** 27/03/2026

---

## Ejercicio 1: Primera Llamada

### 1. Diferencia entre respuesta sin y con system instruction

Como es de esperarse, la diferencia esta justamente en que con el system prompt el modelo devuelve la respuesta como se le indica: Con un lenguaje menos tecnico y con una forma mas "personal".

### 2. ¿Pudiste modificar los parámetros internos del modelo? ¿Qué sí controlaste?

No, lo que modificamos no fueron los parametros internos sino los parametros externos como el prompt.

### 3. ¿Qué pasaría si cambiaras el rol en el system instruction?

Si cambio el rol en el system instruction esto obviamente se veria reflejado en la respuesta del modelo, ya que este comenzaria a "actuar" como le indique.

### 4. ¿Qué system instruction sería útil para tu campo de estudio?

En mi caso, yo elegi que el modelo actue como un farmaco. Seria util que la instruccion dada fuera que el modelo indique todo lo que puede ser contraproducente al tomar alguna medicacion para que el paciente tenga pleno conocimiento.
---

## Ejercicio 2: Hiperparámetros

### 1. ¿Qué temperature usarías para un informe médico? ¿Y para brainstorming?

Para un informe medico no buscaria que el modelo sea creativo, sino que este me de la respuesta mas precisa o la que mejor se adecue, por lo que usaria un temp=0. En cambio, en un brainstorming justamente lo que mas quiero es creativiad, es decir, un temp alto (1.5-2).

### 2. ¿Qué pasó con maxOutputTokens=50? ¿Fue útil?

No, el mensaje fue demasiado corto para que se pueda entender algo o que proporcione alguna info.

### 3. Diferencia entre topP bajo y alto

Entiendo por lo que dice en las anotaciones que un topP bajo es mas restrictivo y uno alto es mas creativo pero en las respuestas del modelo la verdad es que no me di cuenta de una diferencia muyu notoria.

### 4. ¿Las respuestas con temperature=0 fueron idénticas? Implicancias para reproducibilidad

Las respuestas no fueron identicas en su manera pero si en contenido, por lo que creo que mientras no van a estar "escritas" en la misma manera la reproducibilidad no esta afectada.

### 5. Hiperparámetros ideales para un chatbot médico. Justificá.

Como mencione en la pregunta sobre la temepratura, quiero que un chatbot medico sea lo menos creativo posible, con una temp y topP bajos. Al mismo tiempo, tal vez se deberia limitar la cantidad de tokens para que no se extienda demasiado en sus respuestas.

---

## Ejercicio 3: Prompt Engineering

### 1. Ranking de técnicas (peor a mejor) con justificación

Claramente como en los ejercicios anteriores el uso de una tecnica sobre otra depende mucho de que es lo que se esta buscando, pero si hablamos puramente de este ejercicio, en mi opinion la mejor fue la few-shot (fue corta y directa y respeto el formato que se le indico), seguida por el zero-shot (fue corta y directa tambien) y por ultimo el chain-of-thought (fue la mas logica pero en este caso no servia mas que las otras dos, ademas de ser por lejos la mas larga).

### 2. ¿La respuesta JSON fue clínicamente correcta? Ventajas del output estructurado

En este caso, como mencione en la pregunta anterior, el hecho de tener la respuesta estructurad hace mucho mas facil la visualizacion de la informacion y su busqueda.

### 3. ¿El chain-of-thought cambió el diagnóstico o solo el razonamiento?

El diagnostico fue el mismo en todos los casos, lo que hizo el chain-of-thought fue mostrar el razonamiento paso a paso de como llego a esa conclusion y proveer info adicional que las dos maneras anteriores no habian hecho.

### 4. ¿Encontraste información incorrecta presentada con confianza? ¿Cómo mitigarlo?

La verdad que no se si alguna parte de la informacion preentada es incorrecta o como mitigar esto.

### 5. Tu diseño ideal de asistente diagnóstico

Probablemente utilizaria el chain-of-thought para que el modelo me muestre el razonamiento paso a paso de como llego a esa conclusion, ya que me daria algo de miedo que se encaje mucho en los ejemplos que le pase o que en el caso de zero-shot no me de la informacion suficiente. 

---

## Reflexión Final

### ¿Qué aprendiste que no esperabas?

Basicamente en que consisten los parametros y tecnicas presentadas y como estas afectan la respuesta del modelo.

### ¿Qué riesgos ves en el uso de LLMs en medicina?

El mas obvio y principal son las alucinaciones o la falta de informacion provista. Aunque tambien veo un problema si estos se usan sin un profesional que los revise, ya que me encuentro conflictuado con que las decisiones finales de un paciente dependan de una IA.

### ¿Qué oportunidades ves para tu área de especialización?

Montones, mientras esto se utilice como la herramienta que es literalmente no hay un aforo en la cantidad de forma y areas en las que se puede aplicar.