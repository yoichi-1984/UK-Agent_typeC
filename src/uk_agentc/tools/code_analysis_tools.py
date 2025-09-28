"""
UK-Agent-TypeC Code Analysis Tools: コード分析・品質チェックツール群
"""
import os
import subprocess
import autopep8
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from ..config import ROOT_DIRECTORY
# 必要な関数を直接インポートするように修正
from .safe_code_editing_tools import read_file_safely

class AnalyzeAndFormatCodeArgs(BaseModel):
    """ analyze_and_format_python_code ツールの引数モデル。 """
    file_path: str = Field(..., description="分析・整形するPythonファイルのパス")

@tool("analyze_and_format_python_code", args_schema=AnalyzeAndFormatCodeArgs)
def analyze_and_format_python_code(file_path: str) -> str:
    """
    指定されたPythonコードを静的解析(lint)し、PEP 8に準拠するよう自動整形します。
    このツールはファイルを直接書き換えません。
    """
    # ファイル読み込みをsafe_read_fileに任せる。パスチェックもそこで行われる。
    # safe_tools. を削除し、直接関数を呼び出す
    original_code = read_file_safely(file_path=file_path)
    if original_code.startswith("Error:"):
        return original_code

    full_path = os.path.join(ROOT_DIRECTORY, file_path)

    try:
        # flake8による静的解析
        process = subprocess.run(
            ['flake8', full_path],
            capture_output=True, text=True, encoding='utf-8', check=False
        )
        lint_report = process.stdout.strip()
        if not lint_report:
            lint_report = "素晴らしい！flake8による静的解析で問題は見つかりませんでした。"
        
        # autopep8による自動整形
        formatted_code = autopep8.fix_code(original_code)
        
        summary = (
            f"--- 品質レポート ---\n{lint_report}\n\n"
            f"--- 整形後のコード提案 ---\n{formatted_code}"
        )
        return summary
    except subprocess.CalledProcessError as e:
        return f"Error during code analysis: {e.stderr}"
    except Exception as e:
        return f"Error during code analysis or formatting: {e}"

code_analysis_tools_list = [
    analyze_and_format_python_code
]