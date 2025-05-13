# 安装依赖: pip install openai
from openai import OpenAI

# 配置客户端
client = OpenAI(
    api_key="sk-efc873f59a9643e59864347dd502505f",  # 替换为您的 API Key
    base_url="https://api.deepseek.com"
)


# 非流式调用
def test_chat_completion():
    response = client.chat.completions.create(
        model="deepseek-chat",  # DeepSeek-V3 模型
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "写一个简单的Python函数计算斐波那契数列"}
        ],
        stream=False
    )
    print(response.choices[0].message.content)


# 流式调用
def test_streaming():
    stream = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "解释量子计算的基本原理"}
        ],
        stream=True
    )

    for chunk in stream:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="")
    print()


if __name__ == "__main__":
    print("=== 非流式调用测试 ===")
    test_chat_completion()

    print("\n=== 流式调用测试 ===")
    test_streaming()
