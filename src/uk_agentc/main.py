"""
UK-Agent-TypeCのメイン実行モジュール。

エージェントの中核ロジックと、従来のコマンドラインインターフェースを提供します。
"""
import os
import sys
import importlib.metadata
from typing import List

from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from langchain_core.exceptions import OutputParserException
from openai import APIError

# --- 1. 初期設定 ---
# configモジュールをインポートするだけで初期設定が完了します
from . import config

# --- エージェントとツールのインポート ---
from .agents.supervisor import create_plan, present_plan
from .agents.executor import execute_plan, format_execution_summary
from .agents.verifier import verify_task
from .agents.reporter import create_final_report


# --- ★ 新機能: エージェントの中核ロジックを関数化 ---
def run_agent_cycle(user_input: str, conversation_history: List[BaseMessage]) -> str:
    """
    エージェントの思考サイクルを1回実行し、最終的な結果を返す。
    """
    initial_objective = user_input
    conversation_history.append(HumanMessage(content=user_input))

    max_attempts = 3
    feedback = None
    final_result = ""

    for attempt in range(max_attempts):
        print(f"\n--- 試行 {attempt + 1}/{max_attempts} ---")

        plan = create_plan(conversation_history, feedback)

        if not present_plan(plan):
            conversation_history.pop()
            return "ユーザーによって操作がキャンセルされました。"

        if not plan.plan:
            final_result = plan.thought
            break
        
        execution_result = execute_plan(plan)
        execution_summary = format_execution_summary(execution_result)

        conversation_history.append(AIMessage(content=f"ツールの実行結果:\n{execution_summary}"))

        verification_result = verify_task(
            objective=initial_objective,
            original_plan=plan.thought,
            execution_summary=execution_summary
        )

        if verification_result.is_success:
            final_result = create_final_report(
                objective=initial_objective,
                plan=plan,
                execution_result=execution_result
            )
            break
        else:
            feedback = verification_result.feedback
            final_result = f"試行 {attempt + 1} は失敗しました。フィードバック: {feedback}"
            if attempt >= max_attempts - 1:
                print("\n❌ 最大試行回数に達しました。タスクを完了できませんでした。")
                break
            print("\n🔄 タスクが不完全なため、Supervisorが修正計画を立てます...")

    conversation_history.append(AIMessage(content=final_result))
    return final_result


# --- 従来のコマンドライン実行用ループ ---
def cli_main():
    """
    コマンドラインで対話を実行するためのメインループ。
    """
    try:
        version = importlib.metadata.version("UK-Agent-TypeC")
    except importlib.metadata.PackageNotFoundError:
        version = "dev (not installed)"

    print(f"\nUK-Agent-TypeCへようこそ！ (Ver. {version})")
    print("ファイル操作やコーディングに関するタスクをお手伝いします。'exit'で終了します。")

    conversation_history: List[BaseMessage] = []

    while True:
        try:
            user_input = input("\n💬 あなた: ")
            if user_input.lower().strip() in ["exit", "quit"]:
                print("セッションを終了します。またお会いしましょう！")
                break
            
            print("---")
            agent_response = run_agent_cycle(user_input, conversation_history)
            print(f"\n✅ エージェント: {agent_response}")
            print("---")

        except (KeyboardInterrupt, EOFError):
            print("\nユーザー操作によりセッションを中断しました。")
            break
        except (OutputParserException, APIError) as e:
            print(f"\n処理中にエラーが発生しました: {e}", file=sys.stderr)
        except Exception as e:
            print(f"\n予期せぬエラーが発生しました: {e}", file=sys.stderr)

if __name__ == "__main__":
    cli_main()