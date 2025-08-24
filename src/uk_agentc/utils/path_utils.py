"""
UK-Agent-TypeC Path Utilities: パス関連の共通ユーティリティ関数群。

ファイルパスの許可チェックや、.agentignoreファイルの読み込みなど、
パス操作に関する共通ロジックを提供します。
"""
import os
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern

# configからROOT_DIRECTORYをインポート
from ..config import ROOT_DIRECTORY

def _load_agentignore() -> PathSpec:
    """ .agentignore ファイルを読み込み、無視するパターンのリストを生成します。 """
    ignore_patterns = []
    ignore_file_path = os.path.join(ROOT_DIRECTORY, '.agentignore')
    if os.path.exists(ignore_file_path):
        with open(ignore_file_path, 'r', encoding='utf-8') as f:
            ignore_patterns = f.readlines()
    # デフォルトで無視するパターンを追加
    ignore_patterns.extend([
        '.env', '.agentignore', 'env/agent.env', '**/env', '.git', 'agent_log'
    ])
    return PathSpec.from_lines(GitWildMatchPattern, ignore_patterns)

AGENT_IGNORE_SPEC = _load_agentignore()

def is_path_allowed(path: str, for_read: bool = True) -> bool:
    """ 指定されたパスへのアクセスが許可されているかを確認します。 """
    try:
        full_path = os.path.abspath(os.path.join(ROOT_DIRECTORY, path))
        # ルートディレクトリ外へのアクセスを禁止
        if not full_path.startswith(ROOT_DIRECTORY):
            return False
        relative_path = os.path.relpath(full_path, ROOT_DIRECTORY)
        # .agentignore に一致するパスを禁止
        if AGENT_IGNORE_SPEC.match_file(relative_path):
            return False
        # 書き込み時に特定の重要ファイルへのアクセスを禁止
        if not for_read and os.path.basename(full_path) in [
            '.env', '.agentignore', 'agent.env'
        ]:
            return False
        return True
    except Exception:  # pylint: disable=broad-exception-caught
        return False
