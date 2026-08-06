"""
Constellation Journey Engine API — Durable Backend v2.0
========================================================
Connects the Creative Journey Organ to Neo4j (graph memory) and Qdrant (semantic vectors).

Architecture:
  HTML/JS Journey Organ → FastAPI → Neo4j (structural paths) + Qdrant (semantic embeddings)

Dependencies:
  pip install fastapi uvicorn pydantic neo4j qdrant-client sentence-transformers

Docker:
  docker run -d -p 6333:6333 -p 6334:6334 qdrant/qdrant
  docker run -d -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password neo4j:latest

Run:
  uvicorn main:app --reload --port 8000
"""

import os
import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sentence_transformers import SentenceTransformer

from neo4j import AsyncGraphDatabase
from qdrant_client import QdrantClient
from qdrant_client.http import models as qmodels

# =====================================================================
# 1. APPLICATION & SCHEMAS
# =====================================================================

app = FastAPI(
    title="Constellation Journey Engine API",
    description="Durable backend connecting Creative Journey UI with Qdrant + Neo4j.",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class PhysicalState(BaseModel):
    chamber_volume: float
    material_density: float

class JourneyStepPayload(BaseModel):
    traveler_id: str
    journey_thread_id: str
    state_index: int
    state_name: str
    narrative_reflection: str
    parameters: PhysicalState

# =====================================================================
# 2. PERSISTENCE DRIVERS & LIFESPAN
# =====================================================================

class ConstellationStorage:
    def __init__(self):
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")
        self.qdrant: Optional[QdrantClient] = None
        self.neo4j_driver: Optional[AsyncGraphDatabase] = None
        self.collection_name = "journey_reflections"

    async def initialize(self):
        # A. Connect to Qdrant
        qdrant_url = os.getenv("QDRANT_URL", "http://localhost:6333")
        self.qdrant = QdrantClient(url=qdrant_url)
        
        try:
            self.qdrant.get_collection(self.collection_name)
        except Exception:
            self.qdrant.create_collection(
                collection_name=self.collection_name,
                vectors_config=qmodels.VectorParams(size=384, distance=qmodels.Distance.COSINE)
            )

        # B. Connect to Neo4j
        neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        neo4j_user = os.getenv("NEO4J_USER", "neo4j")
        neo4j_pass = os.getenv("NEO4J_PASSWORD", "password")
        self.neo4j_driver = AsyncGraphDatabase.driver(
            neo4j_uri, auth=(neo4j_user, neo4j_pass)
        )

    async def close(self):
        if self.neo4j_driver:
            await self.neo4j_driver.close()

storage = ConstellationStorage()

@app.on_event("startup")
async def startup_event():
    await storage.initialize()

@app.on_event("shutdown")
async def shutdown_event():
    await storage.close()

# =====================================================================
# 3. JOURNEY PIPELINE ENDPOINT
# =====================================================================

@app.post("/api/v1/journey/step")
async def record_journey_step(payload: JourneyStepPayload):
    try:
        # Step A: Vector Embedding & Qdrant Upsert
        reflection_vector = storage.encoder.encode(
            payload.narrative_reflection, 
            normalize_embeddings=True
        ).tolist()

        # Generate deterministic numeric point ID from thread_id + step_index
        point_id = abs(hash(f"{payload.journey_thread_id}_{payload.state_index}")) % (10**15)

        storage.qdrant.upsert(
            collection_name=storage.collection_name,
            points=[
                qmodels.PointStruct(
                    id=point_id,
                    vector=reflection_vector,
                    payload={
                        "traveler_id": payload.traveler_id,
                        "thread_id": payload.journey_thread_id,
                        "state_name": payload.state_name,
                        "state_index": payload.state_index,
                        "reflection": payload.narrative_reflection,
                        "volume": payload.parameters.chamber_volume,
                        "density": payload.parameters.material_density
                    }
                )
            ]
        )

        # Step B: Cypher Graph Mutation in Neo4j
        cypher = """
        MERGE (t:Traveler {traveler_id: $traveler_id})
        MERGE (j:JourneyThread {thread_id: $thread_id})
        MERGE (t)-[:WALKS]->(j)

        CREATE (s:StateNode {
            state_index: $state_index,
            state_name: $state_name,
            narrative: $narrative,
            chamber_volume: $volume,
            material_density: $density,
            timestamp: timestamp()
        })
        CREATE (j)-[:HAS_STEP]->(s)

        WITH j, s
        MATCH (j)-[:HAS_STEP]->(prev:StateNode)
        WHERE prev.state_index = $state_index - 1
        CREATE (prev)-[:TRANSITIONED_TO]->(s)
        """

        async with storage.neo4j_driver.session() as session:
            await session.run(
                cypher,
                traveler_id=payload.traveler_id,
                thread_id=payload.journey_thread_id,
                state_index=payload.state_index,
                state_name=payload.state_name,
                narrative=payload.narrative_reflection,
                volume=payload.parameters.chamber_volume,
                density=payload.parameters.material_density
            )

        # Step C: Loom Engine Vector Match (Check for Semantic Resonance)
        loom_resonance = None
        if payload.state_index >= 4:  # Discovery or higher
            hits = storage.qdrant.search(
                collection_name=storage.collection_name,
                query_vector=reflection_vector,
                limit=3
            )
            # Find closest historical reflection from other threads
            matches = [h for h in hits if h.payload.get("thread_id") != payload.journey_thread_id]
            if matches:
                top_match = matches[0]
                loom_resonance = {
                    "bridge_detected": True,
                    "matched_artifact": f"Thread '{top_match.payload['thread_id']}' ({top_match.payload['state_name']})",
                    "coherence_score": round(float(top_match.score), 4)
                }

        return {
            "success": True,
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "point_id": point_id,
            "loom_feedback": loom_resonance
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline error: {str(e)}")

# =====================================================================
# 4. HEALTH & GRAPH QUERY ENDPOINTS
# =====================================================================

@app.get("/api/v1/health")
async def health():
    return {
        "status": "alive",
        "qdrant": storage.qdrant is not None,
        "neo4j": storage.neo4j_driver is not None,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

@app.get("/api/v1/journey/{thread_id}/path")
async def get_journey_path(thread_id: str):
    """Retrieve the full journey path for a given thread."""
    cypher = """
    MATCH path = (t:Traveler)-[:WALKS]->(j:JourneyThread {thread_id: $thread_id})
    -[:HAS_STEP*]->(s:StateNode)
    RETURN path
    ORDER BY s.state_index
    """
    try:
        async with storage.neo4j_driver.session() as session:
            result = await session.run(cypher, thread_id=thread_id)
            records = await result.data()
            return {"thread_id": thread_id, "path": records}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
