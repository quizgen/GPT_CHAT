import streamlit as st
import streamlit.components.v1 as components
from utils.auth import (
    check_authentication,
    logout,
    get_user_email,
    get_user_display_name,
    login_anonymously,
    handle_google_callback,
)
from datetime import datetime, timedelta
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


def format_chat_date(chat_date):
    """채팅 날짜를 포맷팅하는 함수"""
    if not chat_date:
        return "날짜 없음"

    chat_date = chat_date.replace(tzinfo=None)  # timezone 정보 제거
    now = datetime.now()

    if chat_date.date() == now.date():
        return chat_date.strftime("%H:%M")
    elif chat_date.date() == (now - timedelta(days=1)).date():
        return "어제"
    elif now - timedelta(days=7) <= chat_date:
        return chat_date.strftime("%A")  # 요일
    else:
        return chat_date.strftime("%Y-%m-%d")


def group_chats_by_date(chats):
    """채팅을 날짜별로 그룹화하는 함수"""
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)

    today_chats = []
    yesterday_chats = []
    week_chats = []
    month_chats = []
    older_chats = []

    for chat in chats:
        chat_date = chat.get("created_at")
        if not chat_date:
            older_chats.append(chat)
            continue

        chat_date = chat_date.replace(tzinfo=None)  # timezone 정보 제거

        if chat_date.date() == now.date():
            today_chats.append(chat)
        elif chat_date.date() == yesterday.date():
            yesterday_chats.append(chat)
        elif chat_date >= week_ago:
            week_chats.append(chat)
        elif chat_date >= month_ago:
            month_chats.append(chat)
        else:
            older_chats.append(chat)

    return {
        "오늘": today_chats,
        "어제": yesterday_chats,
        "지난 7일": week_chats,
        "지난 30일": month_chats,
        "이전": older_chats,
    }


def render_chat_group(chats, title):
    """채팅 그룹을 렌더링하는 함수"""
    if not chats:
        return

    st.markdown(f"#### {title}")
    for chat in chats:
        col1, col2 = st.columns([5, 1])
        with col1:
            if st.button(
                chat.get("summary", "새로운 채팅"),
                key=f"chat_{chat['id']}",
                use_container_width=True,
            ):
                st.session_state["selected_chat"] = chat["id"]
                st.rerun()
        with col2:
            if st.button("삭제", key=f"delete_{chat['id']}", use_container_width=True):
                delete_chat(st.session_state["user"], chat["id"])
                if st.session_state.get("selected_chat") == chat["id"]:
                    st.session_state.pop("selected_chat", None)
                st.rerun()


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

        # 로그인 상태 표시
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

        # 모델 선택
        model = st.selectbox(
            "GPT 모델 선택",
            AVAILABLE_MODELS,
            index=0,
        )
        st.session_state["model"] = model

        # 새 채팅 버튼
        if st.button("새 채팅 시작", key="new_chat_button", use_container_width=True):
            new_chat_id = create_new_chat(st.session_state["user"])
            st.session_state["selected_chat"] = new_chat_id
            st.rerun()

        # 채팅 기록 섹션
        st.markdown("## 채팅 기록")

        user_chats = get_user_chats_with_metadata(st.session_state["user"])
        if user_chats:
            grouped_chats = group_chats_by_date(user_chats)

            # 각 그룹별로 채팅 표시
            for group_title, chats in grouped_chats.items():
                render_chat_group(chats, group_title)

            # 선택된 채팅이 없으면 첫 번째 채팅 선택
            if "selected_chat" not in st.session_state and user_chats:
                st.session_state["selected_chat"] = user_chats[0]["id"]

    # 메인 컨텐츠 영역
    if "show_login" in st.session_state and st.session_state["show_login"]:
        login.render()
    elif "show_signup" in st.session_state and st.session_state["show_signup"]:
        signup.render()
    else:
        if "selected_chat" in st.session_state and st.session_state["selected_chat"]:
            chat.render(st.session_state["selected_chat"], st.session_state["model"])
        else:
            if not user_chats:
                new_chat_id = create_new_chat(st.session_state["user"])
                st.session_state["selected_chat"] = new_chat_id
                st.rerun()
            else:
                st.write(
                    "선택된 채팅이 없습니다. 새 채팅을 생성하거나 기존 채팅을 선택하세요."
                )


if __name__ == "__main__":
    main()
