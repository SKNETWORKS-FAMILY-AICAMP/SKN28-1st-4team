import importlib
from contextlib import asynccontextmanager

numpy = importlib.import_module("numpy")
onnx = importlib.import_module("onnx")
ort = importlib.import_module("onnxruntime")
fastapi = importlib.import_module("fastapi")
FastAPI = fastapi.FastAPI

from grpc_server import create_grpc_server
from model_runtime import predict_engine_runtime
from settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    server = create_grpc_server(settings=settings, runtime=predict_engine_runtime)
    server.start()
    app.state.grpc_server = server
    try:
        yield
    finally:
        server.stop(5).wait()


app = FastAPI(title="Predict Engine Host", version="0.1.0", lifespan=lifespan)


@app.get("/")
def root() -> dict[str, object]:
    health = predict_engine_runtime.health()
    return {
        "message": "Predict engine host is running",
        "app_env": settings.app.env,
        "service_name": settings.app.service_name,
        "http": {
            "host": settings.app.host,
            "port": settings.app.port,
        },
        "grpc": {
            "bind_address": settings.grpc.bind_address,
        },
        "model_path": health.model_path,
        "model_exists": health.model_exists,
        "model_loaded": health.model_loaded,
    }


@app.get("/health")
def health() -> dict[str, object]:
    model_health = predict_engine_runtime.health()
    return {
        "status": "ok",
        "service": settings.app.service_name,
        "http": {
            "host": settings.app.host,
            "port": settings.app.port,
        },
        "grpc": {
            "bind_address": settings.grpc.bind_address,
        },
        "model_path": model_health.model_path,
        "model_exists": model_health.model_exists,
        "model_loaded": model_health.model_loaded,
        "model_input_name": model_health.model_input_name,
        "model_output_names": list(model_health.model_output_names),
        "model_error": model_health.model_error,
        "numpy_version": numpy.__version__,
        "onnx_version": onnx.__version__,
        "onnxruntime_version": ort.__version__,
        "providers": predict_engine_runtime.available_providers(),
    }
