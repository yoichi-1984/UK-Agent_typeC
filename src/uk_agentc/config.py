"""
UK-Agent-TypeC Configuration: アプリケーション全体で共有される設定を管理します。
"""
import os
from datetime import datetime

# --- バックアップ設定 ---
ROOT_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
LOG_DIR_NAME = "agent_log"
LOG_DIR_PATH = os.path.join(ROOT_DIRECTORY, LOG_DIR_NAME)

def _create_session_backup_dir() -> str:
    """
    セッションごとのバックアップディレクトリを作成し、そのパスを返す。
    形式: agent_log/YYYYMMDD_NN
    """
    # agent_logディレクトリがなければ作成
    os.makedirs(LOG_DIR_PATH, exist_ok=True)

    # 今日の日付 (YYYYMMDD)
    today_str = datetime.now().strftime("%Y%m%d")
    
    # 今日の日付で既に作成されたディレクトリを検索し、次の通し番号を決定
    next_seq = 1
    for dirname in os.listdir(LOG_DIR_PATH):
        if dirname.startswith(today_str):
            try:
                seq = int(dirname.split('_')[-1])
                if seq >= next_seq:
                    next_seq = seq + 1
            except (ValueError, IndexError):
                continue
    
    # 新しいセッションディレクトリ名を作成
    session_dir_name = f"{today_str}_{next_seq:02d}"
    session_dir_path = os.path.join(LOG_DIR_PATH, session_dir_name)
    
    # ディレクトリ作成
    os.makedirs(session_dir_path, exist_ok=True)
    
    return session_dir_path

# アプリケーション起動時に一度だけ実行され、パスが定数として保持される
SESSION_BACKUP_DIR = _create_session_backup_dir()

# バックアップ対象とするファイルの拡張子リスト
CODE_FILE_EXTENSIONS = {
    '.py', '.bat', '.sh', '.js', '.ts', '.jsx', '.tsx', 
    '.html', '.css', '.scss', '.json', '.yml', '.yaml', 
    '.toml', '.md', '.txt', 'Dockerfile'
}


