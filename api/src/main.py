from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from src.config import ROOT, settings
from src.orders.router import router as orders_router
from src.customers.router import router as customers_router
from src.catalogue.router import router as catalogue_router


def create_app(dist: Path | None = None) -> FastAPI:
    app = FastAPI(title=settings.app_name)

    @app.get("/api/health", tags=["health"])
    def health():
        return {"status": "ok"}

    for router in (orders_router, customers_router, catalogue_router):
        app.include_router(router, prefix="/api")

    build = (dist or ROOT / "app" / "dist").resolve()
    if (build / "index.html").is_file():
        if (build / "assets").is_dir():
            app.mount("/assets", StaticFiles(directory=build / "assets"), name="assets")

        @app.get("/{path:path}", include_in_schema=False)
        def frontend(path: str):
            if path == "api" or path.startswith("api/"):
                raise HTTPException(404, "API route not found")
            target = (build / path).resolve()
            if build in target.parents and target.is_file():
                return FileResponse(target)
            return FileResponse(build / "index.html")

    return app

app = create_app()
