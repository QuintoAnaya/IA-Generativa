import * as fs from 'fs';
import { createRequire } from 'module';

const require = createRequire(import.meta.url);
const synaptic = require('synaptic');

let vocab: string[] = [];
let VOCAB_SIZE = 0;
let myNetwork: any;

// Helper functions to convert between words and Normalized numerical vectors (0 to 1)
function wordToEmbedding(word: string): number[] {
    const vec = new Array(vocab.length).fill(0);
    const index = vocab.indexOf(word);
    if (index !== -1) {
        vec[index] = 1;
    }
    return vec;
}

function embeddingToWord(vec: number[] | undefined): { word: string, confidence: number }[] {
    if (!vec) return [];

    // Map probabilities to words
    const results = Array.from(vec).map((score, index) => ({
        word: vocab[index],
        confidence: score
    }));

    // Sort by highest probability
    return results.sort((a, b) => b.confidence - a.confidence);
}

/**
 * Step 1: Reads corpus.txt, tokenizes sentences, and builds the unique vocabulary dictionary
 */
export function loadCorpusAndVocab(): string[][] {
    // Load our corpus from the root directory
    const corpusPath = new URL('../corpus.txt', import.meta.url).pathname;
    const rawText = fs.readFileSync(corpusPath, 'utf-8');

    // Tokenize the sentences
    const lines = rawText.split(/\r?\n/).filter(line => line.length > 0);
    const allTokens: string[] = [];

    // Clean and extract all distinct tokens
    const sentences = lines.map(line => {
        const tokens = line.split(/\s+/)
            .map(t => t.toLowerCase().replace(/[^a-z0-9]/g, ''))
            .filter(t => t.length > 0);
        allTokens.push(...tokens);
        return tokens;
    });

    // Create a unique vocabulary dictionary 
    vocab = Array.from(new Set(allTokens));
    VOCAB_SIZE = vocab.length;
    console.log(`Vocabulary (${VOCAB_SIZE} words):`, vocab);

    return sentences;
}

/**
 * Step 2: Creates numerical training pairs (Given word N, predict word N+1)
 */
export function buildTrainingData(sentences: string[][]): { input: number[], output: number[] }[] {
    const trainingData: { input: number[], output: number[] }[] = [];

    sentences.forEach(sentence => {
        for (let i = 0; i < sentence.length - 1; i++) {
            const inputWord = sentence[i];
            const outputWord = sentence[i + 1];

            trainingData.push({
                input: wordToEmbedding(inputWord),
                output: wordToEmbedding(outputWord)
            });
        }
    });

    console.log(`\nGenerated ${trainingData.length} training pairs:`);
    console.log(JSON.stringify(trainingData, null, 2));
    return trainingData;
}

/**
 * Step 3: Configures a 1-Hidden-Layer Network and trains it on our data
 */
export async function train(trainingData: { input: number[], output: number[] }[]) {
    // Create a network with Input:10 -> Hidden:10 -> Output:10
    const { Layer, Network, Trainer } = synaptic;

    const inputLayer = new Layer(VOCAB_SIZE);
    const hiddenLayer = new Layer(10);
    const outputLayer = new Layer(VOCAB_SIZE);

    inputLayer.project(hiddenLayer);
    hiddenLayer.project(outputLayer);

    myNetwork = new Network({
        input: inputLayer,
        hidden: [hiddenLayer],
        output: outputLayer
    });

    console.log("\nTraining native Synaptic JS library network (this might take a few seconds)...");

    // Train the network
    const trainer = new Trainer(myNetwork);
    const stats = trainer.train(trainingData, {
        rate: 0.1,        // Learning rate: controls the step size at each gradient descent update (higher = faster but less stable)
        iterations: 5000, // Maximum number of training epochs to run before stopping
        error: 0.005,     // Target mean squared error threshold; training stops early if this is reached
        shuffle: true,    // Randomize the order of training samples each epoch to reduce overfitting
        log: 1000         // Print training progress to the console every N iterations
    });

    console.log(`\nTraining complete in ${stats.iterations} iterations with error ${stats.error.toFixed(4)}.`);
}

/**
 * Helper to dynamically execute the Neural Network and print the next predicted word
 */
function predictNext(word: string) {
    if (!vocab.includes(word)) {
        console.log(`\nCannot predict for '${word}': Word not in vocabulary.`);
        return;
    }

    const inputVec = wordToEmbedding(word);

    // Activate the network with the input vector to get output probabilities
    const outputVec = myNetwork.activate(inputVec) as number[];

    const predictions = embeddingToWord(outputVec);

    console.log(`\n--- Predicting next word after '${word}' ---`);
    predictions.slice(0, 3).forEach((pred, i) => { // show top 3
        console.log(`${i + 1}. ${pred.word} (${(pred.confidence * 100).toFixed(2)}%)`);
    });
}

/**
 * Step 4: Runs inferences against the trained network
 */
export async function evaluate() {
    // Predict test cases based on corpus:
    // "the cat sat on mat", "a dog ran to bed", "the dog sat on bed", "a cat ran to mat", "the cat ran to dog"

    predictNext('the'); // Expected path: cat/dog -> sat/ran
    predictNext('a');
    predictNext('dog');
    predictNext('ran');
    predictNext('on');
    predictNext('to');  // Should predict 'bed', 'mat', or 'dog'
}

/**
 * Main Execution Pipeline
 */
export async function main() {
    try {
        const sentences = loadCorpusAndVocab();
        const trainingData = buildTrainingData(sentences);
        await train(trainingData);
        await evaluate();
    } catch (error) {
        console.error("Execution failed:", error);
        process.exit(1);
    }
}

// Automatically run main if this file is executed directly 
if (process.argv[1] === new URL(import.meta.url).pathname) {
    main();
}
