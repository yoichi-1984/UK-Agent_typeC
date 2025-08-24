"""
UK-Agent-TypeC Code Tools: コーディング支援ツール群。

ファイル操作の基本ツールに加え、コードの静的解析や整形など、
コーディングに特化した機能を提供します。
"""
import os
import glob
import subprocess
import autopep8
import shutil
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

# ★ 修正: 共有設定と共有LLMクライアント、そしてバックアップヘルパー関数をインポート
from ..config import SESSION_BACKUP_DIR, CODE_FILE_EXTENSIONS, ROOT_DIRECTORY
from ..llm_client import llm_client as summarizer_llm
from .file_tools import _backup_file_if_needed

from ..utils.path_utils import is_path_allowed


# --- 引数モデルの定義 ---
class AnalyzeAndFormatCodeArgs(BaseModel):
    """ analyze_and_format_python_code ツールの引数モデル。 """
    file_path: str = Field(..., description="分析・整形するPythonファイルのパス")

class AddLineToFilesByPatternArgs(BaseModel):
    """ add_line_to_files_by_pattern ツールの引数モデル。 """
    pattern: str = Field(..., description="対象ファイルの検索パターン (例: '**/*.py')")
    line_to_add: str = Field(..., description="ファイルの先頭に追加する一行のテキスト")

class RemoveLineFromFilesByPatternArgs(BaseModel):
    """ remove_line_from_files_by_pattern ツールの引数モデル。 """
    pattern: str = Field(..., description="対象ファイルの検索パターン (例: '**/*.py')")
    line_to_remove: str = Field(..., description="ファイルの先頭から削除する一行のテキスト")

class GenerateCodebaseReportArgs(BaseModel):
    """ generate_codebase_report ツールの引数モデル。 """
    directory_path: str = Field(..., description="調査対象のディレクトリパス")
    output_file_path: str = Field(..., description="生成されるレポートの出力先ファイルパス")


# --- ツール関数の定義 ---
@tool("analyze_and_format_python_code", args_schema=AnalyzeAndFormatCodeArgs)
def analyze_and_format_python_code(file_path: str) -> str:
    """
    指定されたPythonコードを静的解析(lint)し、PEP 8に準拠するよう自動整形します。
    このツールはファイルを直接書き換えません。
    """
    # (このツールは変更しないので、内容は省略)
    if not is_path_allowed(file_path):
        return f"Error: Access denied to file '{file_path}'."
    full_path = os.path.join(ROOT_DIRECTORY, file_path)
    if not os.path.exists(full_path):
        return f"Error: File '{file_path}' not found."
    try:
        process = subprocess.run(
            ['flake8', full_path],
            capture_output=True, text=True, encoding='utf-8', check=False
        )
        lint_report = process.stdout.strip()
        if not lint_report:
            lint_report = "素晴らしい！flake8による静的解析で問題は見つかりませんでした。"
        with open(full_path, 'r', encoding='utf-8') as f:
            original_code = f.read()
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


@tool("add_line_to_files_by_pattern", args_schema=AddLineToFilesByPatternArgs)
def add_line_to_files_by_pattern(pattern: str, line_to_add: str) -> str:
    """指定されたパターンに一致する全てのファイルの先頭に、指定された一行を追加します。"""
    search_path = os.path.join(ROOT_DIRECTORY, pattern)
    found_files = [
        f for f in glob.glob(search_path, recursive=True)
        if is_path_allowed(os.path.relpath(f, ROOT_DIRECTORY), for_read=False) and os.path.isfile(f)
    ]
    if not found_files:
        return f"No files found matching pattern: {pattern}"
    # ★ バックアップ処理を追加
    for file_path in found_files:
        _backup_file_if_needed(file_path)
    modified_files = []
    errors = []
    for file_path in found_files:
        try:
            with open(file_path, 'r+', encoding='utf-8') as f:
                original_content = f.read()
                if original_content.startswith(line_to_add):
                    continue
                new_content = line_to_add + '\n' + original_content
                f.seek(0)
                f.write(new_content)
                f.truncate()
                modified_files.append(os.path.relpath(file_path, ROOT_DIRECTORY))
        except (IOError, OSError) as e:
            errors.append(f"Could not modify {os.path.relpath(file_path, ROOT_DIRECTORY)}: {e}")
    summary = f"Added line to {len(modified_files)} file(s): {', '.join(modified_files)}"
    if errors:
        summary += "\nErrors occurred: \n" + "\n".join(errors)
    return summary

@tool("remove_line_from_files_by_pattern", args_schema=RemoveLineFromFilesByPatternArgs)
def remove_line_from_files_by_pattern(pattern: str, line_to_remove: str) -> str:
    """指定されたパターンに一致する全てのファイルについて、先頭行が指定されたテキストと一致する場合にのみ、その行を削除します。"""
    search_path = os.path.join(ROOT_DIRECTORY, pattern)
    found_files = [
        f for f in glob.glob(search_path, recursive=True)
        if is_path_allowed(os.path.relpath(f, ROOT_DIRECTORY), for_read=False) and os.path.isfile(f)
    ]
    if not found_files:
        return f"No files found matching pattern: {pattern}"
    # ★ バックアップ処理を追加
    for file_path in found_files:
        _backup_file_if_needed(file_path)
    modified_files = []
    errors = []
    for file_path in found_files:
        try:
            with open(file_path, 'r+', encoding='utf-8') as f:
                lines = f.readlines()
                if not lines or lines[0].strip() != line_to_remove.strip():
                    continue
                f.seek(0)
                f.writelines(lines[1:])
                f.truncate()
                modified_files.append(os.path.relpath(file_path, ROOT_DIRECTORY))
        except (IOError, OSError) as e:
            errors.append(f"Could not modify {os.path.relpath(file_path, ROOT_DIRECTORY)}: {e}")
    summary = f"Removed line from {len(modified_files)} file(s): {', '.join(modified_files)}"
    if errors:
        summary += "\nErrors occurred: \n" + "\n".join(errors)
    return summary

@tool("generate_codebase_report", args_schema=GenerateCodebaseReportArgs)
def generate_codebase_report(directory_path: str, output_file_path: str) -> str:
    """指定されたディレクトリ内の全.pyファイルを分析し、その構造と機能に関するレポートを生成します。"""
    if not is_path_allowed(directory_path) or not is_path_allowed(output_file_path, for_read=False):
        return "Error: Access denied to the specified directory or output path."
    full_output_path = os.path.join(ROOT_DIRECTORY, output_file_path)
    _backup_file_if_needed(full_output_path) # ★ バックアップ処理を追加
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
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if not content.strip():
                summary = "このファイルは空です。"
            else:
                prompt = f"""以下のPythonコードを分析し、その主な役割と機能を日本語で簡潔に要約してください。
コードの細部ではなく、全体として何をするためのファイルなのかを説明してください。

---コード---
{content}
---要約---
"""
                response = summarizer_llm.invoke([SystemMessage(content=prompt)])
                summary = response.content
            relative_path = os.path.relpath(file_path, ROOT_DIRECTORY)
            report_body += f"## ファイル: `{relative_path}`\n\n"
            report_body += f"{summary}\n\n---\n\n"
        summary_prompt = f"""以下のプログラム分析レポート全体を読み、冒頭に挿入するための「全体を通してのまとめ」を、
2〜3文程度の簡潔で分かりやすい日本語で作成してください。

---レポート本文---
{report_body}
---まとめ---
"""
        summary_response = summarizer_llm.invoke([SystemMessage(content=summary_prompt)])
        overall_summary = summary_response.content
        with open(full_output_path, 'w', encoding='utf-8') as f:
            f.write(f"# {os.path.basename(directory_path)} コードベース分析レポート\n\n")
            f.write("## 全体を通してのまとめ\n\n")
            f.write(f"{overall_summary}\n\n---\n\n")
            f.write("## 各ファイルの詳細\n\n")
            f.write(report_body)
        return f"Report successfully generated at '{output_file_path}'."
    except Exception as e:
        return f"An error occurred while generating the report: {e}"

code_tools = [
    analyze_and_format_python_code,
    add_line_to_files_by_pattern,
    remove_line_from_files_by_pattern,
    generate_codebase_report
]
