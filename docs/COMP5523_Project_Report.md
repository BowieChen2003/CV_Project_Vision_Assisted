# 计算机视觉课程项目报告：视障人士视觉辅助抓取系统
(Project Report: Vision-Assisted Grasping System for the Visually Impaired)

根据课程项目规范 (Group Project Specification)，本报告详细阐述了我们在**数据准备 (Data Preparation)** 和 **算法设计与模型架构 (Algorithm Design)** 两个核心阶段的实现细节。

---

## 1. 数据准备 (Data Preparation)

本项目的数据准备分为三个主要部分，分别用于训练和验证目标物体检测、手部姿态估计，以及模拟真实的抓取场景。

### 1.1 目标检测数据集 (Dataset for Objects)
为了让模型能够准确识别视障人士日常生活中需要抓取的常见物体，我们准备并使用了 **COCO (Common Objects in Context) 2017 数据集** 进行 YOLOv8 模型的训练与微调。
*   **数据规模与类别**：COCO 2017 包含超过 33 万张图像，其中 20 万张具有详细的标注。数据集涵盖了 80 个日常物体类别。在本项目中，我们特别提取了与“日常抓取”高度相关的子集类别，如 `cup` (杯子)、`bottle` (瓶子)、`cell phone` (手机)、`apple` (苹果) 等。
*   **标注格式**：使用 COCO 格式的边界框 (Bounding Box, $x, y, w, h$) 和类别标签。
*   **数据增强 (Data Augmentation)**：在训练过程中，为了提升模型在不同光照、遮挡和视角下的鲁棒性，我们引入了 Mosaic（马赛克数据增强）、MixUp、随机裁剪和色彩抖动 (HSV) 等增强策略。这使得模型在视障人士佩戴的胸前/头部摄像头的复杂第一人称视角 (Egocentric view) 下依然保持高召回率。

### 1.2 手部姿态数据集 (Dataset for Hand Pose)
手部追踪的准确性直接决定了抓取引导的质量。本系统中的手部模型训练基于大规模的**野外真实场景手部数据集 (In-the-wild Hand Dataset)**。
*   **数据特征**：包含约 30,000 张具有丰富背景的真实图像。
*   **关键点标注**：每只手标注了 **21 个 3D 关键点 (3D Landmarks)**。在抓取任务中，我们主要利用其中的 Landmark 9（中指根部，作为手掌中心）和 Landmark 8（食指指尖）作为关键的参考坐标。

### 1.3 触达与抓取视频数据 (Reaching/Grasping Videos)
为了评估系统的空间理解和语音引导策略的延迟与成功率，我们自己录制并构建了一个小型的 **第一人称抓取视频验证集**。
*   **数据内容**：包含不同光照条件下、不同背景桌面上的目标抓取视频（如：手从画面边缘进入，摸索并最终抓住杯子）。
*   **用途**：主要用于离线回放测试，验证动态追踪 (Tracking) 过程中的抖动情况以及“Left/Right/Up/Down/Grasp”引导策略的时效性。

---

## 2. 算法设计与模型架构 (Algorithm Design)

本系统的算法架构分为三个模块：目标检测、手部追踪，以及空间关系理解与引导策略。

### 2.1 目标检测模型架构 (YOLOv8)
在综合对比了多种检测算法（如 Faster R-CNN, SSD, 早期 YOLO 系列）后，我们最终选择了 **YOLOv8n (Nano)** 架构作为目标检测的核心模型。选择 YOLOv8n 的主要原因是其在边缘设备和 CPU 上具有极佳的**实时性 (Real-time performance)**。

YOLOv8 的核心网络架构设计如下：
1.  **Backbone (主干网络)**：采用了改进的 CSPDarknet 结构，使用 C2f (Cross Stage Partial network with 2 convolutions) 模块替代了 YOLOv5 的 C3 模块，进一步丰富了梯度流，提升了特征提取能力。
2.  **Neck (颈部网络)**：采用 PANet (Path Aggregation Network) 结构，实现自顶向下和自底向上的多尺度特征融合，这对识别桌面上的小物体（如钥匙）非常有效。
3.  **Head (检测头)**：采用了 **Decoupled Head (解耦头)** 和 **Anchor-Free (无锚框)** 设计。解耦头将分类和回归任务分开处理，加速了收敛；无锚框设计减少了超参数预测，提高了泛化能力。

### 2.2 手部追踪模型架构 (MediaPipe Hand Tracking)
为了实现轻量级的高精度手部追踪，我们采用了基于两阶段 Pipeline 的算法设计：
1.  **BlazePalm (手掌检测器)**：首先运行于全图，使用类似于 SSD 的单阶段检测架构，快速输出手掌的边界框（Bounding Box）。该模型对不同大小和遮挡的手部具有很强的鲁棒性。
2.  **Hand Landmark Model (手部关键点模型)**：在 BlazePalm 裁剪出的手部感兴趣区域 (ROI) 内运行，利用卷积神经网络直接回归出 21 个 3D 手部关键点的相对坐标。通过使用这种级联架构，显著降低了计算量，确保了整体系统的低延迟。

### 2.3 空间关系理解与引导策略 (Spatial Relation Understanding & Guidance Strategy)
算法的最后一步是将视觉坐标转化为物理引导指令。

*   **空间关系建模 (Spatial Relation)**：
    系统在每一帧中提取目标物体的边界框中心点坐标 $T(x_t, y_t)$ 和手掌核心关键点坐标 $H(x_h, y_h)$。
    我们计算两点之间的二维欧氏距离 (Euclidean Distance)：
    $$ D = \sqrt{(x_t - x_h)^2 + (y_t - y_h)^2} $$
    同时计算水平和垂直方向的偏移量：
    $$ dx = x_t - x_h $$
    $$ dy = y_t - y_h $$

*   **引导策略 (Guidance Strategy)**：
    为了提供**用户友好的音频接口 (User-friendly audio interface)**，我们将复杂的坐标偏移转化为极简的方向指令：
    1.  **抓取判定**：当 $D < D_{threshold}$（如 50 像素）时，系统判定手部已到达目标上方，触发 `"Grasp now!"` (可以抓取) 指令。
    2.  **方向引导**：若未达到抓取距离，系统比较 $|dx|$ 和 $|dy|$ 的大小，优先修正偏移量更大的维度。
        *   若 $|dx| > |dy|$：根据 $dx$ 的正负，触发 `"Move Right"` 或 `"Move Left"`。
        *   若 $|dy| \ge |dx|$：根据 $dy$ 的正负，触发 `"Move Down"` 或 `"Move Up"`。
    
    这种正交分解的引导策略能够避免给视障用户传递过于复杂的斜向指令（如“向右上方移动”），有效降低了用户的认知负荷。
