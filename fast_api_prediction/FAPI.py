from fastapi import FastAPI, HTTPException,Query 
from fastapi.security.api_key import APIKeyHeader
import sys
import os
from fastapi_functions import predict
import pandas as pd

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI()


@app.get("/prediction")
async def get_prediction( openweathermap_api_key: str = Query(..., description="openweathermap_api_key")):
    try:
        prediction,origin_point = await predict(openweathermap_api_key)
        if isinstance(prediction, pd.DataFrame):
            return prediction.to_dict(orient="records")
        else:
            return {"error": prediction}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 