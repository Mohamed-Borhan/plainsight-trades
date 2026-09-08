import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);

test("the complete ledger exposes transactions, reviews, filters, and pagination", async () => {
  const [html, script, rawData] = await Promise.all([
    readFile(new URL("index.html", root), "utf8"),
    readFile(new URL("script.js", root), "utf8"),
    readFile(new URL("data/signals.json", root), "utf8")
  ]);
  const data = JSON.parse(rawData);

  for (const id of [
    "ledger-total-count",
    "ledger-buy-count",
    "ledger-sale-count",
    "ledger-review-count",
    "ledger-sort",
    "ledger-results",
    "ledger-previous",
    "ledger-next"
  ]) {
    assert.match(html, new RegExp(`id=["']${id}["']`));
  }

  for (const filter of ["all", "buy", "sell", "review"]) {
    assert.match(html, new RegExp(`data-filter=["']${filter}["']`));
  }

  assert.match(script, /const transactions = \(data\.transactions \|\| \[\]\)\.map\(recordToSignal\)/);
  assert.match(script, /const reviewRecords = \(data\.reviewNeeded \|\| \[\]\)\.map\(reviewToSignal\)/);
  assert.match(script, /ledgerRecords = \[\.\.\.transactions, \.\.\.reviewRecords\]/);
  assert.ok(data.transactions.length > 0, "published transaction data should not be empty");
  assert.equal(
    data.transactions.length,
    data.transactions.filter((record) => record.side === "BUY" || record.side === "SELL").length,
    "every published transaction should be represented by a supported ledger type"
  );
});
