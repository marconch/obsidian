#!/usr/bin/env python3
"""
为公众号文章截图打马赛克
处理敏感信息：公司名、人名、车牌号、金额等
"""

from PIL import Image, ImageFilter, ImageDraw
import os

SCREENSHOTS_DIR = "article-screenshots"
OUTPUT_DIR = "article-screenshots-blurred"

# 定义每张图片需要打码的区域 (x1, y1, x2, y2)
# 坐标基于原始图片尺寸 2400x1486
# 注意：显示坐标需要乘以1.2才能得到原始坐标

BLUR_REGIONS = {
    "01-login.png": [
        # 公司帐套下拉框 "上海展形实业有限公司" - 位于左侧表单区域
        (90, 400, 580, 470),  # 调整到下拉框位置
    ],
    "03-purchase-contract-list.png": [
        # 供应商列 - 人名和公司名 (第6列)
        (780, 360, 960, 430),   # 任建瑞
        (780, 450, 960, 560),   # 上海大众众谊
        (780, 560, 960, 680),   # 上海大众众谊
        (780, 690, 960, 760),   # 李超
        (780, 770, 960, 840),   # 陈兴扑
        (780, 860, 960, 950),   # 常州博俊科技
        # 合同所属公司 (第7列)
        (960, 360, 1120, 430),
        (960, 450, 1120, 560),
        (960, 690, 1120, 760),
    ],
    "05-purchase-arrival-edit.png": [
        # 供应商 "李超" - 右上角供应商字段
        (1290, 260, 1450, 320),
        # 车牌号 "皖CF6235" - 车/船号字段
        (900, 390, 1200, 450),
        # 仓库名 "铨富仓" - 商品明细表格中
        (780, 680, 940, 730),
    ],
    "06-sales-contract-list.png": [
        # 客户公司名 (第4列)
        (600, 360, 780, 430),
        (600, 450, 780, 560),
        (600, 545, 780, 620),
        (600, 625, 780, 720),
        (600, 730, 780, 830),
        (600, 830, 780, 920),
        (600, 930, 780, 1010),
        # 合同所属公司 (第5列)
        (800, 360, 960, 430),
        (800, 450, 960, 560),
        (800, 625, 960, 720),
        (800, 730, 960, 830),
    ],
    "09-financial-receivable.png": [
        # 客户公司名 (第6列)
        (1000, 360, 1200, 430),
        (1000, 450, 1200, 540),
        (1000, 545, 1200, 620),
        (1000, 630, 1200, 720),
    ],
}

def apply_mosaic(image, region, block_size=10):
    """对指定区域应用马赛克效果"""
    x1, y1, x2, y2 = region
    
    # 确保坐标在图片范围内
    x1 = max(0, min(x1, image.width))
    x2 = max(0, min(x2, image.width))
    y1 = max(0, min(y1, image.height))
    y2 = max(0, min(y2, image.height))
    
    if x2 <= x1 or y2 <= y1:
        return image
    
    # 裁剪区域
    crop = image.crop((x1, y1, x2, y2))
    
    # 缩小再放大实现马赛克效果
    small_size = (max(1, (x2-x1)//block_size), max(1, (y2-y1)//block_size))
    crop = crop.resize(small_size, Image.Resampling.NEAREST)
    crop = crop.resize((x2-x1, y2-y1), Image.Resampling.NEAREST)
    
    # 粘贴回原图
    image.paste(crop, (x1, y1))
    return image

def process_image(filename, regions):
    """处理单张图片"""
    input_path = os.path.join(SCREENSHOTS_DIR, filename)
    output_path = os.path.join(OUTPUT_DIR, filename)
    
    if not os.path.exists(input_path):
        print(f"文件不存在: {input_path}")
        return False
    
    image = Image.open(input_path)
    print(f"处理: {filename} ({image.width}x{image.height})")
    
    for region in regions:
        image = apply_mosaic(image, region)
    
    image.save(output_path, quality=95)
    print(f"✅ 已处理: {filename}")
    return True

def main():
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 复制所有图片到输出目录（未在列表中的直接复制）
    for filename in os.listdir(SCREENSHOTS_DIR):
        if not filename.endswith('.png'):
            continue
            
        input_path = os.path.join(SCREENSHOTS_DIR, filename)
        output_path = os.path.join(OUTPUT_DIR, filename)
        
        if filename in BLUR_REGIONS:
            process_image(filename, BLUR_REGIONS[filename])
        else:
            # 直接复制不需要处理的图片
            image = Image.open(input_path)
            image.save(output_path)
            print(f"📋 已复制: {filename}")
    
    print(f"\n✨ 处理完成！输出目录: {OUTPUT_DIR}/")

if __name__ == "__main__":
    main()
