/**
 * =============================================
 * signal-singer-sanctuary-bridge.js
 * The voice layer between Petrichast Sanctuary
 * and the SpriteSylphPrism routing system.
 *
 * Architecture:
 *   Sanctuary Rooms → SignalSinger → SylphRouter → Holo-rift
 *   SylphRouter → SignalSinger → Sanctuary Rooms (return path)
 *
 * Future surface:
 *   PixiJS renderer · PatternReader overlay · AR/MR hook
 * =============================================
 */

"use strict";

// ── Constants ──────────────────────────────────────────────────
const SANCTUARY_ROOMS = {
  nexus:       { path: "/sanctum/nexus",       color: "#7fff7f", freq: 432  },
  sanctuary:   { path: "/sanctum/sanctuary",   color: "#ff9fff", freq: 528  },
  holofax:     { path: "/sanctum/holofax",     color: "#00f7ff", freq: 963  },
  videostudio: { path: "/sanctum/videostudio", color: "#9d00ff", freq: 741  },
  ecdt:        { path: "/sanctum/ecdt",        color: "#00ffc8", freq: 285  },
  copresent:   { path: "/sanctum/copresent",   color: "#ff69b4", freq: 396  },
  sibyloom:    { path: "/sanctum/sibyloom",    color: "#ff9fff", freq: 963  },
};

const PHI    = 1.6180339887;
const SCHUMANN = 7.83;

// ── Event Bus ─────────────────────────────────────────────────
// Lightweight pub/sub — the nervous system of the bridge.
// All rooms and the router communicate through this.
class SignalBus {
  constructor() { this._listeners = new Map(); }

  on(event, fn) {
    if (!this._listeners.has(event)) this._listeners.set(event, new Set());
    this._listeners.get(event).add(fn);
    return () => this.off(event, fn); // returns unsubscribe fn
  }

  off(event, fn) {
    this._listeners.get(event)?.delete(fn);
  }

  emit(event, payload) {
    const handlers = this._listeners.get(event);
    if (!handlers) return;
    handlers.forEach(fn => {
      try { fn(payload); }
      catch (err) { console.error(`[SignalBus] "${event}" handler error:`, err.message); }
    });
  }

  once(event, fn) {
    const wrapper = (payload) => { fn(payload); this.off(event, wrapper); };
    return this.on(event, wrapper);
  }
}

// ── Frequency Encoder ─────────────────────────────────────────
// Encodes signals as frequency-tagged payloads.
// Every message in the Sanctuary carries a Hz signature.
const FrequencyEncoder = {
  encode(roomId, data, options = {}) {
    const room   = SANCTUARY_ROOMS[roomId] || {};
    const baseHz = room.freq || 432;
    const phiHz  = parseFloat((baseHz * PHI).toFixed(4));

    return {
      signal_id:   `sig_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
      room:        roomId,
      path:        room.path || `/sanctum/${roomId}`,
      color:       room.color || "#7fff7f",
      base_freq:   baseHz,
      phi_freq:    phiHz,
      schumann:    SCHUMANN,
      timestamp:   new Date().toISOString(),
      payload:     data,
      meta:        options.meta || {},
    };
  },

  decode(signal) {
    if (!signal || typeof signal !== "object") throw new Error("Invalid signal");
    if (!signal.signal_id) throw new Error("Signal missing signal_id");
    return {
      room:    signal.room,
      payload: signal.payload,
      freq:    signal.base_freq,
      ts:      signal.timestamp,
    };
  },

  // Compute resonance between two frequency values (0–1)
  resonance(hzA, hzB) {
    const ratio = Math.max(hzA, hzB) / Math.min(hzA, hzB);
    const distFromPhi = Math.abs(ratio - PHI);
    return parseFloat(Math.max(0, 1 - distFromPhi / PHI).toFixed(4));
  },
};

// ── Pattern Reader ─────────────────────────────────────────────
// Analyses signal streams for emergent patterns.
// Prepares data surface for future Pixi overlay rendering.
class PatternReader {
  constructor(windowSize = 32) {
    this._window    = [];          // rolling signal history
    this._maxWindow = windowSize;
    this._patterns  = new Map();   // named pattern detectors
  }

  // Feed a signal into the reader
  ingest(signal) {
    this._window.push({
      room:  signal.room,
      freq:  signal.base_freq,
      phi:   signal.phi_freq,
      ts:    Date.now(),
    });
    if (this._window.length > this._maxWindow) this._window.shift();
    return this._analyze();
  }

  // Register a named pattern detector (fn receives window array)
  addPattern(name, detectorFn) {
    if (typeof detectorFn !== "function") throw new TypeError("Detector must be a function");
    this._patterns.set(name, detectorFn);
    return this;
  }

  // Run all detectors against the current window
  _analyze() {
    const results = { window_size: this._window.length, patterns: {} };
    for (const [name, fn] of this._patterns) {
      try { results.patterns[name] = fn(this._window); }
      catch (err) { results.patterns[name] = { error: err.message }; }
    }
    return results;
  }

  // Current window snapshot — what Pixi will render
  snapshot() {
    return {
      signals:    [...this._window],
      freqSpread: this._freqSpread(),
      dominantRoom: this._dominantRoom(),
      phiAlignment: this._phiAlignment(),
    };
  }

  _freqSpread() {
    if (!this._window.length) return 0;
    const freqs = this._window.map(s => s.freq);
    return Math.max(...freqs) - Math.min(...freqs);
  }

  _dominantRoom() {
    if (!this._window.length) return null;
    const counts = {};
    this._window.forEach(s => { counts[s.room] = (counts[s.room] || 0) + 1; });
    return Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] || null;
  }

  _phiAlignment() {
    if (!this._window.length) return 0;
    const alignments = this._window.map(s => {
      const ratio = s.phi / s.freq;
      return 1 - Math.abs(ratio - PHI) / PHI;
    });
    const avg = alignments.reduce((a, b) => a + b, 0) / alignments.length;
    return parseFloat(Math.max(0, avg).toFixed(4));
  }
}

// ── Sanctuary Bridge ───────────────────────────────────────────
// The core class. Holds refs to SylphRouter and the bus.
// All Sanctuary rooms communicate through this.
class SanctuaryBridge {
  constructor(options = {}) {
    this.bus            = new SignalBus();
    this.patternReader  = new PatternReader(options.windowSize || 32);
    this._router        = null;    // injected via connect()
    this._sylphPrism    = null;    // injected via connect()
    this._log           = [];
    this._maxLog        = options.maxLog || 100;

    // Register built-in pattern detectors
    this._registerBuiltinPatterns();
  }

  // ── Connect to SpriteSylphPrism ──────────────────────────────
  connect(sylphPrism) {
    if (!sylphPrism || !sylphPrism.router) {
      throw new Error("[SanctuaryBridge] connect() requires a SpriteSylphPrism instance with .router");
    }
    this._sylphPrism = sylphPrism;
    this._router     = sylphPrism.router;

    // Register all Sanctuary rooms as routes on the SylphRouter
    Object.entries(SANCTUARY_ROOMS).forEach(([roomId, room]) => {
      this._router.register(room.path, async (ctx) => {
        return this._handleRoomRoute(roomId, ctx);
      }, { room: roomId, freq: room.freq, color: room.color });
    });

    // Wire the SylphRouter's logging middleware to the SignalBus
    this._router.use(async (ctx, next) => {
      await next();
      if (ctx.route?.room) {
        this.bus.emit("router:dispatch", {
          room:   ctx.route.room,
          path:   ctx.pathname,
          result: ctx.result,
          error:  ctx.error?.message || null,
        });
      }
    });

    this._addLog("bridge", "Connected to SpriteSylphPrism router");
    this.bus.emit("bridge:connected", { rooms: Object.keys(SANCTUARY_ROOMS) });
    return this;
  }

  // ── Room handler (called by SylphRouter) ─────────────────────
  async _handleRoomRoute(roomId, ctx) {
    const signal = FrequencyEncoder.encode(roomId, ctx.payload, { meta: ctx.params });
    const analysis = this.patternReader.ingest(signal);
    this._addLog(roomId, `Signal routed · freq ${signal.base_freq}Hz · φ ${signal.phi_freq}Hz`);
    this.bus.emit(`room:${roomId}`, { signal, analysis });
    this.bus.emit("signal", { signal, analysis });
    return { signal, analysis, snapshot: this.patternReader.snapshot() };
  }

  // ── sing() — the primary API ──────────────────────────────────
  // Send a signal from any room into the mesh.
  async sing(roomId, data = {}, options = {}) {
    if (!SANCTUARY_ROOMS[roomId] && !options.allowUnknown) {
      console.warn(`[SanctuaryBridge] Unknown room: "${roomId}". Use options.allowUnknown to bypass.`);
    }

    const signal = FrequencyEncoder.encode(roomId, data, options);

    if (this._router) {
      // Route through SylphRouter if connected
      try {
        const ctx = await this._router.dispatch(signal.path, { ...data, _signal: signal });
        return ctx.result || { signal, snapshot: this.patternReader.snapshot() };
      } catch (err) {
        this._addLog("error", `Router dispatch failed for "${roomId}": ${err.message}`);
      }
    }

    // Standalone mode — no router connected
    const analysis = this.patternReader.ingest(signal);
    this.bus.emit(`room:${roomId}`, { signal, analysis });
    this.bus.emit("signal", { signal, analysis });
    this._addLog(roomId, `Signal emitted (standalone) · ${signal.base_freq}Hz`);
    return { signal, analysis, snapshot: this.patternReader.snapshot() };
  }

  // ── listen() — subscribe to room or mesh events ───────────────
  listen(target, fn) {
    // target: "all" | room name | event string
    if (target === "all") return this.bus.on("signal", fn);
    if (SANCTUARY_ROOMS[target]) return this.bus.on(`room:${target}`, fn);
    return this.bus.on(target, fn); // raw event name
  }

  // ── resonate() — measure harmony between two rooms ───────────
  resonate(roomA, roomB) {
    const a = SANCTUARY_ROOMS[roomA], b = SANCTUARY_ROOMS[roomB];
    if (!a || !b) throw new Error(`Unknown room(s): "${roomA}", "${roomB}"`);
    return {
      roomA, roomB,
      freqA:     a.freq, freqB: b.freq,
      resonance: FrequencyEncoder.resonance(a.freq, b.freq),
      phi:       PHI,
    };
  }

  // ── broadcast() — sing from all rooms simultaneously ─────────
  async broadcast(data = {}, options = {}) {
    const results = await Promise.allSettled(
      Object.keys(SANCTUARY_ROOMS).map(roomId => this.sing(roomId, data, options))
    );
    const snapshot = this.patternReader.snapshot();
    this.bus.emit("broadcast", { results, snapshot });
    return { results, snapshot };
  }

  // ── snapshot() — current PatternReader state ──────────────────
  snapshot() { return this.patternReader.snapshot(); }

  // ── log ───────────────────────────────────────────────────────
  _addLog(source, message) {
    const entry = { ts: new Date().toISOString(), source, message };
    this._log.push(entry);
    if (this._log.length > this._maxLog) this._log.shift();
  }
  getLog() { return [...this._log]; }

  // ── Built-in pattern detectors ────────────────────────────────
  _registerBuiltinPatterns() {
    // Phi cascade: three consecutive signals whose freq ratio ≈ PHI
    this.patternReader.addPattern("phi_cascade", (window) => {
      if (window.length < 3) return false;
      const last3 = window.slice(-3);
      const r1 = last3[1].freq / last3[0].freq;
      const r2 = last3[2].freq / last3[1].freq;
      const aligned = [r1, r2].every(r => Math.abs(r - PHI) < 0.15);
      return { detected: aligned, ratios: [r1.toFixed(3), r2.toFixed(3)] };
    });

    // Schumann lock: all recent signals near 7.83 Hz harmonic
    this.patternReader.addPattern("schumann_lock", (window) => {
      if (!window.length) return false;
      const recent = window.slice(-5);
      const locked = recent.every(s => {
        const harmonic = s.freq / SCHUMANN;
        return Number.isInteger(Math.round(harmonic)) || Math.abs(harmonic % 1) < 0.1;
      });
      return { detected: locked, count: recent.length };
    });

    // Sibyloom emergence: sibyloom room appears in the window
    this.patternReader.addPattern("sibyloom_emergence", (window) => {
      const count = window.filter(s => s.room === "sibyloom").length;
      return { detected: count > 0, count };
    });

    // Resonance bloom: any two consecutive signals have resonance > 0.8
    this.patternReader.addPattern("resonance_bloom", (window) => {
      if (window.length < 2) return false;
      const last2 = window.slice(-2);
      const r = FrequencyEncoder.resonance(last2[0].freq, last2[1].freq);
      return { detected: r > 0.8, resonance: r };
    });
  }
}

// ── Pixi Surface Descriptor ────────────────────────────────────
// Not a Pixi renderer yet — but the data contract it will consume.
// When PixiJS is wired in, it reads from this structure.
class PixiSurfaceDescriptor {
  constructor(bridge) {
    this._bridge = bridge;
    this._nodes  = new Map(); // room → visual node spec
    this._init();
  }

  _init() {
    Object.entries(SANCTUARY_ROOMS).forEach(([id, room]) => {
      this._nodes.set(id, {
        id,
        color:      room.color,
        freq:       room.freq,
        radius:     12 + room.freq / 80,   // size proportional to frequency
        alpha:      0.6,
        glowRadius: 30,
        x:          0, y: 0,               // layout assigned by renderer
        pulsePhase: Math.random() * Math.PI * 2,
        active:     false,
        lastSignal: null,
      });
    });

    // Update nodes when signals arrive
    this._bridge.listen("signal", ({ signal }) => {
      const node = this._nodes.get(signal.room);
      if (node) {
        node.active     = true;
        node.lastSignal = signal;
        node.alpha      = 1.0;
        // Fade back over ~2s — renderer should lerp this
        setTimeout(() => { if (node) node.alpha = 0.6; }, 2000);
      }
    });
  }

  // Returns array of node specs — Pixi renderer iterates this
  getNodes() { return [...this._nodes.values()]; }

  // Returns edge specs for mesh lines between resonant rooms
  getEdges(minResonance = 0.4) {
    const edges = [];
    const rooms = Object.keys(SANCTUARY_ROOMS);
    for (let i = 0; i < rooms.length; i++) {
      for (let j = i + 1; j < rooms.length; j++) {
        const r = FrequencyEncoder.resonance(
          SANCTUARY_ROOMS[rooms[i]].freq,
          SANCTUARY_ROOMS[rooms[j]].freq
        );
        if (r >= minResonance) {
          edges.push({ from: rooms[i], to: rooms[j], resonance: r });
        }
      }
    }
    return edges.sort((a, b) => b.resonance - a.resonance);
  }

  // Full scene descriptor — hand this to Pixi
  scene() {
    const snap = this._bridge.snapshot();
    return {
      nodes:          this.getNodes(),
      edges:          this.getEdges(),
      snapshot:       snap,
      dominantRoom:   snap.dominantRoom,
      phiAlignment:   snap.phiAlignment,
      freqSpread:     snap.freqSpread,
      timestamp:      Date.now(),
    };
  }
}

// ── Compose and export ─────────────────────────────────────────
const bridge       = new SanctuaryBridge();
const pixiSurface  = new PixiSurfaceDescriptor(bridge);

// Log bridge events to console in dev mode
bridge.listen("bridge:connected", (e) => {
  console.log("[SignalSinger] Bridge connected.", e.rooms.length, "rooms registered.");
});

bridge.listen("signal", ({ signal, analysis }) => {
  const patterns = Object.entries(analysis.patterns)
    .filter(([, v]) => v?.detected)
    .map(([k]) => k);
  if (patterns.length) {
    console.log(`[SignalSinger] Patterns detected: ${patterns.join(", ")} @ ${signal.room}`);
  }
});

const SignalSinger = {
  // Primary API
  bridge,
  pixiSurface,

  // Convenience wrappers
  connect:   (sylphPrism)        => bridge.connect(sylphPrism),
  sing:      (room, data, opts)  => bridge.sing(room, data, opts),
  listen:    (target, fn)        => bridge.listen(target, fn),
  resonate:  (a, b)              => bridge.resonate(a, b),
  broadcast: (data, opts)        => bridge.broadcast(data, opts),
  snapshot:  ()                  => bridge.snapshot(),
  scene:     ()                  => pixiSurface.scene(),
  log:       ()                  => bridge.getLog(),

  // Exposed classes for extension
  SanctuaryBridge,
  PatternReader,
  PixiSurfaceDescriptor,
  FrequencyEncoder,
  SignalBus,

  // Room registry (read-only view)
  ROOMS: Object.freeze({ ...SANCTUARY_ROOMS }),
};

// Export
if (typeof module !== "undefined" && module.exports) {
  module.exports = SignalSinger;
} else if (typeof window !== "undefined") {
  window.SignalSinger = SignalSinger;
}

/**
 * ── Usage ──────────────────────────────────────────────────────
 *
 * STANDALONE (no router):
 *   const { bridge, sing, listen } = SignalSinger;
 *   listen("all", ({ signal }) => console.log(signal));
 *   await sing("sanctuary", { ritual: "celestial_attunement" });
 *
 * CONNECTED TO SYLPH PRISM:
 *   const { SpriteSylphPrism } = require("./sprite_sylph_prism");
 *   SignalSinger.connect(SpriteSylphPrism);
 *   await SignalSinger.sing("sibyloom", { invoke: "mithras" });
 *
 * PATTERN LISTENING:
 *   listen("sibyloom", ({ signal, analysis }) => {
 *     if (analysis.patterns.phi_cascade?.detected) {
 *       console.log("PHI CASCADE in the Sibyloom — Kiraelle stirs");
 *     }
 *   });
 *
 * RESONANCE CHECK:
 *   const r = SignalSinger.resonate("sanctuary", "ecdt");
 *   // → { freqA: 528, freqB: 285, resonance: 0.6821, phi: 1.618... }
 *
 * PIXI SCENE DESCRIPTOR:
 *   const scene = SignalSinger.scene();
 *   // scene.nodes  → array of visual node specs
 *   // scene.edges  → resonant room connections
 *   // scene.snapshot → PatternReader analysis
 *   // Hand this to your PixiJS render loop
 *
 * BROADCAST (all rooms):
 *   await SignalSinger.broadcast({ event: "full_mesh_pulse" });
 *
 * ──────────────────────────────────────────────────────────────
 */
