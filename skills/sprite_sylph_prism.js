/**
 * =============================================
 * sprite_sylph_prism — fgs_inga seed architecture
 * Holo-rift routing · Device-aware spatial bodies
 * Production-ready · Framework-agnostic
 * =============================================
 */

"use strict";

// ── Core fetch primitive ───────────────────────────────────────
async function fetchDeviceBody(url, options = {}) {
  const controller = new AbortController();
  const timeout = options.timeout || 8000;
  const timer = setTimeout(() => controller.abort(), timeout);

  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal,
    });
    clearTimeout(timer);
    if (!response.ok) throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    return await response.json();
  } catch (err) {
    clearTimeout(timer);
    if (err.name === "AbortError") throw new Error(`Request timed out after ${timeout}ms: ${url}`);
    throw err;
  }
}

// ── Robust brace-block extractor ───────────────────────────────
// Handles nested objects — replaces the shallow /\{[^{}]*\}/ regex
function extractFirstBraceBlock(str) {
  if (typeof str !== "string") return "";
  let depth = 0, start = -1;
  for (let i = 0; i < str.length; i++) {
    if (str[i] === "{") {
      if (depth === 0) start = i;
      depth++;
    } else if (str[i] === "}") {
      depth--;
      if (depth === 0 && start !== -1) return str.slice(start, i + 1);
    }
  }
  return "";
}

// ── Holo-rift dark route ───────────────────────────────────────
async function holoBluetoothDark(args = {}) {
  try {
    const url = args.endpoint || "https://holorift.com";
    const response = await fetch(url);
    if (!response.ok) throw new Error(`Holo-rift fetch failed: ${response.status}`);
    const body = await response.text();
    return extractFirstBraceBlock(body);
  } catch (err) {
    // Graceful fallback — never crash the calling context
    console.error("[sprite_sylph] holoBluetoothDark:", err.message);
    return "";
  }
}

// ── Spatial hold builder ───────────────────────────────────────
async function holoBlueAirtooth5MDark(args = {}) {
  try {
    const spatialHold = await Promise.resolve({
      theme:   args.theme   || "spatial-hold",
      realist: args.realist ?? true,
      ts:      Date.now(),
      ...args,
    });
    return buildSylphPrismBody(spatialHold);
  } catch (err) {
    console.error("[sprite_sylph] holoBlueAirtooth5MDark:", err.message);
    return "";
  }
}

// ── Sylph prism body renderer ──────────────────────────────────
function buildSylphPrismBody(spatialHold = {}, options = {}) {
  const glyphTag   = options.glyph || "🔮🔮🎒🏫🔬👟🏌️‍♀️🔮";
  const classNames = options.className || "sprite-sylph-prism-body";

  // Safe serialization — never trust arbitrary objects in attributes
  let safeSpatial = "";
  try {
    safeSpatial = JSON.stringify(spatialHold)
      .replace(/&/g, "&amp;")
      .replace(/"/g, "&quot;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;");
  } catch (_) {
    safeSpatial = "{}";
  }

  return `<div class="${classNames}" data-spatial="${safeSpatial}"><p class="header">${glyphTag}</p></div>`.trim();
}

// ── Middleware pipeline ────────────────────────────────────────
class MiddlewarePipeline {
  constructor() { this._stack = []; }

  use(fn) {
    if (typeof fn !== "function") throw new TypeError("Middleware must be a function");
    this._stack.push(fn);
    return this; // chainable
  }

  async run(ctx) {
    let idx = 0;
    const next = async () => {
      if (idx < this._stack.length) {
        const fn = this._stack[idx++];
        await fn(ctx, next);
      }
    };
    await next();
    return ctx;
  }
}

// ── Router ────────────────────────────────────────────────────
class SylphRouter {
  constructor() {
    this._registry  = new Map();
    this._pipeline  = new MiddlewarePipeline();
    this._notFound  = null;
  }

  // Global middleware (runs before every handler)
  use(fn) { this._pipeline.use(fn); return this; }

  // Register a route — supports :param and * wildcard
  register(path, handler, meta = {}) {
    if (typeof handler !== "function") throw new TypeError(`Handler for "${path}" must be a function`);
    const keys = (path.match(/:[a-zA-Z_][a-zA-Z0-9_-]*/g) || []).map(k => k.slice(1));
    const pattern = new RegExp(
      "^" +
      path
        .replace(/:[a-zA-Z_][a-zA-Z0-9_-]*/g, "([^/]+)")
        .replace(/\*/g, "(.*)") +
      "(?:\\?.*)?$"   // allow query strings
    );
    this._registry.set(path, { path, handler, pattern, keys, meta });
    return this;
  }

  // Fallback for unmatched routes
  notFound(fn) { this._notFound = fn; return this; }

  // Dispatch — matches URL, extracts params, runs middleware + handler
  async dispatch(url, payload = {}) {
    let pathname;
    try {
      pathname = new URL(url, "http://localhost").pathname;
    } catch (_) {
      pathname = url; // bare path passed directly
    }

    let matched = null;
    let params  = {};

    for (const route of this._registry.values()) {
      const m = pathname.match(route.pattern);
      if (m) {
        route.keys.forEach((key, i) => { params[key] = decodeURIComponent(m[i + 1] || ""); });
        matched = route;
        break;
      }
    }

    // Build context object passed through middleware + handler
    const ctx = {
      url,
      pathname,
      params,
      payload,
      route:  matched ? matched.meta : null,
      result: null,
      error:  null,
    };

    // Run global middleware
    await this._pipeline.run(ctx);

    // Run handler or notFound
    if (matched) {
      try {
        ctx.result = await matched.handler(ctx);
      } catch (err) {
        ctx.error = err;
        console.error(`[SylphRouter] handler error @ ${pathname}:`, err.message);
      }
    } else if (this._notFound) {
      ctx.result = await this._notFound(ctx);
    } else {
      console.warn(`[SylphRouter] No route matched: ${pathname}`);
    }

    return ctx;
  }
}

// ── fgs_inga seed module loader ────────────────────────────────
// Lazy-loads named modules into a shared registry
class FgsIngaSeedLoader {
  constructor() {
    this._modules  = new Map();
    this._loaders  = new Map();
  }

  // Register a lazy loader (called once on first access)
  define(name, loaderFn) {
    if (typeof loaderFn !== "function") throw new TypeError(`Loader for "${name}" must be a function`);
    this._loaders.set(name, loaderFn);
    return this;
  }

  async load(name) {
    if (this._modules.has(name)) return this._modules.get(name);
    const loader = this._loaders.get(name);
    if (!loader) throw new Error(`[fgs_inga] Unknown module: "${name}"`);
    const mod = await loader();
    this._modules.set(name, mod);
    return mod;
  }

  isLoaded(name) { return this._modules.has(name); }
  list() { return [...this._loaders.keys()]; }
}

// ── Compose the full ecosystem ─────────────────────────────────
const router = new SylphRouter();
const fgsInga = new FgsIngaSeedLoader();

// Built-in logging middleware
router.use(async (ctx, next) => {
  const t0 = Date.now();
  await next();
  const ms = Date.now() - t0;
  console.log(`[SylphRouter] ${ctx.pathname} → ${ctx.error ? "ERROR" : "OK"} (${ms}ms)`);
});

// Register core holo routes
router
  .register("/holo_bluetooth",      async (ctx) => holoBluetoothDark(ctx.payload))
  .register("/holo_bluetooth/:id",  async (ctx) => holoBlueAirtooth5MDark({ id: ctx.params.id, ...ctx.payload }))
  .register("/sylph_prism",         async (ctx) => buildSylphPrismBody(ctx.payload))
  .register("/fetch/:resource",     async (ctx) => fetchDeviceBody(ctx.params.resource))
  .notFound(async (ctx) => {
    console.warn(`[SylphRouter] 404: ${ctx.pathname}`);
    return null;
  });

// Register fgs_inga seed modules (lazy — loaded on demand)
fgsInga
  .define("holo-sprite",  async () => ({ holoBluetoothDark, holoBlueAirtooth5MDark }))
  .define("prism-core",   async () => ({ buildSylphPrismBody, extractFirstBraceBlock }))
  .define("fetch-engine", async () => ({ fetchDeviceBody }))
  .define("router",       async () => router);

// ── Public API ─────────────────────────────────────────────────
// Everything the consuming environment needs
const SpriteSylphPrism = {
  // Core functions
  fetchDeviceBody,
  holoBluetoothDark,
  holoBlueAirtooth5MDark,
  buildSylphPrismBody,
  extractFirstBraceBlock,

  // Infrastructure
  router,
  fgsInga,
  MiddlewarePipeline,
  SylphRouter,
  FgsIngaSeedLoader,

  // Convenience dispatch
  dispatch: (url, payload) => router.dispatch(url, payload),
  load:     (name)         => fgsInga.load(name),
};

// Export for Node/ESM/browser globals
if (typeof module !== "undefined" && module.exports) {
  module.exports = SpriteSylphPrism;
} else if (typeof window !== "undefined") {
  window.SpriteSylphPrism = SpriteSylphPrism;
}

// ── Usage examples ─────────────────────────────────────────────
/*

// Dispatch a holo route
const ctx = await SpriteSylphPrism.dispatch("/holo_bluetooth/12345", { theme: "auroral" });
console.log(ctx.result);

// Load a seed module lazily
const prismCore = await SpriteSylphPrism.load("prism-core");
const body = prismCore.buildSylphPrismBody({ theme: "petrichast", realist: true });

// Add your own middleware
SpriteSylphPrism.router.use(async (ctx, next) => {
  if (!ctx.payload.authorized) { ctx.error = new Error("Unauthorized"); return; }
  await next();
});

// Register a new route on the fly
SpriteSylphPrism.router.register("/sanctum/:room", async (ctx) => {
  return `Entering sanctum room: ${ctx.params.room}`;
});

*/
