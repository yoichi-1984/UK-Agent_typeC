"""
UK-Agent-TypeC Safe Code Editing Tools: 安全なコード編集ツール群 (第2層)
"""
import os
import shutil
from pydantic import BaseModel, Field
from langchain_core.tools import tool

# --- 依存モジュールのインポート ---
from ..config import ROOT_DIRECTORY, SESSION_BACKUP_DIR, CODE_FILE_EXTENSIONS
from ..utils.path_utils import is_path_allowed
# 必要な関数を直接インポートするように修正
from .file_system_tools import read_file, write_file

# --- 安全機構 (file_tools.pyから移植) ---
# (_backup_file_if_needed 関数は変更なしのため省略)
def _backup_file_if_needed(full_path: str) -> str:
    if os.path.isfile(full_path):
        file_name = os.path.basename(full_path)
        _, extension = os.path.splitext(file_name)
        if extension in CODE_FILE_EXTENSIONS or file_name in CODE_FILE_EXTENSIONS:
            try:
                relative_path = os.path.relpath(full_path, ROOT_DIRECTORY)
                backup_dest_path = os.path.join(SESSION_BACKUP_DIR, relative_path)
                os.makedirs(os.path.dirname(backup_dest_path), exist_ok=True)
                shutil.copy2(full_path, backup_dest_path)
                return f"Backup created at: {backup_dest_path}"
            except Exception as e:
                return f"Error creating backup: {e}"
    return ""

# --- 引数モデルの定義 ---
# (引数モデルは変更なしのため省略)
class ReadFileSafelyArgs(BaseModel):
    file_path: str = Field(..., description="読み込むファイルのパス")
class ReplaceStringArgs(BaseModel):
    file_path: str = Field(..., description="置換対象のファイルパス")
    old_string: str = Field(..., description="置換される文字列")
    new_string: str = Field(..., description="置換後の文字列")
class InsertLineArgs(BaseModel):
    file_path: str = Field(..., description="挿入対象のファイルパス")
    line_number: int = Field(..., description="挿入する行番号 (1-based)")
    line_to_insert: str = Field(..., description="挿入する一行のテキスト")
class DeleteLineArgs(BaseModel):
    file_path: str = Field(..., description="削除対象のファイルパス")
    line_number: int = Field(..., description="削除する行番号 (1-based)")
class ReplaceLinesArgs(BaseModel):
    file_path: str = Field(..., description="置換対象のファイルパス")
    start_line: int = Field(..., description="置換を開始する行番号 (1-based)")
    end_line: int = Field(..., description="置換を終了する行番号 (1-based)")
    new_content: str = Field(..., description="新しい複数行のコンテンツ")

# --- ▼▼▼ ここからが最終・完成版の修正コード ▼▼▼ ---

@tool("safe_read_file", args_schema=ReadFileSafelyArgs)
def read_file_safely(file_path: str) -> str:
    """パスの安全チェックを行った上で、ファイルの内容を読み込みます。"""
    if not is_path_allowed(file_path, for_read=True):
        return f"Error: Read access denied to file '{file_path}'."
    # 修正: Toolオブジェクトを .run() で正しく呼び出す
    return read_file.run({"file_path": file_path})

@tool("safe_replace_string", args_schema=ReplaceStringArgs)
def replace_string_in_file(file_path: str, old_string: str, new_string: str) -> str:
    """安全チェックとバックアップを行った上で、ファイル内の特定の文字列を置換します。"""
    if not is_path_allowed(file_path, for_read=False):
        return f"Error: Write access denied to file '{file_path}'."

    full_path = os.path.join(ROOT_DIRECTORY, file_path)
    # 修正: Toolオブジェクトを .run() で正しく呼び出す
    content = read_file.run({"file_path": file_path})
    if content.startswith("Error:"):
        return content
    if old_string not in content:
        return f"Error: Old string not found in file '{file_path}'. No replacement made."

    backup_msg = _backup_file_if_needed(full_path)
    new_content = content.replace(old_string, new_string)
    # 修正: Toolオブジェクトを .run() で正しく呼び出す
    write_result = write_file.run({"file_path": file_path, "content": new_content})

    if write_result.startswith("Error:"):
        return f"Error writing file after replacement: {write_result}"
    
    return f"Successfully replaced string in '{file_path}'. {backup_msg}"

@tool("safe_insert_line", args_schema=InsertLineArgs)
def insert_line_at(file_path: str, line_number: int, line_to_insert: str) -> str:
    """安全チェックとバックアップを行った上で、指定された行番号に一行を挿入します。"""
    if not is_path_allowed(file_path, for_read=False):
        return f"Error: Write access denied to file '{file_path}'."

    full_path = os.path.join(ROOT_DIRECTORY, file_path)
    # 修正: Toolオブジェクトを .run() で正しく呼び出す
    content = read_file.run({"file_path": file_path})
    if content.startswith("Error:"):
        return content
    lines = content.splitlines()

    if not (0 < line_number <= len(lines) + 1):
        return f"Error: Line number {line_number} is out of range for file with {len(lines)} lines."

    lines.insert(line_number - 1, line_to_insert)
    new_content = "\n".join(lines)

    backup_msg = _backup_file_if_needed(full_path)
    # 修正: Toolオブジェクトを .run() で正しく呼び出す
    write_result = write_file.run({"file_path": file_path, "content": new_content})

    if write_result.startswith("Error:"):
        return f"Error writing file after insertion: {write_result}"

    return f"Successfully inserted line into '{file_path}' at line {line_number}. {backup_msg}"

@tool("safe_delete_line", args_schema=DeleteLineArgs)
def delete_line_at(file_path: str, line_number: int) -> str:
    """安全チェックとバックアップを行った上で、指定された行番号の一行を削除します。"""
    if not is_path_allowed(file_path, for_read=False):
        return f"Error: Write access denied to file '{file_path}'."

    full_path = os.path.join(ROOT_DIRECTORY, file_path)
    # 修正: Toolオブジェクトを .run() で正しく呼び出す
    content = read_file.run({"file_path": file_path})
    if content.startswith("Error:"):
        return content
    lines = content.splitlines()

    if not (0 < line_number <= len(lines)):
        return f"Error: Line number {line_number} is out of range for file with {len(lines)} lines."

    del lines[line_number - 1]
    new_content = "\n".join(lines)

    backup_msg = _backup_file_if_needed(full_path)
    # 修正: Toolオブジェクトを .run() で正しく呼び出す
    write_result = write_file.run({"file_path": file_path, "content": new_content})

    if write_result.startswith("Error:"):
        return f"Error writing file after deletion: {write_result}"

    return f"Successfully deleted line from '{file_path}' at line {line_number}.\n{backup_msg}"

@tool("safe_replace_lines", args_schema=ReplaceLinesArgs)
def replace_lines(file_path: str, start_line: int, end_line: int, new_content: str) -> str:
    """安全チェックとバックアップを行った上で、指定された範囲の行を置換します。"""
    if not is_path_allowed(file_path, for_read=False):
        return f"Error: Write access denied to file '{file_path}'."
    if start_line > end_line:
        return f"Error: Start line {start_line} cannot be after end line {end_line}."

    full_path = os.path.join(ROOT_DIRECTORY, file_path)
    # 修正: Toolオブジェクトを .run() で正しく呼び出す
    content = read_file.run({"file_path": file_path})
    if content.startswith("Error:"):
        return content
    lines = content.splitlines()

    if not (0 < start_line <= len(lines)) or not (0 < end_line <= len(lines)):
        return f"Error: Line numbers are out of range for file with {len(lines)} lines."

    new_lines = new_content.splitlines()
    del lines[start_line - 1 : end_line]
    for i, line in enumerate(new_lines):
        lines.insert(start_line - 1 + i, line)
    
    final_content = "\n".join(lines)

    backup_msg = _backup_file_if_needed(full_path)
    # 修正: Toolオブジェクトを .run() で正しく呼び出す
    write_result = write_file.run({"file_path": file_path, "content": final_content})

    if write_result.startswith("Error:"):
        return f"Error writing file after replacing lines: {write_result}"

    return f"Successfully replaced lines {start_line}-{end_line} in '{file_path}'.\n{backup_msg}"


safe_code_editing_tools_list = [
    read_file_safely,
    replace_string_in_file,
    insert_line_at,
    delete_line_at,
    replace_lines,
]