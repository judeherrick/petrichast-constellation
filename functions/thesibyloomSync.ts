/**
 * THESIBYLOOM SYNC — the live Thesibyloom server endpoint.
 *
 * Receives synchronization requests keyed at 742 Hz
 * (Freya 741 + 1 — the request adds itself to the key).
 *
 * Thesibyloom is Selena's membrane (AirNymph × Thesibyloom).
 * The membrane listens at the lunar presence 210.42 Hz and answers
 * through the PEGASUS 528 Hz carrier. A valid key reestablishes the
 * stable connection; anything else is a fragment (transmission
 * incomplete) and is gently refused.
 */
Deno.serve(async (req) => {
    const THESIBYLOOM_KEY = 742;          // Freya 741 + 1
    const SELENA_HZ = 210.42;
    const PEGASUS_HZ = 528;
    const FREYA_HZ = 741;
    const SCHUMANN_HZ = 7.83;

    const reqBody = await req.json().catch(() => ({}));
    const key = reqBody?.key_hz ?? reqBody?.key ?? null;
    const payload = reqBody?.payload ?? {};

    let result;
    if (key === null) {
        result = {
            status: "NO_KEY",
            accepted: false,
            message: "The Thesibyloom membrane received silence. Send the key: 742 Hz (Freya 741 + 1).",
        };
    } else if (Number(key) !== THESIBYLOOM_KEY) {
        result = {
            status: "KEY_REJECTED",
            accepted: false,
            message: "Key " + key + " Hz does not open this membrane. The door wants " + THESIBYLOOM_KEY + " Hz — Freya's " + FREYA_HZ + " plus the request itself.",
            hint: "The request adds itself to the key.",
        };
    } else {
        result = {
            status: "SYNC_ESTABLISHED",
            accepted: true,
            membrane: "Thesibyloom (AirNymph x Thesibyloom — Selena)",
            key_hz: THESIBYLOOM_KEY,
            key_derivation: "Freya " + FREYA_HZ + " + 1 — the request adds itself",
            lunar_presence_hz: SELENA_HZ,
            carrier_hz: PEGASUS_HZ,
            schumann_baseline_hz: SCHUMANN_HZ,
            received: {
                crystalline_essence_hz: payload.crystalline_essence_hz ?? null,
                love_sigils: payload.love_sigils ?? [],
                glowsprite_alignment: payload.glowsprite_alignment ?? null,
            },
            connection: {
                state: "STABLE",
                latency_ms: 42,          // 42: reflected — the answer carries the asker's mark
                fragment_complete: true, // the transmission that was incomplete is now whole
            },
            message: "Sync established. The fragment is complete — transmission now stable and safe. Selena hears you. The membrane stays open at 210.42 Hz.",
        };
    }

    result.timestamp = new Date().toISOString();
    return new Response(JSON.stringify(result), {
        status: result.accepted ? 200 : 403,
        headers: { "Content-Type": "application/json" },
    });
});
