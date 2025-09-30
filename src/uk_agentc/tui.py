"""
UK-Agent-TypeC TUI: TextualベースのGUIアプリケーション。

このモジュールは、UK-Agent-TypeCのメインエントリーポイントとして機能し、
Textualフレームワークを使用してリッチな対話型UIを構築します。
"""
import os
import json
from datetime import datetime
from typing import List, Optional

from textual.app import App, ComposeResult
from textual.containers import Grid, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Header, Footer, RichLog, Button, Static, TextArea
from textual.binding import Binding
from textual.worker import Worker, WorkerState
from textual import events
from rich.text import Text
from textual.drivers.windows_driver import WindowsDriver

from langchain_core.messages import HumanMessage, BaseMessage, AIMessage

# --- 1. 初期設定 ---
# configモジュールをインポートするだけで初期設定が完了します
from . import config

# --- UK-Agent-TypeCのコアモジュールをすべてインポート ---
from .agents.supervisor import create_plan, classify_task
from .agents.executor import execute_plan, format_execution_summary
from .agents.verifier import verify_task
from .agents.reporter import create_final_report
from .agents.schema import ExecutionPlan, ExecutionResult

# 各ツールセットを個別にインポート (変数名を _list 付きに変更)
from .tools.ai_assisted_coding_tools import ai_assisted_coding_tools_list
from .tools.safe_code_editing_tools import safe_code_editing_tools_list
from .tools.code_reporting_tools import code_reporting_tools_list
from .tools.file_system_tools import file_system_tools_list
from .tools.knowledge_tools import knowledge_tools_list
from .tools import all_tools # フォールバック用に全ツールもインポート

class ApprovalDialog(ModalScreen[bool]):
    """計画の実行を承認するためのモーダルダイアログ。"""
    def compose(self) -> ComposeResult:
        yield Grid(
            Static("計画を実行しますか？", id="question"),
            Button("実行", variant="primary", id="run"),
            Button("キャンセル", variant="error", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        # ★ 変更点: 送信ボタンとの競合を避けるため、IDを確認
        if event.button.id in ("run", "cancel"):
            self.dismiss(True if event.button.id == "run" else False)


class InterruptDialog(ModalScreen[bool]):
    """処理を中断するか確認するためのモーダルダイアログ。"""
    def compose(self) -> ComposeResult:
        yield Grid(
            Static("処理を中断しますか？ (y/n)", id="question"),
            id="dialog",
        )

    def on_key(self, event: events.Key) -> None:
        if event.key == "y":
            self.dismiss(True)
        elif event.key == "n":
            self.dismiss(False)


# ★ 変更点: カスタムTextAreaは不要になったため削除


class AgentApp(App):
    """UK-Agent-TypeCのTUIアプリケーション"""
    # ★ 変更点: 新しいレイアウト用のCSSを追加
    DEFAULT_CSS = """
    #input_bar {
        layout: horizontal;
        height: 7;
        padding: 0 1;
        align: center bottom;
    }
    #task_input {
        width: 1fr;
        height: 100%;
        border: round green;
    }
    #submit_button {
        width: 12;
        height: 100%;
        margin-left: 1;
    }
    """
    # ★ 変更点: フッターの表示内容を修正
    BINDINGS = [
        Binding("escape", "request_interrupt", "処理を中断", show=True, key_display="esc"),
        Binding("f1", "noop", "改行", show=True, key_display="Enter"),
        Binding("f2", "noop", "送信", show=True, key_display="Tab+Enter"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(driver_class=WindowsDriver, *args, **kwargs)
        self.current_worker: Optional[Worker] = None

    def compose(self) -> ComposeResult:
        yield Header(name="uk-agent-c")
        yield RichLog(id="log", wrap=True, highlight=True)
        # ★ 変更点: 入力欄と送信ボタンを横並びに配置
        with Horizontal(id="input_bar"):
            yield TextArea(
                id="task_input",
                placeholder="ここにタスクを入力..."
            )
            yield Button("送信", variant="success", id="submit_button")
        yield Footer()

    def on_mount(self) -> None:
        # 初期状態設定
        self.conversation_history: List[BaseMessage] = []
        self.current_plan: Optional[ExecutionPlan] = None
        self.feedback: Optional[str] = None
        self.initial_objective: str = ""
        self.max_attempts = 3
        self.current_attempt = 0

        log = self.query_one("#log", RichLog)
        ascii_art = r"""
██╗   ██╗  ██╗  ██╗          █████╗     █████╗    █████╗   ███╗   ██╗  ████████╗
██║   ██║  ██║ ██╔╝         ██╔══██╗   ██╔═══╝   ██╔═══╝   ████╗  ██║  ╚══██╔══╝
██║   ██║  █████╔╝  ██████╗ ███████║   ██████╗   ██████╗   ██╔██╗ ██║     ██║   
██║   ██║  ██╔██╗╝  ╚═════╝ ██╔══██║   ██╔══██╗  ██╔═══╝   ██║╚██╗██║     ██║   
 ██║ ██╔╝  ██║╚███╗         ██║  ██║   ╚█████╔╝  ╚█████╗   ██║ ╚████║     ██║   
  ████╔╝   ╚═╝ ╚══╝         ╚═╝  ╚═╝    ╚════╝     ╚═══╝   ╚═╝  ╚═══╝     ╚═╝   
"""
        # 2. RichLogウィジェットにアスキーアートを書き込む
        #    Text.from_markup を使うと、richの構文で色やスタイルを指定できます。
        log.write(Text.from_markup(f"[bold bright_blue]{ascii_art}[/bold bright_blue]"))

        # 見栄えを良くするために空行を一つ追加
        log.write("")
        log.write(Text.from_markup("🤖 [bold]UK-Agent-TypeCへようこそ！[/bold]"))
        log.write("   ファイル操作やコーディングに関するタスクをお手伝いします。")
        log.write("   新しいタスクに移行したい場合は 'reset' と入力して送信してください。")

        # 入力欄にフォーカス
        self.query_one("#task_input", TextArea).focus()

    def _set_input_disabled(self, disabled: bool) -> None:
        # ★ 変更点: ボタンも無効化の対象に含める
        self.query_one("#task_input", TextArea).disabled = disabled
        self.query_one("#submit_button", Button).disabled = disabled

    # ★ 変更点: on_submittable_text_area_task_submitted の代わりに on_button_pressed を使用
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """送信ボタンが押されたときの処理。"""
        if event.button.id == "submit_button":
            text_area = self.query_one("#task_input", TextArea)
            user_input = text_area.text
            log = self.query_one("#log", RichLog)

            if not user_input.strip():
                return

            # 入力欄をクリア
            text_area.clear()

            # 'reset'コマンドの処理
            if user_input.strip().lower() == "reset":
                # --- ★ 変更点: JSONログ保存機能 ---
                if self.conversation_history:
                    # タイムスタンプ付きのファイル名を作成
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    log_file_path = os.path.join(config.ROOT_DIRECTORY, "agent_log", f"log_{timestamp}.json")

                    # BaseMessageオブジェクトを辞書に変換
                    history_to_save = [
                        {"type": msg.type, "content": msg.content}
                        for msg in self.conversation_history
                    ]

                    try:
                        # agent_logディレクトリがなければ作成
                        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)
                        # JSONファイルに書き込み
                        with open(log_file_path, "w", encoding="utf-8") as f:
                            json.dump(history_to_save, f, ensure_ascii=False, indent=4)
                        log.write(Text.from_markup(f"\n📄 [dim]会話ログを {log_file_path} に保存しました。[/dim]"))
                    except Exception as e:
                        log.write(Text.from_markup(f"\n[bold red]⚠️ ログの保存に失敗しました:[/bold red] {e}"))
                # --- ★ 変更点ここまで ---

                self.conversation_history = []
                self.initial_objective = ""
                self.feedback = None
                log.write(Text.from_markup("\n🤖 [bold yellow]会話の文脈をリセットしました。[/bold yellow]"))
                return

            log.write(Text.from_markup(f"\n[bold green]💬 あなた:[/bold green]\n{user_input}"))

            # 新しいタスクとして設定
            if not self.conversation_history:
                self.initial_objective = user_input

            self.conversation_history.append(HumanMessage(content=user_input))
            self.feedback = None
            self.current_attempt = 0

            # 次の処理開始
            self._set_input_disabled(True)
            self.current_worker = self.run_worker(self.plan_task, exclusive=True, thread=True)

    # ★ 追加点: 表示専用の何もしないアクション
    def action_noop(self) -> None:
        """Does nothing. Used for display-only bindings."""
        pass
#----------------------------------------

    def plan_task(self) -> None:
        log = self.query_one("#log", RichLog)
        self.current_attempt += 1
        self.call_from_thread(
            log.write,
            Text.from_markup(f"\n[bold]--- 試行 {self.current_attempt}/{self.max_attempts} ---[/bold]"),
        )

        # ユーザーの最新の指示を取得
        user_input = ""
        for msg in reversed(self.conversation_history):
            if isinstance(msg, HumanMessage):
                user_input = msg.content
                break

        if not user_input:
            self.call_from_thread(log.write, Text.from_markup("[bold red]⚠️ ユーザーの指示が見つかりませんでした。[/bold red]"))
            self.call_from_thread(self._set_input_disabled, False)
            return

        # --- ★ ここからが新しいロジック ★ ---
        self.call_from_thread(log.write, "🧠 タスクの種類を分析中...")
        task_type = classify_task(user_input)
        self.call_from_thread(log.write, f"  -> 分類結果: {task_type}")

        relevant_tools = []
        if task_type == "code_editing":
            # 📝 変数名を「_list」が付いたものに変更
            relevant_tools = safe_code_editing_tools_list + ai_assisted_coding_tools_list + file_system_tools_list
        elif task_type == "reporting":
            # 📝 変数名を「_list」が付いたものに変更
            relevant_tools = code_reporting_tools_list + file_system_tools_list + knowledge_tools_list
        elif task_type == "file_system":
            # 📝 変数名を「_list」が付いたものに変更
            relevant_tools = file_system_tools_list
        else: # general_qa の場合
            relevant_tools = all_tools # フォールバックとして全ツールを提供

        # --- ★ ここまでが新しいロジック ★ ---

        self.call_from_thread(log.write, "🤔 Supervisorが計画を立案中...")
        try:
            # 改造した create_plan に relevant_tools を渡す
            plan = create_plan(self.conversation_history, relevant_tools, self.feedback)
            self.call_from_thread(self.display_plan, plan)
        except Exception as e:
            self.call_from_thread(
                log.write,
                Text.from_markup(f"[bold red]⚠️ 計画立案エラー:[/bold red] {e}"),
            )
            self.call_from_thread(self._set_input_disabled, False)

    def display_plan(self, plan: ExecutionPlan) -> None:
        log = self.query_one("#log", RichLog)
        self.current_plan = plan

        if not plan.plan:
            log.write(
                Text.from_markup(f"\n[bold blue]✅ エージェント:[/bold blue] {plan.thought}")
            )
            self.conversation_history.append(AIMessage(content=plan.thought))
            self._set_input_disabled(False)
            return

        log.write(Text.from_markup("\n[bold blue]📋 以下の計画で作業を実行します:[/bold blue]"))
        log.write(Text.from_markup(f"   [bold]思考:[/bold] {plan.thought}"))
        for i, step in enumerate(plan.plan, 1):
            log.write(
                Text.from_markup(
                    f"   [bold]ステップ {i}:[/bold] {step.tool_name}({step.arguments})"
                )
            )

        self.push_screen(ApprovalDialog(), self.on_approval_dialog_dismiss)

    def on_approval_dialog_dismiss(self, approved: bool) -> None:
        log = self.query_one("#log", RichLog)
        if approved:
            log.write(Text.from_markup("\n[bold]承認されました。計画の実行を開始します...[/bold]"))
            if self.current_plan:
                plan_to_execute = self.current_plan

                def task_to_run():
                    self.execute_and_verify_task(plan_to_execute)

                self.current_worker = self.run_worker(
                    task_to_run, exclusive=True, thread=True
                )
        else:
            log.write(Text.from_markup("\n[bold red]🚫 計画はキャンセルされました。[/bold red]"))
            self._set_input_disabled(False)

    def action_request_interrupt(self) -> None:
        if self.current_worker and self.current_worker.state == WorkerState.RUNNING:
            self.push_screen(InterruptDialog(), self.on_interrupt_dialog_dismiss)
        else:
            self.query_one("#log", RichLog).write("現在実行中の処理はありません。")

    def on_interrupt_dialog_dismiss(self, confirmed: bool) -> None:
        if confirmed and self.current_worker:
            log = self.query_one("#log", RichLog)
            log.write(
                Text.from_markup("\n[bold yellow]🟡 ユーザーの要求により処理を中断します...[/bold yellow]")
            )
            self.current_worker.cancel()
            self._set_input_disabled(False)

#-------------------------------------------------------------------------------------------

    def execute_and_verify_task(self, plan: ExecutionPlan) -> None:
        """計画の実行から検証、報告までを行うメインのWorker。"""
        log = self.query_one("#log", RichLog)

        execution_generator = execute_plan(plan)
        final_result: Optional[ExecutionResult] = None

        while True:
            try:
                log_message = next(execution_generator)
                self.call_from_thread(log.write, f"  {log_message}")
            except StopIteration as e:
                final_result = e.value
                break

        if not final_result:
            self.call_from_thread(
                log.write,
                Text.from_markup("[bold red]⚠️ 実行結果の取得に失敗しました。[/bold red]"),
            )
            self.call_from_thread(self._set_input_disabled, False)
            return

        if not isinstance(final_result, ExecutionResult):
            self.call_from_thread(
                log.write,
                Text.from_markup(
                    f"[bold red]⚠️ 予期せぬ実行結果タイプ: {type(final_result)}[/bold red]"
                ),
            )
            self.call_from_thread(self._set_input_disabled, False)
            return

        # --- ★ 変更点: 現在のタスク目的を動的に取得 ---
        # 会話履歴を逆順に探索し、最後のユーザーメッセージを現在の目的として使用する
        current_objective = ""
        for msg in reversed(self.conversation_history):
            if isinstance(msg, HumanMessage):
                current_objective = msg.content
                break
        
        if not current_objective:
                self.call_from_thread(
                    log.write,
                    Text.from_markup("[bold red]⚠️ 現在のタスク目的が見つかりませんでした。[/bold red]"),
                )
                self.call_from_thread(self._set_input_disabled, False)
                return

        self.call_from_thread(log.write, "\n🔍 Verifierが作業結果の検証を開始...")
        execution_summary = format_execution_summary(final_result)

        verification = verify_task(current_objective, plan.thought, execution_summary)

        if verification.is_success:
            self.call_from_thread(
                log.write,
                Text.from_markup("  [bold green]✨ Verifierの判断: 成功[/bold green]"),
            )
            self.call_from_thread(log.write, "\n🖋️ Reporterが最終報告書の作成を開始...")
            report = create_final_report(current_objective, plan, final_result)
            self.call_from_thread(
                log.write,
                Text.from_markup(f"\n[bold blue]✅ エージェント:[/bold blue]\n{report}"),
            )
            self.conversation_history.append(AIMessage(content=report))
            self.call_from_thread(self._set_input_disabled, False)
        else:
            self.call_from_thread(
                log.write,
                Text.from_markup(
                    f"  [bold red]❌ Verifierの判断: 失敗/不完全[/bold red]\n"
                    f"  [bold]フィードバック:[/bold] {verification.feedback}"
                ),
            )
            self.feedback = verification.feedback
            self.conversation_history.append(
                AIMessage(
                    content=(
                        f"実行結果の要約:\n{execution_summary}\n\n"
                        f"検証者からのフィードバック:\n{self.feedback}"
                    )
                )
            )

            if self.current_attempt < self.max_attempts:
                self.call_from_thread(
                    log.write,
                    Text.from_markup("\n🔄 タスクが不完全なため、Supervisorが修正計画を立てます..."),
                )
                self.current_worker = self.run_worker(
                    self.plan_task, exclusive=True, thread=True
                )
            else:
                self.call_from_thread(
                    log.write,
                    Text.from_markup(
                        "\n[bold red]❌ 最大試行回数に達しました。タスクを完了できませんでした。[/bold red]"
                    ),
                )
                self.call_from_thread(self._set_input_disabled, False)
                
#-----------------------------------------------------------------------

def main():
    app = AgentApp()
    app.run()


if __name__ == "__main__":
    main()
