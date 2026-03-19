from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from version_compare_service import version_compare_service


app = FastAPI(title="Version Comparison Service")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/status")
async def status_endpoint():
    return {
        "success": True,
        **version_compare_service.get_index_metadata(),
    }


@app.post("/reload")
async def reload_endpoint():
    version_compare_service.reload_index()
    return {
        "success": True,
        **version_compare_service.get_index_metadata(),
    }


@app.post("/compare")
async def compare_endpoint(file: UploadFile = File(...)):
    try:
        content = (await file.read()).decode("utf-8", errors="ignore")
        result = version_compare_service.compare_content(content)
        return {"success": True, **result}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc