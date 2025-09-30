"""
UK-Agent-TypeC Configuration: アプリケーション全体で共有される設定を管理します。
"""
import os
from datetime import datetime
import yaml

# --- プロジェクトルートとログディレクトリの基本設定 ---
# このファイル(__file__)の場所を基準に、プロジェクトのルートディレクトリを絶対パスで取得
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

def _load_extensions_from_yaml() -> set:
    """
    code_pattern.yamlから対応拡張子を読み込み、セットとして返す。
    """
    # YAMLファイルのパスをこのファイルの場所を基準に解決
    config_path = os.path.join(os.path.dirname(__file__), 'code_pattern.yaml')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        if config_data and 'supported_extensions' in config_data:
            # YAMLファイルから拡張子リストを取得し、セットに変換して返す
            return set(config_data['supported_extensions'])
        else:
            print(f"Warning: 'supported_extensions' key not found in {config_path}. Using default extensions.")
            return {'.py', '.js', '.html', '.css'}
    except FileNotFoundError:
        print(f"Warning: {config_path} not found. Using default extensions.")
        # YAMLがない場合のフォールバック
        return {'.py', '.js', '.html', '.css', '.md', '.txt'}
    except Exception as e:
        print(f"Error reading {config_path}: {e}")
        return set()
        
# アプリケーション起動時に一度だけ実行され、パスが定数として保持される
SESSION_BACKUP_DIR = _create_session_backup_dir()
CODE_FILE_EXTENSIONS = _load_extensions_from_yaml()

'''
# バックアップ対象とするファイルの拡張子リスト
CODE_FILE_EXTENSIONS = {
    '.py', '.bat', '.sh', '.js', '.ts', '.jsx', '.tsx', 
    '.html', '.css', '.scss', '.json', '.yml', '.yaml', 
    '.toml', '.md', '.txt', 'Dockerfile'
}
'''
