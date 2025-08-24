"""
UK-Agent-TypeC LLM Client: LLMクライアントを一元管理するモジュール。

アプリケーション全体で共有される、単一のLLMクライアントインスタンスを定義します。
"""
import os

from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

from .config import ROOT_DIRECTORY

# .envファイルから環境変数を一度だけ読み込む
load_dotenv(os.path.join(ROOT_DIRECTORY, 'env', 'agent.env'))

# アプリケーション全体で共有されるLLMクライアントの単一インスタンス

required_env_vars = [
    "AZURE_OPENAI_API_VERSION",
    "AZURE_OPENAI_DEPLOYMENT_NAME",
    "AZURE_OPENAI_ENDPOINT",
    "AZURE_OPENAI_API_KEY",
]

for var in required_env_vars:
    if not os.environ.get(var):
        raise ValueError(f"環境変数 '{var}' が設定されていません。'env/agent.env' ファイルを確認してください。")

llm_client = AzureChatOpenAI(
    openai_api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
    azure_deployment=os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME"),
    azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
    api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
)
