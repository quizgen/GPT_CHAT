# login.py

import streamlit as st
from utils.auth import login, login_with_google


def render():
    # 페이지 타이틀 및 설명
    st.markdown(
        """
        <div style='text-align: center; margin-top: 20px; margin-bottom: 20px;'>
            <h1>로그인</h1>
            <p style='color: gray;'>계속하려면 로그인하세요</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Google로 계속하기 버튼
    auth_url = login_with_google()
    st.markdown(
        f"""
        <div style='text-align: center; margin-bottom: 30px;'>
            <a href="{auth_url}">
                <button style="background-color: #4285F4; color: white; padding: 12px 24px; border-radius: 4px; font-size: 18px; cursor: pointer; border: none;">Google로 계속하기</button>
            </a>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 구분선
    st.markdown("<hr style='margin: 40px 0;'>", unsafe_allow_html=True)

    # 이메일 및 비밀번호 입력 폼
    st.markdown(
        "<h3 style='text-align: center; margin-bottom: 20px;'>이메일로 로그인</h3>",
        unsafe_allow_html=True,
    )
    email = st.text_input(
        "이메일 입력", key="login_email", placeholder="example@example.com"
    )
    password = st.text_input(
        "비밀번호", type="password", key="login_password", placeholder="비밀번호"
    )

    # 로그인 및 회원가입 버튼이 같은 라인에 존재하도록 설정
    col1, col2, col3 = st.columns([1, 1.5, 1.5])

    with col1:
        if st.button("로그인", key="email_login_button"):
            if login(email, password):
                st.session_state["show_login"] = False
                st.rerun()

    with col2:
        st.markdown(
            """
            <p style='margin-top: 10px; color: gray; text-align: center;'>계정이 없으신가요?</p>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        if st.button("회원가입", key="signup_button"):
            st.session_state["show_login"] = False
            st.session_state["show_signup"] = True
            st.rerun()
