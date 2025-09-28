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
    # --- デバッグコード ---
    print("\n" + "="*20 + " DEBUG: RECEIVED PLAN " + "="*20)
    print(plan.model_dump_json(indent=2))
    print("="*60 + "\n")
    # --- デバッグコードここまで ---

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
            results.append(error_msg)
            return ExecutionResult(status="failure", results=results, failed_step=i, error_message=error_msg)

        if not callable(tool_func):
            error_msg = f"エラー: ツール '{step.tool_name}' は実行できません。"
            yield f"  -> {error_msg}"
            results.append(error_msg)
            return ExecutionResult(status="failure", results=results, failed_step=i, error_message=error_msg)
        
        try:
            expected_args = tool_func.args_schema.schema().get('properties', {}).keys()
            
            sanitized_args = {
                key: value for key, value in step.arguments.items()
                if key in expected_args
            }

            yield f"  -> [Debug] Expected args: {list(expected_args)}"
            yield f"  -> [Debug] LLM generated args: {step.arguments}"
            yield f"  -> [Debug] Sanitized args: {sanitized_args}"

            # --- ▼▼▼ ここが最終・最重要の修正点 ▼▼▼ ---
            # 問題のツールだけを名指しで特別扱いし、LangChainの実行メカニズムをバイパスして、
            # 中身のPython関数を直接呼び出すことで、'BaseTool.__call__()'のエラーを回避する。
            
            result = None
            if step.tool_name == "ai_read_and_apply_changes":
                yield "  -> [Debug] Bypassing LangChain execution for 'ai_read_and_apply_changes'."
                # tool_func.func で、デコレータがラップしている元の関数にアクセスできる
                raw_function = tool_func.func 
                # **sanitized_args で辞書をキーワード引数に展開して関数を直接呼び出す
                result = raw_function(**sanitized_args) 
            else:
                # 他の正常なツールは通常通り実行
                result = tool_func.run(sanitized_args)
            # --- ▲▲▲ 修正ここまで ▲▲▲ ---

            result_str = str(result)
            
            problematic_tools = ["modify_code"]
            if step.tool_name in problematic_tools and \
               ("エラー" in result_str or "error" in result_str.lower()):
                error_msg = f"ツール '{step.tool_name}' がエラーを報告しました: {result_str}"
                yield f"  -> ⚠️ {error_msg}"
                results.append(error_msg)
                return ExecutionResult(status="failure", results=results, failed_step=i, error_message=error_msg)

            yield f"  -> 実行結果: {result_str}"
            results.append(result_str)
        except Exception as e:
            error_msg = f"ツール '{step.tool_name}' の実行中に予期せぬ例外が発生しました: {e}"
            yield f"  -> ⚠️ {error_msg}"
            results.append(error_msg)
            return ExecutionResult(status="failure", results=results, failed_step=i, error_message=error_msg)

    yield "\n✅ 全てのステップが完了しました。"

    return ExecutionResult(status="success", results=results, failed_step=None, error_message=None)


def format_execution_summary(execution_result: ExecutionResult) -> str:
    """ExecutionResultオブジェクトから検証用のサマリー文字列を生成する。"""
    if execution_result.status == "success":
        summary_header = "計画の実行が正常に完了しました。各ステップの結果は以下の通りです:"
        return summary_header + "\n" + "\n".join(execution_result.results)
    else:
        summary_header = "計画の実行が失敗しました。"
        summary = summary_header + "\n"
        if execution_result.results:
            summary += "成功したステップの結果:\n" + "\n".join(execution_result.results) + "\n"
        summary += f"失敗したステップ {execution_result.failed_step}: {execution_result.error_message}"
        return summary