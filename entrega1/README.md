# AIG4B - Clase 1: Fundamentos de AI Generativa. 

Este repositorio contiene los ejercicios prácticos y ejemplos interactivos para la primera clase. El código está dividido en conceptos fundamentales de Inteligencia Artificial Clásica y ejemplos de Modelos Generativos modernos (LLMs).

---

## 💡 Sección 1: Ejemplos Conceptuales (`src/ejemplo`)

Ejemplos didácticos de conceptos fundamentales de IA. No requieren ninguna clave de API — corren completamente de forma local usando la librería de embeddings `word2vec` y la red neuronal `synaptic`.

### `src/ejemplo/word2vec`
Exploramos los fundamentos matemáticos de los **Embeddings** (Vectores de Palabras) y cómo el lenguaje puede ser representado estadísticamente en el espacio.
- **Comando:** `npm run start`
- Entrena un modelo Word2Vec sobre el corpus local `corpus.txt`.
- Demuestra similitud del coseno para encontrar palabras relacionadas (ej: distancia vectorial entre `cat` y `dog`).
- Expone la pérdida de orden secuencial en modelos CBOW como limitación clave.

### `src/ejemplo/neural-network`
Construimos una Red Neuronal Feed-Forward para la predicción de la próxima palabra.
- **Comando:** `npm run start:nn`
- Transforma el vocabulario de 10 palabras en representaciones **One-Hot (Embeddings)**.
- Entrena una red de 1 Capa Oculta usando la librería JavaScript nativa `synaptic`.
- Devuelve una distribución probabilística de la próxima palabra más probable en la oración.

---

## 📝 Sección 2: Entregable — IA Generativa y APIs (`src/entrega`)

Ejercitaciones para integrar Modelos de Lenguaje Grande (LLMs) mediante la **API de Google Gemini**.

> **Requisito previo:** configurá tu clave de API en el archivo `.env` (ver sección de Requisitos más abajo).

### Ejercicio 1 — Conexión y Autenticación
- **Archivo:** `src/entrega/01-primera-llamada.ts`
- **Comando:** `npm run start:llm:01`
- **Objetivo:** Establecer la conexión básica con el SDK de `@google/generative-ai`.
- **Qué hace:** Configura tu clave de API, inicializa el modelo `gemini-2.5-flash`, y ejecuta un prompt sencillo para verificar que la autenticación funciona y el modelo responde correctamente.

### Ejercicio 2: Hiperparámetros de Generación
- **Archivo:** `src/entrega/02-hiperparametros.ts`
- **Comando:** `npm run start:llm:02`
- **Objetivo:** Comprender las configuraciones de manipulación y probabilidad de generación del modelo.
- **Qué hace:** Experimenta enviando prompts idénticos pero variando los parámetros clave de generación:
  - `temperature`: Modifica la creatividad o el determinismo del output.
  - `maxOutputTokens`: Limita o explaya el largo de la respuesta que el LLM tiene permitido generar.
  - `topP` y `topK`: Controlan estadísticamente el núcleo de muestreo de las alucinaciones.
- **Tu Tarea (Parte D):** Debes agregar tu própio prompt biomédico y configurar 3 sets de hiperparámetros simulando un informe clínico formal, un brainstorming creativo, y un resumen estricto.

### Ejercicio 3: Prompt Engineering Avanzado
- **Archivo:** `src/entrega/03-prompt-engineering.ts`
- **Comando:** `npm run start:llm:03`
- **Objetivo:** Explorar técnicas de refinamiento estructural de entrada.
- **Qué hace:** Ejerce las mejores prácticas de armado de contexto clínico utilizando System Prompts para controlar el tono de la I.A., el formato estricto de respuesta que queremos (por ej., JSON), y estrategias como Few-Shot Prompting.

---

## 🚀 Requisitos de Ejecución

1. Node.js v18+ y NPM instalados.
2. Ejecutá `npm install` en la raíz del proyecto.
3. **Configuración de API Key (solo para `src/entrega`):**
   - Obtené tu clave gratuita en [Google AI Studio](https://aistudio.google.com/app/apikey).
   - Copiá el archivo `.env.example` y renombralo a `.env`.
   - Pegá tu clave en `.env`: `GEMINI_API_KEY="tu-clave-aqui"`
4. Ejecutá los módulos desde tu terminal con los scripts NPM o usá **Run and Debug** en VS Code.
