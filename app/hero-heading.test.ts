import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';

const page = readFileSync(new URL('./page.tsx', import.meta.url), 'utf8');

describe('home hero heading', () => {
  it('keeps the headline in three deliberate visual lines', () => {
    expect(page).toContain('<span className="hero-title-line">Where ideas</span>');
    expect(page).toContain('<span className="hero-title-line">become</span>');
    expect(page).toContain('<span className="hero-title-line hero-title-accent">intelligent.</span>');
  });
});
