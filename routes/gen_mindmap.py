from flask import Blueprint, request, jsonify
from openai import OpenAI

# 创建蓝图
mindmap_bp = Blueprint('mindmap', __name__)

# # MongoDB 连接  --暂时不需要保存数据到数据库
# client = MongoClient('mongodb://localhost:27017/')
# db = client.mindmaps

# 初始化 OpenAI 客户端
openai_client = OpenAI()

@mindmap_bp.route('/generate', methods=['POST'])
def generate_mindmap():
    try:
        # 获取上传的 PDF 文件和层数
        pdf_file = request.files['pdf']
        number_of_layers = request.form.get('layers')

        # 上传 PDF 到 OpenAI 的 API
        assistant = openai_client.beta.assistants.create(
            name="Mindmap Assistant",
            instructions="You are a mind map master.",
            model="gpt-4o",
            tools=[{"type": "file_search"}],
        )

        vector_store = openai_client.beta.vector_stores.create(name="database")
        file_streams = [pdf_file.stream]  # PDF 文件流
        file_batch = openai_client.beta.vector_stores.file_batches.upload_and_poll(
            vector_store_id=vector_store.id, files=file_streams
        )

        # 更新助理工具资源
        openai_client.beta.assistants.update(
            assistant_id=assistant.id,
            tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
        )

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

        print("message:",message_content)

        # 数据埋点的时候可以思考如何保存首次的number of layers
        # 将生成的思维导图数据存储到 MongoDB 
        # mindmap_data = {"content": message_content, "layers": number_of_layers}
        # db.mindmap_collection.insert_one(mindmap_data)

        # 返回思维导图数据
        return jsonify(message_content)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
