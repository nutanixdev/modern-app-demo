import os

import motor.motor_asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

MONGODB_USERNAME = os.environ['MONGODB_USERNAME']
MONGODB_PASSWORD = os.environ['MONGODB_PASSWORD']
MONGODB_DATABASE = os.environ.get('MONGODB_DATABASE', 'mongodb')
MONGODB_ADDRESS = os.environ['MONGODB_ADDRESS']
MONGODB_PORT = os.environ.get('MONGODB_PORT', 27017)

DB_URI = f'mongodb://{MONGODB_USERNAME}:{MONGODB_PASSWORD}@{MONGODB_ADDRESS}:{MONGODB_PORT}/{MONGODB_DATABASE}?authSource=admin&directConnection=true'

app = FastAPI()
client = motor.motor_asyncio.AsyncIOMotorClient(DB_URI)
db = client.vod


@app.get(
    "/", response_description="List all videos")
async def list_videos():
    videos = await db["videos"].find().to_list(1000)
    return JSONResponse(videos)


@app.get(
    "/{id}", response_description="Get a single video")
async def show_video(id: str):
    if (video := await db["videos"].find_one({"_id": id})) is not None:
        return video

    raise HTTPException(status_code=404, detail=f"Video {id} not found")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)
