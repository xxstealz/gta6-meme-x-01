// gta6-meme-x-01 entry (Node 22, standard library only): it copies
// POST.json from the repository root to /output/POST.json, where the
// gate reads it. That is all the program has to do. The entry is the
// post itself: the meme (meme.png, drawn by draw_meme.py) is posted on
// X from a public account with make.fun in its text and the entrant's
// play code, POST.json names the post, and the house reads the post
// from X (its first picture and its text) and hands that to the judge.
// Nothing this program writes about the post is judged.
//
// POST.json still holds a placeholder address until the user posts the
// meme and sends back the post URL, so the gate refuses it as it stands
// (valid 0). Replace the placeholder with the real post address
// before submitting.
//
// Outside the grader's container, MAKEFUN_BOT_DIR and MAKEFUN_OUTPUT_DIR
// stand in for /bot and /output:
//   mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts

import { copyFileSync, mkdirSync, readFileSync } from 'node:fs';
import { join } from 'node:path';

const BOT_DIR = process.env.MAKEFUN_BOT_DIR ?? '/bot';
const OUTPUT_DIR = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';

mkdirSync(OUTPUT_DIR, { recursive: true });
try {
  // Fail loudly on a malformed POST.json instead of copying it blind:
  // the gate only accepts a JSON object naming an X post address.
  const parsed: unknown = JSON.parse(
    readFileSync(join(BOT_DIR, 'POST.json'), 'utf8'),
  );
  if (parsed === null || typeof parsed !== 'object' || Array.isArray(parsed)) {
    throw new Error('POST.json is not a JSON object');
  }
  copyFileSync(join(BOT_DIR, 'POST.json'), join(OUTPUT_DIR, 'POST.json'));
} catch (err) {
  console.error(`POST.json could not be copied from ${BOT_DIR}: ${(err as Error).message}`);
  process.exit(1);
}
