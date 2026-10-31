import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);

test("Trust Meter is data-driven and separates score from confidence", async () => {
  const [html, script, rawTrust] = await Promise.all([
    readFile(new URL("index.html", root), "utf8"),
    readFile(new URL("script.js", root), "utf8"),
    readFile(new URL("data/trust-scores.json", root), "utf8")
  ]);
  const trust = JSON.parse(rawTrust);

  assert.match(html, /id="trust-leaders"/);
  assert.match(html, /Sample size earns confidence/);
  assert.doesNotMatch(script, /const trustLeaders\s*=/);
  assert.match(script, /fetch\("\.\/data\/trust-scores\.json"/);
  assert.match(script, /function trustScoreBand/);
  assert.match(script, /function trustConfidenceBand/);
  assert.equal(trust.methodologyVersion, "trust-meter-v1");
  assert.ok(trust.insiders.length > 5);
  assert.ok(trust.insiders.every((item) => item.sampleSize >= 3));
});

test("roadmap voting and the milestone timeline have honest static fallbacks", async () => {
  const [html, script, rawVotes] = await Promise.all([
    readFile(new URL("index.html", root), "utf8"),
    readFile(new URL("script.js", root), "utf8"),
    readFile(new URL("data/roadmap-votes.json", root), "utf8")
  ]);
  const votes = JSON.parse(rawVotes);

  assert.equal(votes.options.length, 6);
  for (const option of votes.options) {
    assert.match(html, new RegExp(`data-vote-count=["']${option.id}["']`));
  }
  assert.match(html, /class="timeline-list"/);
  assert.match(html, /datetime="2026-10-31"/);
  assert.match(html, /issues\/new\?template=roadmap-vote\.yml/);
  assert.match(script, /fetch\("\.\/data\/roadmap-votes\.json"/);
  assert.match(html, /View every code and data update on GitHub/);
});
