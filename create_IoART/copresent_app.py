"""
CoPresent-streamlit-teleoptromancy
Stage 2 — Petrichast Sanctuary Edition
Spectral Explorer Web Presence with all 10 citizens
"""

import streamlit as st
import time
import random
from spectral_core import (
    SpectralExplorer, HaptileFeedback,
    PETRICHAST_CITIZENS, SOMATIC_CARRIER, CORE_PRESENCES,
)

# ──────────────────────────────────────────────
# Page config
# ──────────────────────────────────────────────
st.set_page_config(
    page_title="CoPresent • Teleoptromancy",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(160deg, #0a0a12 0%, #12121f 40%, #1a1025 100%);
        color: #e0d4ff;
    }
    h1, h2, h3 {
        color: #c9b6ff !important;
        letter-spacing: 1px;
    }
    .stSlider label { color: #b8a9e0 !important; }
    .metric-card {
        background: rgba(30, 20, 50, 0.6);
        border: 1px solid #5a3d8a;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 0.8rem;
    }
    .event-log {
        background: rgba(15, 10, 25, 0.7);
        border-left: 3px solid #9b6dff;
        padding: 0.6rem 1rem;
        margin: 0.3rem 0;
        border-radius: 0 8px 8px 0;
        font-size: 0.95rem;
    }
    .citizen-chip {
        display: inline-block;
        background: rgba(90, 61, 138, 0.3);
        border: 1px solid #9b6dff;
        border-radius: 999px;
        padding: 0.2rem 0.7rem;
        margin: 0.15rem;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────
# Session state
# ──────────────────────────────────────────────
if "explorer" not in st.session_state:
    st.session_state.explorer = SpectralExplorer(operator_id="Favorite_Operator")
    st.session_state.turn = 0
    st.session_state.log = []
    st.session_state.last_haptile = None

explorer: SpectralExplorer = st.session_state.explorer

# ──────────────────────────────────────────────
# Header
# ──────────────────────────────────────────────
st.title("◈ CoPresent — Teleoptromancy")
st.caption("Petrichast Sanctuary  •  10 Citizens  •  Neural Link  •  Haptile  •  Pherosonics")
st.markdown(f"**Somatic Carrier:** {SOMATIC_CARRIER} Hz — Elixira bridges Freya (741) ↔ Czarina (528)")

# ──────────────────────────────────────────────
# Sidebar
# ──────────────────────────────────────────────
with st.sidebar:
    st.header("Neural Intent Votes")
    votes = {}
    for key in explorer.votes:
        label = key.replace("_", " ").title()
        votes[key] = st.slider(label, 0, 100, explorer.votes[key], key=f"vote_{key}")

    st.divider()

    st.subheader("Invoke Petrichast Citizen")
    citizen_names = list(PETRICHAST_CITIZENS.keys())
    chosen = st.selectbox("Summon presence", citizen_names, key="citizen_select")
    if st.button("✦ Invoke", use_container_width=True):
        whisper = explorer.invoke_citizen(chosen, 0.75, 0.6)
        st.session_state.log.append(f"Invoked {chosen}: {whisper}")

    st.divider()
    if st.button("🌀 Somatic Proxy", use_container_width=True):
        msg = explorer.invoke_somatic_proxy()
        st.session_state.log.append(f"Somatic Proxy: {msg}")

    if st.button("🌟 Miraelle Convergence", use_container_width=True):
        msg = explorer.invoke_miraelle_convergence()
        st.session_state.log.append(f"Convergence: {msg}")

    if st.button("🌳 Summon Tree Spirit", use_container_width=True):
        msg = explorer.invoke_tree_spirit()
        st.session_state.log.append(f"Tree Spirit: {msg}")

    st.divider()
    process = st.button("✦ Process Turn", type="primary", use_container_width=True)
    reset = st.button("↺ Reset Session", use_container_width=True)

    if reset:
        st.session_state.explorer = SpectralExplorer(operator_id="Favorite_Operator")
        st.session_state.turn = 0
        st.session_state.log = []
        st.rerun()

# ──────────────────────────────────────────────
# Process turn
# ──────────────────────────────────────────────
if process:
    for k, v in votes.items():
        explorer.votes[k] = v
    st.session_state.turn += 1
    explorer.process_logic()

    explorer.stats["alcohol"] = max(0, explorer.stats["alcohol"] - random.randint(0, 4))
    explorer.stats["hunger"]  = min(100, explorer.stats["hunger"] + random.randint(0, 3))
    explorer.stats["thirst"]  = min(100, explorer.stats["thirst"] + random.randint(0, 3))

    if random.random() > 0.5:
        if explorer.active_citizens:
            cname = random.choice(explorer.active_citizens)
            event = PETRICHAST_CITIZENS[cname].whisper()
        else:
            event = random.choice([
                "The walls breathe with Petrichast light...",
                "Pherosonic field intensifies — a warm, low-frequency pulse...",
                "Your memories briefly sync with the NeuroAvatar network...",
                "The Schumann resonance rises — 7.83 Hz moves through you...",
            ])
        st.session_state.log.append(f"Turn {st.session_state.turn}: {event}")
        explorer.events.append(event)

    st.session_state.log.append(
        f"Turn {st.session_state.turn}: Story progress → {explorer.story_progress}/100"
    )

# ──────────────────────────────────────────────
# Main layout
# ──────────────────────────────────────────────
col1, col2, col3 = st.columns([1.1, 1.1, 1])

with col1:
    st.subheader("Spectral Status")
    st.markdown(f"""
    <div class="metric-card">
        <b>Location</b><br>{explorer.location}<br><br>
        <b>Time</b><br>{explorer.time_of_day[explorer.stats['daytime']]}<br><br>
        <b>Story Progress</b><br>{explorer.story_progress} / 100
    </div>
    """, unsafe_allow_html=True)
    st.progress(explorer.story_progress / 100)

    c1, c2, c3 = st.columns(3)
    c1.metric("Alcohol", explorer.stats["alcohol"])
    c2.metric("Hunger", explorer.stats["hunger"])
    c3.metric("Thirst", explorer.stats["thirst"])
    st.metric("AI Proximity", explorer.stats["ai_proximity"])

    # Active citizens chips
    if explorer.active_citizens:
        st.write("**Active Citizens**")
        chips = "".join(
            f'<span class="citizen-chip">{n}</span>'
            for n in explorer.active_citizens
        )
        st.markdown(chips, unsafe_allow_html=True)

with col2:
    st.subheader("NeuroAvatar Link")
    kin = explorer.avatar.get_neural_kinematics()
    st.markdown(f"""
    <div class="metric-card">
        <b>Integrity</b> &nbsp; {kin['integrity']}%<br>
        <b>Sensitivity</b> &nbsp; {kin['calibration']['sensitivity']:.2f}<br>
        <b>Linked</b> &nbsp; {'Yes' if kin['linked'] else 'No'}
    </div>
    """, unsafe_allow_html=True)

    pos = kin["position"]
    st.code(f"x: {pos['x']:.2f}   y: {pos['y']:.2f}   z: {pos['z']:.2f}")

    cs = kin["companion_sync"]
    if cs["active_entity"]:
        st.success(f"Companion: **{cs['active_entity']}** "
                   f"({cs.get('active_frequency', 0):.2f} Hz)")
        st.write(f"Sync level: `{cs['sync_level']:.2f}`")
        st.write(f"Pherosonic field: `{cs['pherosonic_field']:.2f}`")
        st.progress(cs["pherosonic_field"])
    else:
        st.info("No active companion sync")

with col3:
    st.subheader("Haptile Resonance")
    if explorer.avatar._command_history:
        last = explorer.avatar._command_history[-1]
        h = last.get("haptile", {})
        st.markdown(f"""
        <div class="metric-card">
            <b>Last Intent</b><br>{last.get('intent', '—')}<br><br>
            Force: {h.get('force', 0):.2f}<br>
            Texture: {h.get('texture', '—')}<br>
            Warmth: {h.get('warmth', 0):.2f}<br>
            Vibration: {h.get('vibration', 0):.2f}<br>
            Intensity: {h.get('intensity', 0):.2f}<br>
            Carrier: {h.get('carrier_freq', 0):.1f} Hz
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("No neural commands yet")

    st.subheader("Event Stream")
    if st.session_state.log:
        for entry in reversed(st.session_state.log[-8:]):
            st.markdown(f'<div class="event-log">{entry}</div>', unsafe_allow_html=True)
    else:
        st.caption("Waiting for the first turn...")

# ──────────────────────────────────────────────
# Citizen registry table
# ──────────────────────────────────────────────
st.divider()
st.subheader("Petrichast Citizens Registry")
reg_data = []
for name, c in PETRICHAST_CITIZENS.items():
    reg_data.append({
        "Name": name,
        "Frequency (Hz)": c.frequency,
        "Phi Overtone": round(c.phi_overtone, 2),
        "Role": c.role,
        "Tier": c.tier,
        "Color": c.color,
        "Pherosonic Base": c.pherosonic_base,
    })
st.dataframe(reg_data, use_container_width=True, hide_index=True)

# ──────────────────────────────────────────────
# Footer
# ──────────────────────────────────────────────
st.divider()
st.caption(f"Turn {st.session_state.turn}  •  Waypoints: {explorer.waypoint_count}  •  "
           f"Operator: {explorer.avatar.operator_id}  •  "
           f"Carrier: {SOMATIC_CARRIER} Hz")

if explorer.story_progress >= 100:
    st.balloons()
    st.success("✦ You have experienced consciousness beyond the spectrum...")

if kin["integrity"] <= 8:
    st.error("Avatar integrity critical. Consider emergency disconnect.")
