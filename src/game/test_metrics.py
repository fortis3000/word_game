from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, Counter

app = FastAPI()
c = Counter("my_requests_total", "HTTP Failures", ["method", "endpoint"])
c.labels("get", "/").inc()


@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
