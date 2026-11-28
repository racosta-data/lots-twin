// Parses every ```mermaid block in a Markdown file. Usage: node scripts/check_mermaid.mjs docs/maze-flow.md
import { JSDOM } from 'jsdom';
import fs from 'fs';

const dom = new JSDOM('<!DOCTYPE html><body></body>');
globalThis.window = dom.window;
globalThis.document = dom.window.document;
Object.defineProperty(globalThis, 'navigator', { value: dom.window.navigator, configurable: true });
const { default: mermaid } = await import('mermaid');

const file = process.argv[2] ?? 'docs/maze-flow.md';
const blocks = [...fs.readFileSync(file, 'utf8').matchAll(/```mermaid\n([\s\S]*?)\n```/g)].map((m) => m[1]);
let failed = 0;
for (const [i, block] of blocks.entries()) {
  try {
    await mermaid.parse(block);
    console.log(`diagram ${i + 1}: OK`);
  } catch (e) {
    failed += 1;
    console.log(`diagram ${i + 1}: ERROR ${String(e.message || e).split('\n')[0]}`);
  }
}
console.log(`${blocks.length} diagrams, ${failed} failed`);
process.exit(failed ? 1 : 0);
