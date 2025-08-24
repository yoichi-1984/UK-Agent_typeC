"""
uk-agent Executor: 計画実行エージェント。

Supervisorによって立案された実行計画(ExecutionPlan)を忠実に実行します。
このエージェントは自律的な思考を行わず、計画されたツール呼び出しを
順番に実行することに専念します。
"""
from typing import Dict, Any, Callable, Generator

from ..tools import all_tools
from .schema import ExecutionPlan, ExecutionResult

# --- ツールディスパッチャの作成 ---
TOOL_DISPATCHER: Dict[str, Callable[..., Any]] = {
    tool.name: tool for tool in all_tools
}

# --- Executorのロジック ---
def execute_plan(plan: ExecutionPlan) -> Generator[str, None, ExecutionResult]:
    """
    Supervisorによって作成された計画を忠実に実行し、
    途中経過をyieldし、最後に構造化された結果を返すジェネレータ。
    """
    if not plan.plan:
        final_result = ExecutionResult(
            status="success",
            results=[plan.thought],
            failed_step=None,
            error_message=None
        )
        yield "計画が空のため、思考を最終結果とします。"
        return final_result

    results = []
    yield "🚀 計画の実行を開始します..."
    for i, step in enumerate(plan.plan, 1):
        yield f"\n--- ステップ {i}/{len(plan.plan)}: {step.tool_name} を実行 ---"

        tool_func = TOOL_DISPATCHER.get(step.tool_name)

        if not tool_func:
            error_msg = f"エラー: ツール '{step.tool_name}' が見つかりません。"
            yield f"  -> {error_msg}"
            # ジェネレータを終了させるために、returnでExecutionResultを返す
            return ExecutionResult(
                status="failure",
                results=results,
                failed_step=i,
                error_message=error_msg
            )

        try:
            validated_args = tool_func.args_schema(**step.arguments)
            result = tool_func.invoke(validated_args.dict())

            result_str = str(result)
            yield f"  -> 実行結果: {result_str}"
            results.append(result_str)
        except Exception as e:  # pylint: disable=broad-exception-caught
            error_msg = f"ツール '{step.tool_name}' の実行中にエラー: {e}"
            yield f"  -> {error_msg}"
            # エラーが発生した場合も、returnでジェネレータを終了させる
            return ExecutionResult(
                status="failure",
                results=results,
                failed_step=i,
                error_message=error_msg
            )

    yield "\n✅ 全てのステップが完了しました。"

    # 成功した場合も、returnで最終結果を返す
    return ExecutionResult(
        status="success",
        results=results,
        failed_step=None,
        error_message=None
    )
