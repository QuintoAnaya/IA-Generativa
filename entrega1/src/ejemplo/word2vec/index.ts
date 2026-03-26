import w2v from 'word2vec';
import * as os from 'os';
import * as path from 'path';
import * as fs from 'fs';
import { fileURLToPath } from 'url';

const corpusPath = fileURLToPath(new URL('../corpus.txt', import.meta.url));
const modelPath = fileURLToPath(new URL('./vectors.txt', import.meta.url));

/**
 * Trains a Word2Vec model from the corpus.txt and saves it to vectors.txt
 */
export async function train() {
    return new Promise<void>((resolve, reject) => {
        w2v.word2vec(corpusPath, modelPath, {
            cbow: 1, // Use Continuous Bag of Words (1 = CBOW, 0 = Skip-Gram)
            size: 5, // Vector dimension size 
            window: 2, // Max skip length between words
            hs: 0, // Use Hierarchical Softmax
            sample: 1e-3, // Threshold for occurrence of words
            threads: 1, // Number of threads
            iter: 50, // Number of training iterations
            minCount: 1, // Minimum word count (important for tiny datasets)
            binary: 0 // Output text vectors instead of binary
        }, (error) => {
            if (error) {
                console.error("Training failed:", error);
                reject(error);
                return;
            }
            console.log(`Model trained and dynamically saved to ${modelPath}\n`);
            resolve();
        });
    });
}

// Softmax Helper Function
export function softmax(scores: number[]): number[] {
    const max = Math.max(...scores); // helps numerical stability
    const exps = scores.map(s => Math.exp(s - max));
    const sumOfExps = exps.reduce((a, b) => a + b, 0);
    return exps.map(e => e / sumOfExps);
}

/**
 * Loads the trained vectors.txt model and evaluates nearest neighbors for "cat" and "dog"
 */
export async function evaluate() {
    return new Promise<void>((resolve, reject) => {
        w2v.loadModel(modelPath, (error, model) => {
            if (error) {
                console.error("Error loading model:", error);
                reject(error);
                return;
            }

            const vocab = model.getVectors().map(v => v.word);
            console.log("Vocabulary:", vocab.join(', '));
            console.log("Vocabulary Size:", vocab.length);

            console.log("\n--- Vector representation of 'cat' ---");
            console.log(model.getVector('cat'));

            console.log("\n--- Nearest Neighbors to 'cat' ---");
            const catVec = model.getVector('cat');
            if (catVec) {
                const nearestCat = model.getNearestWords(catVec, vocab.length) as { word: string, dist: number }[];
                const probabilities = softmax(nearestCat.map(n => n.dist));

                nearestCat.forEach((n, i) => {
                    console.log(`${n.word}: Similarity ${n.dist.toFixed(4)} | Probability ${(probabilities[i] * 100).toFixed(2)}%`);
                });
            }

            console.log("\n--- Nearest Neighbors to 'dog' ---");
            const dogVec = model.getVector('dog');
            if (dogVec) {
                const nearestDog = model.getNearestWords(dogVec, vocab.length) as { word: string, dist: number }[];
                const probabilities = softmax(nearestDog.map(n => n.dist));

                nearestDog.forEach((n, i) => {
                    console.log(`${n.word}: Similarity ${n.dist.toFixed(4)} | Probability ${(probabilities[i] * 100).toFixed(2)}%`);
                });
            }

            resolve();
        });
    });
}

/**
 * Loads the trained vectors.txt model and infers missing outer bounds for CBOW inputs.
 */
export async function evaluateCbow() {
    return new Promise<void>((resolve, reject) => {
        w2v.loadModel(modelPath, (error, model) => {
            if (error) {
                console.error("Error loading model:", error);
                reject(error);
                return;
            }

            const vocab = model.getVectors().map(v => v.word);

            console.log("\n--- Inferring context around 'sat on' ---");
            /*
            Here's what mostSimilar does step by step:

                    Splits the input string into individual tokens (e.g. 'sat on' → ['sat', 'on'])
                    Looks up the vector for each token in the model
                    Averages the vectors of all valid tokens (words found in the vocabulary) into a single combined vector
                    Finds nearest neighbors to that averaged vector across the whole vocabulary, returning words sorted by cosine similarity
                    So model.mostSimilar('cat mat', vocab.length) is essentially asking: "what word lives closest to the midpoint between 'cat' and 'mat' in vector space?"

                    This is why the comment at the bottom of 

                    evaluateMiddleWord()
                    notes that order doesn't matter — 'cat mat' and 'mat cat' produce the exact same averaged vector, and therefore the exact same results.
            */

            const satOn = model.mostSimilar('sat on', vocab.length) as { word: string, dist: number }[];
            if (satOn && satOn.length > 0) {
                const probabilities = softmax(satOn.map(n => n.dist));
                satOn.forEach((n, i) => {
                    console.log(`${n.word}: Similarity ${n.dist.toFixed(4)} | Probability ${(probabilities[i] * 100).toFixed(2)}%`);
                });
            }

            console.log("\n--- Inferring context around 'ran to' ---");
            const ranTo = model.mostSimilar('ran to', vocab.length) as { word: string, dist: number }[];
            if (ranTo && ranTo.length > 0) {
                const probabilities = softmax(ranTo.map(n => n.dist));
                ranTo.forEach((n, i) => {
                    console.log(`${n.word}: Similarity ${n.dist.toFixed(4)} | Probability ${(probabilities[i] * 100).toFixed(2)}%`);
                });
            }

            resolve();
        });
    });
}



export async function main() {
    try {
        await train();
        await evaluate();
    } catch (error) {
        console.error("Execution failed:", error);
        process.exit(1);
    }
}

// Automatically run main if this file is executed directly 
if (process.argv[1] === fileURLToPath(import.meta.url)) {
    main();
}
