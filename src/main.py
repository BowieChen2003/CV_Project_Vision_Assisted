import json
from pathlib import Path

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

try:
    from src.vision_processor import VisionProcessor
except ImportError:
    from vision_processor import VisionProcessor

app = FastAPI(title="Vision Assistant Backend", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
MODELS_DIR = BASE_DIR / "models"
INDEX_FILE = BASE_DIR / "static" / "index.html"

processor = VisionProcessor(
    model_asset_path=str(MODELS_DIR / "hand_landmarker.task"),
    yolo_model_path=str(MODELS_DIR / "yolov8n.pt"),
    target_class_name="cup",
)



@app.get("/")
async def root():
    if INDEX_FILE.exists():
        return FileResponse(INDEX_FILE)
    return JSONResponse(
        {
            "service": "Vision Assistant Backend",
            "status": "running",
            "routes": {
                "health": "/health",
                "websocket": "/ws/vision",
                "docs": "/docs",
            },
        }
    )


@app.get("/health")
async def health():
    return {"status": "ok", "target_class_name": processor.target_class_name}


@app.websocket("/ws/vision")
async def ws_vision(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            raw = await websocket.receive_text()
            data = json.loads(raw)
            message_type = data.get("type")

            if message_type == "set_target":
                class_name = data.get("target_class_name", "").strip()
                if class_name:
                    processor.set_target_class(class_name)
                await websocket.send_json(
                    {
                        "type": "ack",
                        "target_class_name": processor.target_class_name,
                    }
                )
                continue

            if message_type == "frame":
                image_b64 = data.get("image")
                if not image_b64:
                    await websocket.send_json({"type": "error", "message": "缺少 image 字段"})
                    continue

                result = processor.process_base64_frame(image_b64)
                await websocket.send_json({"type": "result", **result})
                continue

            await websocket.send_json({"type": "error", "message": "未知消息类型"})
    except WebSocketDisconnect:
        return
    except Exception as e:
        await websocket.send_json({"type": "error", "message": str(e)})
