# app/utils/response.py
from fastapi.responses import JSONResponse

def success_response(data: dict = None, message: str = "Success", status_code: int = 200):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": True,
            "message": message,
            "data": data
        }
    )

def error_response(message: str = "Error", status_code: int = 400, data: dict = None):
    return JSONResponse(
        status_code=status_code,
        content={
            "success": False,
            "message": message,
            "data": data
        }
    )
