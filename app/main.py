from fastapi import FastAPI

from app.config.settings import Settings
from app.api.http.error_handlers import register_error_handlers
from app.api.routes.payments import router as payments_router
from app.api.routes.stripe_webhooks import router as stripe_webhooks_router


def create_app() -> FastAPI:
    settings = Settings()

    app = FastAPI(
        title="Async Payments Service",
        version="0.1.0",
    )

    # Routers
    app.include_router(payments_router, prefix="/payments", tags=["payments"])
    app.include_router(
        stripe_webhooks_router, prefix="/webhooks/stripe", tags=["webhooks"]
    )

    # Error handlers
    register_error_handlers(app)

    return app


app = create_app()
