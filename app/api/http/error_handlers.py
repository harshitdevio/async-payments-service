from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from app.domain.payments.state_machine import InvalidPaymentTransition


def register_error_handlers(app: FastAPI):
    @app.exception_handler(InvalidPaymentTransition)
    async def payment_transition_exception(request: Request, exc: InvalidPaymentTransition):
        return JSONResponse(
            status_code=400,
            content={"detail": str(exc)}
        )

    @app.exception_handler(Exception)
    async def generic_exception(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"detail": str(exc)}
        )
