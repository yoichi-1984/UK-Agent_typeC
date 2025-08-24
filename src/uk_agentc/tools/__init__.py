"""
UK-Agent-TypeC Tools Package: エージェントの能力を定義するツール群。

このパッケージは、エージェントが利用可能なすべてのツールを集約し、
単一のリストとして提供します。
"""
from .file_tools import file_tools
from .code_tools import code_tools
from .system_tools import system_tools

all_tools = file_tools + code_tools + system_tools
