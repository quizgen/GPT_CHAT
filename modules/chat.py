import streamlit as st
from utils.firestore import get_chat_history, save_message, update_chat_summary
from utils.auth import get_user_id
from openai_api import (
    get_response,
    summarize_chat,
    analyze_user_input_for_image_request,
    generate_image,
    analyze_image  # 수정된 부분
)
from firebase_admin import storage
import PyPDF2
import pandas as pd
import os

# Firebase Storage에 이미지 파일을 업로드하고 URL 반환
def upload_file_to_storage(image_file):
    bucket = storage.bucket()  # Firebase Storage 버킷 가져오기
    blob = bucket.blob(image_file.name)  # 파일 이름을 그대로 사용하거나 고유 이름 설정
    blob.upload_from_file(image_file)  # Firebase Storage에 파일 업로드
    blob.make_public()  # 파일을 공개로 설정
    return blob.public_url  # 파일의 공개 URL 반환

def process_file(uploaded_file):
    if uploaded_file.type == "application/pdf":
        return process_pdf(uploaded_file)
    elif uploaded_file.type == "text/csv":
        return process_csv(uploaded_file)
    elif uploaded_file.type in [
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ]:
        return process_word(uploaded_file)
    else:
        return "Unsupported file type."

def process_pdf(file):
    reader = PyPDF2.PdfReader(file)
    text = ""
    for page in range(len(reader.pages)):
        text += reader.pages[page].extract_text()
    return text

def process_csv(file):
    df = pd.read_csv(file)
    return df.to_string()

def process_word(file):
    try:
        import docx
    except ImportError:
        return "Please install python-docx to process Word files."

    doc = docx.Document(file)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def render(selected_chat, model):
    st.title("GPT Chat")

    user_id = get_user_id()

    if selected_chat is None:
        st.write(
            "No chat selected. Please create a new chat or select an existing one."
        )
        return

    if f"chat_history_{selected_chat}" not in st.session_state:
        chat_history = get_chat_history(user_id, selected_chat)
        st.session_state[f"chat_history_{selected_chat}"] = chat_history
        st.session_state[f"summary_created_{selected_chat}"] = False
    else:
        chat_history = st.session_state[f"chat_history_{selected_chat}"]

    for chat in chat_history:
        with st.chat_message(chat["role"]):
            st.markdown(chat["message"])

    if model == "gpt-3.5-turbo-0125" or model == "llama-3.1-8b-instant":
        file = None  # 파일 업로드 기능 비활성화
        if not st.session_state.get("chat_started", False):
            st.warning(f"{model} 모델에서는 파일 업로드가 지원되지 않습니다.")
    else:
        file = st.file_uploader(
            "Upload file",
            type=["pdf", "csv", "docx", "doc", "png", "jpg", "jpeg"],
            key="file_uploader",
            label_visibility="collapsed",
        )

    prompt = st.chat_input("Send a message", key="chat_input")

    if prompt or file:
        if file and not prompt:
            st.warning("Please enter a message to accompany the file.")
            return

        if prompt:
            st.session_state["chat_started"] = True

        if file:
            if file.type.startswith("image/"):
                # 이미지 파일 처리 및 분석
                with st.chat_message("user"):
                    st.image(file, caption="Uploaded Image", use_column_width=True)
                    st.markdown(prompt)

                # Firebase Storage에 이미지 업로드 후 URL 반환
                image_url = upload_file_to_storage(file)
                save_message(
                    user_id,
                    selected_chat,
                    "user",
                    f"![Uploaded Image]({image_url})\n\n{prompt}",
                )
                chat_history.append(
                    {
                        "role": "user",
                        "message": f"![Uploaded Image]({image_url})\n\n{prompt}",
                    }
                )

                # OpenAI Vision API로 이미지 URL과 사용자 프롬프트 전달하여 분석
                with st.spinner("Analyzing image..."):
                    analysis_result = analyze_image(image_url, model=model, user_prompt=prompt)  # URL과 프롬프트 전달
                    with st.chat_message("assistant"):
                        st.markdown(analysis_result)
                    save_message(user_id, selected_chat, "assistant", analysis_result)
                    chat_history.append({"role": "assistant", "message": analysis_result})
            else:
                # 기타 파일(예: PDF, CSV 등) 처리
                file_content = process_file(file)
                prompt = f"{prompt}\n\nAttached file content:\n{file_content}"

        if prompt and (file is None or not file.type.startswith("image/")):
            with st.chat_message("user"):
                st.markdown(prompt)
            save_message(user_id, selected_chat, "user", prompt)
            chat_history.append({"role": "user", "message": prompt})

            with st.spinner("Analyzing input..."):
                is_image_request = analyze_user_input_for_image_request(prompt)

            if is_image_request:
                with st.spinner("Generating image..."):
                    image_url = generate_image(prompt)

                with st.chat_message("assistant"):
                    if "Error" in image_url:
                        st.markdown(image_url)
                    else:
                        st.image(image_url, caption=prompt, use_column_width=True)
                        st.markdown(f"![Generated Image]({image_url})")
                save_message(
                    user_id,
                    selected_chat,
                    "assistant",
                    f"![Generated Image]({image_url})",
                )
                chat_history.append(
                    {"role": "assistant", "message": f"![Generated Image]({image_url})"}
                )
            else:
                with st.spinner("Thinking..."):
                    response = get_response(chat_history, model)
                    with st.chat_message("assistant"):
                        st.markdown(response)
                    save_message(user_id, selected_chat, "assistant", response)
                    chat_history.append({"role": "assistant", "message": response})

        st.session_state[f"chat_history_{selected_chat}"] = chat_history

        if not st.session_state[f"summary_created_{selected_chat}"]:
            summary = summarize_chat(chat_history)
            update_chat_summary(user_id, selected_chat, summary)
            st.session_state[f"summary_created_{selected_chat}"] = True

        st.rerun()
