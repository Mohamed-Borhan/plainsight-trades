document.documentElement.classList.add("js");

let signals = [
  {
    ticker: "KMX",
    company: "CarMax",
    insider: "Keith Barr",
    role: "President & CEO",
    filed: "Filed Jun 24, 2026",
    value: 498294,
    positionChange: 39.2,
    price: 53.01,
    shares: 9400,
    sharesAfter: 33375,
    move5d: -3.1,
    strength: 70,
    trust: null,
    trustN: 0,
    source: "https://www.sec.gov/edgar/search/#/q=0001170010-26-000067",
    context: "A CEO increased his reported direct position by about 39%, a stronger conviction input than a large purchase that barely changes an existing stake.",
    caveat: "This is one buyer, not a cluster. The filing reports what traded, not why, and the first five sessions were negative."
  },
  {
    ticker: "EQPT",
    company: "EquipmentShare.com",
    insider: "Jabbok Schlacks",
    role: "Co-founder & CEO",
    filed: "Filed Jun 17, 2026",
    value: 1056039,
    positionChange: null,
    price: 21.1208,
    shares: 50000,
    sharesAfter: 50000,
    move5d: -18.2,
    strength: 55,
    trust: null,
    trustN: 0,
    source: "https://www.sec.gov/edgar/search/#/q=0000950103-26-009152",
    context: "A seven-figure CEO purchase deserves attention, but position-change data could not be calculated reliably from the archived filing history.",
    caveat: "The stock fell sharply over the next five sessions. Dollar size alone does not make a signal predictive."
  },
  {
    ticker: "NXST",
    company: "Nexstar Media Group",
    insider: "Perry A. Sook",
    role: "Chief Executive Officer",
    filed: "Filed Jun 29, 2026",
    value: 1985251,
    positionChange: 1.4,
    price: 162.26,
    shares: 12235,
    sharesAfter: 899044,
    move5d: 3.4,
    strength: 54,
    trust: null,
    trustN: 0,
    source: "https://www.sec.gov/edgar/search/#/q=0001193125-26-288030",
    context: "The cash commitment is large and came from the CEO, but it increased an already-large reported position by only about 1.4%.",
    caveat: "High dollar value can appear more meaningful than it is when the insider already owns a very large stake."
  },
  {
    ticker: "PGY",
    company: "Pagaya Technologies",
    insider: "Gal Krubiner",
    role: "Chief Executive Officer",
    filed: "Filed Jun 25, 2026",
    value: 250429,
    positionChange: 3.0,
    price: 15.43,
    shares: 16230,
    sharesAfter: 555906,
    move5d: 19.3,
    strength: 45,
    trust: 51,
    trustN: 1,
    source: "https://www.sec.gov/edgar/search/#/q=0001628280-26-045532",
    context: "This followed another disclosed purchase earlier in June. Repeat buying can be more informative than an isolated transaction.",
    caveat: "The Trust Meter is effectively neutral because only one mature historical signal is available."
  },
  {
    ticker: "OXY",
    company: "Occidental Petroleum",
    insider: "Richard A. Jackson",
    role: "President & CEO",
    filed: "Filed Jun 24, 2026",
    value: 249853,
    positionChange: 1.1,
    price: 52.38,
    shares: 4770,
    sharesAfter: 444098,
    move5d: -4.3,
    strength: 41,
    trust: null,
    trustN: 0,
    source: "https://www.sec.gov/edgar/search/#/q=0001628280-26-045313",
    context: "A senior executive used cash to add shares, but the purchase changed the reported position only modestly.",
    caveat: "No mature follower history is available for this insider, so the Trust Meter remains unscored."
  },
  {
    ticker: "NTST",
    company: "NETSTREIT",
    insider: "Mark Manheimer",
    role: "President, CEO & Secretary",
    filed: "Filed Jun 22, 2026",
    value: 95950,
    positionChange: 1.2,
    price: 19.19,
    shares: 5000,
    sharesAfter: 415260,
    move5d: 7.5,
    strength: 36,
    trust: 48,
    trustN: 1,
    source: "https://www.sec.gov/edgar/search/#/q=0001628280-26-044503",
    context: "The trade cleared the minimum-dollar filter and was followed by a positive five-session move in the archived snapshot.",
    caveat: "The stake increase was small and one mature historical observation is not enough to infer repeatable skill."
  }
];

const politicalTrades = [
  { filer: "August Pfluger", chamber: "House", office: "TX-11", asset: "Fidelity National Financial", ticker: "FNF", side: "SELL", tradeDate: "Jan 12, 2026", filed: "Feb 11, 2026", range: "$1,001–$15,000", owner: "N/A", source: "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2026/20033920.pdf" },
  { filer: "August Pfluger", chamber: "House", office: "TX-11", asset: "SiriusXM Holdings", ticker: "SIRI", side: "SELL", tradeDate: "Jan 13, 2026", filed: "Feb 11, 2026", range: "$1,001–$15,000", owner: "Dependent child", source: "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2026/20033920.pdf" },
  { filer: "Dan Newhouse", chamber: "House", office: "WA-04", asset: "T-Mobile US", ticker: "TMUS", side: "BUY", tradeDate: "Dec 11, 2025", filed: "Jan 15, 2026", range: "$1,001–$15,000", owner: "Spouse", source: "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2026/20033654.pdf" },
  { filer: "Dan Newhouse", chamber: "House", office: "WA-04", asset: "Textron", ticker: "TXT", side: "BUY", tradeDate: "Dec 11, 2025", filed: "Jan 15, 2026", range: "$1,001–$15,000", owner: "Spouse", source: "https://disclosures-clerk.house.gov/public_disc/ptr-pdfs/2026/20033654.pdf" }
];

const trustLeaders = [
  { name: "Frank B. Holding Jr.", role: "Chairman & CEO", score: 65, n: 14, excess: 17.4, hit: 64 },
  { name: "Anthony Noto", role: "Chief Executive Officer", score: 61, n: 34, excess: 6.3, hit: 41 },
  { name: "Morris Goldfarb", role: "CEO", score: 60, n: 7, excess: 17.4, hit: 71 },
  { name: "Gary G. Friedman", role: "Chairman & CEO", score: 60, n: 6, excess: 16.5, hit: 83 },
  { name: "Joseph M. Hogan", role: "President & CEO", score: 59, n: 7, excess: 19.7, hit: 57 }
];

const compactMoney = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", notation: "compact", maximumFractionDigits: 1 });
const whole = new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 });
const readableDate = new Intl.DateTimeFormat("en-US", { month: "short", day: "numeric", year: "numeric" });
const signalRows = document.querySelector("#signal-rows");
const signalEmpty = document.querySelector("#signal-empty");
const searchInput = document.querySelector("#signal-search");
const filterButtons = [...document.querySelectorAll("[data-filter]")];
let selectedTicker = signals[0].ticker;
let moveFilter = "all";

function recordToSignal(record) {
  const filedDate = record.filedAt ? new Date(record.filedAt) : null;
  return {
    ...record,
    filed: filedDate && !Number.isNaN(filedDate.valueOf()) ? `Filed ${readableDate.format(filedDate)}` : "Filed date N/A",
    positionChange: record.positionChange ?? null,
    move5d: typeof record.move5d === "number" ? record.move5d : null,
    trust: record.trust ?? null,
    trustN: record.trustN ?? 0,
    strength: record.strength ?? 0
  };
}

function displayDate(value) {
  if (!value) return "N/A";
  const parsed = new Date(`${value.slice(0, 10)}T12:00:00`);
  return Number.isNaN(parsed.valueOf()) ? value : readableDate.format(parsed);
}

function escapeHtml(value) {
  return String(value ?? "").replace(/[&<>'"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "'": "&#39;",
    '"': "&quot;"
  })[character]);
}

function trustStatus(score) {
  if (score === null) return "Unscored";
  if (score >= 62) return "Established";
  if (score >= 55) return "Developing";
  if (score >= 45) return "Neutral";
  return "Weak";
}

function setField(name, value) {
  const element = document.querySelector(`[data-field="${name}"]`);
  if (element) element.textContent = value;
}

function renderContext(signal) {
  selectedTicker = signal.ticker;
  setField("ticker", signal.ticker);
  setField("filed", signal.filed);
  setField("company", signal.company);
  setField("insider", `${signal.insider} · ${signal.role}`);
  setField("trust-score", signal.trust ?? "—");
  setField("trust-status", trustStatus(signal.trust));
  setField("trust-caption", signal.trust === null ? "Not enough mature public signals to score this history." : `Based on ${signal.trustN} mature historical signal${signal.trustN === 1 ? "" : "s"}; low sample confidence.`);
  setField("value", compactMoney.format(signal.value));
  setField("price", typeof signal.price === "number" ? `$${signal.price.toFixed(2)}` : "N/A");
  setField("shares-after", typeof signal.sharesAfter === "number" ? whole.format(signal.sharesAfter) : "N/A");
  setField("strength", `${signal.strength}/100`);
  setField("context", signal.context);
  setField("caveat", signal.caveat);

  const meter = document.querySelector("#signal-context .meter");
  meter.style.setProperty("--score", signal.trust ?? 50);
  meter.classList.toggle("unscored", signal.trust === null);
  const source = document.querySelector('[data-field="source"]');
  source.href = signal.source;

  document.querySelectorAll(".signal-row").forEach((row) => {
    row.classList.toggle("selected", row.dataset.ticker === signal.ticker);
    row.setAttribute("aria-pressed", String(row.dataset.ticker === signal.ticker));
  });
}

function renderSignals() {
  const query = searchInput.value.trim().toLowerCase();
  const filtered = signals.filter((signal) => {
    const matchesQuery = `${signal.ticker} ${signal.company} ${signal.insider}`.toLowerCase().includes(query);
    const hasMove = typeof signal.move5d === "number";
    const matchesMove = moveFilter === "all" || (hasMove && (moveFilter === "up" ? signal.move5d >= 0 : signal.move5d < 0));
    return matchesQuery && matchesMove;
  });

  signalRows.replaceChildren();
  signalEmpty.hidden = filtered.length !== 0;
  for (const signal of filtered) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = `signal-row${selectedTicker === signal.ticker ? " selected" : ""}`;
    button.dataset.ticker = signal.ticker;
    button.setAttribute("aria-pressed", String(selectedTicker === signal.ticker));
    const position = signal.positionChange === null ? "N/A" : `+${signal.positionChange.toFixed(1)}%`;
    const hasMove = typeof signal.move5d === "number";
    const move = hasMove ? `${signal.move5d >= 0 ? "+" : ""}${signal.move5d.toFixed(1)}%` : "N/A";
    button.innerHTML = `
      <span class="company-cell"><i>${escapeHtml(signal.ticker.slice(0, 2))}</i><span><b>${escapeHtml(signal.ticker)} · ${escapeHtml(signal.company)}</b><small>${escapeHtml(signal.insider)}, ${escapeHtml(signal.role)}</small></span></span>
      <span><b>${compactMoney.format(signal.value)}</b><small>${whole.format(signal.shares)} shares</small></span>
      <span><b>${position}</b><small>reported change</small></span>
      <span class="${!hasMove ? "pending" : signal.move5d >= 0 ? "positive" : "negative"}"><b>${move}</b><small>${hasMove ? "next 5 sessions" : "outcome pending"}</small></span>
      <span class="score-chip">${signal.strength}</span>`;
    button.addEventListener("click", () => renderContext(signal));
    signalRows.append(button);
  }

  if (filtered.length && !filtered.some((signal) => signal.ticker === selectedTicker)) renderContext(filtered[0]);
}

searchInput.addEventListener("input", renderSignals);
for (const button of filterButtons) {
  button.addEventListener("click", () => {
    moveFilter = button.dataset.filter;
    filterButtons.forEach((item) => item.classList.toggle("active", item === button));
    renderSignals();
  });
}

const politicalRows = document.querySelector("#political-rows");
for (const trade of politicalTrades) {
  const link = document.createElement("a");
  link.className = "political-row";
  link.href = trade.source;
  link.target = "_blank";
  link.rel = "noreferrer";
  link.innerHTML = `
    <span class="politician-cell"><i>${trade.chamber[0]}</i><span><b>${trade.filer}</b><small>${trade.chamber} · ${trade.office}</small></span></span>
    <span><b>${trade.ticker} · ${trade.asset}</b><small>${trade.owner} ownership</small></span>
    <span class="${trade.side === "BUY" ? "positive" : "negative"}"><b>${trade.side}</b><small>${trade.tradeDate}</small></span>
    <span><b>${trade.range}</b><small>filed ${trade.filed}</small></span><span aria-hidden="true">↗</span>`;
  politicalRows.append(link);
}

const trustBoard = document.querySelector("#trust-leaders");
trustLeaders.forEach((leader, index) => {
  const initials = leader.name.split(" ").map((part) => part[0]).slice(0, 2).join("");
  const row = document.createElement("div");
  row.className = "leader";
  row.innerHTML = `
    <span class="rank">0${index + 1}</span><div class="avatar">${initials}</div>
    <div class="leader-name"><b>${leader.name}</b><small>${leader.role}</small></div>
    <div class="leader-stat"><small>Avg. excess</small><b class="positive">+${leader.excess.toFixed(1)}%</b></div>
    <div class="leader-stat"><small>Hit rate</small><b>${leader.hit}%</b></div>
    <div class="leader-stat"><small>Sample</small><b>${leader.n}</b></div>
    <div class="mini-score"><b>${leader.score}</b><span style="width:${leader.score}%"></span></div>`;
  trustBoard.append(row);
});

const marketMoves = document.querySelector("#market-moves");

function renderEditionSignals(items, weekly = false) {
  marketMoves.replaceChildren();
  if (!items.length) {
    const empty = document.createElement("p");
    empty.className = "edition-empty";
    empty.textContent = "No qualifying new transactions were recorded for this edition.";
    marketMoves.append(empty);
    return;
  }
  const ranked = weekly ? items : [...items].filter((item) => typeof item.move5d === "number").sort((a, b) => Math.abs(b.move5d) - Math.abs(a.move5d)).slice(0, 3);
  ranked.slice(0, 5).forEach((signal) => {
    const row = document.createElement("a");
    row.className = "move";
    row.href = signal.source;
    row.target = "_blank";
    row.rel = "noreferrer";
    const outcome = weekly ? `${signal.strength ?? 0}/100` : `${signal.move5d >= 0 ? "+" : ""}${signal.move5d.toFixed(1)}%`;
    row.innerHTML = `<span class="move-ticker">${escapeHtml(signal.ticker)}</span><span><b>${escapeHtml(signal.company)}</b><small>${compactMoney.format(signal.value)} disclosed purchase</small></span><strong class="${weekly || signal.move5d >= 0 ? "positive" : "negative"}">${escapeHtml(outcome)}</strong>`;
    marketMoves.append(row);
  });
}

function renderBriefList(targetId, items, renderer) {
  const target = document.querySelector(targetId);
  target.replaceChildren();
  if (!items.length) {
    const empty = document.createElement("p");
    empty.className = "brief-empty";
    empty.textContent = "No qualifying records in this edition.";
    target.append(empty);
    return;
  }
  items.slice(0, 3).forEach((item) => target.append(renderer(item)));
}

function linkedBriefRow(item, detail, value) {
  const row = document.createElement("a");
  row.className = "brief-row";
  row.href = item.source;
  row.target = "_blank";
  row.rel = "noreferrer";
  row.innerHTML = `<span><b>${escapeHtml(item.ticker || item.accession)}</b><small>${escapeHtml(detail)}</small></span><strong>${escapeHtml(value)}</strong>`;
  return row;
}

async function loadStageOneData() {
  try {
    const response = await fetch("./data/signals.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`signal data returned ${response.status}`);
    const data = await response.json();
    const purchases = (data.transactions || []).filter((record) => record.side === "BUY").map(recordToSignal);
    if (purchases.length) {
      signals = purchases;
      selectedTicker = signals[0].ticker;
    }
    const status = data.automation?.status === "active" ? "Automation active" : "Automation scheduled";
    document.querySelector("#automation-status").textContent = status;
    document.querySelector("#automation-note").textContent = data.automation?.note || "Nightly SEC updates are enabled.";
    document.querySelector("#hero-signal-count").textContent = whole.format(data.stats?.purchases ?? purchases.length);
    document.querySelector("#data-freshness").innerHTML = `<i></i> Last SEC check ${displayDate(data.lastCheckedDate)}`;
    document.querySelector("#signal-source-note").textContent = `Public SEC records through ${displayDate(data.lastCheckedDate)}. Automated records show N/A until market outcomes mature.`;
  } catch (error) {
    console.warn("PlainSight is using its archived fallback data.", error);
    document.querySelector("#automation-status").textContent = "Archived fallback";
  }
  renderSignals();
  renderContext(signals[0]);

  try {
    const response = await fetch("./data/weekly/latest.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`weekly data returned ${response.status}`);
    const weekly = await response.json();
    document.querySelector("#weekly-period").textContent = `${displayDate(weekly.periodStart)}–${displayDate(weekly.periodEnd)}`;
    document.querySelector("#weekly-lead").textContent = weekly.lead;
    document.querySelector("#weekly-purchase-count").textContent = whole.format(weekly.counts?.qualifyingPurchases ?? 0);
    document.querySelector("#weekly-sale-count").textContent = whole.format(weekly.counts?.notableSales ?? 0);
    document.querySelector("#weekly-cluster-count").textContent = whole.format(weekly.counts?.clusters ?? 0);
    document.querySelector("#weekly-review-count").textContent = whole.format(weekly.counts?.reviewNeeded ?? 0);
    renderEditionSignals((weekly.strongestBuys || []).map(recordToSignal), true);
    renderBriefList("#weekly-sales", weekly.notableSales || [], (item) => linkedBriefRow(item, item.company, compactMoney.format(item.value)));
    renderBriefList("#weekly-warnings", weekly.reviewNeeded || [], (item) => linkedBriefRow(item, item.reason, "Review ↗"));
    renderBriefList("#weekly-clusters", weekly.clusters || [], (item) => {
      const row = document.createElement("div");
      row.className = "brief-row";
      row.innerHTML = `<span><b>${escapeHtml(item.ticker)}</b><small>${escapeHtml(item.insiderCount)} disclosed insiders · ${escapeHtml(item.company)}</small></span><strong>${compactMoney.format(item.combinedValue)}</strong>`;
      return row;
    });
  } catch (error) {
    console.warn("Weekly preview is not available; archived moves remain visible.", error);
    renderEditionSignals(signals, false);
    renderBriefList("#weekly-sales", [], () => document.createElement("span"));
    renderBriefList("#weekly-clusters", [], () => document.createElement("span"));
    renderBriefList("#weekly-warnings", [], () => document.createElement("span"));
  }
}

const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
if (!reducedMotion && "IntersectionObserver" in window) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("is-visible");
        observer.unobserve(entry.target);
      }
    });
  }, { rootMargin: "0px 0px -10%", threshold: 0.07 });
  document.querySelectorAll(".reveal").forEach((element) => observer.observe(element));
} else {
  document.querySelectorAll(".reveal").forEach((element) => element.classList.add("is-visible"));
}

loadStageOneData();
