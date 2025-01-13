# -*- coding: utf-8 -*-
# 使用顔色過濾圖片，只保留與配置顔色最臨近的顔色

# pip install numpy
# pip install opencv-python

import cv2
import numpy as np
from sklearn.cluster import KMeans

# 定义目标颜色列表（十六进制格式）
TARGET_COLOR_HEX = '''
fefefe
111111
d7190d
fcc60c
193e85
4a8c2a
7fbd70
767ec9
fa8c19
'''
INPUT_FN = 'input_image.png'
OUTPUT_FN = 'output_image.png'

# 将十六进制颜色转换为 RGB 格式
def hex_to_rgb(hex_color):
    """
    将十六进制颜色字符串转换为 RGB 格式
    """
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

# 将目标颜色列表从十六进制转换为 RGB    
list_color = TARGET_COLOR_HEX.split('\n')
list_color = [item.strip() for item in list_color if item]
target_colors_rgb = [hex_to_rgb(color) for color in list_color]

# 将目标颜色从 RGB 转换为 BGR（因为 OpenCV 使用 BGR 格式）
target_colors_bgr = [color[::-1] for color in target_colors_rgb]
target_colors = np.array(target_colors_bgr, dtype=np.uint8)

# 读取图像（支持 PNG 透明度）
image = cv2.imread(INPUT_FN, cv2.IMREAD_UNCHANGED)  # 保留 Alpha 通道

# 检查图像是否有 Alpha 通道
if image.shape[2] == 3:  # 如果没有 Alpha 通道，添加一个
    image = cv2.cvtColor(image, cv2.COLOR_BGR2BGRA)

# 提取图像的 RGB 颜色数据（忽略 Alpha 通道）
pixels = image[:, :, :3].reshape(-1, 3)

# 使用 K-Means 聚类将颜色分组
num_clusters = len(target_colors)  # 聚类数量等于目标颜色数量

# 使用目标颜色作为初始聚类中心
initial_centers = target_colors.astype(np.float32)
kmeans = KMeans(n_clusters=num_clusters, init=initial_centers, n_init=1, random_state=0).fit(pixels)

# 获取每个像素的聚类标签
labels = kmeans.labels_

# 将每个聚类的颜色替换为目标颜色
quantized_pixels = np.zeros_like(pixels)
for i in range(num_clusters):
    quantized_pixels[labels == i] = target_colors[i]

# 将量化后的颜色重新组合为图像
quantized_image = quantized_pixels.reshape(image.shape[0], image.shape[1], 3)

# 将量化后的颜色与原始 Alpha 通道结合
result_image = np.zeros_like(image)
result_image[:, :, :3] = quantized_image
result_image[:, :, 3] = image[:, :, 3]  # 保留原始 Alpha 通道

# 保存结果
cv2.imwrite(OUTPUT_FN, result_image)

# 显示结果
cv2.imshow('Result', result_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
