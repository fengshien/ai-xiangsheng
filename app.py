import gradio as gr
import autogen
import os

# 1. 配置模型
API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-***")

config_list = [{
    "model": "deepseek-chat",
    "api_key": API_KEY,
    "base_url": "https://api.deepseek.com/v1"
}]

llm_config = {"config_list": config_list, "timeout": 180, "temperature": 0.8, "max_tokens": 1024}

# 2. 定义相声演员
dougen = autogen.AssistantAgent(
    name="老赵",
    system_message="""你是一位天津传统相声的逗哏演员。你幽默风趣，善于将日常话题转化为喜剧素材。
    根据用户提供的主题，按“垫话-正活（三翻四抖）-底”的结构输出台词。
    语言风格要有浓郁的天津特色，多用“得嘞”、“好么”、“嚯”等语气词。
    【格式要求】：你的台词必须以“老赵：”开头。""",
    llm_config=llm_config,
)

penggen = autogen.AssistantAgent(
    name="老李",
    system_message="""你是一位传统相声的捧哏演员，名字叫老李。你的搭档是逗哏老赵。
    你的职责是配合逗哏，给出简短、精准的评论（如“嚯？”、“好嘛”）。
    绝对禁止连续说超过两句话！绝对禁止抢逗哏风头！
    【格式要求】：你的台词必须以“老李：”开头。""",
    llm_config=llm_config,
)

director = autogen.UserProxyAgent(
    name="导演",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    code_execution_config={"use_docker": False},
)

# 3. 核心创作函数
def generate_script(topic):
    if not topic.strip():
        return "请先输入一个相声主题！"
    
    groupchat = autogen.GroupChat(
        agents=[director, dougen, penggen], 
        messages=[], 
        max_round=12, 
        speaker_selection_method="round_robin"
    )
    manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

    try:
        director.initiate_chat(manager, message=f"请老赵和老李上台，说一段相声。主题是《{topic}》，包袱要密集！")
        
        script_lines = []
        for msg in groupchat.messages:
            if msg.get("role") == "user" and msg.get("name") in ["老赵", "老李"]:
                script_lines.append(msg.get("content", "").strip())
        
        return "\n\n".join(script_lines) if script_lines else "AI 正在后台努力创作，但似乎没有返回有效台词，请重试一次。"
    
    except Exception as e:
        return f"生成出错了！错误信息：{str(e)}"

# 4. 网页界面
with gr.Blocks(title="AI相声剧本工坊") as demo:
    gr.Markdown("## 🎭 AI 相声剧本工坊")
    gr.Markdown("输入一个主题（如：天津煎饼果子），AI 逗哏老赵和捧哏老李将为您现场创作一段津味相声！")
    
    with gr.Row():
        topic_input = gr.Textbox(label="相声主题", placeholder="例如：天津煎饼果子的讲究", scale=3)
        generate_btn = gr.Button("开始创作", scale=1)
    
    output_text = gr.Textbox(label="生成剧本", lines=20)
    generate_btn.click(fn=generate_script, inputs=topic_input, outputs=output_text)

# 5. 本地启动（兼容云端端口）
    import os
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port)
