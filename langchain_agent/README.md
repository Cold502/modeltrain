# LangChain 本地模型示例

本文档记录了在 `langchain_agent` 子目录下，通过 LangChain 调用本地 OpenAI 兼容模型服务的最小示例。

## 目录结构与关键文件

```
langchain_agent/
├── .env             # 本地模型连接配置
└── agent.py         # LangChain 调用脚本
```

### `.env`

```
MODEL_PROVIDER=openai
MODEL_NAME=llama-3-8b-instruct      # 替换成服务器模型的绝对路径
MODEL_ADDRESS=http://192.168.2.200:9000/v1
MODEL_API_KEY=not-needed            # 若服务需要鉴权，填入真实密钥
```

### `agent.py`

```
import os
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage


def build_model_from_env():
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
```

## 环境准备

1. 进入 `langchain_agent` 目录。
2. 使用 `curl http://192.168.2.200:9000/v1/models` 查看本地服务暴露的模型名称，并修改 `.env` 中的 `MODEL_NAME`。
3. 安装依赖（示例）：

   ```bash
   pip install langchain langchain-openai python-dotenv httpx
   ```

   如使用 uv，可执行：

   ```bash
   uv pip install langchain langchain-openai python-dotenv httpx
   ```

## 运行示例

确保本地推理服务已启动后执行：

```bash
python agent.py
```

按照提示输入问题即可连续对话；回答会以流式方式实时输出，输入 `exit`/`quit` 结束。

## 常见问题排查

- **连接超时 (`ConnectTimeout`)**：检查 `MODEL_ADDRESS` 是否正确，并确认本地服务正在监听该端口。
- **模型不存在 (`NotFoundError`)**：`MODEL_NAME` 与服务返回的模型 id 不一致，重新核对 `/v1/models` 的输出。
- **需要鉴权**：若服务要求 token，在 `.env` 中填写真实的 `MODEL_API_KEY`。

