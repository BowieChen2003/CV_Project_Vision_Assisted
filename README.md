# Vision-Assisted Grasping System (视障人士视觉辅助抓取系统)

本项目是一个为视障人士设计的实时视觉辅助抓取系统。该系统通过普通摄像头捕捉第一人称视角（Egocentric view），利用深度学习模型进行目标检测和手部追踪，并通过空间关系计算，实时输出方向引导指令，帮助用户准确触达并抓取目标物体。

本系统作为 **COMP5523 计算机视觉课程** 的小组项目开发。

## 核心功能 (Features)

- **实时目标检测**: 集成轻量级 YOLOv8n 模型，快速识别日常桌面物体（如杯子、手机、瓶子等）。
- **高精度手部追踪**: 采用 MediaPipe Hand Landmarker，在复杂背景下稳定提取 21 个手部 3D 关键点。
- **空间关系理解**: 实时计算目标中心与手掌中心的像素级二维欧氏距离。
- **正交分解引导策略**: 将复杂的坐标偏移转化为极简的 "Left/Right/Up/Down/Grasp" 纯文字指令（可无缝接入 TTS 语音播报），有效降低视障用户的认知负荷。
- **前后端分离架构**: 前端基于 Web 技术调用本地摄像头并通过 WebSocket 传输视频流；后端基于 FastAPI 提供高并发的异步 AI 推理服务。

## 项目结构 (Directory Structure)

```text
cv/
├── src/                    # 核心源代码目录
│   ├── __init__.py
│   ├── main.py             # FastAPI 后端服务入口 (WebSocket & API)
│   ├── vision_processor.py # 核心视觉处理类 (YOLO + MediaPipe 逻辑)
│   ├── vision_baseline.py  # 本地 OpenCV 离线测试脚本 (无需前端)
│   └── train_yolov8.py     # YOLOv8 独立训练脚本
├── static/                 # 前端静态文件
│   └── index.html          # Web UI 交互界面 (摄像头调用、WebSocket 通信)
├── models/                 # 预训练模型存放目录 (需要手动下载或运行脚本生成)
│   ├── yolov8n.pt          # YOLOv8n 目标检测权重
│   └── hand_landmarker.task# MediaPipe 手部关键点模型
├── docs/                   # 项目文档与报告
│   ├── COMP5523_Project_Report.md
│   └── ...
├── requirements-backend.txt# Python 依赖清单
└── .gitignore              # Git 忽略配置
```

## 环境准备与安装 (Installation)

### 1. 克隆项目

```bash
git clone https://github.com/BowieChen2003/CV_Project_Vision_Assisted.git
cd CV_Project_Vision_Assisted
```

### 2. 创建并激活虚拟环境 (推荐)

```bash
# 创建虚拟环境
python3 -m venv vision-env

# 激活虚拟环境 (macOS/Linux)
source vision-env/bin/activate

# 激活虚拟环境 (Windows)
# vision-env\Scripts\activate
```

### 3. 安装依赖库

```bash
pip install -r requirements-backend.txt
pip install ultralytics mediapipe opencv-python-headless
```

### 4. 准备模型文件

确保 `models/` 目录下存在以下两个文件：

1. **`yolov8n.pt`**: YOLOv8 Nano 预训练模型。如果在代码中直接运行，`ultralytics` 库通常会自动下载。
2. **`hand_landmarker.task`**: MediaPipe 手部模型。你需要从 [MediaPipe 官方文档](https://developers.google.com/mediapipe/solutions/vision/hand_landmarker/index#models) 下载。

*(注：如果你已经运行过该项目，这些文件应该已经存在。)*

## 🚀 如何运行项目 (How to Run)

本项目提供了两种运行模式：**Web 服务模式**（完整体验）和 **本地离线模式**（快速测试）。

### 模式一：Web 服务模式 (推荐，前后端分离体验)

此模式将启动一个 FastAPI 服务器，提供前端页面和 WebSocket 通信。

1. **启动后端服务**：
   在项目根目录下运行以下命令启动 FastAPI 服务：
   ```bash
   uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
   ```
2. **访问前端页面**：
   打开浏览器（推荐使用 Chrome 或 Edge），访问：
   `http://localhost:8000`
3. **开始使用**：
   - 页面加载后，点击“连接服务器”。
   - 允许浏览器访问您的摄像头。
   - 点击“开启摄像头”，此时视频流将通过 WebSocket 发送给后端。
   - 后端处理后，会在页面右侧实时显示带有检测框、追踪点和引导指令的画面。

### 模式二：本地离线基线测试 (Baseline Test)

如果你只想快速验证 YOLO 和 MediaPipe 的检测效果，不想启动 Web 服务，可以直接运行基线脚本。该脚本使用 OpenCV 直接读取摄像头并弹出本地窗口显示结果。

1. **运行脚本**：
   ```bash
   python src/vision_baseline.py
   ```
2. **操作说明**：
   - 运行后会弹出一个名为 "Vision Assistant Baseline" 的窗口。
   - 把手和目标物体（默认是杯子 `cup`）放在摄像头前。
   - 画面左上角会实时显示 `Distance` 和 `Move Left/Right...` 等引导指令。
   - 按键盘上的 **`q`** 键退出程序。

## 训练自定义模型 (Training Custom Model)

虽然项目默认使用 COCO 预训练模型，但我们也提供了独立的训练脚本，方便你使用自定义数据集（或 COCO 的子集）进行微调训练。

```bash
# 基本训练命令 (使用 COCO128 数据集作为示例，训练 50 轮)
python src/train_yolov8.py --data coco128.yaml --model yolov8n.pt --epochs 50 --imgsz 640 --batch 16

# 如果你有自定义的数据集配置文件 (例如 my_dataset.yaml)
# python src/train_yolov8.py --data my_dataset.yaml --model yolov8n.pt --epochs 100
```

训练产物（包括最佳权重 `best.pt`）将自动保存在项目根目录的 `runs/train/` 文件夹下。

## 贡献与许可

本代码仅供 COMP5523 课程项目学习与交流使用。
