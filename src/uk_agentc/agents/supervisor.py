"""
UK-Agent-TypeC Supervisor: 計画立案エージェント。

ユーザーの要求や過去の失敗フィードバックを元に、タスクを達成するための
具体的な実行計画(ExecutionPlan)を立案します。
"""
import os
import yaml
from typing import List, Optional

from langchain_core.messages import BaseMessage, SystemMessage
from pydantic import ValidationError

# --- ローカルモジュールからのインポート ---
from ..llm_client import get_planner_llm_client, get_llm_client
from .schema import ExecutionPlan, ToolCall


# --- ヘルパー関数 ---
def get_tools_string(tools: List) -> str:
    """利用可能なツールの一覧と説明を整形して返す。"""
    tool_strings = []
    for tool in tools:
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

def _validate_plan(plan: ExecutionPlan) -> Optional[str]:
    """
    LLMによって生成された計画が、ツールの引数スキーマに準拠しているか検証する。
    致命的なエラーがないかを確認し、余分な引数は警告のみに留める。
    """
    from ..tools import all_tools
    tool_map = {tool.name: tool.args_schema for tool in all_tools}

    if not plan.plan:
        return None

    for step in plan.plan:
        if not isinstance(step, ToolCall):
            return f"計画のステップ {step} が不正な形式です。"

        schema = tool_map.get(step.tool_name)
        if not schema:
            return f"計画に含まれるツール '{step.tool_name}' は存在しません。"

        expected_args = set(schema.schema().get('properties', {}).keys())
        received_args = set(step.arguments.keys())

        extra_args = received_args - expected_args
        if extra_args:
            print(f"[DEBUG] 警告: ツール '{step.tool_name}' に予期しない引数 {list(extra_args)} が含まれていますが、無視して続行します。")
            for arg in extra_args:
                del step.arguments[arg]

        try:
            schema(**step.arguments)
        except ValidationError as e:
            return (f"ツール '{step.tool_name}' の引数が不正です（必須引数の不足や型の誤り）。\n"
                    f"エラー詳細: {e}")

    return None

# --- Supervisorのロジック ---
def create_plan(
    messages: List[BaseMessage], tools: List, feedback: Optional[str] = None
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

    prompt_file_path = os.path.join(os.path.dirname(__file__), "supervisor_prompt.yaml")
    with open(prompt_file_path, "r", encoding="utf-8") as f:
        yaml_content = yaml.safe_load(f)
        planner_system_prompt_template = yaml_content["prompt_template"]

    planner_system_prompt = planner_system_prompt_template.format(
        replan_prompt=replan_prompt,
        tools_string=get_tools_string(tools)
    )

    planner_messages = [SystemMessage(content=planner_system_prompt)] + messages

    if feedback:
        print("\n🤔 失敗フィードバックに基づき、高性能モデルで再計画を実行します...")
        llm_instance = get_llm_client()
    else:
        llm_instance = get_planner_llm_client()

    structured_llm = llm_instance.with_structured_output(ExecutionPlan, method="function_calling")

    try:
        plan = structured_llm.invoke(planner_messages)

        validation_error = _validate_plan(plan)
        if validation_error:
            print(f"\n⚠️ 生成された計画に論理的な問題があったため、修正を試みます: {validation_error}")
            return create_plan(messages, tools, feedback=validation_error)

        return plan
    except ValidationError as e:
        error_message = f"LLMの出力構造にエラーがありました。修正して再計画します。エラー詳細: {e}"
        print(f"\n⚠️ {error_message}")
        return create_plan(messages, tools, feedback=error_message)
    except Exception as e:
        error_message = f"計画の立案中に予期せぬエラーが発生しました。根本的な原因: {e}"
        print(f"\n⚠️ {error_message}")
        return ExecutionPlan(thought=error_message, plan=[])

def present_plan(plan: ExecutionPlan) -> bool:
    """
    計画を提示する（TUI/CLIモードの互換性のために残されています）。
    現在は常にTrueを返します。
    """
    return True

def classify_task(user_input: str) -> str:
    """
    ユーザーの指示を事前定義されたカテゴリに分類する。
    """
    from ..llm_client import get_llm_client

    prompt = f"""ユーザーの要求を以下のカテゴリのいずれか一つに分類してください。
回答は必ずカテゴリ名のみ（例: code_editing）とし、他の単語は一切含めないでください。

# カテゴリ
- code_editing: ファイルの作成、変更、修正、リファクタリング、コードの記述など。
- reporting: コードベースの分析、レポート作成、ファイルの要約など。
- file_system: ファイルやディレクトリの検索、一覧表示、削除など。
- general_qa: 上記以外。一般的な質問への回答、計画の相談など。

# ユーザーの要求
{user_input}

# 分類結果:"""

    try:
        response = get_llm_client().invoke([SystemMessage(content=prompt)])
        classification = response.content.strip().lower()
        
        if classification not in ["code_editing", "reporting", "file_system", "general_qa"]:
            return "general_qa"
            
        return classification
    except Exception:
        return "general_qa"