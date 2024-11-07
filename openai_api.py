from dotenv import load_dotenv

load_dotenv()

from groq import Groq
from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL_TOKEN_LIMITS = {
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4": 8192,
    "gpt-3.5-turbo-0125": 16385,
    "llama-3.1-8b-instant": 131072,
}


def split_messages(messages, max_tokens):
    result = []
    current_chunk = []
    current_length = 0

    for message in messages:
        message_tokens = len(message["message"].split())
        if current_length + message_tokens > max_tokens:
            result.append(current_chunk)
            current_chunk = [message]
            current_length = message_tokens
        else:
            current_chunk.append(message)
            current_length += message_tokens

    if current_chunk:
        result.append(current_chunk)

    return result


def get_response(messages, model="gpt-4o", temperature=0.7):
    if model not in MODEL_TOKEN_LIMITS:
        raise ValueError(f"Model {model} not found in MODEL_TOKEN_LIMITS.")

    max_tokens = MODEL_TOKEN_LIMITS[model] - 1000
    message_chunks = split_messages(messages, max_tokens)

    responses = []

    if model == "llama-3.1-8b-instant":
        for chunk in message_chunks:
            filtered_messages = [
                {"role": message["role"], "content": message["message"]}
                for message in chunk
                if message["message"] is not None
            ]
            try:
                response = groq_client.chat.completions.create(
                    model=model,
                    messages=filtered_messages,
                    temperature=temperature,
                )
                responses.append(response.choices[0].message.content)
            except Exception as e:
                responses.append(f"Error: {str(e)}")
    else:
        for chunk in message_chunks:
            filtered_messages = [
                {"role": message["role"], "content": message["message"]}
                for message in chunk
                if message["message"] is not None
            ]
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=filtered_messages,
                    temperature=temperature,
                )
                responses.append(response.choices[0].message.content)
            except Exception as e:
                responses.append(f"Error: {str(e)}")

    return "\n".join(responses)


def summarize_chat(chat_history, model="gpt-4o"):
    prompt = "다음 대화의 핵심 주제를 15자 이내로 작성해:\n\n" + "\n".join(
        [f"{msg['role']}: {msg['message']}" for msg in chat_history]
    )
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": prompt},
    ]
    response = client.chat.completions.create(model=model, messages=messages)
    return response.choices[0].message.content

def analyze_image(image_url, model, user_prompt):
    """
    이미지 URL과 사용자 프롬프트를 받아 OpenAI Vision API를 사용하여 설명을 생성합니다.
    
    Parameters:
    - image_url (str): 분석할 이미지의 URL.
    - model (str): 사용할 OpenAI 모델. Streamlit UI에서 선택된 모델을 사용.
    - user_prompt (str): 사용자 입력 프롬프트. 이미지 분석에 사용할 질문이나 요청.

    Returns:
    - str: 이미지 설명 또는 오류 메시지.
    """
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": [{"type": "text", "text": user_prompt}]},
                {"role": "user", "content": [{"type": "image_url", "image_url": {"url": image_url}}]},
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error analyzing image: {str(e)}"





def analyze_user_input_for_image_request(prompt, model="gpt-4o"):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": f"Is the following user input a request to generate an image? '{prompt}' Please answer 'yes' or 'no'.",
            },
        ],
        temperature=0,
    )
    answer = response.choices[0].message.content.strip().lower()
    return "yes" in answer


def generate_image(prompt, model="dall-e-3", size="1024x1024"):
    try:
        response = client.images.generate(
            model=model,
            prompt=prompt,
            size=size,
            quality="standard",
            n=1,
        )
        return response.data[0].url
    except Exception as e:
        return f"Error generating image: {str(e)}"
