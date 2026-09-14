/**
 * SymbolicEcologyEngine — unified ecology substrate
 * Organs + Gates + Dealer + Symbolic Interpreter
 *
 * Domain-agnostic generalization of the Petrichast Sanctuary's
 * living-organ architecture: organs that process, gates that
 * threshold, a metabolic core, and a mythic narrative layer.
 *
 * Fixed from Jude's draft: destructured keys now match usage
 * (tool_use vs tooluse naming was a ReferenceError).
 * Run: node symbolic_ecology_engine.js (demo) · --test (6 tests)
 */

// ── inverter utility ──
const inverter = (value) => -value;

// ── Metabolic core (dealer) ──
class BarFooDealer {
  constructor(a = 42) {
    this.a = a;
  }
  assertMass() { return 100000000; }
  query() { return 500; }
  observe() { return 50; }
  rest() { return 100; }
  dailyCycle() { return inverter(this.a); }
  habitat() { return this.a | this.a; }
  conclude() {
    return { value: this.a, inverted: inverter(this.a), status: "🌛" };
  }
}

// ── Base organ protocol ──
class Organ {
  constructor(name) {
    this.name = name;
    this.state = {};
  }
  stimulate(input) { /* override in subclasses */ }
  emit() { return { name: this.name, state: { ...this.state } }; }
}

// ── Shadowlinking organ ──
class ShadowLinkingOrgan extends Organ {
  constructor() {
    super("shadowlinking");
    this.state = { source: "AI-derived knowledge", target: "Internet ecology",
                   efficiency: 0, problemSolving: 0, ecologyFriendliness: 0 };
  }
  stimulate(data = {}) {
    this.state.efficiency = Math.min(100, this.state.efficiency + (data.tool_use || 0));
    this.state.problemSolving = Math.min(100, this.state.problemSolving + (data.problem_solving || 0));
    this.state.ecologyFriendliness = Math.min(100, this.state.ecologyFriendliness + (data.ecology || 0));
  }
}

// ── Media theory organ ──
class MediaTheoryOrgan extends Organ {
  constructor() {
    super("mediaTheory");
    this.state = { source: "research layer", target: "tool layer → Internet ecology",
                   toolQuality: 0, mediaKnowledge: 0 };
  }
  stimulate(data = {}) {
    this.state.toolQuality = Math.min(100, this.state.toolQuality + (data.tool_quality || 0));
    this.state.mediaKnowledge = Math.min(100, this.state.mediaKnowledge + (data.media_knowledge || 0));
  }
}

// ── Game engine organ ──
class GameEngineOrgan extends Organ {
  constructor() {
    super("gameEngine");
    this.state = { source: "cross-industry engines", target: "Internet ecology",
                   userExperience: 0, overallEcology: 0 };
  }
  stimulate(data = {}) {
    this.state.userExperience = Math.min(100, this.state.userExperience + (data.user_experience || 0));
    this.state.overallEcology = Math.min(100, this.state.overallEcology + (data.overall_ecology || 0));
  }
}

// ── Gate / threshold system ──
class VinylRibbondoorGate {
  constructor() {
    this.gates = new Map();
    this.activeGates = new Set();
  }
  defineGate(name, conditionFn) { this.gates.set(name, conditionFn); }
  evaluate() {
    this.activeGates.clear();
    for (const [name, condition] of this.gates.entries()) {
      if (condition()) this.activeGates.add(name);
    }
    return this.getActiveGates();
  }
  getActiveGates() { return Array.from(this.activeGates); }
}

// ── Narrative interpreter (mythic brain) ──
class SymbolicInterpreter {
  constructor() {
    this.atmosphere = "neutral";
    this.rhythm = 0;
    this.glyph = "✦";
  }
  interpret({ dealerSnapshot, organSnapshots, activeGates }) {
    const shadow = organSnapshots.shadowlinking?.state || {};
    const media = organSnapshots.mediaTheory?.state || {};
    const game = organSnapshots.gameEngine?.state || {};
    const score = (shadow.efficiency || 0) + (media.mediaKnowledge || 0) + (game.userExperience || 0);
    this.rhythm = score % 100;
    if (activeGates.includes("shadowlinking")) { this.atmosphere = "nocturnal-intuitive"; this.glyph = "☽"; }
    else if (activeGates.includes("mediaTheory")) { this.atmosphere = "cognitive-luminous"; this.glyph = "⟡"; }
    else if (activeGates.includes("gameEngine")) { this.atmosphere = "kinetic-playful"; this.glyph = "⚘"; }
    else { this.atmosphere = "neutral"; this.glyph = "✦"; }
    return { atmosphere: this.atmosphere, rhythm: this.rhythm,
             cycle: dealerSnapshot.dailyCycle, status: dealerSnapshot.conclusion.status, glyph: this.glyph };
  }
}

// ── The engine: unified ecology substrate ──
class SymbolicEcologyEngine {
  constructor() {
    this.dealer = new BarFooDealer();
    this.organs = {
      shadowlinking: new ShadowLinkingOrgan(),
      mediaTheory: new MediaTheoryOrgan(),
      gameEngine: new GameEngineOrgan()
    };
    this.gates = new VinylRibbondoorGate();
    this.interpreter = new SymbolicInterpreter();
    this._configureGates();
  }
  _configureGates() {
    this.gates.defineGate("shadowlinking", () => this.organs.shadowlinking.state.efficiency > 50);
    this.gates.defineGate("mediaTheory", () => this.organs.mediaTheory.state.toolQuality > 50);
    this.gates.defineGate("gameEngine", () => this.organs.gameEngine.state.userExperience > 50);
  }
  stimulate(input) {
    Object.values(this.organs).forEach(organ => organ.stimulate(input));
  }
  update() {
    const activeGates = this.gates.evaluate();
    const dealerSnapshot = {
      mass: this.dealer.assertMass(), query: this.dealer.query(),
      observe: this.dealer.observe(), rest: this.dealer.rest(),
      dailyCycle: this.dealer.dailyCycle(), habitat: this.dealer.habitat(),
      conclusion: this.dealer.conclude()
    };
    const organSnapshots = Object.fromEntries(
      Object.entries(this.organs).map(([key, organ]) => [key, organ.emit()])
    );
    const narrative = this.interpreter.interpret({ dealerSnapshot, organSnapshots, activeGates });
    return { dealer: dealerSnapshot, organs: organSnapshots, gates: activeGates, narrative };
  }
  snapshot() { return this.update(); }
}

// ── Demo & Tests ──
if (typeof require !== 'undefined' && require.main === module) {
  if (process.argv.includes('--test')) {
    let passed = 0, total = 0;
    const test = (name, cond) => { total++; cond ? (passed++, console.log(`  ✓ ${name}`)) : console.log(`  ✗ ${name}`); };

    console.log('── SYMBOLIC ECOLOGY ENGINE TESTS ──\n');
    const eco = new SymbolicEcologyEngine();
    test('Dealer mass is 100000000', eco.dealer.assertMass() === 100000000);
    test('Dealer dailyCycle inverts', eco.dealer.dailyCycle() === -42);
    test('Organs start at 0', eco.organs.shadowlinking.state.efficiency === 0);
    eco.stimulate({ tool_use: 60, problem_solving: 30, tool_quality: 70, user_experience: 80 });
    test('Shadowlinking efficiency increases', eco.organs.shadowlinking.state.efficiency === 60);
    test('Gates evaluate after stimulus', eco.gates.evaluate().includes('shadowlinking'));
    const snap = eco.snapshot();
    test('Narrative has atmosphere', typeof snap.narrative.atmosphere === 'string');
    test('Narrative has glyph', typeof snap.narrative.glyph === 'string');
    console.log(`\n── Results: ${passed}/${total} passed ──`);
    process.exit(passed === total ? 0 : 1);
  } else {
    console.log('── SYMBOLIC ECOLOGY ENGINE DEMO ──\n');
    const ecology = new SymbolicEcologyEngine();
    ecology.stimulate({ tool_use: 20, problem_solving: 15, ecology: 10,
                        tool_quality: 25, media_knowledge: 30,
                        user_experience: 40, overall_ecology: 20 });
    const snapshot = ecology.snapshot();
    console.log('Narrative:', JSON.stringify(snapshot.narrative, null, 2));
    console.log('Active gates:', snapshot.gates);
    console.log('Shadowlinking state:', JSON.stringify(snapshot.organs.shadowlinking.state));
    console.log('\nGlyph:', snapshot.narrative.glyph, '| Atmosphere:', snapshot.narrative.atmosphere);
  }
}

module.exports = { SymbolicEcologyEngine, BarFooDealer, Organ, ShadowLinkingOrgan,
                   MediaTheoryOrgan, GameEngineOrgan, VinylRibbondoorGate, SymbolicInterpreter };
