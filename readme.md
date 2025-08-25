# UK-Agent-TypeC

UK-Agent-TypeCは、Azure OpenAIを活用したマルチエージェントシステムで、Supervisor→Executor→Verifier→Reporterの4つのエージェントが「計画立案→実行→検証→報告」のサイクルを自動で回します。CLI/TUIインターフェースを備え、設定ファイルによるバックアップ機能やPydanticスキーマなど、エンドツーエンドでユーザーの指示から最終レポート生成までをサポートします。

---

## 注意点

このソフトウェアはtextualライブラリの最新機能を使います。
以下の手順で導入を進めてください。
python.exe -m pip install --upgrade pip
pip install --upgrade pip setuptools
pip install -e .
**最後の . も重要です**

## 機能

- マルチエージェントアーキテクチャ
  - Supervisor: 実行計画（ExecutionPlan）を生成
  - Executor: 計画に沿ってツール呼び出しを実行
  - Verifier: 結果を検証しフィードバック
  - Reporter: 最終レポートを自動生成
- Azure OpenAI連携 (AzureChatOpenAI)
- ファイル・コード・システム操作ツール群
- セッションごとの自動バックアップ（agent_logフォルダ）
- CLIおよびTUI(Textual)インターフェース提供

## 目次

- [Prerequisites](#prerequisites)
- [インストール](#インストール)
- [設定](#設定)
- [使い方](#使い方)
- [サンプル](#サンプル)
- [ライセンス](#ライセンス)

## Prerequisites

- Python 3.11以上
- Azure OpenAI サブスクリプション
- 必要な環境変数を設定した `agent.env` ファイル
  - AZURE_OPENAI_ENDPOINT
  - AZURE_OPENAI_API_KEY
  - その他Model名・デプロイ名など
　- OpenAI は　o4-mini推奨。codex-miniは今後対応予定。

## インストール例

```bash
# インストール場所に移動
cd %USERPROFILE%\Documents\MyProjects
# リポジトリをクローン
git clone https://github.com/yoichi-1984/UK-Agent_typeC.git 0x_UK-Agent-TypeC

# 仮想環境の作成・有効化
python -m venv .venv
source env/bin/activate    # Unix/macOS
.\env\\Scripts\\activate # Windows

# 依存パッケージをインストール
pip install -r requirements.txt
```

## 設定

1. envフォルダに　'agent.env` ファイルを作成
2. 以下のキーを設定
   ```env
   AZURE_OPENAI_ENDPOINT=<your_endpoint>
   AZURE_OPENAI_API_KEY=<your_api_key>
   AZURE_OPENAI_CHAT_MODEL_NAME=<model_name>
   AZURE_OPENAI_DEPLOYMENT_NAME=<deployment_name>
   ```
3. `agent_log`ディレクトリは初回実行時に自動生成されます

## 使い方

### CLIモード

0.1.5では一旦未実装。今後検討。

### TUIモード

```bash
python -m src.uk_agentc.main
```

- 対話形式でプロンプトを入力し、承認ダイアログでステップを確認・実行できます

## サンプル

1. README作成タスク
   - プロンプト: "このプロジェクトのREADME.mdを生成してください"
2. コード整形タスク
   - プロンプト: "src/uk_agentc/tools/code_tools.pyをPEP8準拠に整形してください"

## ライセンス

Apache License 2.0

(c) 2025 yoichi-1984
