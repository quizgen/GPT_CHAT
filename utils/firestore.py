from firebase_config import db
from firebase_admin import firestore


def get_user_chats(user_id):
    return (
        db.collection("users")
        .document(user_id)
        .collection("chats")
        .order_by("created_at", direction=firestore.Query.DESCENDING)
        .stream()
    )


def get_chat_history(user_id, chat_id):
    chat_ref = (
        db.collection("users")
        .document(user_id)
        .collection("chats")
        .document(chat_id)
        .collection("messages")
        .order_by("timestamp")
    )
    chats = chat_ref.stream()
    return [
        {"role": chat.to_dict()["role"], "message": chat.to_dict()["message"]}
        for chat in chats
    ]


def save_message(user_id, chat_id, role, message):
    chat_ref = (
        db.collection("users")
        .document(user_id)
        .collection("chats")
        .document(chat_id)
        .collection("messages")
        .document()
    )
    chat_ref.set(
        {"role": role, "message": message, "timestamp": firestore.SERVER_TIMESTAMP}
    )


def create_new_chat(user_id):
    chat_ref = db.collection("users").document(user_id).collection("chats").document()
    chat_ref.set({"created_at": firestore.SERVER_TIMESTAMP})
    return chat_ref.id


def delete_chat(user_id, chat_id):
    # 채팅 문서 삭제
    chat_ref = (
        db.collection("users").document(user_id).collection("chats").document(chat_id)
    )

    # 채팅에 속한 모든 메시지 삭제
    messages = chat_ref.collection("messages").get()
    for msg in messages:
        msg.reference.delete()

    # 채팅 문서 자체 삭제
    chat_ref.delete()


def update_chat_summary(user_id, chat_id, summary):
    chat_ref = (
        db.collection("users").document(user_id).collection("chats").document(chat_id)
    )
    chat_ref.update({"summary": summary})
