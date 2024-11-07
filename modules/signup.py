# signup.py

import streamlit as st
from utils.auth import signup
from utils.firestore import create_new_chat


def render():
    # 페이지 타이틀 및 설명
    st.markdown(
        """
        <div style='text-align: center; margin-top: 40px; margin-bottom: 40px;'>
            <h1>회원가입</h1>
            <p style='color: gray;'>간단히 회원가입하고 모든 기능을 이용하세요.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 이메일 및 비밀번호 입력 폼
    email = st.text_input(
        "이메일", key="signup_email", placeholder="example@example.com"
    )
    password = st.text_input(
        "비밀번호", type="password", key="signup_password", placeholder="비밀번호"
    )

    # 가입하기 버튼
    if st.button("가입하기", key="signup_create_button"):
        success = signup(email, password)
        if success:
            st.session_state["show_signup"] = False
            st.experimental_set_query_params()
            st.session_state["show_login"] = False
            user = st.session_state.get("user")
            if user:
                new_chat_id = create_new_chat(user)
                st.session_state["selected_chat"] = new_chat_id
            st.rerun()

    # 구분선
    st.markdown(
        "<hr style='margin-top: 40px; margin-bottom: 40px;'>", unsafe_allow_html=True
    )
