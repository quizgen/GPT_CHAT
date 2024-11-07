import uuid
import streamlit as st
import requests
from firebase_admin import auth
from firebase_config import db
from google_auth_oauthlib.flow import Flow
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from firebase_admin import auth
from firebase_admin.auth import UserNotFoundError
import os

# 환경 변수에서 서버 호스트와 포트를 가져옵니다.
# 기본값은 localhost와 8501입니다.
host = os.environ.get("STREAMLIT_SERVER_ADDRESS", "localhost")
port = os.environ.get("STREAMLIT_SERVER_PORT", "8501")

# REDIRECT_URI를 동적으로 설정합니다.
REDIRECT_URI = f"http://{host}:{port}"


def get_google_flow():
    return Flow.from_client_secrets_file(
        "client_secret.json",
        scopes=[
            "openid",
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
        ],
        redirect_uri=REDIRECT_URI,
    )


def signup(email, password):
    try:
        user = auth.create_user(email=email, password=password)
        db.collection("users").document(user.uid).set({"email": email})
        st.session_state["user"] = user.uid
        st.success("User created and logged in successfully.")
        return True
    except auth.EmailAlreadyExistsError:
        st.error("The user with the provided email already exists.")
        return False
    except Exception as e:
        st.error(f"Error creating user: {e}")
        return False


def login(email, password):
    try:
        firebase_auth_url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key=AIzaSyDYK-J_eC1LCtPOCLpwOrgJKhmdDIozZJ8"
        payload = {"email": email, "password": password, "returnSecureToken": True}
        response = requests.post(firebase_auth_url, json=payload)
        response.raise_for_status()
        data = response.json()
        st.session_state["user"] = data["localId"]
        st.success("Logged in successfully")
        st.session_state["show_login"] = False
        st.rerun()
        return True
    except requests.exceptions.HTTPError as e:
        st.error(f"Login failed: {e.response.text}")
        return False


def login_with_google():
    try:
        flow = get_google_flow()
        auth_url, _ = flow.authorization_url(prompt="consent")
        return auth_url
    except Exception as e:
        st.error(f"Google login failed: {e}")
        return None


def handle_google_callback(code):
    try:
        flow = get_google_flow()
        flow.fetch_token(code=code)
        credentials = flow.credentials
        request = google_requests.Request()
        id_info = id_token.verify_oauth2_token(
            credentials.id_token, request, credentials.client_id
        )

        user_id = id_info["sub"]
        user_email = id_info["email"]

        try:
            # Try to get the user by user_id
            user = auth.get_user(user_id)
        except auth.UserNotFoundError:
            # If user is not found, create a new user
            user = auth.create_user(uid=user_id, email=user_email)
            db.collection("users").document(user.uid).set({"email": user_email})

        st.session_state["user"] = user.uid
        return True
    except Exception as e:
        if "invalid_grant" not in str(e):
            st.error(f"Google login callback failed: {e}")
        return False


def login_anonymously():
    try:
        if "user" not in st.session_state:
            anon_id = f"anon-{uuid.uuid4()}"
            st.session_state["user"] = anon_id
            st.success("Logged in anonymously")
    except Exception as e:
        st.error(f"Anonymous login failed: {e}")


def logout():
    if "user" in st.session_state:
        del st.session_state["user"]
        st.success("Logged out successfully")


def check_authentication():
    return "user" in st.session_state and not st.session_state["user"].startswith(
        "anon"
    )


def get_user_id():
    return st.session_state.get("user")


def get_user_email():
    if check_authentication():
        user = auth.get_user(st.session_state["user"])
        return user.email
    return None


def get_user_display_name():
    if check_authentication():
        user = auth.get_user(st.session_state["user"])
        return user.display_name
    return None
