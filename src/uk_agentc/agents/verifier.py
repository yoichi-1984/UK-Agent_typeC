"""
UK-Agent-TypeC Verifier: 計画検証エージェント。

実行されたタスクがユーザーの当初の目的を達成しているかを、
提示された証拠のみを元に判断し、最終的な成功・失敗とフィードバックを生成します。
"""
import os


from langchain_core.messages import SystemMessage

from .schema import VerificationResult
from ..llm_client import get_llm_client

# --- Verifierのロジック (アーキテクチャ刷新) ---
def verify_task(
    objective: str, original_plan: str, execution_summary: str
) -> VerificationResult:
    """
    実行されたタスクがユーザーの当初の目的を達成しているかを、
    提示された情報のみに基づいて判断する。
    """
    print("\n🔍 Verifierが作業結果の検証を開始...")

    # --- 最終判断 ---
    final_judgment_prompt = f"""あなたは、提示された証拠のみを元に最終的な判断を下す、
極めて厳格で注意深い品質保証（QA）スペシャリスト（裁判官）です。思考と言語は日本語で行ってください。
あなたは、これ以上ツールを呼び出すことはできません。

**審議対象:**
---
1. **ユーザーの当初の目的:**
{objective}

2. **実行された計画の思考:**
{original_plan}

3. **実行結果の最終要約（事実）:**
{execution_summary}
---

**判断基準:**
- **レポートタスクの特別ルール**: ユーザーの目的が「レポート作成」「調査」「分析」などであり、計画の最後のステップが`read_file`であった場合、「実行結果の最終要約」に含まれる`read_file`の結果（ファイルの中身）は、ユーザーの要求に対する**完全な答えそのもの**です。その内容がユーザーの目的に対して十分な詳細さで書かれているかを評価してください。内容が充実していれば、タスクは「成功」です。追加の要約を要求してはいけません。
- **エラーの厳格な扱い**: 「実行結果の最終要約」に 'Error:' という文字列が**一つでも含まれている場合**、原則としてタスクは**「失敗」**です。
- **セキュリティエラーの特別解釈**: もし 'Error:' の内容が 'Access denied' だった場合、これは意図されたセキュリティ機能です。タスクは「失敗」と判断し、フィードバックでは**必ず**「セキュリティルールにより、この操作は許可されていません。」とだけ報告してください。
- **成功の定義**: 上記のルールに当てはまらない場合、「実行結果の最終要約」に**一切のエラーがなく**、かつその内容が「ユーザーの当初の目的」を完全に満たしている場合のみ、タスクは成功です。

以上のすべての情報に基づき、タスクが完全に成功したか、それとも不完全または失敗したかを判断してください。
最終的な判断を、指定されたJSON形式(`VerificationResult`)で出力してください。

**フィードバックに関する重要ルール:**
- **成功した場合:** `feedback`には、後のプロセスで利用するため、簡潔に「タスクは正常に完了しました。」とだけ記述してください。ユーザーへの詳細な報告は、この後専門のReporterが行います。
- **失敗した場合:** `feedback`には、単なるエラー内容の報告に留めず、「〇〇というエラーが発生しましたが、これは△△が原因と考えられます。次の試行では、□□というアプローチで解決を試みます。」のように、**原因の推測と、具体的な次のアクションプラン**を必ずセットで記述してください。
- **【重要】引数エラーの扱い:** もしエラーが `unexpected keyword argument` に関するものであった場合、**引数名を安易に推測してはいけません。** Supervisorに対して「**ツールの定義を再確認し、正しい引数名で再実行する**」ように明確に指示してください。安易な代替案（例: 'path' を 'file_path' にするなど）を提示することは禁止します。 # ◀️ このルールを追加
"""

    judgment_llm = get_llm_client().with_structured_output(
        VerificationResult, method="function_calling"
    )

    try:
        print("  -> 最終判断を下しています...")
        result = judgment_llm.invoke(
            [SystemMessage(content=final_judgment_prompt)]
        )
        if result.is_success:
            print("  -> Verifierの最終判断: 成功 ✨")
        else:
            print(f"  -> Verifierの最終判断: 失敗/不完全 ❌\n  -> フィードバック: {result.feedback}")
        return result
    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"\n⚠️ 検証の最終判断中にエラーが発生しました: {e}")
        return VerificationResult(
            is_success=False,
            feedback="検証の最終判断プロセスで予期せぬエラーが発生しました。"
        )
