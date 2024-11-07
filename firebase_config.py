import firebase_admin
from firebase_admin import credentials, firestore, storage

# Firebase 초기화 확인 및 초기화
if not firebase_admin._apps:
    # Firebase 서비스 계정 키 경로
    cred = credentials.Certificate("gpt-chating-c72cacf446d4.json")
    firebase_admin.initialize_app(cred, {
        'storageBucket': 'gpt-chating.appspot.com'  # Firebase Storage 버킷 이름 설정
    })

# Firestore 클라이언트 초기화
db = firestore.client()

# Firebase Storage 사용을 위한 bucket 초기화
bucket = storage.bucket()  # Firebase Storage 기본 버킷을 가져오기
