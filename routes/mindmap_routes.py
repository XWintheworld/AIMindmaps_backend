# coding=utf-8
from flask import Blueprint, request, jsonify
from models.mindmap import Mindmap
from openai import OpenAI
import json  # 引入json库
import os
from models.images import NodeImages
from models.user import User
from models.mindmap import Mindmap
from services.openai_service import generate_image_and_save

# 创建蓝图，用于注册路由
mindmap_bp = Blueprint('mindmap', __name__)

# 定义上传文件保存路径
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@mindmap_bp.route('/login', methods=['POST'])
def login():
    try:
        # 获取前端传递的用户名
        username = request.json.get('username')
        if not username:
            return jsonify({"error": "Missing username"}), 400

        # 创建用户或获取已有用户的 user_id
        user_id = User.create_user(username)

        return jsonify({
            "message": "Login successful",
            "user_id": user_id
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@mindmap_bp.route('/get_images', methods=['GET'])
def get_images_for_node():
    try:
        # 获取请求参数
        node_uid = request.args.get('uid')

        if not node_uid:
            return jsonify({"error": "Missing node uid"}), 400

        # 从数据库获取节点的图片信息
        node_images = NodeImages.get_images_by_node_id(node_uid)

        if not node_images:
            return jsonify({"error": "Node not found"}), 404

        # 获取当前图片的 URL
        current_image_url = node_images.get('current_image', {}).get('url', None)

        # 将历史图片解析为 URL 列表
        history_images_urls = [image.get('url') for image in node_images.get('history_images', [])]

        return jsonify({
            "display_image": current_image_url,
            "history_images": history_images_urls
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@mindmap_bp.route('/update', methods=['POST'])
def update_mindmap():
    try:
        # 从请求体中获取传回的思维导图数据
        mindmap_data = request.json.get('mindmap_data')
        user_id = request.json.get('user_id')

        # print('user_id',user_id)

        # 检查数据是否包含所需字段
        if not mindmap_data or not user_id:
            return jsonify({"error": "Invalid data structure or missing user_id"}), 400
        
        # 将 user_id 添加到思维导图数据中
        mindmap_data['user_id'] = user_id

        # print('mindmap_data:', mindmap_data)
        print('mindmap_data user_id:', mindmap_data['user_id'])

        # 调用数据模型更新数据库中的思维导图
        updated = Mindmap.update_mindmap(mindmap_data)

        if updated:
            return jsonify({"message": "Mindmap updated successfully"}), 200
        else:
            return jsonify({"error": "Mindmap update failed"}), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@mindmap_bp.route('/get', methods=['GET'])
def get_mindmap():
    try:
        # 从请求中获取 UID
        uid = request.args.get('uid')
        if not uid:
            return jsonify({"error": "UID is required"}), 400

        # 查询数据库
        mindmap_data = Mindmap.get_by_uid(uid)

        if mindmap_data:
            return jsonify(mindmap_data), 200
        else:
            return jsonify({"error": "Mindmap not found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@mindmap_bp.route('/generate_image', methods=['POST'])
def generate_image_for_node():
    try:
        # 获取请求参数
        prompt = request.json.get('prompt')
        node_uid = request.json.get('uid')
        user_id = request.json.get('user_id')  # 获取 user_id

        if not prompt or not node_uid or not user_id:
            return jsonify({"error": "Missing prompt, uid, or user_id"}), 400

        # 调用 OpenAI DALLE 生成新图片并保存到本地
        new_image_url = generate_image_and_save(prompt)

        print('new_image_url',new_image_url)

        if not new_image_url:
            return jsonify({"error": "Image generation failed"}), 500
        
        # 获取当前节点的图片信息
        node_images = NodeImages.get_images_by_node_id(node_uid)
        
        if not node_images:
            # 如果 node_uid 在数据库中不存在，则创建新的图片记录
            history_images = []
            print(f"Node {node_uid} not found in the database. Creating new record.")   #输出到这报错了
        else:
            # 如果存在当前节点的图片信息，提取历史图片
            history_images = node_images.get('history_images', [])
            if node_images.get('current_image'):
                history_images.append(node_images['current_image'])
        
        # 更新节点的图片信息（如果不存在则插入新记录）
        updated = NodeImages.update_images_by_node_id(node_uid, new_image_url, prompt, history_images, user_id)

        print('updated',updated)

        if updated:
            return jsonify({
                "message": "Image updated successfully", 
                "image": new_image_url, 
                "history_images": [img.get('url') for img in history_images]   # 基于目前的数据结构如何保证只return 包含有url的list数据？ --用代码解析？
            }), 200
        else:
            return jsonify({"error": "Failed to update node"}), 500


    except Exception as e:
        return jsonify({"error": str(e)}), 500

openai_client = OpenAI()

@mindmap_bp.route('/generate', methods=['POST'])
def generate_mindmap():
    try:
        # 获取上传的 PDF 文件和层数
        pdf_file = request.files['pdf']
        level_of_detail = request.form.get('layers')
        user_id = request.form.get('user_id') 

        if not user_id:
            return jsonify({"error": "Missing user_id"}), 400

        # 将文件保存到本地
        file_path = os.path.join(UPLOAD_FOLDER, pdf_file.filename)
        pdf_file.save(file_path)
        

        # 上传 PDF 到 OpenAI 的 API
        assistant = openai_client.beta.assistants.create(
            name="Mindmap Assistant",
            instructions="You are a mind map master.",
            model="gpt-4o",
            tools=[{"type": "file_search"}],
        )

        # # 将 PDF 文件转换为字节流
        # pdf_bytes = BytesIO(pdf_file.read())
        # file_streams = [pdf_bytes]  # 确保传递的是字节流
        # 准备文件流列表，读取保存的文件
        file_paths = [file_path]
        file_streams = [open(path, "rb") for path in file_paths]

        vector_store = openai_client.beta.vector_stores.create(name="database")
        

        # # upload_and_poll 出现问题
        # file_batch = openai_client.beta.vector_stores.file_batches.upload_and_poll(
        #     vector_store_id=vector_store.id, files=file_streams
        # )
        try:
            file_batch = openai_client.beta.vector_stores.file_batches.upload_and_poll(
                vector_store_id=vector_store.id, files=file_streams
            )
            print(f"File batch uploaded successfully: {file_batch}")
        except Exception as e:
            print(f"File upload failed: {e}")
            raise
        
        # 更新助理工具资源
        openai_client.beta.assistants.update(
            assistant_id=assistant.id,
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
        )

        print(f'Please help me summarize the key points from this PDF file into a structured mind map with {level_of_detail} level of detail. The output should follow this format:')

        # 创建线程并附加文件到消息
        thread = openai_client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": f"""
                        Please help me summarize the key points from this PDF file into a structured mind map with {level_of_detail} level of detail. The output should follow this format:

                        {{
                            "data": {{
                                "text": "root node content"
                            }},
                            "children": [
                                {{
                                    "data": {{
                                        "text": "subnode content"
                                    }},
                                    "children": []
                                }}
                            ]
                        }}
                        """
                }
            ]
        )

        # 运行并等待结果
        run = openai_client.beta.threads.runs.create_and_poll(
            thread_id=thread.id, assistant_id=assistant.id
        )

        # 获取并解析返回的消息
        messages = list(openai_client.beta.threads.messages.list(thread_id=thread.id, run_id=run.id))
        message_content = messages[0].content[0].text

        # print("message:",message_content)

        parse_content = message_content.value

        # print("message:",parse_content)

        if '```json' in parse_content:
            print("message:")
            try:
                final_data = parse_content.split('```json')[1].split('```')[0].strip()
                print('final_data',final_data)
            except IndexError:
                print("Error: code block not found or improperly formatted.")
        else:
            print("Error: No code block found in the message content.")

        print('parsed')
        #  确保final_data是有效的JSON字符串
        try:
            final_data_dict = json.loads(final_data)  # 将字符串解析为字典
            saved_record = Mindmap.save_mindmap(user_id, pdf_file.filename, level_of_detail, final_data_dict)
            print('saved_record:',saved_record)
            return jsonify(final_data_dict), 200  # 返回JSON响应
        except json.JSONDecodeError as e:
            print('Invalid JSON format')
            return jsonify({"error": "Invalid JSON format"}), 500


    except Exception as e:
        return jsonify({"error": str(e)}), 500