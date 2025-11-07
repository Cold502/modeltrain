import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


def build_model_from_env():
    """根据 .env 配置初始化聊天模型。"""

    load_dotenv()

    model_name = os.getenv("MODEL_NAME")
    provider = os.getenv("MODEL_PROVIDER", "openai")
    base_url = os.getenv("MODEL_ADDRESS")
    api_key = os.getenv("MODEL_API_KEY") or "not-needed"

    if not model_name or not base_url:
        raise RuntimeError("请在 .env 中设置 MODEL_NAME 和 MODEL_ADDRESS")

    return init_chat_model(
        model=model_name,
        model_provider=provider,
        base_url=base_url,
        api_key=api_key,
    )


def interactive_chat():
    """循环对话，输入 exit/quit 结束。"""

    model = build_model_from_env()

    messages = [SystemMessage(content="你是吉斗云开发的中医大模型助手")]

    print("已连接模型，输入 exit/quit 退出。")

    try:
        while True:
            user_text = input("用户: ").strip()
            if not user_text:
                continue
            if user_text.lower() in {"exit", "quit", "exit()"}:
                print("对话结束。")
                break

            messages.append(HumanMessage(content=user_text))

            print("助手: ", end="", flush=True)
            full_response = None  # type: AIMessage | None
            printed_any = False
            for chunk in model.stream(messages):
                chunk_text = getattr(chunk, "text", None)
                if not chunk_text:
                    chunk_content = getattr(chunk, "content", None)
                    if isinstance(chunk_content, list):
                        chunk_text = "".join(
                            block.get("text", "")
                            for block in chunk_content
                            if isinstance(block, dict) and block.get("type") == "text"
                        )
                    elif isinstance(chunk_content, str):
                        chunk_text = chunk_content

                if chunk_text:
                    print(chunk_text, end="", flush=True)
                    printed_any = True

                full_response = chunk if full_response is None else full_response + chunk

            if full_response is None:
                response = model.invoke(messages)
                if isinstance(response, AIMessage):
                    full_response = response
                    print(response.content)
                else:
                    content = getattr(response, "content", str(response))
                    print(content)
                    full_response = AIMessage(content=content)
            else:
                if printed_any:
                    print()

            if hasattr(full_response, "to_message"):
                message_to_store = full_response.to_message()
            else:
                message_to_store = full_response

            if not isinstance(message_to_store, AIMessage):
                message_to_store = AIMessage(content=getattr(message_to_store, "content", str(message_to_store)))

            messages.append(message_to_store)
    except KeyboardInterrupt:
        print("\n对话已取消。")


if __name__ == "__main__":
    interactive_chat()