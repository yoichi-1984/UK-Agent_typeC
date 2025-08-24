"""
UK-Agent-TypeC: ファイル操作とコーディングに特化した、コマンドラインAIエージェント。

このパッケージは、計画、実行、検証のサイクルを通じて、ユーザーの指示を
自律的に実行する機能を提供します。
"""
# 修正箇所: main -> cli_main
from .main import cli_main

# 修正箇所: "main" -> "cli_main"
__all__ = ["cli_main"]