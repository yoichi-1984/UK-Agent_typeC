"""
UK-Agent-TypeC Knowledge Tools: AIの知識を直接活用するためのツール群。

このモジュールには、ファイル操作やコード実行といった具体的な「行動」とは異なり、
エージェント自身の知識ベースから直接回答を生成するためのツールが含まれます。
"""
from langchain_core.tools import tool
from pydantic import BaseModel, Field

class FinalAnswerInputs(BaseModel):
    """
    final_answerツールのための入力スキーマを定義します。
    """
    answer: str = Field(
        description="ユーザーの質問に対する最終的な回答。他のツールが不要な場合や、全ての情報が揃った場合に使用します。"
    )

@tool(args_schema=FinalAnswerInputs)
def final_answer(answer: str) -> str:
    """
    この関数は、ユーザーへの最終的な回答を返すために使用します。
    質問がツールを必要としない一般的な知識に関するものであったり、
    一連のツール実行が完了した後の最終報告に使用します。
    Supervisor(計画立案者)がこのツールを呼び出す際、'answer'引数にAIの知識に基づいた回答を生成して渡します。
    このツール自体は、その渡された回答をそのまま最終結果として返すだけのシンプルな構造です。
    """
    return answer

# __init__.pyがインポートできるように、ツールのリストを定義します。
knowledge_tools = [final_answer]

