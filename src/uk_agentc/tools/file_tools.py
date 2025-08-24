"""
UK-Agent-TypeC File Tools: 基本的なファイル操作ツール群。

ファイルの読み書き、検索、作成、削除など、エージェントがローカル
ファイルシステムと対話するための基本的な機能を提供します。
(TUI対応版: input/printを削除)
"""
import os
import shutil
import glob
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from ..config import SESSION_BACKUP_DIR, CODE_FILE_EXTENSIONS, ROOT_DIRECTORY
from ..utils.path_utils import is_path_allowed

def _backup_file_if_needed(full_path: str) -> str:
    """
    指定されたパスがバックアップ対象であれば、セッションログにコピーする。
    バックアップしたパスを文字列として返す。
    """
    if os.path.isfile(full_path):
        file_name = os.path.basename(full_path)
        _, extension = os.path.splitext(file_name)
        if extension in CODE_FILE_EXTENSIONS or file_name in CODE_FILE_EXTENSIONS:
            try:
                relative_path = os.path.relpath(full_path, ROOT_DIRECTORY)
                backup_dest_path = os.path.join(SESSION_BACKUP_DIR, relative_path)
                os.makedirs(os.path.dirname(backup_dest_path), exist_ok=True)
                shutil.copy2(full_path, backup_dest_path)
                return f"バックアップを作成しました: {backup_dest_path}"
            except Exception as e:
                return f"バックアップ作成中にエラーが発生しました: {e}"
    return ""

# --- 引数モデルの定義 (変更なし) ---
class ListFilesArgs(BaseModel):
    directory: str = Field(default='.', description="ファイル一覧を取得するディレクトリパス")
class FindFilesArgs(BaseModel):
    pattern: str = Field(..., description="検索するファイルパターン (例: '*.py', '**/__init__.py')")
class ReadFileArgs(BaseModel):
    file_path: str = Field(..., description="内容を読み取るファイルパス")
class WriteFileArgs(BaseModel):
    file_path: str = Field(..., description="書き込み先のファイルパス。ファイルが存在しない場合は新規作成され、存在する場合は上書きされます。")
    content: str = Field(..., description="書き込む内容")
class AppendToFileArgs(BaseModel):
    file_path: str = Field(..., description="追記先のファイルパス。")
    content: str = Field(..., description="ファイルの末尾に追記する内容。")
class CreateDirectoryArgs(BaseModel):
    directory_path: str = Field(..., description="作成するディレクトリのパス")
class MoveFileArgs(BaseModel):
    source_path: str = Field(..., description="移動元のパス")
    destination_path: str = Field(..., description="移動先のパス")
class MoveFilesByPatternArgs(BaseModel):
    pattern: str = Field(..., description="移動するファイルの検索パターン (例: '*.log')")
    destination_directory: str = Field(..., description="移動先のディレクトリパス")
class DeleteFileArgs(BaseModel):
    file_path: str = Field(..., description="削除する単一のファイルパス")
class DeleteDirectoryArgs(BaseModel):
    directory_path: str = Field(..., description="中身ごと削除するディレクトリのパス")
class GetPathTypeArgs(BaseModel):
    path: str = Field(..., description="種類を判別するファイルまたはディレクトリのパス")


# --- ツール関数の定義 (input/printを削除) ---
@tool("list_files", args_schema=ListFilesArgs)
def list_files(directory: str = '.') -> str:
    """指定された単一のディレクトリ内のファイルとフォルダのリストを返します。"""
    if not is_path_allowed(directory):
        return f"Error: Access denied to directory '{directory}'."
    try:
        target_dir = os.path.join(ROOT_DIRECTORY, directory)
        if not os.path.isdir(target_dir):
            return f"Error: '{directory}' is not a valid directory."
        files = os.listdir(target_dir)
        allowed_files = [f for f in files if is_path_allowed(os.path.join(directory, f))]
        return "\n".join(allowed_files)
    except OSError as e:
        return f"Error listing files in '{directory}': {e}"

@tool("find_files", args_schema=FindFilesArgs)
def find_files(pattern: str) -> str:
    """指定されたパターンに一致するファイルを再帰的に検索します。"""
    found_files = []
    search_path = os.path.join(ROOT_DIRECTORY, pattern)
    for file_path in glob.glob(search_path, recursive=True):
        relative_path = os.path.relpath(file_path, ROOT_DIRECTORY)
        if is_path_allowed(relative_path):
            found_files.append(relative_path.replace("\\", "/"))
    if not found_files:
        return f"No files found matching pattern: {pattern}"
    return "\n".join(found_files)

@tool("read_file", args_schema=ReadFileArgs)
def read_file(file_path: str) -> str:
    """指定されたテキストファイルの内容を読み取って返します。"""
    if not is_path_allowed(file_path):
        return f"Error: Access denied to file '{file_path}'."
    try:
        full_path = os.path.join(ROOT_DIRECTORY, file_path)
        with open(full_path, 'rb') as f:
            if b'\0' in f.read(1024):
                return "Error: Cannot read binary file."
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except (IOError, UnicodeDecodeError) as e:
        return f"Error reading file '{file_path}': {e}"

@tool("write_file", args_schema=WriteFileArgs)
def write_file(file_path: str, content: str) -> str:
    """指定されたファイルに内容を書き込みます（上書き）。承認はUI側で行われます。"""
    if not is_path_allowed(file_path, for_read=False):
        return f"Error: Write access denied to file '{file_path}'."
    full_path = os.path.join(ROOT_DIRECTORY, file_path)
    backup_msg = _backup_file_if_needed(full_path)
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        result = f"'{file_path}' への書き込みが成功しました。"
        if backup_msg:
            result += f"\n{backup_msg}"
        return result
    except IOError as e:
        return f"ファイル '{file_path}' への書き込み中にエラー: {e}"

@tool("append_to_file", args_schema=AppendToFileArgs)
def append_to_file(file_path: str, content: str) -> str:
    """指定されたファイルの末尾に内容を追記します。承認はUI側で行われます。"""
    if not is_path_allowed(file_path, for_read=False):
        return f"Error: Write access denied to file '{file_path}'."
    full_path = os.path.join(ROOT_DIRECTORY, file_path)
    backup_msg = _backup_file_if_needed(full_path)
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'a', encoding='utf-8') as f:
            f.write(content)
        result = f"'{file_path}' への追記が成功しました。"
        if backup_msg:
            result += f"\n{backup_msg}"
        return result
    except IOError as e:
        return f"ファイル '{file_path}' への追記中にエラー: {e}"

@tool("create_directory", args_schema=CreateDirectoryArgs)
def create_directory(directory_path: str) -> str:
    """指定されたパスに新しいディレクトリを作成します。"""
    if not is_path_allowed(directory_path, for_read=False):
        return f"Error: Access denied for directory creation '{directory_path}'."
    try:
        os.makedirs(os.path.join(ROOT_DIRECTORY, directory_path), exist_ok=True)
        return f"ディレクトリ '{directory_path}' の作成に成功しました。"
    except OSError as e:
        return f"ディレクトリ '{directory_path}' の作成中にエラーが発生しました: {e}"

@tool("move_file", args_schema=MoveFileArgs)
def move_file(source_path: str, destination_path: str) -> str:
    """単一のファイルまたはディレクトリを移動します。"""
    if not is_path_allowed(source_path, True):
        return f"Error: Access denied to source path '{source_path}'."
    if not is_path_allowed(destination_path, False):
        return f"Error: Access denied to destination path '{destination_path}'."
    full_source = os.path.join(ROOT_DIRECTORY, source_path)
    backup_msg = _backup_file_if_needed(full_source)
    try:
        full_destination = os.path.join(ROOT_DIRECTORY, destination_path)
        os.makedirs(os.path.dirname(full_destination), exist_ok=True)
        shutil.move(full_source, full_destination)
        result = f"'{source_path}' から '{destination_path}' への移動が成功しました。"
        if backup_msg:
            result += f"\n{backup_msg}"
        return result
    except (shutil.Error, OSError) as e:
        return f"ファイル移動中にエラーが発生しました: {e}"

@tool("move_files_by_pattern", args_schema=MoveFilesByPatternArgs)
def move_files_by_pattern(pattern: str, destination_directory: str) -> str:
    """指定されたパターンに一致する全てのファイルを、指定されたディレクトリに移動します。"""
    if not is_path_allowed(destination_directory, for_read=False):
        return f"Error: Access denied to destination directory '{destination_directory}'."
    search_path = os.path.join(ROOT_DIRECTORY, pattern)
    found_files = [f for f in glob.glob(search_path, recursive=True) if is_path_allowed(os.path.relpath(f, ROOT_DIRECTORY)) and os.path.isfile(f)]
    if not found_files:
        return f"No files found matching pattern: {pattern}"
    
    backup_msgs = []
    for file_path in found_files:
        msg = _backup_file_if_needed(file_path)
        if msg: backup_msgs.append(msg)

    full_dest_dir = os.path.join(ROOT_DIRECTORY, destination_directory)
    os.makedirs(full_dest_dir, exist_ok=True)
    moved_files = []
    errors = []
    for file_path in found_files:
        try:
            shutil.move(file_path, full_dest_dir)
            moved_files.append(os.path.basename(file_path))
        except (shutil.Error, OSError) as e:
            errors.append(f"Could not move {os.path.basename(file_path)}: {e}")
            
    summary = f"Moved {len(moved_files)} file(s) to '{destination_directory}': {', '.join(moved_files)}"
    if backup_msgs:
        summary += "\n" + "\n".join(backup_msgs)
    if errors:
        summary += "\nErrors occurred: \n" + "\n".join(errors)
    return summary

@tool("delete_file", args_schema=DeleteFileArgs)
def delete_file(file_path: str) -> str:
    """指定された単一のファイルを削除します。承認はUI側で行われます。"""
    if not is_path_allowed(file_path, False):
        return f"Error: Access denied to '{file_path}'."
    full_path = os.path.join(ROOT_DIRECTORY, file_path)
    if not os.path.exists(full_path):
        return f"Error: File '{file_path}' not found."
    if not os.path.isfile(full_path):
        return f"Error: '{file_path}' is a directory. Use 'delete_directory' instead."
    backup_msg = _backup_file_if_needed(full_path)
    try:
        os.remove(full_path)
        result = f"ファイル '{file_path}' の削除に成功しました。"
        if backup_msg:
            result += f"\n{backup_msg}"
        return result
    except OSError as e:
        return f"ファイル削除中にエラーが発生しました: {e}"

@tool("delete_directory", args_schema=DeleteDirectoryArgs)
def delete_directory(directory_path: str) -> str:
    """指定されたディレクトリを、中身ごと再帰的に削除します。承認はUI側で行われます。"""
    if not is_path_allowed(directory_path, False):
        return f"Error: Access denied to '{directory_path}'."
    full_path = os.path.join(ROOT_DIRECTORY, directory_path)
    if not os.path.exists(full_path):
        return f"Error: Directory '{directory_path}' not found."
    if not os.path.isdir(full_path):
        return f"Error: '{directory_path}' is a file. Use 'delete_file' instead."
    try:
        shutil.rmtree(full_path)
        return f"ディレクトリ '{directory_path}' の削除に成功しました。"
    except OSError as e:
        return f"ディレクトリ削除中にエラーが発生しました: {e}"

@tool("get_path_type", args_schema=GetPathTypeArgs)
def get_path_type(path: str) -> str:
    """指定されたパスがファイルかディレクトリかを判別して返します。"""
    if not is_path_allowed(path):
        return f"Error: Access denied to path '{path}'."
    full_path = os.path.join(ROOT_DIRECTORY, path)
    if os.path.isdir(full_path):
        return "directory"
    if os.path.isfile(full_path):
        return "file"
    return "not_found"

file_tools = [
    list_files, find_files, read_file, write_file, append_to_file, create_directory,
    move_file, move_files_by_pattern, delete_file, delete_directory, get_path_type
]
