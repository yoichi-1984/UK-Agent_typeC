"""
UK-Agent-TypeC Tools Entrypoint: 利用可能な全ツールの集約モジュール。

このモジュールは、エージェントが利用できる全てのツールを各専門ファイルから
インポートし、'all_tools'という単一のリストに集約します。
Supervisorは、この'all_tools'リストを参照して計画を立案します。
"""
# 各ツールファイルから、名前を変更した「_list」変数をインポートする
from .file_system_tools import file_system_tools_list
from .safe_code_editing_tools import safe_code_editing_tools_list
from .ai_assisted_coding_tools import ai_assisted_coding_tools_list
from .system_tools import system_tools_list
from .knowledge_tools import knowledge_tools_list
from .code_analysis_tools import code_analysis_tools_list
from .code_reporting_tools import code_reporting_tools_list

# 全てのツールリストを結合
all_tools = (
    file_system_tools_list +
    safe_code_editing_tools_list +
    ai_assisted_coding_tools_list +
    system_tools_list +
    knowledge_tools_list +
    code_analysis_tools_list +
    code_reporting_tools_list
)