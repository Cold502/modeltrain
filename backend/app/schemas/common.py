from pydantic import BaseModel, Field
from typing import Any, Optional


class ErrorDetail(BaseModel):
    """统一错误明细（同时兼顾机器可读与人类可读）。

    字段含义：
    - code：稳定的机器可读错误码，建议使用命名空间格式，例如 "AUTH_401"、"VALIDATION_ERROR"、"DB_500"，以便前端做分支处理。
    - message：人类可读的错误信息，面向用户/前端展示，需简洁明了，避免泄露敏感信息。
    - debug：开发调试用的附加上下文（如校验错误列表、请求上下文等）。生产环境必须置为 None，避免泄密；该约束由全局异常处理根据 ENVIRONMENT 控制。
    """

    code: str = Field(..., description="稳定的机器可读错误码，如 AUTH_401、DB_500")
    message: str = Field(..., description="人类可读的错误信息（对用户/前端展示）")
    debug: Optional[Any] = Field(
        None,
        description="可选的调试信息（校验错误等），生产环境必须为 None",
    )


class ErrorResponse(BaseModel):
    """所有非 2xx 响应的标准错误外层包裹结构。

    字段含义：
    - success：错误响应固定为 False，便于前端快速分支。
    - error：错误明细（见 ErrorDetail）。

    示例：
    {
      "success": false,
      "error": { "code": "HTTP_401", "message": "Unauthorized", "debug": null }
    }
    """

    success: bool = Field(False, description="错误响应恒为 False")
    error: ErrorDetail


