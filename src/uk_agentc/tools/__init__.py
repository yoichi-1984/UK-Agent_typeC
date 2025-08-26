"""
UK-Agent-TypeC Tools Package: エージェントの能力を定義するツール群。

このパッケージは、エージェントが利用可能なすべてのツールを集約し、
単一のリストとして提供します。
"""
from .file_tools import file_tools
from .code_tools import code_tools
from .system_tools import system_tools
# ★ 新しいknowledge_toolsからツールのリストをインポートします。
#   (事前に knowledge_tools.py ファイル内で 'knowledge_tools = [final_answer]' のように
#    リストを定義しておく必要があります)
from .knowledge_tools import knowledge_tools

# ★ 既存のツールリストの末尾にknowledge_toolsを追加します。
all_tools = file_tools + code_tools + system_tools + knowledge_tools