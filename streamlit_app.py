import streamlit as st
from utils.auth import (
    check_authentication,
    logout,
    get_user_email,
    get_user_display_name,
    login_anonymously,
    handle_google_callback,
)
from modules import login, signup, chat
from utils.firestore import get_user_chats, create_new_chat, delete_chat
import urllib.parse
import os

st.set_page_config(page_title="GPT 채팅", page_icon=":robot_face:", layout="wide")

AVAILABLE_MODELS = [
    "gpt-4o",
    "gpt-4o-mini",
    "gpt-4-turbo",
    "gpt-4",
    "gpt-3.5-turbo-0125",
    "llama-3.1-8b-instant",
]


def main():
    query_params = st.experimental_get_query_params()
    if "code" in query_params:
        code = query_params["code"][0]
        decoded_code = urllib.parse.unquote(code)
        if handle_google_callback(decoded_code):
            st.experimental_set_query_params()
            st.rerun()

    if "user" not in st.session_state:
        login_anonymously()

    with st.sidebar:
        st.title("GPT 채팅")
        user_email = get_user_email()
        if "user" in st.session_state and st.session_state["user"].startswith("anon"):
            st.markdown(
                "<p style='text-align:center;'>환영합니다! 로그인해주세요.</p>",
                unsafe_allow_html=True,
            )
            if st.button("로그인", key="sidebar_login_button"):
                st.session_state["show_login"] = True
                st.rerun()
        else:
            if user_email:
                st.markdown(
                    f"<p style='text-align:center;'>로그인 상태: {get_user_display_name() or user_email}</p>",
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    "<p style='text-align:center;'>로그인 상태: 익명</p>",
                    unsafe_allow_html=True,
                )
            if st.button("로그아웃", key="sidebar_logout_button"):
                logout()
                st.rerun()

        model = st.selectbox(
            "GPT 모델 선택",
            AVAILABLE_MODELS,
            index=0,
        )
        st.session_state["model"] = model

        st.markdown("## 채팅 기록")
        user_chats = get_user_chats(st.session_state["user"])
        chat_ids = [
            (chat.id, chat.to_dict().get("summary", "새로운 채팅"))
            for chat in user_chats
        ]

        if chat_ids:
            if "selected_chat" not in st.session_state:
                st.session_state["selected_chat"] = chat_ids[0][0]

            col1, col2 = st.columns([2, 1])
            with col1:
                selected_chat = st.selectbox(
                    "채팅 선택",
                    [chat_id for chat_id, _ in chat_ids],
                    format_func=lambda x: next(
                        (summary for cid, summary in chat_ids if cid == x), x
                    ),
                    key="chat_selectbox",
                    label_visibility="collapsed",
                )
            with col2:
                if st.button(
                    "삭제", key="delete_chat_button", use_container_width=True
                ):
                    if selected_chat:
                        delete_chat(st.session_state["user"], selected_chat)
                        st.session_state.pop("selected_chat", None)
                        st.rerun()
        else:
            selected_chat = None

        st.session_state["selected_chat"] = selected_chat

        if st.button("새 채팅 시작", key="new_chat_button", use_container_width=True):
            new_chat_id = create_new_chat(st.session_state["user"])
            st.session_state["selected_chat"] = new_chat_id
            st.rerun()

    if "show_login" in st.session_state and st.session_state["show_login"]:
        login.render()
    elif "show_signup" in st.session_state and st.session_state["show_signup"]:
        signup.render()
    else:
        if "selected_chat" in st.session_state and st.session_state["selected_chat"]:
            chat.render(st.session_state["selected_chat"], st.session_state["model"])
        else:
            if not chat_ids:
                new_chat_id = create_new_chat(st.session_state["user"])
                st.session_state["selected_chat"] = new_chat_id
                st.rerun()
            else:
                st.write(
                    "선택된 채팅이 없습니다. 새 채팅을 생성하거나 기존 채팅을 선택하세요."
                )


if __name__ == "__main__":
    main()
