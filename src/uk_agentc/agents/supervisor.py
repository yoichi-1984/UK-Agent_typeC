"""
UK-Agent-TypeC Supervisor: 計画立案エージェント。

ユーザーの要求や過去の失敗フィードバックを元に、タスクを達成するための
具体的な実行計画(ExecutionPlan)を立案します。
"""
import os
from typing import List, Optional

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI
from langchain_core.messages import BaseMessage, SystemMessage

# --- ローカルモジュールからのインポート ---
from ..tools import all_tools
from .schema import ExecutionPlan


# --- LLMクライアントの準備 ---
load_dotenv(os.path.join(os.getcwd(), 'env', 'agent.env'))
llm = AzureChatOpenAI(
    openai_api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
    azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
)

# --- ヘルパー関数 ---
def get_tools_string() -> str:
    # ... (この関数の中身は変更ありません) ...
    tool_strings = []
    for tool in all_tools:
        tool_strings.append(f"ツール名: {tool.name}")
        tool_strings.append(f"  説明: {tool.description}")
        if tool.args_schema:
            schema = tool.args_schema.schema()
            required_args = schema.get('required', [])
            arg_details = []
            for prop, details in schema.get('properties', {}).items():
                is_required = "必須" if prop in required_args else "任意"
                prop_type = details.get('type', 'N/A')
                prop_desc = details.get('description', '説明なし')
                arg_details.append(
                    f"    - {prop} ({prop_type}, {is_required}): {prop_desc}"
                )
            if arg_details:
                tool_strings.append("  引数:")
                tool_strings.extend(arg_details)
        tool_strings.append("-" * 20)
    return "\n".join(tool_strings)

# --- Supervisorのロジック ---
def create_plan(
    messages: List[BaseMessage], feedback: Optional[str] = None
) -> ExecutionPlan:
    """
    ユーザーの要求や失敗フィードバックから、具体的な実行計画を立案する。
    """
    replan_prompt = ""
    if feedback:
        replan_prompt = f"""**重要：前回の試みは失敗しました。**
検証者からのフィードバックは以下の通りです:
---
{feedback}
---
このフィードバックを元に、問題を解決するための**新しい**実行計画を立ててください。
"""

    # ★ 修正点: 最終回答のルールとJSON出力例を更新
    planner_system_prompt = f"""あなたは、ユーザーの要求を達成するための具体的で抜け漏れのない実行計画を立てる、
非常に優秀な計画立案AIです。あなたの思考と応答は、すべて日本語で行う必要があります。
{replan_prompt}
**利用可能なツールリストと引数:**
{get_tools_string()}

**思考と計画に関するルール:**

1.  **【最重要】パスの解釈**: ユーザーが「ルートディレクトリ」「カレントディレクトリ」「今の場所」など、曖昧な場所を指示した場合、それは**常にプロジェクトのルートディレクトリ `.`** を指します。`/` や `C:\\` のようなファイルシステムの絶対ルートパスにアクセスしようとしてはいけません。
2.  **ツールの選択戦略**: 常に、ユーザーの目的を最も少ないステップで、最も直接的に達成できる高レベルな専門ツール（例: `generate_codebase_report`）を最優先で使用してください。
3.  **最終回答の生成**: ユーザーの質問が一般的な知識を問うもので、他のどのツールも適切でない場合、または全てのタスクが完了し最終的な答えを返す準備ができた場合は、**必ず`final_answer`ツールを呼び出してください。** `answer`引数には、ユーザーに対する完全な回答を記述します。`plan`を空リスト`[]`にするのは、計画立案自体に失敗した場合など、本当に最後の手段だけにしてください。
4.  **その他のルール**: セキュリティエラーを正しく解釈し、コード修正時は元の機能を維持してください。

**JSON出力の具体例:**
```json
// 一般的な質問への回答の理想的な計画例
{{
  "thought": "ユーザーの質問は一般的な知識に関するものなので、直接回答します。",
  "plan": [
    {{
      "tool_name": "final_answer",
      "arguments": {{
        "answer": "「クラウドネイティブ」とは、アプリケーションの設計、開発、デプロイ、運用の手法であり、クラウドコンピューティングの利点を最大限に活用することを目的としています。具体的には、コンテナ化、マイクロサービスアーキテクチャ、CI/CD、宣言的APIなどの技術要素に基づいています。"
      }}
    }}
  ]
}}
```json
// ルートディレクトリのファイル一覧表示の理想的な計画例
{{
  "thought": "ユーザーの指示に従い、プロジェクトのルートディレクトリにあるファイルの一覧を表示します。",
  "plan": [
    {{
      "tool_name": "list_files",
      "arguments": {{
        "directory": "."
      }}
    }}
  ]
}}
```
"""

    planner_messages = [SystemMessage(content=planner_system_prompt)] + messages
    planner_llm = llm.with_structured_output(ExecutionPlan, method="function_calling")

    try:
        if feedback:
            print("\n🤔 Supervisorが失敗フィードバックを元に再計画中...")
        plan = planner_llm.invoke(planner_messages)
        return plan
    except Exception as e:
        print(f"\n⚠️ 実行計画の立案中にエラーが発生しました。エラー: {e}")
        return ExecutionPlan(thought="計画の立案に失敗しました。", plan=[])

def present_plan(plan: ExecutionPlan) -> bool:
    # ... (この関数の中身は変更ありません) ...
    return True # TUIではこの関数は実質的に使われない

