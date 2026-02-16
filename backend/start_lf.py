"""LLaMA-Factory 启动包装器 - 禁止自动打开浏览器"""
import webbrowser
webbrowser.open = lambda *a, **k: True
webbrowser.open_new = lambda *a, **k: True
webbrowser.open_new_tab = lambda *a, **k: True

import sys
sys.argv = ["llamafactory-cli", "webui", "--port", "7860"]

from llamafactory.cli import main
main()
