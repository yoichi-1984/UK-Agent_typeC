"""
UK-Agent-TypeC Code Reporting Tools: コードベースのレポート作成ツール群
"""
import os
import glob
from typing import Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage

from ..config import ROOT_DIRECTORY
from ..llm_client import get_llm_client
from ..utils.path_utils import is_path_allowed
# 必要な関数を直接インポートするように修正
from .safe_code_editing_tools import _backup_file_if_needed, read_file_safely
from .file_system_tools import write_file

class GenerateCodebaseReportArgs(BaseModel):
    """ generate_codebase_report ツールの引数モデル。 """
    directory_path: str = Field(..., description="調査対象のディレクトリパス")
    output_file_path: str = Field(..., description="生成されるレポートの出力先ファイルパス")

@tool("generate_codebase_report", args_schema=GenerateCodebaseReportArgs)
def generate_codebase_report(directory_path: str, output_file_path: str, **kwargs: Any) -> str:
    """指定されたディレクトリ内の全.pyファイルを分析し、その構造と機能に関するレポートを生成します。"""
    callbacks = kwargs.get("callbacks")
    # パスチェックは読み込み・書き込み時に各ツールで行うため、ここでは出力パスの書き込み権限のみをチェック
    if not is_path_allowed(output_file_path, for_read=False):
        return f"Error: Write access denied to the output path '{output_file_path}'."
    
    full_output_path = os.path.join(ROOT_DIRECTORY, output_file_path)
    # 直接インポートした関数を呼び出す
    _backup_file_if_needed(full_output_path)

    try:
        search_pattern = os.path.join(ROOT_DIRECTORY, directory_path, '**', '*.py')
        py_files = [
            f for f in glob.glob(search_pattern, recursive=True)
            if is_path_allowed(os.path.relpath(f, ROOT_DIRECTORY)) and os.path.isfile(f)
        ]
        if not py_files:
            return "No Python files found in the specified directory."
        
        report_body = ""
        for file_path in py_files:
            relative_path = os.path.relpath(file_path, ROOT_DIRECTORY)
            # 直接インポートした関数を呼び出す
            content = read_file_safely.run({"file_path": relative_path})
            if content.startswith("Error:"):
                summary = f"ファイルの読み込みに失敗しました: {content}"
            elif not content.strip():
                summary = "このファイルは空です。"
            else:
                prompt = f"""以下のPythonコードを分析し、その主な役割と機能を日本語で簡潔に要約してください。
コードの細部ではなく、全体として何をするためのファイルなのかを説明してください。

---コード---
{content}
---要約---
"""
                response = get_llm_client().invoke([SystemMessage(content=prompt)], config={"callbacks": callbacks})
                summary = response.content
            
            report_body += f"## ファイル: `{relative_path}`\n\n"
            report_body += f"{summary}\n\n---\n\n"

        summary_prompt = f"""以下のプログラム分析レポート全体を読み、冒頭に挿入するための「全体を通してのまとめ」を、
2〜3文程度の簡潔で分かりやすい日本語で作成してください。

---レポート本文---
{report_body}
---まとめ---
"""
        summary_response = get_llm_client().invoke([SystemMessage(content=summary_prompt)], config={"callbacks": callbacks})
        overall_summary = summary_response.content
        
        final_report = (
            f"# {os.path.basename(directory_path)} コードベース分析レポート\n\n"
            f"## 全体を通してのまとめ\n\n"
            f"{overall_summary}\n\n---\n\n"
            f"## 各ファイルの詳細\n\n"
            f"{report_body}"
        )

        # 直接インポートした関数を呼び出す
        write_result = write_file.run({"file_path": output_file_path, "content": final_report})
        if write_result.startswith("Error:"):
            return write_result

        return f"Report successfully generated at '{output_file_path}'."
    except Exception as e:
        return f"An error occurred while generating the report: {e}"

code_reporting_tools_list = [
    generate_codebase_report
]