"""
UK-Agent-TypeC Reporter: 最終報告生成エージェント。

タスクの全コンテキストを統合し、ユーザー向けの洗練された最終報告書を生成します。
計画の複雑度に応じて、簡潔な要約と詳細なレポートを自動で切り替えます。
"""
from langchain_core.messages import SystemMessage

from .schema import ExecutionPlan, ExecutionResult
from ..llm_client import llm_client as llm # 共有クライアントをインポート

# --- Reporterのロジック ---
def create_final_report(
    objective: str, plan: ExecutionPlan, execution_result: ExecutionResult
) -> str:
    """
    タスクの全コンテキストを元に、最終的な成果報告書を生成する。
    計画のステップ数に応じて、簡潔な要約か詳細なレポートかを切り替える。
    """
    print("\n🖋️ Reporterが最終報告書の作成を開始...")

    # 実行結果を整形
    execution_details = "\n".join(execution_result.results)

    # --- タスクの複雑度を判断 ---
    # 計画のステップ数が2以下の場合は「単純なタスク」と見なす
    is_simple_task = len(plan.plan) <= 2

    if is_simple_task:
        # --- 簡潔な要約用のプロンプト ---
        prompt = f"""あなたは、作業結果を簡潔に要約する優秀なアシスタントです。
以下の作業ログを読み、ユーザーへの最終報告を日本語で1〜3文の平易な文章で作成してください。

**作業ログ:**
- **目的:** {objective}
- **実行した思考:** {plan.thought}
- **最終結果:** {execution_details}

--- 簡潔な最終報告 ---
"""
        print("  -> 単純なタスクと判断し、簡潔な要約を生成します。")
    else:
        # --- 詳細なレポート用のプロンプト（従来通り） ---
        prompt = f"""あなたは、技術的な成果を一般のユーザーにも分かりやすく説明する、非常に優秀なテクニカルライターです。
以下の作業ログ全体を読み、最終的な成果報告書を日本語で作成してください。

**報告書に含めるべき要素:**
1.  **はじめに**: ユーザーの当初の目的を再確認し、それが達成されたことを簡潔に述べます。
2.  **実施した内容**: どのような思考プロセスと計画で、具体的にどのような手順を実行したのかを、物語のように分かりやすく要約します。
3.  **結論**: 最終的な成果と、それがユーザーの目的にどう貢献するかを明確に記述します。
4.  **今後の提案（任意）**: もしあれば、次に行うと良いかもしれないアクションや、さらなる改善案を提案します。

--- 作業ログ ---

### ユーザーの当初の目的
{objective}

### Supervisorの最終的な思考プロセス
{plan.thought}

### 実行されたステップの詳細
{execution_details}

--- 最終報告書 ---
"""
        print("  -> 複雑なタスクと判断し、詳細なレポートを生成します。")

    try:
        response = llm.invoke([SystemMessage(content=prompt)])
        report = response.content
        print("  -> 報告書の作成が完了しました。")
        return report
    except Exception as e:
        print(f"\n⚠️ 最終報告書の作成中にエラーが発生しました: {e}")
        return "タスクは成功しましたが、最終報告書の生成中にエラーが発生しました。"
