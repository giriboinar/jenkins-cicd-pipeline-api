"""Deployment Tracker API — records deployments so a CI/CD pipeline has
something real to promote through dev -> staging -> prod.

In-memory store on purpose: this project proves the pipeline, not a
database. A restart clears the records (see README limitations).
"""

import uuid

from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, Counter, Gauge, generate_latest
from pydantic import BaseModel, Field
from typing import Literal

app = FastAPI(title="Deployment Tracker API", version="0.1.0")

deployments: dict[str, dict] = {}
deployments_created_total = Counter(
    "deployments_created_total", "Total deployments recorded"
)
deployments_total = Gauge("deployments_total", "Current deployments recorded")


class DeploymentIn(BaseModel):
    service: str = Field(..., min_length=1, description="Service being deployed")
    version: str = Field(..., min_length=1, description="Version or image tag")
    environment: Literal["dev", "staging", "prod"] = "dev"
    status: Literal["pending", "success", "failed", "rolled_back"] = "pending"


class Deployment(DeploymentIn):
    id: str


@app.get("/")
def root():
    return {"service": "deployment-tracker-api", "status": "ok"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.get("/metrics")
def metrics():
    return PlainTextResponse(generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@app.post("/api/deployments", response_model=Deployment, status_code=201)
def create_deployment(payload: DeploymentIn):
    item = Deployment(id=str(uuid.uuid4()), **payload.model_dump())
    deployments[item.id] = item.model_dump()
    deployments_created_total.inc()
    deployments_total.set(len(deployments))
    return item


@app.get("/api/deployments", response_model=list[Deployment])
def list_deployments(environment: str | None = None, status: str | None = None):
    items = list(deployments.values())
    if environment is not None:
        items = [d for d in items if d["environment"] == environment]
    if status is not None:
        items = [d for d in items if d["status"] == status]
    return items


@app.get("/api/deployments/{deployment_id}", response_model=Deployment)
def get_deployment(deployment_id: str):
    if deployment_id not in deployments:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return deployments[deployment_id]


@app.delete("/api/deployments/{deployment_id}", status_code=204)
def delete_deployment(deployment_id: str):
    if deployment_id not in deployments:
        raise HTTPException(status_code=404, detail="Deployment not found")
    del deployments[deployment_id]
    deployments_total.set(len(deployments))
    return None
