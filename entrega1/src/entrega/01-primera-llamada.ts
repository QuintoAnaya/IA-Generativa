/**
 * =============================================================================
 * EJERCICIO 1: Tu Primera Llamada a un LLM (~45 min)
 * =============================================================================
 *
 * OBJETIVO:
 * Entender qué es un "parámetro" en el contexto de un LLM y cómo interactuar
 * con un modelo generativo a través de una API.
 *
 * CONCEPTOS CLAVE:
 * - Parámetros del modelo: Son los pesos internos aprendidos durante el
 *   entrenamiento (ej: Gemini 1.5 Flash tiene miles de millones de parámetros).
 *   Vos NO los modificás; son lo que hace que el modelo "sepa" cosas.
 * - Parámetros de la API: Son los valores que vos pasás al hacer la llamada
 *   (el prompt, el modelo elegido, etc.)
 *
 * INSTRUCCIONES:
 * 1. Completá las secciones marcadas con "TODO"
 * 2. Ejecutá con: npm run start:llm:01
 * 3. Observá las respuestas y respondé las preguntas al final
 * =============================================================================
 */

import { GoogleGenerativeAI } from "@google/generative-ai";
import * as dotenv from "dotenv";
dotenv.config();

// ---------------------------------------------------------------------------
// CONFIGURACIÓN
// ---------------------------------------------------------------------------
// TODO 1: Configurá tu clave de Google AI Studio en el archivo .env
//         (ver README.md para instrucciones de cómo obtenerla)
const API_KEY = process.env.GEMINI_API_KEY || "";

const genAI = new GoogleGenerativeAI(API_KEY);

// ---------------------------------------------------------------------------
// PARTE A: Llamada básica - Pregunta simple
// ---------------------------------------------------------------------------
async function parteA() {
  console.log("=== PARTE A: Llamada Básica ===\n");

  // Usamos el modelo Gemini 1.5 Flash (gratuito, rápido)
  const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" });

  // Un prompt simple
  const prompt = "¿Qué es la hemoglobina y cuál es su función principal?";

  console.log(`Prompt: "${prompt}"\n`);
  console.log("Enviando al modelo...\n");

  const result = await model.generateContent(prompt);
  const response = result.response.text();

  console.log("Respuesta del modelo:");
  console.log("-".repeat(60));
  console.log(response);
  console.log("-".repeat(60));
  console.log();
}

// ---------------------------------------------------------------------------
// PARTE B: Usando un System Prompt (instrucción de sistema)
// ---------------------------------------------------------------------------
async function parteB() {
  console.log("\n=== PARTE B: System Prompt ===\n");

  // El "system instruction" le da contexto/rol al modelo ANTES del prompt
  const model = genAI.getGenerativeModel({
    model: "gemini-2.5-flash",
    systemInstruction:
      "Sos un médico clínico explicando resultados de laboratorio a un paciente. " +
      "Usá lenguaje simple, evitá jerga técnica innecesaria. " +
      "Sé empático y claro.",
  });

  const prompt =
    "Mi análisis de sangre muestra hemoglobina en 10.2 g/dL. ¿Qué significa?";

  console.log(`System Instruction: (médico clínico, lenguaje simple)`);
  console.log(`Prompt: "${prompt}"\n`);

  const result = await model.generateContent(prompt);
  console.log("Respuesta:");
  console.log("-".repeat(60));
  console.log(result.response.text());
  console.log("-".repeat(60));
}

// ---------------------------------------------------------------------------
// PARTE C: TODO - Escribí tu propio prompt biomédico
// ---------------------------------------------------------------------------
async function parteC() {
  console.log("\n=== PARTE C: Tu Propio Prompt ===\n");

  // TODO 2: Creá un model con un systemInstruction que defina un rol biomédico.
  //         Ejemplos: patólogo, radiólogo, bioinformático, farmacólogo...
  const model = genAI.getGenerativeModel({
    model: "gemini-2.5-flash",
    systemInstruction: "Sos un farmacologo experto. Explica los efectos secundarios y las contraindicaciones de los medicamentos sobre los que te consultan tus pacientes."
  });

  // TODO 3: Escribí un prompt relacionado a biomedicina.
  //         Puede ser sobre un diagnóstico, un resultado de laboratorio,
  //         una interacción farmacológica, interpretación de imágenes, etc.
  const prompt = "Mi paciente toma 40 mg de deltisona y 15 mg de metrotexate diarios, puede ralizar deporte sin ninguna preocupacion? Puede tomar bebidas alcoholicas sin problema?"; // <-- Tu prompt aquí

  if (!prompt) {
    console.log("⚠️  Completá el TODO 2 y 3 antes de correr esta parte.\n");
    return;
  }

  console.log(`Prompt: "${prompt}"\n`);

  const result = await model.generateContent(prompt);
  console.log("Respuesta:");
  console.log("-".repeat(60));
  console.log(result.response.text());
  console.log("-".repeat(60));
}

// ---------------------------------------------------------------------------
// EJECUTAR TODO
// ---------------------------------------------------------------------------
async function main() {
  try {
    await parteA();
    await parteB();
    await parteC();

    console.log("\n" + "=".repeat(60));
    console.log("PREGUNTAS PARA REFLEXIONAR (anotá en CONCLUSIONES.md):");
    console.log("=".repeat(60));
    console.log(`
1. ¿Qué diferencia notaste entre la respuesta de Parte A (sin system
   instruction) y Parte B (con system instruction)?

2. El modelo Gemini 2.5 Flash tiene miles de millones de parámetros internos.
   ¿Pudiste modificar alguno de esos parámetros? ¿Qué SÍ pudiste controlar?

3. ¿Qué pasaría si en el system instruction le dijeras al modelo que es
   un veterinario en vez de un médico? ¿Cambiaría la respuesta? ¿Por qué?

4. Pensá en tu campo de estudio: ¿qué tipo de system instruction sería
   útil para tu trabajo diario?
`);
  } catch (error: any) {
    if (error.message?.includes("API_KEY")) {
      console.error(
        "\n❌ Error de API Key. ¿Configuraste tu clave correctamente?", error
      );
      console.error("   Revisá el README.md para instrucciones.\n");
    } else {
      console.error("\n❌ Error:", error.message);
    }
  }
}

main();
