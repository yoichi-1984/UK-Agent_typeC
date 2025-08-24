"""
uk-agent 共有データスキーマ定義。

このモジュールは、Supervisor, Executor, Verifier間で受け渡される
データの構造をPydanticモデルとして定義します。
これにより、エージェント間の連携におけるデータの整合性を保証します。
"""
from typing import List, Optional
from pydantic import BaseModel, Field

# --- 共有データ構造の定義 ---

class ToolCall(BaseModel):
    """実行すべき単一のツール呼び出しを定義します。"""
    tool_name: str = Field(..., description="呼び出すツールの名前。")
    arguments: dict = Field(..., description="ツールに渡す引数の辞書。")

class ExecutionPlan(BaseModel):
    """ユーザーの要求を達成するための、具体的なツール呼び出しのリスト。"""
    thought: str = Field(..., description="計画全体に対する高レベルな思考プロセス。")
    plan: List[ToolCall] = Field(
        ...,
        description="実行すべきツール呼び出しのリスト。このリストは上から順番に実行される。"
    )

class VerificationResult(BaseModel):
    """検証結果を格納するデータモデル。"""
    is_success: bool = Field(
        ...,
        description="タスクがユーザーの要求通りに成功したかどうか。"
    )
    feedback: str = Field(
        ...,
        description="成功した場合はその旨を、失敗した場合は具体的な失敗理由と、それを修正するための次の行動案を記述する。"
    )

# ★ 新機能: Executorが返す構造化された結果
class ExecutionResult(BaseModel):
    """Executorによる計画実行の結果を格納するデータモデル。"""
    status: str = Field(..., description="実行ステータス ('success' or 'failure')。")
    results: List[str] = Field(..., description="成功した各ステップの結果のリスト。")
    failed_step: Optional[int] = Field(None, description="失敗したステップの番号（失敗時のみ）。")
    error_message: Optional[str] = Field(None, description="エラーメッセージ（失敗時のみ）。")
