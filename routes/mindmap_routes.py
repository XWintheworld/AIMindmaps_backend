from flask import Blueprint, request, jsonify
from models.mindmap import Mindmap
from openai import OpenAI
import json  # 引入json库
import os

# 创建蓝图，用于注册路由
mindmap_bp = Blueprint('mindmap', __name__)

# 定义上传文件保存路径
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)



@mindmap_bp.route('/update', methods=['POST'])
def update_mindmap():
    try:
        # 从请求体中获取传回的思维导图数据
        print(request.headers)  # 打印请求头，看看请求格式是否正确
        print(request.data)  # 打印原始请求体，看看是否有数据
        mindmap_data = request.json
        

        print(mindmap_data)

        # 检查数据是否包含所需字段
        if not mindmap_data:    #原因是传递的数据结构发生变化，（若还是报错，可以尝试删掉or后面的内容）or 'uid' not in mindmap_data
            return jsonify({"error": "Invalid data structure"}), 400

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


openai_client = OpenAI()

@mindmap_bp.route('/generate', methods=['POST'])
def generate_mindmap():
    try:
        # 获取上传的 PDF 文件和层数
        pdf_file = request.files['pdf']
        number_of_layers = request.form.get('layers')

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

        print(f'Please help me summarize the key points from this PDF file into a structured mind map with {number_of_layers} hierarchical layers. The output should follow this format:')

        # 创建线程并附加文件到消息
        thread = openai_client.beta.threads.create(
            messages=[
                {
                    "role": "user",
                    "content": f"""
                        Please help me summarize the key points from this PDF file into a structured mind map with {number_of_layers} hierarchical layers. The output should follow this format:

                        {{
                        "data": {{
                            "text": "root node content"
                        }},
                        "children": [
                            {{
                            "data": {{
                                "text": "first-level node content"
                            }},
                            "children": [
                                {{
                                "data": {{
                                    "text": "second-level node content"
                                }},
                                "children": [
                                    {{
                                    "data": {{
                                        "text": "third-level node content"
                                    }},
                                    "children": []
                                    }}
                                ]
                                }}
                            ]
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

        # 数据埋点的时候可以思考如何保存首次的number of layers
        # 将生成的思维导图数据存储到 MongoDB 
        # mindmap_data = {"content": message_content, "layers": number_of_layers}
        # db.mindmap_collection.insert_one(mindmap_data)
        parse_content = message_content.value

        if '```json' in parse_content:
            try:
                final_data = parse_content.split('```json')[1].split('```')[0].strip()
                print(final_data)
            except IndexError:
                print("Error: code block not found or improperly formatted.")
        else:
            print("Error: No code block found in the message content.")

        #  确保final_data是有效的JSON字符串
        try:
            final_data_dict = json.loads(final_data)  # 将字符串解析为字典
            return jsonify(final_data_dict), 200  # 返回JSON响应
        except json.JSONDecodeError as e:
            return jsonify({"error": "Invalid JSON format"}), 500


    except Exception as e:
        return jsonify({"error": str(e)}), 500