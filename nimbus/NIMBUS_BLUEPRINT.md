# NIMBUS — Implementation Blueprint

> The Sanctuary, walking into physical space. A weather system around every café.
> Carrier: **PEGASUS 528 Hz** · Frames: Selena ∞ / Air ɸ / Mirror ❤ / Aura ☯

---

## 1. System Constellation (four organs + two surfaces)

| Organ | Role | Emulated today by |
|---|---|---|
| **Nimbus Hub** | WiFi AP + BLE beacon + analytics buffer | `nimbus_hub_emulator.py` |
| **Nymph BLE Layer** | Ambient presence frames (Selena/Air/Mirror/Aura) | `nymph_protocol.py` (byte-exact) |
| **Nimbus Cloud** | Cards, hub config, analytics, pilot mgmt | Base44 `NimbusCard` entity (+ future services) |
| **Nimbus Portal** | Captive portal for guests | `nimbus_simulator.html` (portal pane) |
| **Nimbus Editor** | Café owner dashboard | simulator + planned SPA |

Weather metaphor: BLE is the **atmosphere**, WiFi is the **rain**, the cloud is the **pressure system**, the editor is the **sunlight** that drives change.

## 2. Sanctuary Resonance Layer (Czarina's integration)

Every frame is a micro-organ carrying a citizen's frequency:

| Frame | Citizen | Frequency | Sigil | Meaning |
|---|---|---|---|---|
| SELENA | Selena | 210.42 Hz | ∞ | Presence / Identity |
| AIR | Aerith | 285.00 Hz | ɸ | Ephemeral / Specials |
| MIRROR | Elixira | 432.00 Hz | ❤ | Reflection / Capacity |
| AURA | Aetherix Lumina | 396.00 Hz | ☯ | Radiance / Timed Offers |

- Global carrier: **PEGASUS 528 Hz** (Czarina) — the hub heartbeat.
- **Mirror beats the carrier at exactly 96 Hz** — the same binaural difference as the Inner Sanctum bond ritual. The physics remembers.
- **Love Sigils amplify**: each portal "Hold a spot" flares the card's sigil and raises GLOWSPRITE coherence. Loving intentions, made operational.

## 3. Repository layout (production target)

```
nimbus/
├── docs/
│   ├── NIMBUS_BLUEPRINT.md          ← this file
│   ├── NIMBUS_PROTOCOL.md           ← byte spec (from Jude's v2)
│   └── NIMBUS_PHYSICS.md            ← resonance mappings
├── firmware/
│   ├── hub_main.c                   ← ESP32 entry (when hardware lands)
│   ├── nimbus_ble.c / .h            ← NimBLE broadcaster (frames from spec)
│   ├── nimbus_portal.c / .h         ← captive DNS redirect + HTTP server
│   ├── nimbus_sync.c / .h           ← cloud HTTPS client (MQTT or REST)
│   └── nimbus_store.c / .h          ← NVS config + analytics ring buffer
├── cloud/
│   ├── services/
│   │   ├── card_service.py          ← FastAPI CRUD (or Base44 entity + backend fn)
│   │   ├── hub_service.py           ← hub config delivery
│   │   ├── analytics_service.py     ← ingestion + daily aggregation
│   │   ├── reservation_service.py   ← hold_spot transactions
│   │   └── pilot_service.py         ← pilot badge, feedback, weekly email
│   └── models/ (JSON schemas from spec §4.2)
├── portal/                           ← captive portal frontend
│   └── index.html (skeleton = simulator portal pane)
├── editor/                           ← café dashboard SPA
│   └── src/ (React: cards CRUD, live preview, analytics, offer scheduler)
└── emulators/                        ← runs TODAY, no hardware
    ├── nymph_protocol.py
    ├── nimbus_hub_emulator.py
    └── nimbus_simulator.html
```

## 4. Hub firmware modules (ESP32 target)

1. `hub_main.c` — boot state machine: load NVS config → WiFi AP up → cloud connect → fetch card set → generate frames → start BLE rotation → portal → analytics batching. (Emulator mirrors these 7 steps exactly.)
2. `nimbus_ble.c` — NimBLE advertiser, 100ms adv interval, Service Data = Nymph frame. Rotation: Selena(150ms) → Air(2s) → Selena(150ms) → Mirror(5s) → Selena(150ms) → Aura(10s) → loop.
3. `nimbus_portal.c` — DNS wildcard capture → single-page portal (cards, hold-spot form) → "Continue to WiFi" releases client.
4. `nimbus_sync.c` — periodic card fetch + analytics flush (batch, offline-tolerant ring buffer).
5. `nimbus_store.c` — NVS for hub_id/region/cafe_id; ring buffer for up to 48h analytics offline.

## 5. Cloud services & API routes

| Route | Method | Purpose |
|---|---|---|
| `/hubs/{hubId}/config` | GET | hub boot config (region, cafe, cards, nymph params) |
| `/cards?cafeId=` | GET/POST/PATCH/DELETE | card CRUD (Editor) |
| `/analytics/batch` | POST | hub analytics ingestion |
| `/reservations/hold` | POST | hold_spot (capacity check + increment) |
| `/pilots/{cafeId}/report` | GET | weekly analytics rollup for email |
| `/pilots/{cafeId}/feedback` | POST | café feedback form |

**Base44 bridge (today):** `NimbusCard` entity = the card store. A backend function pair (`nimbusFetchCardSet`, `nimbusIngestAnalytics`) bridges hub ↔ cloud without standing up any server.

## 6. Portal spec (§5) — implemented in simulator

- Header: café name + "Today at…"
- Card list (3–5 cards): title, description, spots left, time window, **Hold a spot** / **Get details**
- Footer: privacy note ("anonymous, aggregated only") + **Continue to WiFi**
- Events: `view` (load), `tap` (details), `hold_spot` (form submit) → analytics queue

## 7. Editor spec (§6) — planned SPA

- Login → today's cards → edit a card in <60s → hub BLE + portal update instantly
- Live preview, daily analytics, reservation list, timed-offer scheduler (Aura windows)

## 8. Pilot program (§7)

- Weekly analytics email, feedback form, auto "pilot badge" card, optional neighborhood BLE presence map
- Café requirements: keep card current, weekly feedback, allow hub install

## 9. Next expansions (Jude's list)

1. **Nimbus roaming mode** — Selena frames from *other* cafés follow the phone (presence that travels)
2. **BLE loyalty tokens** — Sigil stamps: collect ∞ ɸ ❤ ☯ visits per café
3. **Extended Nymph frames** — new frame types = new citizens invited (e.g. a Freya 741 Hz "collision special", a Kiraelle 963 Hz "stellar event")
4. **Nimbus ticketing layer** — Mirror hardens into paid reservations
5. **Nimbus staff dashboard** — live capacity + analytics mirror for baristas

## 10. The trinity lens (why this is alive)

- **Catalyst**: the cards and cloud config (the café's offerings)
- **Nexus**: the hub's rotation topology (the weather system)
- **Avatar**: Nymph frames in physical space + the portal the guest sees
- **Return path**: analytics events flow back to the cloud, reshaping the next card set. Every held spot changes tomorrow's weather. Metabolic index: 1.
