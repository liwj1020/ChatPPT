import gradio as gr
from config import Config
from chatbot import ChatBot
from input_parser import parse_input_text
from ppt_generator import generate_presentation
from template_manager import load_template, print_layouts, get_layout_mapping
from layout_manager import LayoutManager
from logger import LOG

# 初始化配置和必要组件
config = Config()
chatbot = ChatBot(config.chatbot_prompt)
ppt_template = load_template(config.ppt_template)
layout_manager = LayoutManager(get_layout_mapping(ppt_template))

def generate_contents(message, history):
    """处理用户输入并生成PPT内容格式"""
    # 调用ChatBot生成标准格式的PPT内容
    slides_content = chatbot.chat_with_history(message)
    return slides_content

def handle_generate(history):
    """处理生成PPT按钮点击事件"""
    if not history or len(history) == 0:
        return None
        
    # 获取最后一条AI回复的内容
    slides_content = history[-1][1]
    
    # 解析内容并生成PowerPoint数据结构
    powerpoint_data, presentation_title = parse_input_text(slides_content, layout_manager)
    
    # 定义输出PowerPoint文件路径
    output_pptx = f"outputs/{presentation_title}.pptx"
    
    # 生成PowerPoint文件
    generate_presentation(powerpoint_data, config.ppt_template, output_pptx)
    
    return output_pptx

# 创建Gradio界面
with gr.Blocks(title="ChatPPT") as demo:
    gr.Markdown("""
    # ChatPPT
    与AI对话，轻松生成专业PPT。只需描述您的想法，AI将帮您组织内容并生成演示文稿。
    """)
    
    # 创建聊天界面
    chatbot = gr.Chatbot(
        label="对话历史",
        height=500,
        bubble_full_width=False,
    )
    
    # 创建输入框
    msg = gr.Textbox(
        label="输入您的想法",
        placeholder="描述您想要制作的PPT内容...",
        lines=3
    )
    
    # 清空按钮
    clear = gr.ClearButton([msg, chatbot], value="清空对话")
    
    # 提交按钮
    submit = gr.Button("发送")
    
    # 生成PPT按钮
    generate_btn = gr.Button("生成PPT")
    
    # 文件下载组件
    output_file = gr.File(label="下载生成的PPT")
    
    # 设置事件处理
    msg.submit(generate_contents, [msg, chatbot], [chatbot])
    submit.click(generate_contents, [msg, chatbot], [chatbot])
    generate_btn.click(handle_generate, chatbot, output_file)

if __name__ == "__main__":
    # 启动Gradio服务
    demo.launch(share=True)


    