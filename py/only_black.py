# -*- coding: utf-8 -*-
# 根據閾值過濾圖片，保留大於一定透明度閾值的像素

# pip install numpy
# pip install opencv-python

import cv2
import numpy as np

INPUT_FN = 'input_image.png'
OUTPUT_FN = 'output_image.png'

# 读取图像（支持 PNG 透明度）
image = cv2.imread(INPUT_FN, cv2.IMREAD_UNCHANGED)  # 保留 Alpha 通道

# 检查图像是否有 Alpha 通道
if image.shape[2] == 3:  # 如果没有 Alpha 通道，添加一个
    image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

# 定义纯黑色（BGR 格式）
pure_black = np.array([0, 0, 0], dtype=np.uint8)

# 创建一个掩码，标记纯黑色且不透明的像素
# 条件：RGB 值为 [0, 0, 0]，且 Alpha 值为 255（100% 不透明）
black_mask = np.all(image[:, :, :3] == pure_black, axis=-1) & (image[:, :, 3] == 255)

# 创建一个全透明的图像
result_image = np.zeros_like(image)  # 初始化为全透明

# 将纯黑色且不透明的像素复制到结果图像
result_image[black_mask] = image[black_mask]

# 保存结果
cv2.imwrite(OUTPUT_FN, result_image)

# 显示结果
cv2.imshow('Result', result_image)
cv2.waitKey(0)
cv2.destroyAllWindows()