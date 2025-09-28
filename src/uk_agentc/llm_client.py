"""
UK-Agent-TypeC LLM Client: LLMクライアントを一元管理するモジュール。

アプリケーション全体で共有される、LLMクライアントインスタンスを定義します。
タスクの特性に応じて、2種類のモデルを使い分けます。

- 高性能モデル (o4-mini): 検証、報告、コード要約など、高度な推論が求められるタスク用。
- 安定モデル (Planner): 計画立案など、一貫性と安定性が求められるタスク用。
"""
import os

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

from .config import ROOT_DIRECTORY

# .envファイルから環境変数を一度だけ読み込む
load_dotenv(os.path.join(ROOT_DIRECTORY, 'env', 'agent.env'))

# --- 環境変数のチェック ---
common_required_vars = [
    "AZURE_OPENAI_API_VERSION",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
]
high_perf_vars = ["AZURE_OPENAI_DEPLOYMENT_NAME"]
planner_vars = ["AZURE_OPENAI_PLANNER_DEPLOYMENT_NAME"]

def check_env_vars(vars_list):
    for var in vars_list:
        if not os.environ.get(var):
            raise ValueError(f"環境変数 '{var}' が設定されていません。'env/agent.env' ファイルを確認してください。")

check_env_vars(common_required_vars)
check_env_vars(high_perf_vars)
check_env_vars(planner_vars)


# --- 高性能モデルクライアント (o4-miniなど) ---
# 推論能力が求められるタスク用 (temperature=1.0)
llm_client = AzureChatOpenAI(
    openai_api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
    azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    temperature=1.0,
)

# --- 安定モデルクライアント (計画用) ---
# 計画立案など、安定性が求められるタスク用 (temperature=0.1)
planner_llm_client = AzureChatOpenAI(
    openai_api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
    azure_deployment=os.environ.get("AZURE_OPENAI_PLANNER_DEPLOYMENT_NAME"),
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    temperature=0.2,
)


def get_llm_client() -> AzureChatOpenAI:
    """
    設定済みの【高性能】LLMクライアントインスタンスを返します。
    """
    return llm_client

def get_planner_llm_client() -> AzureChatOpenAI:
    """
    設定済みの【安定・計画用】LLMクライアントインスタンスを返します。
    """
    return planner_llm_client