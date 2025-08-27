"""
UK-Agent-TypeC Configuration: アプリケーション全体で共有される設定を管理します。
"""
import os
from datetime import datetime

# --- グローバル変数（初期値） ---
# これらの変数は set_project_root 関数によって実行時に適切に初期化されます。
ROOT_DIRECTORY = os.getcwd()  # 安全なデフォルト値としてカレントディレクトリを設定
LOG_DIR_NAME = "agent_log"
LOG_DIR_PATH = os.path.join(ROOT_DIRECTORY, LOG_DIR_NAME)
SESSION_BACKUP_DIR = ""  # 初期化前は空

def set_project_root(path: str):
    """
    プロジェクトのルートディレクトリを設定し、関連パスを再初期化する。
    アプリケーションの起動時に呼び出す必要があります。
    """
    global ROOT_DIRECTORY, LOG_DIR_PATH, SESSION_BACKUP_DIR
    
    ROOT_DIRECTORY = os.path.abspath(path)
    LOG_DIR_PATH = os.path.join(ROOT_DIRECTORY, LOG_DIR_NAME)
    
    # --- セッションバックアップディレクトリの作成ロジック ---
    os.makedirs(LOG_DIR_PATH, exist_ok=True)
    
    today_str = datetime.now().strftime("%Y%m%d")
    next_seq = 1
    for dirname in os.listdir(LOG_DIR_PATH):
        if dirname.startswith(today_str):
            try:
                seq = int(dirname.split('_')[-1])
                if seq >= next_seq:
                    next_seq = seq + 1
            except (ValueError, IndexError):
                continue
    
    session_dir_name = f"{today_str}_{next_seq:02d}"
    session_dir_path = os.path.join(LOG_DIR_PATH, session_dir_name)
    os.makedirs(session_dir_path, exist_ok=True)
    
    SESSION_BACKUP_DIR = session_dir_path

# バックアップ対象とするファイルの拡張子リスト
CODE_FILE_EXTENSIONS = {
    '.py', '.bat', '.sh', '.js', '.ts', '.jsx', '.tsx', 
    '.html', '.css', '.scss', '.json', '.yml', '.yaml', 
    '.toml', '.md', '.txt', 'Dockerfile'
}

# アプリケーション起動時に一度だけ実行されることを保証するため、
# set_project_root が呼ばれたときに初期化処理を行う。
# 安全のため、モジュールロード時にも一度呼び出しておく。
if not SESSION_BACKUP_DIR:
    set_project_root(os.getcwd())
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


