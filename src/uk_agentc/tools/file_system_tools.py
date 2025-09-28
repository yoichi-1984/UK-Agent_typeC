"""
UK-Agent-TypeC File System Tools: 純粋なファイルシステム操作ツール群。
"""
import os
import shutil
import glob
from pydantic import BaseModel, Field
from langchain_core.tools import tool

from ..config import ROOT_DIRECTORY

# --- 引数モデルの定義 ---

class ListDirectoryArgs(BaseModel):
    directory: str = Field(default='.', description="ファイル一覧を取得するディレクトリパス")

class FindFilesArgs(BaseModel):
    pattern: str = Field(..., description="検索するファイルパターン (例: '*.py', '**/__init__.py')")

class ReadFileArgs(BaseModel):
    file_path: str = Field(..., description="内容を読み取るファイルパス")

class WriteFileArgs(BaseModel):
    file_path: str = Field(..., description="書き込み先のファイルパス...")
    content: str = Field(..., description="書き込む内容")

class AppendToFileArgs(BaseModel):
    file_path: str = Field(..., description="追記先のファイルパス。")
    content: str = Field(..., description="ファイルの末尾に追記する内容。")

class CreateDirectoryArgs(BaseModel):
    directory_path: str = Field(..., description="作成するディレクトリのパス")

class MovePathArgs(BaseModel):
    source_path: str = Field(..., description="移動元のパス")
    destination_path: str = Field(..., description="移動先のパス")

class DeletePathArgs(BaseModel):
    file_path: str = Field(..., description="削除するファイルまたはディレクトリのパス")

class PathExistsArgs(BaseModel):
    file_path: str = Field(..., description="存在を確認するパス")

class IsDirectoryArgs(BaseModel):
    file_path: str = Field(..., description="ディレクトリかどうかを判別するパス")


# --- ツール関数の定義 ---

@tool("fs_list_directory", args_schema=ListDirectoryArgs)
def list_directory(directory: str = '.') -> str:
    """指定された単一のディレクトリ内のファイルとフォルダのリストを返します。"""
    try:
        target_dir = os.path.join(ROOT_DIRECTORY, directory)
        if not os.path.isdir(target_dir):
            return f"Error: '{directory}' is not a valid directory."
        files = os.listdir(target_dir)
        return "\n".join(files)
    except OSError as e:
        return f"Error listing files in '{directory}': {e}"

@tool("fs_find_files", args_schema=FindFilesArgs)
def find_files(pattern: str) -> str:
    """指定されたパターンに一致するファイルを再帰的に検索します。"""
    search_path = os.path.join(ROOT_DIRECTORY, pattern)
    try:
        found_files = [
            os.path.relpath(f, ROOT_DIRECTORY).replace("\\", "/")
            for f in glob.glob(search_path, recursive=True)
        ]
        if not found_files:
            return f"No files found matching pattern: {pattern}"
        return "\n".join(found_files)
    except Exception as e:
        return f"Error finding files with pattern '{pattern}': {e}"

@tool("fs_read_file", args_schema=ReadFileArgs)
def read_file(file_path: str) -> str:
    """指定されたテキストファイルの内容を読み取って返します。"""
    try:
        full_path = os.path.join(ROOT_DIRECTORY, file_path)
        with open(full_path, 'rb') as f:
            if b'\0' in f.read(1024):
                return "Error: Cannot read binary file."
        with open(full_path, 'r', encoding='utf-8') as f:
            return f.read()
    except (IOError, UnicodeDecodeError) as e:
        return f"Error reading file '{file_path}': {e}"

@tool("fs_write_file", args_schema=WriteFileArgs)
def write_file(file_path: str, content: str) -> str:
    """指定されたファイルに内容を書き込みます（上書き）。"""
    full_path = os.path.join(ROOT_DIRECTORY, file_path)
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to '{file_path}'."
    except IOError as e:
        return f"Error writing to file '{file_path}': {e}"

@tool("fs_append_to_file", args_schema=AppendToFileArgs)
def append_to_file(file_path: str, content: str) -> str:
    """指定されたファイルの末尾に内容を追記します。"""
    full_path = os.path.join(ROOT_DIRECTORY, file_path)
    try:
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        with open(full_path, 'a', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully appended to '{file_path}'."
    except IOError as e:
        return f"Error appending to file '{file_path}': {e}"

@tool("fs_create_directory", args_schema=CreateDirectoryArgs)
def create_directory(directory_path: str) -> str:
    """指定されたパスに新しいディレクトリを作成します。"""
    try:
        os.makedirs(os.path.join(ROOT_DIRECTORY, directory_path), exist_ok=True)
        return f"Successfully created directory '{directory_path}'."
    except OSError as e:
        return f"Error creating directory '{directory_path}': {e}"

@tool("fs_move_path", args_schema=MovePathArgs)
def move_path(source_path: str, destination_path: str) -> str:
    """ファイルまたはディレクトリを移動します。"""
    try:
        full_source = os.path.join(ROOT_DIRECTORY, source_path)
        full_destination = os.path.join(ROOT_DIRECTORY, destination_path)
        os.makedirs(os.path.dirname(full_destination), exist_ok=True)
        shutil.move(full_source, full_destination)
        return f"Successfully moved '{source_path}' to '{destination_path}'."
    except (shutil.Error, OSError) as e:
        return f"Error moving path: {e}"

@tool("fs_delete_path", args_schema=DeletePathArgs)
def delete_path(file_path: str) -> str:
    """指定されたファイルまたはディレクトリを削除します。"""
    full_path = os.path.join(ROOT_DIRECTORY, file_path)
    try:
        if not os.path.exists(full_path):
            return f"Error: Path '{file_path}' not found."
        if os.path.isfile(full_path):
            os.remove(full_path)
            return f"Successfully deleted file '{file_path}'."
        elif os.path.isdir(full_path):
            shutil.rmtree(full_path)
            return f"Successfully deleted directory '{file_path}'."
        else:
            return f"Error: Path '{file_path}' is not a file or directory."
    except OSError as e:
        return f"Error deleting path '{file_path}': {e}"

@tool("fs_path_exists", args_schema=PathExistsArgs)
def path_exists(file_path: str) -> bool:
    """指定されたパスが存在するかどうかを返します。"""
    full_path = os.path.join(ROOT_DIRECTORY, file_path)
    return os.path.exists(full_path)

@tool("fs_is_directory", args_schema=IsDirectoryArgs)
def is_directory(file_path: str) -> bool:
    """指定されたパスがディレクトリかどうかを判別します。"""
    full_path = os.path.join(ROOT_DIRECTORY, file_path)
    return os.path.isdir(full_path)

# ツールリスト
file_system_tools_list = [
    list_directory,
    find_files,
    read_file,
    write_file,
    append_to_file,
    create_directory,
    move_path,
    delete_path,
    path_exists,
    is_directory,
]