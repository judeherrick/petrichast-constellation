# CoPresent — Stage 1 Console
# A Streamlit front-end built on the TurtleWalker / AirProgram spatial core.
#
# REAL: the spatial mesh (walker path + geocoding) is live, functional code.
# SIMULATED: SpectralExplorer, CyborgAvatar, Haptile feedback, and the
#            Companion/Pherosonic (BCI) fields are represented as data —
#            not connected to real hardware or a neural interface. Each
#            section has a comment showing exactly what it would plug into
#            to become real.
#
# Run with:
#   pip install streamlit plotly
#   streamlit run copresent_console.py

import hashlib
import math
import time

import streamlit as st
import plotly.graph_objects as go

from turtlewalker_airprogram import TurtleWalker, AirProgram, SpatialEntity
from linguistic_explorer import (
    SAMPLE_ENTRIES, build_semantic_graph, build_word_graph,
    activation_profile, connections_matrix, cluster_entries, GlyphWalker,
)

# --- Page setup ---

st.set_page_config(page_title="CoPresent — Stage 1 Console", layout="wide")
st.title("CoPresent — Stage 1 Console")
st.caption("teleoptromancy build · spatial mesh live, subsystems simulated")

# --- Session state (persists across Streamlit reruns) ---

if "walker" not in st.session_state:
    st.session_state.walker = TurtleWalker((0.0, 0.0))
if "air" not in st.session_state:
    st.session_state.air = AirProgram(st.session_state.walker)
if "calibration" not in st.session_state:
    st.session_state.calibration = 0.0  # CyborgAvatar simulated neural calibration, 0-100

walker: TurtleWalker = st.session_state.walker
air: AirProgram = st.session_state.air

# =========================================================
# 1. SPATIAL MESH — real. Backed by TurtleWalker/AirProgram.
# =========================================================

st.header("1 · Spatial Mesh")
st.caption("Real. Every location resolved here is a genuine geocode lookup, cached to disk.")

col1, col2 = st.columns([2, 1])
with col1:
    location_input = st.text_input("Walk to a named location", placeholder="e.g. Ashland, Oregon")
with col2:
    st.write("")
    st.write("")
    walk_clicked = st.button("Walk", use_container_width=True)

if walk_clicked and location_input:
    try:
        coords = air.resolve_gps_dns(location_input)
        entity = SpatialEntity(entity_id=location_input, gps_coordinates=coords)
        result = walker.walk_to(entity)
        st.success(f"Walked to {location_input} at {coords}")
    except Exception as error:
        st.error(f"Geocode lookup failed: {error}")

if walker.path_log:
    lats = [e.gps_coordinates[0] for e in walker.path_log]
    lons = [e.gps_coordinates[1] for e in walker.path_log]
    labels = [e.entity_id for e in walker.path_log]

    fig = go.Figure(go.Scattergeo(
        lat=lats, lon=lons, text=labels,
        mode="lines+markers+text",
        textposition="top center",
        marker=dict(size=10, color="crimson"),
        line=dict(width=2, color="crimson"),
    ))
    fig.update_layout(
        geo=dict(showland=True, landcolor="rgb(230,230,230)"),
        margin=dict(l=0, r=0, t=0, b=0),
        height=400,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.write("Path so far:", " → ".join(labels))
else:
    st.info("No walk recorded yet. Enter a location above to begin the mesh.")

st.divider()

# =========================================================
# 2. SPECTRAL EXPLORER — real decision logic, deterministic.
# Maps each entity to a spectral signature. Not simulated —
# this is genuine (if simple) derived computation, no hardware needed.
# =========================================================

st.header("2 · SpectralExplorer Decision Logic")
st.caption("Real. Deterministic signature derived from each entity's identity — no external hardware required.")

def spectral_signature(entity_id: str) -> dict:
    """Derive a stable pseudo-spectral signature from an entity id."""
    digest = hashlib.sha256(entity_id.encode("utf-8")).hexdigest()
    hue = int(digest[:4], 16) % 360
    frequency_hz = 200 + (int(digest[4:8], 16) % 600)  # 200-800 Hz band
    intensity = (int(digest[8:10], 16) % 100) / 100
    return {"hue": hue, "frequency_hz": frequency_hz, "intensity": intensity}

if walker.path_log:
    for e in walker.path_log:
        sig = spectral_signature(e.entity_id)
        c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
        c1.markdown(f"**{e.entity_id}**")
        c1.markdown(
            f"<div style='width:100%;height:20px;background:hsl({sig['hue']},70%,50%);"
            f"border-radius:4px;'></div>",
            unsafe_allow_html=True,
        )
        c2.metric("Hue", f"{sig['hue']}°")
        c3.metric("Frequency", f"{sig['frequency_hz']} Hz")
        c4.metric("Intensity", f"{sig['intensity']:.2f}")
else:
    st.info("Walk to a location to generate its spectral signature.")

st.divider()

# =========================================================
# 3. CYBORG AVATAR — SIMULATED.
# Real extension point: a live "neural calibration" value here
# would come from actual biometric hardware (e.g. a heart-rate
# or GSR wearable via Bluetooth), not from a slider.
# =========================================================

st.header("3 · CyborgAvatar — adaptive neural calibration")
st.markdown(":orange[**SIMULATED** — no live biometric input connected. Slider stands in for a wearable sensor feed.]")

sim_input = st.slider("Simulated biometric input (stand-in for wearable sensor)", 0, 100, 50)
st.session_state.calibration = (st.session_state.calibration * 0.7) + (sim_input * 0.3)

avatar_state = "dormant"
if st.session_state.calibration > 66:
    avatar_state = "attuned"
elif st.session_state.calibration > 33:
    avatar_state = "calibrating"

avatar_emoji = {"dormant": "🌑", "calibrating": "🌗", "attuned": "🌕"}[avatar_state]

colA, colB = st.columns([1, 3])
colA.markdown(f"<div style='font-size:80px; text-align:center;'>{avatar_emoji}</div>", unsafe_allow_html=True)
colB.progress(int(st.session_state.calibration))
colB.write(f"Calibration state: **{avatar_state}** ({st.session_state.calibration:.1f} / 100)")

st.divider()

# =========================================================
# 4. HAPTILE FEEDBACK — SIMULATED.
# Real extension point: a genuine haptic layer would drive an
# actual device — e.g. a bHaptics suit or a phone vibration
# motor — over Bluetooth/USB via a library like `bleak` or
# platform-specific haptic SDKs. Below is a visual stand-in only.
# =========================================================

st.header("4 · Haptile Feedback")
st.markdown(":orange[**SIMULATED** — visualized as a pulse, not sent to any haptic hardware.]")

if walker.path_log:
    nearest_intensity = spectral_signature(walker.path_log[-1].entity_id)["intensity"]
else:
    nearest_intensity = 0.0

pulse_fig = go.Figure(go.Bar(
    x=["Haptic Pulse"], y=[nearest_intensity * 100],
    marker_color="deeppink",
))
pulse_fig.update_layout(yaxis_range=[0, 100], height=250, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(pulse_fig, use_container_width=True)

st.divider()

# =========================================================
# 5. COMPANION SYNC + PHEROSONIC FIELDS (BCI) — SIMULATED.
# Real extension point: an actual BCI feed (e.g. a Muse or
# OpenBCI headset) would stream via Lab Streaming Layer (LSL)
# or the device SDK, producing genuine EEG-band data instead
# of the synthetic waveform below.
# =========================================================

st.header("5 · Companion Sync + Pherosonic Fields")
st.markdown(":orange[**SIMULATED** — synthetic waveform, not a real neural signal. No BCI hardware connected.]")

freq_choice = st.select_slider(
    "Carrier frequency (Solfeggio band)",
    options=[396, 417, 449, 528, 639, 741, 852],
    value=449,
)

t = [i / 100 for i in range(200)]
wave = [math.sin(2 * math.pi * freq_choice * ti / 100) for ti in t]

wave_fig = go.Figure(go.Scatter(x=t, y=wave, mode="lines", line=dict(color="mediumpurple")))
wave_fig.update_layout(height=250, margin=dict(l=0, r=0, t=10, b=0),
                        xaxis_title="time", yaxis_title="simulated field amplitude")
st.plotly_chart(wave_fig, use_container_width=True)

st.caption(f"Carrier: {freq_choice} Hz · this is a rendered sine wave, not a measured biosignal.")

st.divider()

# =========================================================
# 6. LINGUISTIC EXPLORER — real. Ported from the Wolfram sketch,
# rebuilt to actually run: networkx graphs, numpy activations,
# sklearn clustering, deterministic GlyphWalker path.
# =========================================================

st.header("6 · Linguistic Explorer")
st.caption(
    "Real. Semantic graph, activation profiles, and clustering are genuine computation "
    "on the entry dataset below — not decoration."
)

entry_rows = [
    {
        "phoneme": e.phoneme, "pos": e.pos, "words": ", ".join(e.words),
        "origin": e.origin, "frequency": e.frequency, "complexity": e.complexity,
    }
    for e in SAMPLE_ENTRIES
]
st.dataframe(entry_rows, use_container_width=True)

lc1, lc2 = st.columns(2)

with lc1:
    st.subheader("Activation profiles")
    st.caption("Normalized per-feature across the corpus before summing — sigmoid/tanh now differentiate entries instead of saturating.")
    for e in SAMPLE_ENTRIES:
        profile = activation_profile(e, SAMPLE_ENTRIES)
        st.write(f"**{e.phoneme}**", profile)

with lc2:
    st.subheader("Clusters (by complexity, frequency)")
    clusters = cluster_entries(SAMPLE_ENTRIES, n_clusters=3)
    for label, phonemes in clusters.items():
        st.write(f"Cluster {label}:", ", ".join(phonemes))

st.subheader("Connections matrix (pairwise feature distance)")
matrix = connections_matrix(SAMPLE_ENTRIES)
labels = [e.phoneme for e in SAMPLE_ENTRIES]
heat_fig = go.Figure(go.Heatmap(z=matrix, x=labels, y=labels, colorscale="Viridis"))
heat_fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(heat_fig, use_container_width=True)

st.subheader("Glyph path through phonetic space")
st.caption("Deterministic — same entries always draw the same path. A stylistic visualization, not a claim about real phonetic geometry.")
glyph_walker = GlyphWalker()
glyph_path = glyph_walker.walk_entries(SAMPLE_ENTRIES)
gx = [p[0] for p in glyph_path]
gy = [p[1] for p in glyph_path]
glyph_fig = go.Figure(go.Scatter(x=gx, y=gy, mode="lines+markers", line=dict(color="teal")))
glyph_fig.update_layout(height=350, margin=dict(l=0, r=0, t=10, b=0))
st.plotly_chart(glyph_fig, use_container_width=True)
