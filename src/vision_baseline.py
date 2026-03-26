import mediapipe as mp
from mediapipe.tasks.python.core.base_options import BaseOptions
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions
from ultralytics import YOLO
import cv2
import math
import numpy as np

def main():
    import os
    from pathlib import Path
    
    BASE_DIR = Path(__file__).resolve().parent.parent
    MODELS_DIR = BASE_DIR / "models"
    
    # 1. 初始化 MediaPipe 手部追踪模型 (完全无需自己训练)
    # 加载手部关键点检测模型
    base_options = BaseOptions(model_asset_path=str(MODELS_DIR / 'hand_landmarker.task'))
    options = HandLandmarkerOptions(base_options=base_options,
                                              num_hands=2) # 可以检测两只手
    detector = HandLandmarker.create_from_options(options)

    # 2. 初始化 YOLOv8 目标检测模型 (加载 COCO 预训练权重，无需自己训练)
    # 首次运行会自动下载 yolov8n.pt，它包含了 80 种常见物品（如苹果、杯子、手机、鞋子等）
    model = YOLO(str(MODELS_DIR / 'yolov8n.pt')) 

    # 设定你要抓取的目标物体（需要是 COCO 数据集支持的类别，比如 'apple', 'cup', 'cell phone'）
    TARGET_CLASS_NAME = 'cup'

    # 打开摄像头
    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        success, frame = cap.read()
        if not success:
            print("无法获取摄像头画面")
            break
        
        # --- 模块 A: 目标物体检测 ---
        # 使用 YOLO 预测当前帧
        results = model(frame, stream=True, verbose=False)
        
        target_center = None
        
        for r in results:
            boxes = r.boxes
            for box in boxes:
                cls_id = int(box.cls[0])
                class_name = model.names[cls_id]
                
                # 只处理我们设定的目标物体
                if class_name == TARGET_CLASS_NAME:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = float(box.conf[0])
                    
                    # 绘制目标边界框
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f"{class_name} {conf:.2f}", (x1, y1 - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                    
                    # 计算目标中心点
                    target_center = ((x1 + x2) // 2, (y1 + y2) // 2)
                    cv2.circle(frame, target_center, 5, (0, 255, 0), cv2.FILLED)

        # --- 模块 B: 手部追踪 ---
        # MediaPipe 需要 RGB 格式的图像
        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=img_rgb)
        detection_result = detector.detect(mp_image)
        
        hand_center = None
        
        if detection_result.hand_landmarks:
            for hand_landmarks in detection_result.hand_landmarks:
                h, w, c = frame.shape

                for lm in hand_landmarks:
                    lx, ly = int(lm.x * w), int(lm.y * h)
                    cv2.circle(frame, (lx, ly), 2, (0, 255, 255), -1)

                # 获取手掌中心 (landmark 9: 中指根部) 或者食指指尖 (landmark 8)
                # 使用中指根部作为手部中心
                cx, cy = int(hand_landmarks[9].x * w), int(hand_landmarks[9].y * h)
                hand_center = (cx, cy)
                
                cv2.circle(frame, hand_center, 5, (255, 0, 0), cv2.FILLED)
                cv2.putText(frame, "Hand", (cx, cy - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)

        # --- 模块 C: 空间关系与简单引导逻辑 ---
        if target_center and hand_center:
            # 画一条连接手和目标的线
            cv2.line(frame, hand_center, target_center, (0, 255, 255), 2)
            
            # 计算像素距离
            dx = target_center[0] - hand_center[0]
            dy = target_center[1] - hand_center[1]
            distance = math.sqrt(dx**2 + dy**2)
            
            # 简单的方位判断逻辑 (这里可以将文字替换为 TTS 语音输出)
            guidance_text = ""
            if distance < 50:
                guidance_text = "Grasp now! (可以抓取)"
            else:
                if abs(dx) > abs(dy):
                    guidance_text = "Move Right" if dx > 0 else "Move Left"
                else:
                    guidance_text = "Move Down" if dy > 0 else "Move Up"
            
            cv2.putText(frame, f"Distance: {int(distance)}px -> {guidance_text}", 
                        (30, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
            
            # 注意：实际项目中，TTS语音播报应该放在独立的子线程中，否则会卡住视频帧！

        # 显示画面
        display_width = 1280
        display_height = 720
        resized_frame = cv2.resize(frame, (display_width, display_height))
        cv2.imshow("Vision Assistant Baseline (Pre-trained Models)", resized_frame)
        
        # 按 'q' 键退出
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
