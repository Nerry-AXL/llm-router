// Benchmark harness for Worker CPU test
// Measures classification time to verify <10ms feasibility

const { TFIDFClassifier } = require('./classifier.js');
const testData = require('./test-data.json');
const { performance } = require('perf_hooks');

// Initialize classifier with test data
const classifier = new TFIDFClassifier(
  testData.vocabulary,
  testData.idf,
  testData.weights,
  testData.bias
);

// Warmup (avoid cold-start bias)
console.log('Warming up...');
for (let i = 0; i < 100; i++) {
  classifier.predict(testData.test_prompts[i % testData.test_prompts.length]);
}

// Benchmark
console.log('\nRunning benchmark...');
const times = [];
const iterations = 1000;

for (let i = 0; i < iterations; i++) {
  const prompt = testData.test_prompts[i % testData.test_prompts.length];
  const start = performance.now();
  classifier.predict(prompt);
  const end = performance.now();
  times.push(end - start);
}

// Calculate statistics
times.sort((a, b) => a - b);
const mean = times.reduce((a, b) => a + b, 0) / times.length;
const p50 = times[Math.floor(times.length * 0.5)];
const p95 = times[Math.floor(times.length * 0.95)];
const p99 = times[Math.floor(times.length * 0.99)];
const max = times[times.length - 1];

// Results
console.log('\n=== BENCHMARK RESULTS ===');
console.log(`Iterations: ${iterations}`);
console.log(`Vocabulary size: ${testData.vocabulary.length}`);
console.log(`\nTiming (milliseconds):`);
console.log(`  Mean: ${mean.toFixed(3)} ms`);
console.log(`  p50:  ${p50.toFixed(3)} ms`);
console.log(`  p95:  ${p95.toFixed(3)} ms`);
console.log(`  p99:  ${p99.toFixed(3)} ms`);
console.log(`  Max:  ${max.toFixed(3)} ms`);

// Verdict
const cpuLimit = 10.0; // Cloudflare Worker CPU limit
const passed = p95 < cpuLimit;

console.log(`\n=== VERDICT ===`);
if (passed) {
  console.log(`✓ PASS: p95 (${p95.toFixed(3)} ms) < ${cpuLimit} ms CPU limit`);
  console.log(`  Feasible for Cloudflare Worker deployment`);
} else {
  console.log(`✗ FAIL: p95 (${p95.toFixed(3)} ms) >= ${cpuLimit} ms CPU limit`);
  console.log(`  NOT feasible - need to reduce vocabulary or simplify`);
}

// Test sample predictions
console.log('\n=== SAMPLE PREDICTIONS ===');
testData.test_prompts.forEach((prompt, i) => {
  const result = classifier.predict(prompt);
  const truncated = prompt.length > 60 ? prompt.substring(0, 60) + '...' : prompt;
  console.log(`${i + 1}. "${truncated}"`);
  console.log(`   → ${result.label} (p=${result.probability.toFixed(3)})`);
});

process.exit(passed ? 0 : 1);
