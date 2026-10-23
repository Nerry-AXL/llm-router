// TF-IDF + Logistic Regression classifier (plain JS, no dependencies)
// Designed to run in Cloudflare Worker with <10ms CPU budget

class TFIDFClassifier {
  constructor(vocabulary, idf, weights, bias) {
    this.vocabulary = vocabulary; // Array of terms
    this.vocabIndex = new Map(vocabulary.map((term, i) => [term, i]));
    this.idf = idf; // Array of IDF values (same length as vocabulary)
    this.weights = weights; // Logistic regression weights
    this.bias = bias; // Logistic regression bias term
  }

  // Simple tokenizer (split on whitespace and punctuation, lowercase)
  tokenize(text) {
    return text
      .toLowerCase()
      .replace(/[^a-z0-9\s]/g, ' ')
      .split(/\s+/)
      .filter(t => t.length > 0);
  }

  // Compute term frequencies
  termFrequency(tokens) {
    const tf = new Map();
    for (const token of tokens) {
      tf.set(token, (tf.get(token) || 0) + 1);
    }
    return tf;
  }

  // Create TF-IDF feature vector
  vectorize(text) {
    const tokens = this.tokenize(text);
    const tf = this.termFrequency(tokens);
    const vector = new Array(this.vocabulary.length).fill(0);

    for (const [term, count] of tf) {
      const idx = this.vocabIndex.get(term);
      if (idx !== undefined) {
        // TF-IDF = (term count / total tokens) * IDF
        vector[idx] = (count / tokens.length) * this.idf[idx];
      }
    }

    return vector;
  }

  // Logistic regression prediction
  predict(text) {
    const features = this.vectorize(text);

    // Dot product: sum(features[i] * weights[i])
    let logit = this.bias;
    for (let i = 0; i < features.length; i++) {
      logit += features[i] * this.weights[i];
    }

    // Sigmoid: 1 / (1 + e^(-logit))
    const probability = 1 / (1 + Math.exp(-logit));

    // Return prediction (0 = easy/small model, 1 = hard/large model)
    return {
      prediction: probability > 0.5 ? 1 : 0,
      probability: probability,
      label: probability > 0.5 ? 'hard' : 'easy'
    };
  }
}

// Export for Node.js testing
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { TFIDFClassifier };
}
