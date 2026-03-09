/**
 * =============================================================================
 * EJERCICIO 3: Prompt Engineering para Biomedicina (~60 min)
 * =============================================================================
 *
 * OBJETIVO:
 * Aprender técnicas de prompt engineering y evaluar cómo la estructura del
 * prompt afecta drásticamente la calidad de la respuesta, especialmente en
 * un contexto biomédico donde la precisión es crítica.
 *
 * TÉCNICAS QUE VAS A EXPLORAR:
 *
 * 1. Zero-shot:   "Respondé esto" (sin ejemplos)
 * 2. Few-shot:    "Acá tenés ejemplos, ahora respondé esto"
 * 3. Chain-of-thought: "Pensá paso a paso"
 * 4. Role + constraints: "Sos un X, respondé con formato Y"
 *
 * =============================================================================
 */

import { GoogleGenerativeAI } from "@google/generative-ai";
import * as dotenv from "dotenv";
dotenv.config();

// TODO 1: Configurá tu clave de Google AI Studio en el archivo .env
const API_KEY = process.env.GEMINI_API_KEY || "";

const genAI = new GoogleGenerativeAI(API_KEY);

// ---------------------------------------------------------------------------
// UTILIDAD
// ---------------------------------------------------------------------------
async function llamar(
  prompt: string,
  label: string,
  systemInstruction?: string
) {
  const model = genAI.getGenerativeModel({
    model: "gemini-2.0-flash",
    systemInstruction,
    generationConfig: { temperature: 0.3 }, // Baja para comparar mejor
  });

  console.log(`\n--- ${label} ---`);
  if (systemInstruction) {
    console.log(`System: "${systemInstruction.substring(0, 80)}..."`);
  }
  console.log(`Prompt: "${prompt.substring(0, 120)}..."\n`);

  const result = await model.generateContent(prompt);
  const text = result.response.text();
  console.log(text);
  console.log("-".repeat(60));
  return text;
}

// ---------------------------------------------------------------------------
// CASO CLÍNICO para todos los ejercicios
// ---------------------------------------------------------------------------
const CASO_CLINICO = `
Paciente: Mujer, 58 años
Motivo de consulta: Fatiga progresiva, palidez, disnea de esfuerzo (3 semanas)
Antecedentes: Hipotiroidismo, gastritis crónica, vegetariana estricta hace 2 años
Laboratorio:
  - Hemoglobina: 8.9 g/dL (ref: 12-16)
  - VCM: 112 fL (ref: 80-100)
  - Ferritina: 85 ng/mL (ref: 12-150)
  - Vitamina B12: 95 pg/mL (ref: 200-900)
  - Ácido fólico: 4.2 ng/mL (ref: 2.7-17)
  - TSH: 3.2 mUI/L (ref: 0.4-4.0)
  - LDH: 580 U/L (ref: 140-280)
  - Reticulocitos: 1.2% (ref: 0.5-2.5)
`.trim();

// ---------------------------------------------------------------------------
// PARTE A: Zero-shot (sin contexto ni ejemplos)
// ---------------------------------------------------------------------------
async function parteA() {
  console.log("=".repeat(60));
  console.log("PARTE A: Zero-shot Prompting");
  console.log("=".repeat(60));

  // Prompt mínimo: solo el caso y una pregunta
  const prompt = `${CASO_CLINICO}\n\n¿Cuál es el diagnóstico más probable?`;

  await llamar(prompt, "Zero-shot: pregunta directa");
}

// ---------------------------------------------------------------------------
// PARTE B: Few-shot (con ejemplos)
// ---------------------------------------------------------------------------
async function parteB() {
  console.log("\n" + "=".repeat(60));
  console.log("PARTE B: Few-shot Prompting");
  console.log("=".repeat(60));

  const prompt = `Sos un sistema de apoyo diagnóstico. Dado un caso clínico,
respondé con el formato exacto que se muestra en los ejemplos.

EJEMPLO 1:
Caso: Hombre 65 años, poliuria, polidipsia, pérdida de peso, glucemia 280 mg/dL
Diagnóstico: Diabetes mellitus tipo 2
Evidencia clave: Glucemia elevada + síntomas cardinales (poliuria, polidipsia)
Confianza: ALTA
Siguiente paso: HbA1c, perfil lipídico, función renal

EJEMPLO 2:
Caso: Mujer 30 años, palpitaciones, temblor, pérdida de peso, TSH 0.01, T4L 4.8
Diagnóstico: Hipertiroidismo (probable enfermedad de Graves)
Evidencia clave: TSH suprimida + T4 libre elevada + síntomas hipermetabólicos
Confianza: ALTA
Siguiente paso: Anticuerpos anti-receptor de TSH, ecografía tiroidea

AHORA ANALIZÁ ESTE CASO:
${CASO_CLINICO}`;

  await llamar(prompt, "Few-shot: con ejemplos de formato");
}

// ---------------------------------------------------------------------------
// PARTE C: Chain-of-Thought (razonamiento paso a paso)
// ---------------------------------------------------------------------------
async function parteC() {
  console.log("\n" + "=".repeat(60));
  console.log("PARTE C: Chain-of-Thought Prompting");
  console.log("=".repeat(60));

  const prompt = `Analizá el siguiente caso clínico paso a paso.

INSTRUCCIONES - Seguí este proceso de razonamiento:
1. Primero, identificá los hallazgos ANORMALES del laboratorio
2. Luego, buscá patrones: ¿qué combinación de anormales apunta a qué?
3. Considerá los antecedentes del paciente y cómo se relacionan
4. Proponé un diagnóstico principal con justificación
5. Mencioná diagnósticos diferenciales y cómo descartarlos
6. Sugerí estudios confirmatorios

CASO:
${CASO_CLINICO}

Pensá paso a paso:`;

  await llamar(prompt, "Chain-of-Thought: razonamiento explícito");
}

// ---------------------------------------------------------------------------
// PARTE D: Role + Constraints (rol + restricciones estrictas)
// ---------------------------------------------------------------------------
async function parteD() {
  console.log("\n" + "=".repeat(60));
  console.log("PARTE D: Role + Constraints");
  console.log("=".repeat(60));

  const systemInstruction = `Sos un hematólogo con 20 años de experiencia en un hospital universitario.
REGLAS ESTRICTAS:
- Respondé SOLO en formato JSON válido
- No incluyas texto fuera del JSON
- Usá terminología médica precisa
- Indicá nivel de evidencia para cada afirmación`;

  const prompt = `Analizá este caso y respondé en JSON con esta estructura exacta:
{
  "diagnostico_principal": "...",
  "certeza": "alta|media|baja",
  "hallazgos_clave": ["...", "..."],
  "mecanismo_fisiopatologico": "...",
  "diagnosticos_diferenciales": [
    { "nombre": "...", "probabilidad": "...", "argumento_a_favor": "...", "argumento_en_contra": "..." }
  ],
  "estudios_confirmatorios": ["...", "..."],
  "tratamiento_inicial": "..."
}

CASO:
${CASO_CLINICO}`;

  await llamar(prompt, "Role + JSON constraints", systemInstruction);
}

// ---------------------------------------------------------------------------
// PARTE E: TODO - Compará y diseñá tu propio prompt
// ---------------------------------------------------------------------------
async function parteE() {
  console.log("\n" + "=".repeat(60));
  console.log("PARTE E: Tu Diseño de Prompt");
  console.log("=".repeat(60));

  // TODO 2: Diseñá un prompt que combine las técnicas vistas.
  //
  // El objetivo: crear el prompt más efectivo posible para analizar
  // el CASO_CLINICO de arriba (o podés crear tu propio caso).
  //
  // Considerá:
  //   - ¿Qué rol le das al modelo?
  //   - ¿Le das ejemplos (few-shot)?
  //   - ¿Le pedís que razone paso a paso (chain-of-thought)?
  //   - ¿Qué formato de salida querés?
  //   - ¿Qué restricciones imponés?
  //
  // BONUS: ¿Podés hacer que el modelo detecte si le falta información
  //        y la pida explícitamente en vez de inventarla?

  const miSystemInstruction = ""; // <-- TODO: Tu system instruction
  const miPrompt = ""; // <-- TODO: Tu prompt

  if (!miPrompt) {
    console.log("\n⚠️  Completá el TODO 2 para correr esta parte.\n");
    return;
  }

  await llamar(
    miPrompt,
    "Tu prompt personalizado",
    miSystemInstruction || undefined
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
1. Ordená las 4 técnicas (zero-shot, few-shot, chain-of-thought, role+constraints)
   de PEOR a MEJOR calidad diagnóstica. Justificá tu ranking.

2. ¿La respuesta en formato JSON (Parte D) fue clínicamente correcta?
   ¿Qué ventajas tiene un output estructurado para un sistema real?

3. ¿El chain-of-thought (Parte C) cambió el diagnóstico final, o solo
   cambió cómo llegó a él? ¿Importa el "cómo" en medicina? ¿Por qué?

4. PELIGRO: ¿Alguna respuesta contenía información incorrecta presentada
   con confianza? ¿Cómo se podría mitigar esto en una aplicación real?

5. Si tuvieras que construir un asistente de diagnóstico real,
   ¿qué combinación de técnicas usarías? Describí tu diseño ideal.
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
