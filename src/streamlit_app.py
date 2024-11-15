import streamlit as st
import os
from config import Config
from chatbot import ChatBot
from content_formatter import ContentFormatter
from content_assistant import ContentAssistant
from image_advisor import ImageAdvisor
from input_parser import parse_input_text
from ppt_generator import generate_presentation
from template_manager import load_template, get_layout_mapping
from layout_manager import LayoutManager
from logger import LOG
from openai_whisper import asr, transcribe

# 初始化配置和组件
config = Config()
chatbot = ChatBot(config.chatbot_prompt)
content_formatter = ContentFormatter(config.content_formatter_prompt)
content_assistant = ContentAssistant(config.content_assistant_prompt)
image_advisor = ImageAdvisor(config.image_advisor_prompt)

# 加载 PowerPoint 模板
ppt_template = load_template(config.ppt_template)
layout_manager = LayoutManager(get_layout_mapping(ppt_template))

def generate_contents(text_input, uploaded_files):
    try:
        texts = []
        if text_input:
            texts.append(text_input)

        for uploaded_file in uploaded_files or []:
            file_ext = os.path.splitext(uploaded_file.name)[1].lower()
            if file_ext in ('.wav', '.flac', '.mp3'):
                # 保存上传的音频文件
                with open(f"temp/{uploaded_file.name}", "wb") as f:
                    f.write(uploaded_file.getvalue())
                audio_text = asr(f"temp/{uploaded_file.name}")
                texts.append(audio_text)
                os.remove(f"temp/{uploaded_file.name}")
            elif file_ext in ('.docx', '.doc'):
                with open(f"temp/{uploaded_file.name}", "wb") as f:
                    f.write(uploaded_file.getvalue())
                raw_content = generate_markdown_from_docx(f"temp/{uploaded_file.name}")
                markdown_content = content_formatter.format(raw_content)
                os.remove(f"temp/{uploaded_file.name}")
                return content_assistant.adjust_single_picture(markdown_content)

        user_requirement = "需求如下:\n" + "\n".join(texts)
        LOG.info(user_requirement)
        return chatbot.chat_with_history(user_requirement)

    except Exception as e:
        LOG.error(f"[内容生成错误]: {e}")
        st.error("网络问题，请重试 :)")
        return None

def handle_image_generate(content):
    try:
        content_with_images, image_pair = image_advisor.generate_images(content)
        return content_with_images
    except Exception as e:
        LOG.error(f"[配图生成错误]: {e}")
        st.error("未找到合适配图，请重试！")
        return None

def handle_generate(content):
    try:
        powerpoint_data, presentation_title = parse_input_text(content, layout_manager)
        output_pptx = f"outputs/{presentation_title}.pptx"
        generate_presentation(powerpoint_data, config.ppt_template, output_pptx)
        return output_pptx
    except Exception as e:
        LOG.error(f"[PPT 生成错误]: {e}")
        st.error("请先输入你的主题内容或上传文件")
        return None

# Streamlit UI
st.title("ChatPPT")

# 用户输入区域
text_input = st.text_area("输入你的主题内容", height=200)
uploaded_files = st.file_uploader("或上传文件", accept_multiple_files=True, type=['wav', 'flac', 'mp3', 'docx', 'doc'])

# 生成内容按钮
if st.button("生成内容"):
    if text_input or uploaded_files:
        with st.spinner("正在生成内容..."):
            content = generate_contents(text_input, uploaded_files)
            if content:
                st.session_state['current_content'] = content
                st.markdown(content)

# 配图按钮
if st.button("一键为 PowerPoint 配图"):
    if 'current_content' in st.session_state:
        with st.spinner("正在生成配图..."):
            content_with_images = handle_image_generate(st.session_state['current_content'])
            if content_with_images:
                st.session_state['current_content'] = content_with_images
                st.markdown(content_with_images)
    else:
        st.warning("请先生成内容")

# 生成PPT按钮
if st.button("一键生成 PowerPoint"):
    if 'current_content' in st.session_state:
        with st.spinner("正在生成PPT..."):
            output_file = handle_generate(st.session_state['current_content'])
            if output_file and os.path.exists(output_file):
                with open(output_file, "rb") as file:
                    st.download_button(
                        label="下载 PowerPoint",
                        data=file,
                        file_name=os.path.basename(output_file),
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
                    )
    else:
        st.warning("请先生成内容") 