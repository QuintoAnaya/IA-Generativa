/**
 * =============================================================================
 * EJERCICIO 2: Hiperparámetros - Controlando la Generación (~60 min)
 * =============================================================================
 *
 * OBJETIVO:
 * Entender qué son los hiperparámetros de generación y cómo afectan la salida
 * del modelo. Experimentar con temperature, topP, topK y maxOutputTokens.
 *
 * CONCEPTOS CLAVE:
 *
 * ┌─────────────────┬──────────────────────────────────────────────────────────┐
 * │ Hiperparámetro  │ ¿Qué controla?                                         │
 * ├─────────────────┼──────────────────────────────────────────────────────────┤
 * │ temperature     │ Creatividad/aleatoriedad (0 = determinista, 2 = caótico)│
 * │ topP            │ Nucleus sampling: considera tokens cuya probabilidad    │
 * │                 │ acumulada no supere este valor (0.0 a 1.0)              │
 * │ topK            │ Solo considera los K tokens más probables               │
 * │ maxOutputTokens │ Longitud máxima de la respuesta (en tokens, ~4 chars)   │
 * └─────────────────┴──────────────────────────────────────────────────────────┘
 *
 *
 * INSTRUCCIONES:
 * 1. Ejecutá el código tal cual está: npm run start:llm:02
 * 2. Observá cómo cambian las respuestas con distintos hiperparámetros
 * 3. Completá los TODOs
 * 4. Respondé las preguntas al final
 * =============================================================================
 */

import { GoogleGenerativeAI } from "@google/generative-ai";
import * as dotenv from "dotenv";
dotenv.config();

// TODO 1: Configurá tu clave de Google AI Studio en el archivo .env
const API_KEY = process.env.GEMINI_API_KEY || "";

const genAI = new GoogleGenerativeAI(API_KEY);

// ---------------------------------------------------------------------------
// UTILIDAD: Llamar al modelo con hiperparámetros específicos
// ---------------------------------------------------------------------------
async function generarConConfig(
  prompt: string,
  config: {
    temperature?: number;
    topP?: number;
    topK?: number;
    maxOutputTokens?: number;
  },
  label: string
) {
  const model = genAI.getGenerativeModel({
    model: "gemini-2.0-flash",
    generationConfig: config,
  });

  console.log(`\n--- ${label} ---`);
  console.log(
    `Config: temperature=${config.temperature ?? "default"}, ` +
    `topP=${config.topP ?? "default"}, ` +
    `topK=${config.topK ?? "default"}, ` +
    `maxOutputTokens=${config.maxOutputTokens ?? "default"}`
  );

  const result = await model.generateContent(prompt);
  const text = result.response.text();
  console.log(`\nRespuesta (${text.length} chars):`);
  console.log(text);
  console.log();
}

// ---------------------------------------------------------------------------
// PARTE A: Efecto de Temperature
// ---------------------------------------------------------------------------
async function parteA() {
  console.log("=".repeat(60));
  console.log("PARTE A: Efecto de Temperature");
  console.log("=".repeat(60));

  const prompt =
    "Generá un diagnóstico diferencial breve para un paciente de 45 años " +
    "con dolor torácico agudo, disnea y diaforesis. Listá 3 posibilidades.";

  console.log(`\nPrompt: "${prompt}"`);

  // Temperature BAJA: respuestas conservadoras y consistentes
  await generarConConfig(
    prompt,
    { temperature: 0.0 },
    "Temperature 0.0 (determinista)"
  );

  // Temperature MEDIA
  await generarConConfig(
    prompt,
    { temperature: 1.0 },
    "Temperature 1.0 (balanceada)"
  );

  // Temperature ALTA: respuestas más creativas/variables
  await generarConConfig(
    prompt,
    { temperature: 2.0 },
    "Temperature 2.0 (muy creativa)"
  );
}

// ---------------------------------------------------------------------------
// PARTE B: Efecto de maxOutputTokens
// ---------------------------------------------------------------------------
async function parteB() {
  console.log("\n" + "=".repeat(60));
  console.log("PARTE B: Efecto de maxOutputTokens");
  console.log("=".repeat(60));

  const prompt =
    "Explicá el mecanismo de acción de la metformina en diabetes tipo 2.";

  console.log(`\nPrompt: "${prompt}"`);

  // Respuesta MUY corta
  await generarConConfig(
    prompt,
    { maxOutputTokens: 50 },
    "Max 50 tokens (~200 chars)"
  );

  // Respuesta media
  await generarConConfig(
    prompt,
    { maxOutputTokens: 200 },
    "Max 200 tokens (~800 chars)"
  );

  // Respuesta larga
  await generarConConfig(
    prompt,
    { maxOutputTokens: 1000 },
    "Max 1000 tokens (~4000 chars)"
  );
}

// ---------------------------------------------------------------------------
// PARTE C: Efecto de topP y topK
// ---------------------------------------------------------------------------
async function parteC() {
  console.log("\n" + "=".repeat(60));
  console.log("PARTE C: Efecto de topP y topK");
  console.log("=".repeat(60));

  const prompt =
    "Describí brevemente los efectos secundarios más comunes de los " +
    "inhibidores de la ECA (enalapril, lisinopril).";

  console.log(`\nPrompt: "${prompt}"`);

  // topP bajo: solo los tokens más probables (muy conservador)
  await generarConConfig(
    prompt,
    { temperature: 1.0, topP: 0.1 },
    "topP=0.1 (muy restrictivo)"
  );

  // topP alto: considera más opciones
  await generarConConfig(
    prompt,
    { temperature: 1.0, topP: 0.95 },
    "topP=0.95 (amplio)"
  );

  // topK bajo
  await generarConConfig(
    prompt,
    { temperature: 1.0, topK: 3 },
    "topK=3 (solo top 3 tokens)"
  );

  // topK alto
  await generarConConfig(
    prompt,
    { temperature: 1.0, topK: 100 },
    "topK=100 (top 100 tokens)"
  );
}

// ---------------------------------------------------------------------------
// PARTE D: Tu experimento
// ---------------------------------------------------------------------------
async function parteD() {
  console.log("\n" + "=".repeat(60));
  console.log("PARTE D: Tu Propio Experimento");
  console.log("=".repeat(60));

  // ─────────────────────────────────────────────────────────────────────────
  // TODO 2: Elegí UNO de estos prompts (descomentalo) o escribí uno propio.
  // ─────────────────────────────────────────────────────────────────────────

  // Opción A:
  // const miPrompt = "Interpretá estos resultados de hemograma: WBC 12.5, RBC 3.8, Hb 11.2, Plt 450";

  // Opción B:
  // const miPrompt = "Explicá la fisiopatología del Alzheimer a nivel molecular";

  // Opción C:
  // const miPrompt = "¿Cuáles son las interacciones farmacológicas peligrosas con warfarina?";

  // Opción D (escribí el tuyo):
  // const miPrompt = "...";

  // ⚠️  Borrá esta línea cuando hayas descomentado una opción de arriba:
  const miPrompt = "";

  if (!miPrompt) {
    console.log("\n⚠️  Descomentá una de las opciones de arriba (A, B, C o D) para correr esta parte.\n");
    return;
  }

  // ─────────────────────────────────────────────────────────────────────────
  // TODO 3: Descomentá las 3 llamadas de abajo. Después, modificá los
  //         valores numéricos y observá cómo cambian las respuestas.
  //
  //         Preguntate:
  //           a) ¿Qué config es mejor para un informe médico formal?
  //           b) ¿Y para un brainstorming de hipótesis diagnósticas?
  //           c) ¿Y para una respuesta corta en una app de telemedicina?
  // ─────────────────────────────────────────────────────────────────────────

  // Configuración 1 – "Informe formal": conservadora, determinista, longitud media
  // await generarConConfig(miPrompt, { temperature: 0.0, maxOutputTokens: 200 }, "Config 1: Informe formal");

  // Configuración 2 – "Brainstorming": creativa, amplia, sin límite corto
  // await generarConConfig(miPrompt, { temperature: 1.5, topP: 0.9 }, "Config 2: Brainstorming");

  // Configuración 3 – "App de telemedicina": respuesta corta y precisa
  // await generarConConfig(miPrompt, { temperature: 0.3, maxOutputTokens: 80 }, "Config 3: App de telemedicina");
}

// ---------------------------------------------------------------------------
// PARTE E: Reproducibilidad (correlo 2 veces!)
// ---------------------------------------------------------------------------
async function parteE() {
  console.log("\n" + "=".repeat(60));
  console.log("PARTE E: Test de Reproducibilidad");
  console.log("=".repeat(60));
  console.log("\nMismo prompt, temperature=0. ¿Las respuestas son idénticas?\n");

  const prompt = "Nombrá los 4 tipos principales de tejido humano.";
  const model = genAI.getGenerativeModel({
    model: "gemini-2.0-flash",
    generationConfig: { temperature: 0.0 },
  });

  const respuestas: string[] = [];
  for (let i = 0; i < 3; i++) {
    const result = await model.generateContent(prompt);
    const text = result.response.text();
    respuestas.push(text);
    console.log(`Intento ${i + 1}: ${text.substring(0, 120)}...`);
  }

  const todasIguales = respuestas.every((r) => r === respuestas[0]);
  console.log(
    `\n¿Son todas idénticas? ${todasIguales ? "SÍ ✓" : "NO ✗ (¡interesante!)"}`
  );
}

// ---------------------------------------------------------------------------
// EJECUTAR
// ---------------------------------------------------------------------------
async function main() {
  try {
    await parteA();
    await parteB();
    await parteC();
    await parteD();
    await parteE();

    console.log("\n" + "=".repeat(60));
    console.log("PREGUNTAS PARA REFLEXIONAR (anotá en CONCLUSIONES.md):");
    console.log("=".repeat(60));
    console.log(`
1. ¿Qué temperature usarías para generar un informe médico que va a leer
   un profesional? ¿Y para brainstorming de hipótesis diagnósticas? Justificá.

2. ¿Qué pasó cuando limitaste maxOutputTokens a 50? ¿La respuesta fue útil?
   ¿Qué implica esto para aplicaciones con restricciones de espacio (ej: SMS)?

3. ¿Notaste diferencia entre topP=0.1 y topP=0.95? ¿Cuál producía texto
   más "seguro"? ¿Y cuál más "interesante"?

4. En la Parte E, ¿fueron las 3 respuestas idénticas con temperature=0?
   ¿Qué implicancias tiene esto para la reproducibilidad en investigación?

5. Si tuvieras que configurar un chatbot médico para pacientes, ¿qué
   hiperparámetros elegirías y por qué?
`);
  } catch (error: any) {
    if (error.message?.includes("API_KEY")) {
      console.error(
        "\n❌ Error de API Key. ¿Configuraste tu clave correctamente?"
      );
    } else {
      console.error("\n❌ Error:", error.message);
    }
  }
}

main();
