from concurrent import futures

import grpc

import predict_engine_pb2 as pb2
import predict_engine_pb2_grpc as pb2_grpc
from model_runtime import PredictEngineRuntime
from settings import Settings


class PredictEngineGrpcService(pb2_grpc.PredictEngineServicer):

    def __init__(self, runtime: PredictEngineRuntime, settings: Settings) -> None:
        self._runtime = runtime
        self._settings = settings

    def Health(
        self,
        request: pb2.HealthRequest,
        context: grpc.ServicerContext,
    ) -> pb2.HealthResponse:
        del request, context
        health = self._runtime.health()
        return pb2.HealthResponse(
            status="ok" if health.model_loaded else "degraded",
            service_name=self._settings.app.service_name,
            model_path=health.model_path,
            model_exists=health.model_exists,
            model_loaded=health.model_loaded,
            model_input_name=health.model_input_name,
            model_output_names=list(health.model_output_names),
            model_error=health.model_error or "",
        )

    def Predict(
        self,
        request: pb2.PredictRequest,
        context: grpc.ServicerContext,
    ) -> pb2.PredictResponse:
        try:
            return self._runtime.predict(
                request_id=request.request_id,
                feature_names=request.feature_names,
                rows=request.rows,
            )
        except FileNotFoundError as exc:
            context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        except ValueError as exc:
            context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except RuntimeError as exc:
            context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(exc))
        except Exception as exc:
            context.abort(grpc.StatusCode.INTERNAL, str(exc))


def create_grpc_server(settings: Settings, runtime: PredictEngineRuntime) -> grpc.Server:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=settings.grpc.max_workers))
    pb2_grpc.add_PredictEngineServicer_to_server(
        PredictEngineGrpcService(runtime=runtime, settings=settings),
        server,
    )
    server.add_insecure_port(settings.grpc.bind_address)
    return server
