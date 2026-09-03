from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from routes.triage import router as triage_router

app = FastAPI(title="LLM Triage API")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
):
    return JSONResponse(
        status_code=400,
        content={"detail": exc.errors()},
    )


app.include_router(triage_router)


@app.get("/")
def root():
    return {"message": "LLM Triage API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}