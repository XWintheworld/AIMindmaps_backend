# coding=utf-8
import requests
from openai import OpenAI
import os
import hashlib
import time

# 初始化 OpenAI 客户端
client = OpenAI()

print('openai start')

# 生成图片并返回本地 URL
def generate_image_and_save(prompt):
    try:
        # 调用 OpenAI DALLE 生成图片
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )

        # 获取生成的图片 URL
        image_url = response.data[0].url

        # 生成 prompt 的哈希值作为文件名
        hash_object = hashlib.md5(prompt.encode())
        hash_filename = hash_object.hexdigest()

        # 添加时间戳确保唯一性
        timestamp = int(time.time())

        # 确定图片文件名和保存路径
        image_name = f"{hash_filename}_{timestamp}.jpg"  # 使用哈希值和时间戳生成文件名
        image_path = os.path.join('static', 'images', image_name)

        print(image_path)

        # 下载图片并保存到本地文件系统
        image_data = requests.get(image_url).content
        with open(image_path, 'wb') as handler:
            handler.write(image_data)
        
        print('openai complete')

        # 返回图片的本地 URL
        return f"http://localhost:5000/static/images/{image_name}"

    except Exception as e:
        print(f"Error generating or saving image: {str(e)}")
        return None
