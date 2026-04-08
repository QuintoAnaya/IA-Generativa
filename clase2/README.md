# AIG4B - Clase 2: Ejemplos Conceptuales Clásicos. 

Este directorio contiene los ejemplos interactivos para la segunda clase. El código está enfocado en conceptos fundamentales de Inteligencia Artificial Clásica.

---

## 🚀 Cómo correr los ejemplos

```bash
cd clase2
npm install

# Word2Vec — embeddings y similitud
npm run start

# Red Neuronal — predicción de próxima palabra
npm run start:nn
```

---

## 💡 Ejemplos Conceptuales (`src/ejemplo`)

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

## 🚀 Requisitos de Ejecución

1. Node.js v18+ y NPM instalados.
2. Ejecutá `npm install` en la raíz de la carpeta `clase2`.
3. Ejecutá los módulos desde tu terminal con los scripts NPM o usá **Run and Debug** en VS Code.
