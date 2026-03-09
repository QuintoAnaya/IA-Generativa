import w2v from 'word2vec';
import * as os from 'os';
import * as path from 'path';
import * as fs from 'fs';

const corpusPath = new URL('../../../corpus.txt', import.meta.url).pathname;
const modelPath = new URL('./vectors.txt', import.meta.url).pathname;

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

/**
 * Loads the trained vectors.txt model and calculates the average between two words
 * to predict the contextual middle word.
 */
export async function evaluateMiddleWord() {
    return new Promise<void>((resolve, reject) => {
        w2v.loadModel(modelPath, (error, model) => {
            if (error) {
                console.error("Error loading model:", error);
                reject(error);
                return;
            }

            const vocab = model.getVectors().map(v => v.word);

            // We want to find the middle between "cat" and "mat" 
            const word1 = "cat";
            const word2 = "mat";

            console.log(`\n--- Inferring middle word between '${word1} ${word2}' ---`);

            // mostSimilar averages all the valid words found in the string before looking up Neighbors!
            const middleWords = model.mostSimilar(`${word1} ${word2}`, vocab.length) as { word: string, dist: number }[];

            if (middleWords && middleWords.length > 0) {
                const probabilities = softmax(middleWords.map(n => n.dist));
                middleWords.forEach((n, i) => {
                    console.log(`${n.word}: Similarity ${n.dist.toFixed(4)} | Probability ${(probabilities[i] * 100).toFixed(2)}%`);
                });
            } else {
                console.log(`Could not find vectors for '${word1}' and '${word2}'`);
            }

            console.log(`\n--- Inferring middle word between '${word2} ${word1}' ---`);
            const reverseMiddleWords = model.mostSimilar(`${word2} ${word1}`, vocab.length) as { word: string, dist: number }[];

            if (reverseMiddleWords && reverseMiddleWords.length > 0) {
                const reverseProbabilities = softmax(reverseMiddleWords.map(n => n.dist));
                reverseMiddleWords.forEach((n, i) => {
                    console.log(`${n.word}: Similarity ${n.dist.toFixed(4)} | Probability ${(reverseProbabilities[i] * 100).toFixed(2)}%`);
                });
            } else {
                console.log(`Could not find vectors for '${word2}' and '${word1}'`);
            }

            /* 
             * Explanation: 
             * Because Continuous Bag of Words (CBOW) fundamentally just mathematically averages 
             * the word vectors within the training window together to predict the target context, 
             * it completely loses any concept of sequential order. 
             * 'cat sat on mat' and 'mat sat on cat' create the exact same mathematical average!
             */

            resolve();
        });
    });
}

export async function main() {
    try {
        await train();
        await evaluate();
        await evaluateMiddleWord();
    } catch (error) {
        console.error("Execution failed:", error);
        process.exit(1);
    }
}

// Automatically run main if this file is executed directly 
if (process.argv[1] === new URL(import.meta.url).pathname) {
    main();
}
