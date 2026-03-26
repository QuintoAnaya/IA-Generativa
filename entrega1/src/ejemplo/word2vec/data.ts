import * as fs from 'fs';

const corpusPath = new URL('../corpus.txt', import.meta.url);
const text = fs.readFileSync(corpusPath, 'utf-8').trim();

// Parse words
const words: string[] = text.split(/\s+/).filter(w => w.length > 0);

// 1. Vocabulary
export const vocab: string[] = Array.from(new Set<string>(words));

export const word2idx: Record<string, number> = {};
export const idx2word: Record<number, string> = {};

vocab.forEach((w: string, i: number) => {
    word2idx[w] = i;
    idx2word[i] = w;
});

// 2. Training Data (context window = 1 left, 1 right)
export const trainingData: { context: number[], target: number }[] = [];

for (let i = 1; i < words.length - 1; i++) {
    const context = [word2idx[words[i - 1]], word2idx[words[i + 1]]];
    const target = word2idx[words[i]];
    trainingData.push({ context, target });
}

