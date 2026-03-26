import base64
import math
from typing import Any

import cv2
import mediapipe as mp
import numpy as np
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions
from ultralytics import YOLO


class VisionProcessor:
    """
    视觉处理核心类。

    职责：
    1) 使用 YOLO 检测目标物体并计算目标中心点；
    2) 使用 MediaPipe 手部关键点模型检测手部并计算手中心点；
    3) 基于手-目标相对位置生成简单抓取引导；
    4) 提供 base64 图像输入/输出接口，便于 WebSocket 前后端传输。
    """

    def __init__(
        self,
        model_asset_path: str = "hand_landmarker.task",
        yolo_model_path: str = "yolov8n.pt",
        target_class_name: str = "cup",
        num_hands: int = 2,
    ) -> None:
        """
        初始化推理资源（模型与参数）。

        参数：
        - model_asset_path: MediaPipe hand landmarker 模型文件路径
        - yolo_model_path: YOLO 权重文件路径
        - target_class_name: 当前要引导抓取的目标类别
        - num_hands: 最多检测手的数量
        """
        # 初始化 MediaPipe 手部关键点检测器
        base_options = BaseOptions(model_asset_path=model_asset_path)
        options = HandLandmarkerOptions(base_options=base_options, num_hands=num_hands)
        self.detector = HandLandmarker.create_from_options(options)
        # 初始化 YOLO 目标检测模型
        self.model = YOLO(yolo_model_path)
        # 当前目标类别，可由前端动态切换
        self.target_class_name = target_class_name
        # MediaPipe Hands 的标准连接拓扑，用于绘制手部骨架
        self.hand_connections = [
            (0, 1),
            (1, 2),
            (2, 3),
            (3, 4),
            (0, 5),
            (5, 6),
            (6, 7),
            (7, 8),
            (5, 9),
            (9, 10),
            (10, 11),
            (11, 12),
            (9, 13),
            (13, 14),
            (14, 15),
            (15, 16),
            (13, 17),
            (17, 18),
            (18, 19),
            (19, 20),
            (0, 17),
        ]

    def set_target_class(self, class_name: str) -> None:
        """
        更新目标类别名称。
        """
        self.target_class_name = class_name.strip()

    def _decode_base64_image(self, image_b64: str) -> np.ndarray:
        """
        将前端传来的 base64 图像字符串解码为 OpenCV BGR 图像。
        """
        # 兼容 data URL 前缀，例如 data:image/jpeg;base64,xxxx
        if "," in image_b64:
            image_b64 = image_b64.split(",", 1)[1]
        # base64 -> bytes -> numpy uint8 -> BGR 图像
        raw = base64.b64decode(image_b64)
        arr = np.frombuffer(raw, dtype=np.uint8)
        frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if frame is None:
            raise ValueError("无法解码图像帧")
        return frame

    def _encode_base64_image(self, frame: np.ndarray) -> str:
        """
        将 OpenCV BGR 图像编码为 base64 字符串，供前端显示。
        """
        # 压缩为 JPEG，平衡清晰度与传输体积
        ok, buf = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
        if not ok:
            raise ValueError("无法编码图像帧")
        return base64.b64encode(buf).decode("utf-8")

    def process_frame(self, frame: np.ndarray) -> dict[str, Any]:
        """
        对单帧图像执行完整视觉流程：
        1) 目标检测
        2) 手部关键点检测
        3) 距离和方向引导计算
        4) 将可视化结果绘制回图像
        """
        # 目标中心、手中心及引导信息的默认值
        target_center = None
        hand_center = None
        guidance_text = ""
        distance_px = None

        # YOLO 目标检测：筛选当前目标类别，并绘制目标框与中心点
        results = self.model(frame, stream=True, verbose=False)
        for r in results:
            for box in r.boxes:
                cls_id = int(box.cls[0])
                class_name = self.model.names[cls_id]
                if class_name == self.target_class_name:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    # 画框与标签
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(
                        frame,
                        f"{class_name} {conf:.2f}",
                        (x1, y1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.5,
                        (0, 255, 0),
                        2,
                    )
                    # 计算并绘制目标中心点
                    target_center = ((x1 + x2) // 2, (y1 + y2) // 2)
                    cv2.circle(frame, target_center, 5, (0, 255, 0), cv2.FILLED)

        # MediaPipe 手部检测：输入需要 RGB
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        detection_result = self.detector.detect(mp_image)

        # 遍历每只手并绘制关键点与连线
        if detection_result.hand_landmarks:
            for hand_landmarks in detection_result.hand_landmarks:
                h, w, _ = frame.shape
                pts = []
                # 将归一化坐标映射到像素坐标并绘制关键点
                for lm in hand_landmarks:
                    x, y = int(lm.x * w), int(lm.y * h)
                    pts.append((x, y))
                    cv2.circle(frame, (x, y), 2, (0, 255, 255), -1)

                # 按预定义拓扑绘制手部骨架连线
                for i, j in self.hand_connections:
                    if i < len(pts) and j < len(pts):
                        cv2.line(frame, pts[i], pts[j], (255, 255, 0), 1)

                # 取 landmark 9（中指根部附近）作为手中心
                if len(hand_landmarks) > 9:
                    cx, cy = int(hand_landmarks[9].x * w), int(hand_landmarks[9].y * h)
                    hand_center = (cx, cy)
                    cv2.circle(frame, hand_center, 5, (255, 0, 0), cv2.FILLED)
                    cv2.putText(frame, "Hand", (cx, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # 当手和目标都检测到时，计算距离并给出方向引导
        if target_center and hand_center:
            # 绘制手到目标的连线
            cv2.line(frame, hand_center, target_center, (0, 255, 255), 2)
            # 计算相对位移和欧式距离
            dx = target_center[0] - hand_center[0]
            dy = target_center[1] - hand_center[1]
            distance = math.sqrt(dx**2 + dy**2)
            distance_px = int(distance)

            # 方向决策：近距离提示抓取，远距离提示移动方向
            if distance < 50:
                guidance_text = "Grasp now"
            else:
                if abs(dx) > abs(dy):
                    guidance_text = "Move Left" if dx > 0 else "Move Right"
                else:
                    guidance_text = "Move Down" if dy > 0 else "Move Up"

            # 叠加可视化提示文本
            cv2.putText(
                frame,
                f"Distance: {distance_px}px -> {guidance_text}",
                (30, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 0, 255),
                2,
            )

        # 结构化返回结果，供后端 websocket 层转发
        return {
            "frame": frame,
            "guidance": guidance_text,
            "distance_px": distance_px,
            "target_center": target_center,
            "hand_center": hand_center,
            "target_class_name": self.target_class_name,
        }

    def process_base64_frame(self, image_b64: str) -> dict[str, Any]:
        """
        面向前后端通信的高层入口：
        base64 输入 -> 模型处理 -> base64 输出。
        """
        frame = self._decode_base64_image(image_b64)
        result = self.process_frame(frame)
        result_image_b64 = self._encode_base64_image(result["frame"])
        return {
            "image": f"data:image/jpeg;base64,{result_image_b64}",
            "guidance": result["guidance"],
            "distance_px": result["distance_px"],
            "target_center": result["target_center"],
            "hand_center": result["hand_center"],
            "target_class_name": result["target_class_name"],
        }
