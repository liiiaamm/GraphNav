// GraphNav in the browser: Dijkstra and A* over the street graph of central Madrid.
(() => {
  "use strict";
  const $ = (id) => document.getElementById(id);
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const BLUE = "#0078bf", PINK = "#ff48b0", INK = "#142a3b";

  const PLACES = [
    ["Comillas ICAI, Alberto Aguilera", 40.4299, -3.7136],
    ["Santiago Bernabéu", 40.45306, -3.68835],
    ["Puerta del Sol", 40.41694, -3.70345],
    ["Atocha station", 40.40656, -3.69086],
    ["Puerta de Alcalá", 40.41998, -3.68878],
    ["Plaza de España", 40.4233, -3.71226],
    ["Plaza de Castilla", 40.4666, -3.6889],
    ["Plaza Mayor", 40.41553, -3.70742],
    ["Templo de Debod", 40.424, -3.71782],
  ];

  // ------------------------------------------------------------------ graph

  let G; // { n, x, y, lon, lat, E, out, major, names, geomX, geomY }
  function loadGraph(d) {
    const n = d.nodes.length / 2, s = d.scale, [lon0, lat0] = d.origin;
    const kx = Math.cos(((lat0 + d.bbox[3]) / 2) * Math.PI / 180) * 111320, ky = 110540;
    const lon = new Float64Array(n), lat = new Float64Array(n), x = new Float64Array(n), y = new Float64Array(n);
    for (let i = 0; i < n; i++) {
      lon[i] = lon0 + d.nodes[2 * i] / s; lat[i] = lat0 + d.nodes[2 * i + 1] / s;
      x[i] = d.nodes[2 * i] / s * kx; y[i] = d.nodes[2 * i + 1] / s * ky;
    }
    const gx = new Float64Array(d.geom.length / 2), gy = new Float64Array(d.geom.length / 2);
    for (let i = 0; i < gx.length; i++) { gx[i] = d.geom[2 * i] / s * kx; gy[i] = d.geom[2 * i + 1] / s * ky; }
    const m = d.edges.length / 8;
    const E = Int32Array.from(d.edges);
    const outCount = new Int32Array(n + 1);
    for (let e = 0; e < m; e++) outCount[E[8 * e] + 1]++;
    for (let i = 0; i < n; i++) outCount[i + 1] += outCount[i];
    const outIdx = new Int32Array(m), fill = outCount.slice();
    for (let e = 0; e < m; e++) outIdx[fill[E[8 * e]]++] = e;
    const major = new Uint8Array(n);
    d.major.forEach((i) => { major[i] = 1; });
    let maxSpeed = 0;
    for (let e = 0; e < m; e++) maxSpeed = Math.max(maxSpeed, E[8 * e + 3]);
    const majorHw = new Set(["motorway", "trunk", "primary", "secondary", "tertiary"].map((h) => d.highways.indexOf(h)));
    G = { n, m, x, y, lon, lat, E, outStart: outCount, outIdx, major, names: d.names, gx, gy, maxSpeed, majorHw, kx, ky, lat0, lon0 };
  }

  const from_ = (e) => G.E[8 * e], to_ = (e) => G.E[8 * e + 1];
  const lenM = (e) => G.E[8 * e + 2] / 10;
  const speed = (e) => G.E[8 * e + 3] || 30;
  const nameOf = (e) => G.names[G.E[8 * e + 4]];

  function edgePoints(e) {
    const pts = [[G.x[from_(e)], G.y[from_(e)]]];
    const g0 = G.E[8 * e + 6], gn = G.E[8 * e + 7];
    for (let k = 0; k < gn; k++) pts.push([G.gx[g0 + k], G.gy[g0 + k]]);
    pts.push([G.x[to_(e)], G.y[to_(e)]]);
    return pts;
  }

  function nearestNode(lat, lon) {
    const px = (lon - G.lon0) * G.kx, py = (lat - G.lat0) * G.ky;
    return nearestXY(px, py);
  }
  function nearestXY(px, py) {
    let best = 0, bd = Infinity;
    for (let i = 0; i < G.n; i++) {
      const d = (G.x[i] - px) ** 2 + (G.y[i] - py) ** 2;
      if (d < bd) { bd = d; best = i; }
    }
    return best;
  }

  // ------------------------------------------------------------------ search

  class Heap {
    constructor() { this.k = []; this.v = []; }
    push(key, val) {
      const k = this.k, v = this.v;
      let i = k.length; k.push(key); v.push(val);
      while (i > 0) { const p = (i - 1) >> 1; if (k[p] <= key) break; k[i] = k[p]; v[i] = v[p]; i = p; }
      k[i] = key; v[i] = val;
    }
    pop() {
      const k = this.k, v = this.v, top = v[0], last = k.length - 1, lk = k[last], lv = v[last];
      k.pop(); v.pop();
      if (last > 0) {
        let i = 0;
        for (;;) {
          let c = 2 * i + 1;
          if (c >= last) break;
          if (c + 1 < last && k[c + 1] < k[c]) c++;
          if (k[c] >= lk) break;
          k[i] = k[c]; v[i] = v[c]; i = c;
        }
        k[i] = lk; v[i] = lv;
      }
      return top;
    }
    get size() { return this.k.length; }
  }

  // Cost of an edge in the units of each mode: metres, or hours as in gps.py.
  function weightFn(mode) {
    if (mode === "short") return (e) => lenM(e);
    if (mode === "fast") return (e) => lenM(e) / 1000 / speed(e);
    // expected wait at a junction on a major road: 80 % chance of 30 s, as in aplicar_peso_rapido_sem
    return (e) => lenM(e) / 1000 / speed(e) + (G.major[to_(e)] ? 0.8 * 30 / 3600 : 0);
  }
  function heuristicFn(mode, t) {
    const tx = G.x[t], ty = G.y[t];
    const straight = (v) => Math.hypot(G.x[v] - tx, G.y[v] - ty);
    if (mode === "short") return straight;
    return (v) => straight(v) / 1000 / G.maxSpeed; // never overestimates the driving time
  }

  function search(s, t, mode, algo) {
    const w = weightFn(mode), h = algo === "astar" ? heuristicFn(mode, t) : () => 0;
    const dist = new Float64Array(G.n).fill(Infinity), prevE = new Int32Array(G.n).fill(-1), done = new Uint8Array(G.n);
    const order = [];
    const heap = new Heap();
    dist[s] = 0;
    heap.push(h(s), s);
    while (heap.size) {
      const u = heap.pop();
      if (done[u]) continue;
      done[u] = 1;
      order.push(u);
      if (u === t) break;
      for (let k = G.outStart[u]; k < G.outStart[u + 1]; k++) {
        const e = G.outIdx[k], v = to_(e);
        if (done[v]) continue;
        const nd = dist[u] + w(e);
        if (nd < dist[v]) { dist[v] = nd; prevE[v] = e; heap.push(nd + h(v), v); }
      }
    }
    const path = [];
    for (let v = t; v !== s; v = from_(prevE[v])) { if (prevE[v] < 0) return null; path.push(prevE[v]); }
    path.reverse();
    return { order, path, cost: dist[t] };
  }

  // ------------------------------------------------------------------ directions (after gps.instrucciones)

  const bearing = (a, b) => (Math.atan2(b[0] - a[0], b[1] - a[1]) * 180 / Math.PI + 360) % 360;
  function turnWord(d) {
    if (Math.abs(d) < 25) return ["↑", "Continue"];
    if (Math.abs(d) > 150) return ["↶", "Make a U-turn"];
    return d > 0 ? ["→", Math.abs(d) < 60 ? "Bear right" : "Turn right"] : ["←", Math.abs(d) < 60 ? "Bear left" : "Turn left"];
  }
  function directions(path) {
    const steps = [];
    let i = 0;
    while (i < path.length) {
      const name = nameOf(path[i]);
      let j = i, d = 0;
      while (j < path.length && nameOf(path[j]) === name) { d += lenM(path[j]); j++; }
      steps.push({ name: name || "an unnamed street", first: path[i], last: path[j - 1], dist: d });
      i = j;
    }
    // drop very short unnamed connectors, they only clutter the list
    const kept = steps.filter((s, k) => k === 0 || k === steps.length - 1 || s.dist > 25 || s.name !== "an unnamed street");
    return kept.map((s, k) => {
      if (k === 0) return { icon: "A", text: `Start on <strong>${esc(s.name)}</strong>`, dist: s.dist };
      const a = edgePoints(kept[k - 1].last), b = edgePoints(s.first);
      const d = ((bearing(b[0], b[1]) - bearing(a[a.length - 2], a[a.length - 1]) + 540) % 360) - 180;
      const [icon, word] = turnWord(d);
      return { icon, text: `${word} onto <strong>${esc(s.name)}</strong>`, dist: s.dist };
    });
  }
  const esc = (s) => s.replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const fmtDist = (m) => (m < 1000 ? `${Math.round(m / 10) * 10} m` : `${(m / 1000).toFixed(1)} km`);

  // ------------------------------------------------------------------ drawing

  const canvas = $("map"), ctx = canvas.getContext("2d");
  const base = document.createElement("canvas"), flood = document.createElement("canvas");
  const view = { s: 1, ox: 0, oy: 0, W: 0, H: 0, dpr: 1 };
  const state = { a: null, b: null, mode: "fast", algo: "dijkstra", result: null, shown: 0, anim: 0, clickNext: "a" };

  const sx = (x) => x * view.s + view.ox, sy = (y) => view.H - (y * view.s + view.oy);

  function resize() {
    const r = canvas.getBoundingClientRect();
    view.dpr = Math.min(window.devicePixelRatio || 1, 2);
    const W = Math.round(r.width * view.dpr), H = Math.round(r.height * view.dpr);
    const first = !view.W;
    [canvas, base, flood].forEach((c) => { c.width = W; c.height = H; });
    view.W = W; view.H = H;
    if (first && G) fitTo(0, 0, G.x.reduce((a, b) => Math.max(a, b), 0), G.y.reduce((a, b) => Math.max(a, b), 0));
    redrawAll();
  }
  function fitTo(x0, y0, x1, y1) {
    const pad = 30 * view.dpr;
    view.s = Math.min((view.W - 2 * pad) / (x1 - x0), (view.H - 2 * pad) / (y1 - y0));
    view.ox = pad - x0 * view.s + ((view.W - 2 * pad) - (x1 - x0) * view.s) / 2;
    view.oy = pad - y0 * view.s + ((view.H - 2 * pad) - (y1 - y0) * view.s) / 2;
  }

  function strokeEdge(c, e) {
    const pts = edgePoints(e);
    c.moveTo(sx(pts[0][0]), sy(pts[0][1]));
    for (let k = 1; k < pts.length; k++) c.lineTo(sx(pts[k][0]), sy(pts[k][1]));
  }

  function drawBase() {
    const c = base.getContext("2d");
    c.clearRect(0, 0, view.W, view.H);
    c.lineCap = "round"; c.lineJoin = "round";
    const zoomW = Math.max(0.6, Math.min(2.2, view.s * 1.2));
    for (const pass of [0, 1]) {
      c.beginPath();
      for (let e = 0; e < G.m; e++) {
        const u = from_(e), v = to_(e);
        // draw each two-way street once
        if (u > v && hasEdge(v, u)) continue;
        if (G.majorHw.has(G.E[8 * e + 5]) !== (pass === 1)) continue;
        strokeEdge(c, e);
      }
      c.strokeStyle = pass ? BLUE : "rgba(0,120,191,0.55)";
      c.lineWidth = (pass ? 2.1 : 0.9) * zoomW * view.dpr;
      c.stroke();
    }
  }
  function hasEdge(u, v) {
    for (let k = G.outStart[u]; k < G.outStart[u + 1]; k++) if (to_(G.outIdx[k]) === v) return true;
    return false;
  }

  // Paint the outgoing streets of settled intersections from index i0 to i1.
  function drawFlood(i0, i1) {
    const c = flood.getContext("2d");
    if (i0 === 0) c.clearRect(0, 0, view.W, view.H);
    if (!state.result) return;
    c.lineCap = "round";
    c.beginPath();
    const order = state.result.order;
    for (let i = i0; i < i1; i++) {
      const u = order[i];
      for (let k = G.outStart[u]; k < G.outStart[u + 1]; k++) strokeEdge(c, G.outIdx[k]);
    }
    c.strokeStyle = "rgba(255,72,176,0.85)";
    c.lineWidth = Math.max(1.6, Math.min(3.2, view.s * 1.6)) * view.dpr;
    c.stroke();
  }

  function composite() {
    ctx.clearRect(0, 0, view.W, view.H);
    ctx.drawImage(base, 0, 0);
    ctx.globalCompositeOperation = "multiply";
    ctx.drawImage(flood, 0, 0);
    ctx.globalCompositeOperation = "source-over";
    const r = state.result;
    if (r && r.path && state.shown >= r.order.length) {
      ctx.lineCap = "round"; ctx.lineJoin = "round";
      for (const [col, w, off] of [[INK, 9, 0], [PINK, 5.5, 0]]) {
        ctx.beginPath();
        r.path.forEach((e) => strokeEdge(ctx, e));
        ctx.strokeStyle = col; ctx.lineWidth = w * view.dpr;
        ctx.stroke();
      }
    }
    pin(state.a, "A", BLUE, "#f4f5f1");
    pin(state.b, "B", PINK, INK);
  }
  function pin(node, label, fill, text) {
    if (node == null) return;
    const X = sx(G.x[node]), Y = sy(G.y[node]), R = 13 * view.dpr;
    ctx.beginPath(); ctx.arc(X, Y, R, 0, Math.PI * 2);
    ctx.fillStyle = fill; ctx.fill();
    ctx.lineWidth = 2.5 * view.dpr; ctx.strokeStyle = INK; ctx.stroke();
    ctx.fillStyle = text;
    ctx.font = `800 ${14 * view.dpr}px "Bricolage Grotesque", sans-serif`;
    ctx.textAlign = "center"; ctx.textBaseline = "middle";
    ctx.fillText(label, X, Y + 1);
  }

  function redrawAll() {
    if (!G) return;
    drawBase();
    drawFlood(0, state.result ? state.shown : 0);
    composite();
  }

  // ------------------------------------------------------------------ interaction

  function runRoute() {
    if (state.a == null || state.b == null) return;
    cancelAnimationFrame(state.anim);
    const t0 = performance.now();
    const r = search(state.a, state.b, state.mode, state.algo);
    const ms = performance.now() - t0;
    const other = search(state.a, state.b, state.mode, state.algo === "astar" ? "dijkstra" : "astar");
    state.result = r;
    state.shown = 0;
    drawFlood(0, 0);
    showNumbers(r, other, ms);
    const perFrame = reduceMotion ? r.order.length : Math.max(25, Math.ceil(r.order.length / 150));
    const step = () => {
      const next = Math.min(r.order.length, state.shown + perFrame);
      drawFlood(state.shown, next);
      state.shown = next;
      composite();
      $("nExplored").textContent = next.toLocaleString("en-US");
      if (next < r.order.length) state.anim = requestAnimationFrame(step);
      else showDirections(r);
    };
    $("directions").innerHTML = "";
    step();
  }

  function routeStats(r) {
    let m = 0, h = 0;
    r.path.forEach((e) => { m += lenM(e); h += lenM(e) / 1000 / speed(e) + (state.mode === "junction" && G.major[to_(e)] ? 0.8 * 30 / 3600 : 0); });
    return { m, min: h * 60 };
  }
  function showNumbers(r, other, ms) {
    $("numbers").hidden = false;
    const st = routeStats(r);
    $("nDist").textContent = fmtDist(st.m);
    $("nTime").textContent = `${Math.max(1, Math.round(st.min))} min`;
    const mine = r.order.length, theirs = other.order.length;
    const astar = state.algo === "astar";
    const [a, d] = astar ? [mine, theirs] : [theirs, mine];
    $("compare").hidden = false;
    $("compare").innerHTML = astar
      ? `A* settled <strong>${a.toLocaleString("en-US")}</strong> intersections; Dijkstra would have needed ${d.toLocaleString("en-US")}, ${(d / a).toFixed(1)}× as many, for the same route.`
      : `Dijkstra settled <strong>${d.toLocaleString("en-US")}</strong> intersections. Switch to A* and it finds the same route after ${a.toLocaleString("en-US")}.`;
  }
  function showDirections(r) {
    const list = directions(r.path);
    list.push({ icon: "B", text: `Arrive at <strong>${esc(labelOf(state.b, "b"))}</strong>`, dist: null });
    $("directions").innerHTML = list.map((s) => `<li><span class="turn">${s.icon}</span><span>${s.text}</span><span class="dist">${s.dist != null ? fmtDist(s.dist) : ""}</span></li>`).join("");
  }
  function labelOf(node, which) {
    const sel = $(which === "a" ? "from" : "to");
    const opt = sel.options[sel.selectedIndex];
    return opt && opt.value !== "map" ? opt.textContent : "your point on the map";
  }

  function setPressed(groupId, attr, val) {
    document.querySelectorAll(`#${groupId} button`).forEach((b) => b.setAttribute("aria-pressed", String(b.dataset[attr] === val)));
  }

  function bind() {
    const fill = (sel, def) => {
      PLACES.forEach(([name], i) => { const o = document.createElement("option"); o.value = i; o.textContent = name; sel.appendChild(o); });
      const o = document.createElement("option"); o.value = "map"; o.textContent = "Point on the map"; o.disabled = true; sel.appendChild(o);
      sel.value = def;
    };
    fill($("from"), 0); fill($("to"), 1);
    const place = (i) => nearestNode(PLACES[i][1], PLACES[i][2]);
    state.a = place(0); state.b = place(1);
    $("from").addEventListener("change", (e) => { state.a = place(+e.target.value); runRoute(); });
    $("to").addEventListener("change", (e) => { state.b = place(+e.target.value); runRoute(); });
    document.querySelectorAll("#modes button").forEach((b) => b.addEventListener("click", () => { state.mode = b.dataset.mode; setPressed("modes", "mode", state.mode); runRoute(); }));
    document.querySelectorAll("#algos button").forEach((b) => b.addEventListener("click", () => { state.algo = b.dataset.algo; setPressed("algos", "algo", state.algo); runRoute(); }));
    $("go").addEventListener("click", runRoute);

    // pan, zoom and click-to-place
    let drag = null, moved = false;
    canvas.addEventListener("pointerdown", (e) => { drag = { x: e.clientX, y: e.clientY, ox: view.ox, oy: view.oy }; moved = false; canvas.setPointerCapture(e.pointerId); });
    canvas.addEventListener("pointermove", (e) => {
      if (!drag) return;
      const dx = (e.clientX - drag.x) * view.dpr, dy = (e.clientY - drag.y) * view.dpr;
      if (Math.abs(dx) + Math.abs(dy) > 4) moved = true;
      if (moved) { view.ox = drag.ox + dx; view.oy = drag.oy - dy; composeFast(); }
    });
    canvas.addEventListener("pointerup", (e) => {
      if (drag && moved) redrawAll();
      else if (drag) placeAt(e);
      drag = null;
    });
    canvas.addEventListener("wheel", (e) => { e.preventDefault(); zoomAt(e.clientX, e.clientY, e.deltaY < 0 ? 1.25 : 0.8); }, { passive: false });
    $("zoomIn").addEventListener("click", () => zoomCenter(1.4));
    $("zoomOut").addEventListener("click", () => zoomCenter(1 / 1.4));
    new ResizeObserver(resize).observe(canvas);
  }
  let fastTimer = 0;
  function composeFast() {
    // while dragging, shift the cached layers instead of redrawing 20,000 streets
    cancelAnimationFrame(fastTimer);
    fastTimer = requestAnimationFrame(() => { drawBase(); drawFlood(0, state.result ? state.shown : 0); composite(); });
  }
  function zoomAt(cx, cy, f) {
    const r = canvas.getBoundingClientRect();
    const px = (cx - r.left) * view.dpr, py = (cy - r.top) * view.dpr;
    const wx = (px - view.ox) / view.s, wy = (view.H - py - view.oy) / view.s;
    view.s = Math.max(0.03, Math.min(3, view.s * f));
    view.ox = px - wx * view.s;
    view.oy = view.H - py - wy * view.s;
    redrawAll();
  }
  function zoomCenter(f) { const r = canvas.getBoundingClientRect(); zoomAt(r.left + r.width / 2, r.top + r.height / 2, f); }
  function placeAt(e) {
    const r = canvas.getBoundingClientRect();
    const px = (e.clientX - r.left) * view.dpr, py = (e.clientY - r.top) * view.dpr;
    const wx = (px - view.ox) / view.s, wy = (view.H - py - view.oy) / view.s;
    const node = nearestXY(wx, wy);
    if (state.clickNext === "a") { state.a = node; $("from").value = "map"; state.clickNext = "b"; state.b = null; state.result = null; drawFlood(0, 0); composite(); $("hint").textContent = "Now click where you want to go."; }
    else { state.b = node; $("to").value = "map"; state.clickNext = "a"; $("hint").textContent = "Click again to start a new route."; runRoute(); }
  }

  fetch("web/madrid.json").then((r) => r.json()).then((d) => {
    loadGraph(d);
    bind();
    resize();
    const go = $("go");
    go.disabled = false;
    go.textContent = "Find the route";
    if (!reduceMotion) setTimeout(runRoute, 400); else runRoute();
  }).catch((err) => { $("go").textContent = "Could not load the map"; console.error(err); });
})();
