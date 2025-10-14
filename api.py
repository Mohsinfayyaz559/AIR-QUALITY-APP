#to run file type "uvicorn api:app --reload"

import os
os.makedirs("/tmp/.cache", exist_ok=True)
os.environ["HF_HOME"] = "/tmp/.cache"
os.environ["HF_HUB_CACHE"] = "/tmp/.cache"
os.environ["TRANSFORMERS_CACHE"] = "/tmp/.cache"

from fastapi import FastAPI, HTTPException,Query 
from src.model import predict,training
import pandas as pd
import asyncio

app = FastAPI()

@app.get("/")
def root():
    return {"message":"API is working"}


@app.get("/prediction")
async def get_prediction(city_name: str = Query("rawalpindi", description="City name for prediction")):
    try:
        prediction,origin_point = await predict(city_name)
        if isinstance(prediction, pd.DataFrame):
            return prediction.to_dict(orient="records")
        else:
            return {"error": prediction}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 

@app.post("/retrain")
async def retrain():
    asyncio.create_task(training())
    return {"status": "Retraining started in background"}