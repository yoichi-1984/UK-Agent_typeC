"""
UK-Agent-TypeC AI-Assisted Coding Tools: AI支援コーディングツール群 (第3層)
LLMの能力を最大限に活用し、自然言語の指示に基づく高度なコード修正や
リファクタリングなど、非決定的なTaskを実行します。エージェントが
複雑で抽象的なコード編集を要求された場合の最終手段となります。
"""
import os
from typing import Any
from pydantic import BaseModel, Field
from langchain_core.tools import tool
from langchain_core.messages import SystemMessage

from ..config import ROOT_DIRECTORY
from ..llm_client import get_llm_client
from ..utils.path_utils import is_path_allowed
from .file_system_tools import path_exists, write_file
from .safe_code_editing_tools import read_file_safely, _backup_file_if_needed

# --- ▼▼▼ ここからが最終・完成版のコード ▼▼▼ ---

class ReadAndApplyChangesInputs(BaseModel):
    """read_and_apply_changesツールの入力スキーマ"""
    # 引数名を 'file_path' に統一
    file_path: str = Field(description="変更対象のファイルのパス。")
    instruction: str = Field(description="ファイルに対して行うべき変更内容を記述した自然言語の指示。")

# あなたの提案通り、他のツールと定義方法を統一するため、シンプルな@toolデコレータ方式に戻す。
# これが最も確実で、プロジェクト全体で一貫性のある定義方法となる。
@tool("ai_read_and_apply_changes", args_schema=ReadAndApplyChangesInputs)
# ライブラリのバグを回避するため、**kwargs を削除
def read_and_apply_changes(file_path: str, instruction: str) -> str:
    """
    指定されたファイルを読み込み、自然言語の指示に基づいて内容を修正し、
    安全に上書き保存する。バックアップも自動で作成する。
    """
    if not is_path_allowed(file_path, for_read=False):
        return f"Error: Write access to path '{file_path}' is not allowed."

    full_path = os.path.join(ROOT_DIRECTORY, file_path)
    if not path_exists.run({"file_path": file_path}):
        return f"Error: File '{file_path}' not found."

    try:
        original_content = read_file_safely.run({"file_path": file_path})
        if original_content.startswith("Error:"):
            return f"Error reading file '{file_path}': {original_content}"

        backup_msg = _backup_file_if_needed(full_path)

        llm = get_llm_client()
        prompt = f"""以下のファイル内容を、指示に従って修正してください。
修正後のファイル内容【全文】のみを出力し、余計な説明や ``` は一切含めないでください。

---指示---
{instruction}

---元のファイル内容---
{original_content}
"""
        # **kwargsを削除したため、configも渡さないシンプルな呼び出しにする
        response = llm.invoke(prompt)
        modified_content = response.content.strip()

        if modified_content.startswith("```python"):
            modified_content = modified_content[len("```python"):].strip()
        if modified_content.startswith("```"):
            modified_content = modified_content[3:].strip()
        if modified_content.endswith("```"):
            modified_content = modified_content[:-3].strip()
        
        write_result = write_file.run({"file_path": file_path, "content": modified_content})
        if write_result.startswith("Error:"):
            return f"Error writing file '{file_path}': {write_result}"
        
        result = f"File '{file_path}' was successfully modified."
        if backup_msg:
            result += f" {backup_msg}"
        return result

    except Exception as e:
        return f"An unexpected error occurred: {e}"

ai_assisted_coding_tools_list = [
    read_and_apply_changes,
]
# --- ▲▲▲ 修正ここまで ▲▲▲ ---