document.documentElement.classList.add("js");

const whole = new Intl.NumberFormat("en-US", { maximumFractionDigits: 3 });
const money = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
const price = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 6 });
const dateOnly = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric", timeZone: "America/New_York" });
const dateTime = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit", timeZone: "America/New_York", timeZoneName: "short" });

function clean(value, fallback = "N/A") {
  if (value === null || value === undefined || value === "") return fallback;
  return String(value).replaceAll("�", "·");
}

function escapeHtml(value) {
  return clean(value).replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    "\"": "&quot;"
  })[character]);
}

function displayTicker(value) {
  const ticker = clean(value);
  return ticker.toUpperCase() === "NONE" ? "N/A" : ticker;
}

function displayNumber(value) {
  return typeof value === "number" ? whole.format(value) : "N/A";
}

function displayMoney(value) {
  return typeof value === "number" ? money.format(value) : "N/A";
}

function displayPrice(value) {
  return typeof value === "number" ? price.format(value) : "N/A";
}

function displayPercent(value) {
  if (typeof value !== "number") return "N/A";
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

function displayGrade(record) {
  if (typeof record.trust !== "number") return "N/A";
  return `${record.trust.toFixed(1)}/100${record.trustN ? ` · n=${record.trustN}` : ""}`;
}

function recordRow(record, includeRank) {
  const row = document.createElement("tr");
  const possibleExit = record.side === "SELL" && record.sharesAfter === 0;
  const conviction = typeof record.dailyConviction === "number" ? `${record.dailyConviction}/100` : "N/A";
  const issuer = `<span class="daily-ticker">${escapeHtml(displayTicker(record.ticker))}</span><b>${escapeHtml(record.company)}</b><small>${escapeHtml(record.insider)} · ${escapeHtml(record.role)}</small>`;
  const position = `<b>${escapeHtml(displayNumber(record.sharesAfter))}</b><small>${escapeHtml(displayPercent(record.positionChange))}${possibleExit ? " · possible direct exit" : ""}</small>`;
  const cells = [
    `<td>${includeRank ? `<span class="daily-rank">${includeRank}</span>` : ""}${issuer}</td>`,
    `<td>${escapeHtml(dateTime.format(new Date(record.filedAt)))}</td>`,
    `<td>${escapeHtml(dateOnly.format(new Date(`${record.transactionDate}T12:00:00-04:00`)))}</td>`,
    `<td><b>${escapeHtml(displayNumber(record.shares))}</b><small>${escapeHtml(displayPrice(record.price))}</small></td>`,
    `<td><b>${escapeHtml(displayMoney(record.value))}</b><small>${escapeHtml(record.side)}</small></td>`,
    `<td>${position}</td>`
  ];
  if (record.side === "BUY") {
    cells.push(`<td>${escapeHtml(displayGrade(record))}</td>`);
    cells.push(`<td><b class="positive">${escapeHtml(conviction)}</b></td>`);
  }
  cells.push(`<td><a class="daily-source" href="${escapeHtml(record.source)}" target="_blank" rel="noreferrer">SEC ↗</a></td>`);
  row.innerHTML = cells.join("");
  return row;
}

function renderRecords(selector, records, emptySelector, includeRank = false) {
  const target = document.querySelector(selector);
  const empty = document.querySelector(emptySelector);
  target.replaceChildren();
  if (!records.length) {
    empty.hidden = false;
    return;
  }
  empty.hidden = true;
  records.forEach((record, index) => target.append(recordRow(record, includeRank ? index + 1 : false)));
}

function renderClusters(clusters) {
  const target = document.querySelector("#daily-clusters");
  target.replaceChildren();
  if (!clusters.length) {
    target.innerHTML = '<p class="daily-empty">No same-issuer multi-insider clusters appeared in this edition.</p>';
    return;
  }
  clusters.forEach((cluster) => {
    const card = document.createElement("article");
    card.className = "daily-mini-card";
    card.innerHTML = `<div><span class="daily-ticker">${escapeHtml(displayTicker(cluster.ticker))}</span><b>${escapeHtml(cluster.company)}</b></div><strong class="${cluster.side === "BUY" ? "positive" : "negative"}">${escapeHtml(cluster.side)}</strong><p>${escapeHtml(cluster.insiderCount)} reporting persons · ${escapeHtml(displayMoney(cluster.combinedValue))} combined</p><small>${escapeHtml(cluster.insiders.join(" · "))}</small>`;
    target.append(card);
  });
}

function renderWarnings(warnings) {
  const target = document.querySelector("#daily-review");
  target.replaceChildren();
  if (!warnings.length) {
    target.innerHTML = '<p class="daily-empty">No new amendments or ambiguous qualifying transactions were routed to review.</p>';
    return;
  }
  warnings.forEach((warning) => {
    const card = document.createElement("a");
    card.className = "daily-mini-card daily-warning-card";
    card.href = warning.source;
    card.target = "_blank";
    card.rel = "noreferrer";
    card.innerHTML = `<div><span class="daily-ticker">${escapeHtml(displayTicker(warning.ticker))}</span><b>${escapeHtml(warning.company)}</b></div><strong>${escapeHtml(warning.form)}</strong><p>${escapeHtml(warning.reason)}</p><small>${escapeHtml(warning.insider)} · ${escapeHtml(dateTime.format(new Date(warning.filedAt)))}</small>`;
    target.append(card);
  });
}

async function loadDailyBrief() {
  try {
    const response = await fetch("./data/daily/latest.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`daily brief returned ${response.status}`);
    const data = await response.json();
    document.querySelector("#daily-edition").textContent = `Edition ${dateOnly.format(new Date(`${data.editionDate}T12:00:00-04:00`))} · generated from ${data.source}`;
    document.querySelector("#daily-buy-count").textContent = whole.format(data.counts?.qualifyingPurchases ?? 0);
    document.querySelector("#daily-sale-count").textContent = whole.format(data.counts?.notableSales ?? 0);
    document.querySelector("#daily-cluster-count").textContent = whole.format(data.counts?.clusters ?? 0);
    document.querySelector("#daily-review-count").textContent = whole.format(data.counts?.reviewNeeded ?? 0);
    document.querySelector("#daily-buy-minimum").textContent = displayMoney(data.methodology?.purchaseMinimumUsd);
    document.querySelector("#daily-sale-minimum").textContent = displayMoney(data.methodology?.saleMinimumUsd);
    renderRecords("#daily-buys", data.strongestBuys || [], "#daily-buys-empty", true);
    renderRecords("#daily-sales", data.notableSales || [], "#daily-sales-empty");
    renderClusters(data.clusters || []);
    renderWarnings(data.reviewNeeded || []);
  } catch (error) {
    console.error("The daily brief could not be loaded.", error);
    document.querySelector("#daily-edition").textContent = "The latest edition is temporarily unavailable.";
    document.querySelectorAll(".daily-empty").forEach((element) => { element.hidden = false; });
  }
}

loadDailyBrief();
