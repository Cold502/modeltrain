"""启动 SwanBoard 可视化服务的包装脚本
修复 swanboard 0.1.9b1 中 URL.__str__ 返回 rich.Text 而非 str 的 bug
"""
import sys
import os

def main():
    if len(sys.argv) < 4:
        print("Usage: python start_swanboard.py <data_dir> <host> <port>")
        sys.exit(1)

    data_dir = sys.argv[1]
    host = sys.argv[2]
    port = int(sys.argv[3])

    # Monkey-patch swanboard URL.__str__ bug
    from swanboard.run.utils import URL as _URL
    _original_str = _URL.__str__
    def _patched_str(self):
        result = _original_str(self)
        return str(result) if not isinstance(result, str) else result
    _URL.__str__ = _patched_str

    from swanboard.run import SwanBoardRun
    SwanBoardRun.run(data_dir, host, port)

if __name__ == "__main__":
    main()
