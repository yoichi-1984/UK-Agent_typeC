"""
UK-Agent-TypeCt System Tools: シェルコマンド実行など、システムと対話するツール群。
(TUI対応版: input/printを削除)
"""
import subprocess
import os
from pydantic import BaseModel, Field # ★ 修正点: pantic -> pydantic
from langchain_core.tools import tool

from ..config import ROOT_DIRECTORY

# --- セキュリティ設定 ---
# 実行を禁止する危険なコマンドのリスト
FORBIDDEN_COMMANDS = [
    "rm", "sudo", "su", "reboot", "shutdown", "poweroff", "halt",
    "mv", "cp", "chmod", "chown", # ファイル操作は既存のfile_toolsを使うべき
    "del", "format", "rd", "erase", "taskkill", "net user", "powershell", "wmic", "reg"
]

# --- 引数モデルの定義 ---
class RunShellCommandArgs(BaseModel):
    """ run_shell_command ツールの引数モデル。 """
    command: str = Field(..., description="実行するシェルコマンド文字列。")

# --- ツール関数の定義 ---
@tool("run_shell_command", args_schema=RunShellCommandArgs)
def run_shell_command(command: str) -> str:
    """
    指定されたシェルコマンドを安全に実行し、その結果を返します。
    危険なコマンドやファイルシステムを直接変更するコマンドは禁止されています。
    承認はUI側で行われます。
    """
    # 禁止コマンドのチェック
    command_lower = command.lower()
    for forbidden_cmd in FORBIDDEN_COMMANDS:
        # コマンドが単体、先頭、末尾、またはスペース区切りで含まれているかチェック
        if (f" {forbidden_cmd} " in f" {command_lower} " or
                command_lower.startswith(f"{forbidden_cmd} ") or
                command_lower.endswith(f" {forbidden_cmd}") or
                command_lower == forbidden_cmd):
            return f"Error: Command contains forbidden keyword: '{forbidden_cmd}'. Execution denied for security reasons."

    # コマンドの実行
    try:
        process = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=ROOT_DIRECTORY,
            timeout=60,  # タイムアウトを60秒に設定
            check=False
        )
        
        # 結果の整形
        output = f"--- Execution Result ---\n"
        output += f"Exit Code: {process.returncode}\n"
        output += f"--- STDOUT ---\n{process.stdout.strip()}\n"
        if process.stderr:
            output += f"--- STDERR ---\n{process.stderr.strip()}\n"
        
        return output

    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 60 seconds."
    except Exception as e:
        return f"Error: An unexpected error occurred while running the command: {e}"

# このファイルで定義されたツールのリスト
system_tools = [run_shell_command]
