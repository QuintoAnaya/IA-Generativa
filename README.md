# Inteligencia Artificial Generativa Para Datos Biomédicos

Repositorio de la materia **IA Generativa para Datos Biomédicos** — Universidad Austral.

---

## 🔄 Cómo traer cambios del template original

Este repositorio fue creado a partir de un **template**. Para incorporar actualizaciones que el docente publique en el template original, seguí estos pasos:

**1. Solo la primera vez — agregar el template como remoto `upstream`:**
```bash
git remote add upstream https://github.com/mszsorondo/ia-biomed.git
```

**2. Traer los cambios del template e incorporarlos a tu rama:**
```bash
git fetch upstream
git merge upstream/main --allow-unrelated-histories
```

**3. Si hay nuevas dependencias, reinstalá:**
```bash
cd entrega1 && npm install
```

> **Tip:** Repetí los pasos 2 y 3 cada vez que el docente avise que subió cambios al template.

---

## 📁 Estructura del Repositorio

```
ia-biomed/
├── clase0/          # Guía de configuración del entorno de trabajo
└── entrega1/        # Clase 1: Fundamentos de AI Generativa
```

---

## 🗂️ Contenido por Clase

### Clase 0 — Configuración del Entorno

Guía para configurar el entorno de trabajo básico necesario para cursar la materia.

- 📄 [setup.md](./clase0/setup.md) — Herramientas, GitHub, Antigravity, Python y flujo de trabajo.

---

### Entrega 1 — Fundamentos de AI Generativa

Ejercicios prácticos divididos en dos secciones: conceptos clásicos de IA y uso de LLMs modernos via API.

> 📖 Ver el [README completo de Entrega 1](./entrega1/README.md) para instrucciones detalladas.

#### 💡 Sección 1: Ejemplos Conceptuales (`src/ejemplo`)

Ejemplos locales que **no requieren clave de API**:

| Módulo | Descripción | Comando |
|--------|-------------|---------|
| `word2vec` | Embeddings y similitud del coseno entre palabras | `npm run start` |
| `neural-network` | Red neuronal feed-forward para predicción de próxima palabra con One-Hot Encoding | `npm run start:nn` |

#### 📝 Sección 2: Entregable — IA Generativa y APIs (`src/entrega`)

Integración con la **API de Google Gemini** (requiere clave de API):

| Ejercicio | Archivo | Descripción | Comando |
|-----------|---------|-------------|---------|
| Ejercicio 1 | `01-primera-llamada.ts` | Conexión básica y autenticación con Gemini | `npm run start:llm:01` |
| Ejercicio 2 | `02-hiperparametros.ts` | Exploración de `temperature`, `topP`, `topK`, `maxOutputTokens` | `npm run start:llm:02` |
| Ejercicio 3 | `03-prompt-engineering.ts` | System Prompts, Few-Shot Prompting y formato JSON | `npm run start:llm:03` |

#### 🚀 Cómo correr Entrega 1

```bash
cd entrega1
npm install
# Configurar API Key en .env (copiar desde .env.example)
npm run start:llm:01
```

> **Requisito:** Node.js v18+ y una clave de API gratuita de [Google AI Studio](https://aistudio.google.com/app/apikey).
