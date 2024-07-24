# インデックス作成日次ジョブ

このプログラムは、Azure AI Search のインデックスを日次で作成し、Azure Blob Storage に保存された文書を処理してインデックスにアップロードするためのものです。主な機能は以下の通りです。

## 機能

- **Blob Storageからの文書のダウンロード**: Azure Blob Storage から最新の文書をダウンロードします。
- **文書のチャンク分割**: ダウンロードした文書をチャンクに分割し、処理を容易にします。このスクリプトでは、`RecursiveCharacterTextSplitter`を使用しています。
- **ベクトルの埋め込み**: 分割された各チャンクに対して、Azure OpenAI を使用してテキストのベクトル埋め込みを取得します。
- **インデックスの作成**: Azure AI Search に新しいインデックスを作成します。このステップは、インデックスが存在しない場合にのみ実行されます。
- **文書のアップロード**: ベクトル埋め込みを含む文書をAzure AI Search のインデックスにアップロードします。
- **ダウンロードファイルのクリーンアップ**: 処理が完了した後、ダウンロードしたファイルをクリーンアップします。

## 使用方法

1. Dockerfile に必要な環境変数を設定します。
    - `AI_SEARCH_SERVICE_NAME`: Azure AI Search のサービス名。
    - `AI_SEARCH_INDEX_NAME`: 作成または更新するインデックスの名前。
    - `AI_SEARCH_API_KEY`: Azure AI Search のAPIキー。
    - `STORAGE_ACCOUNT_NAME`: Azure Blob Storage のアカウント名。
    - `STORAGE_CONTAINER_NAME`: 文書が保存されている Blob Storage のコンテナ名。
    - `AZURE_OPENAI_API_KEY`: Azure OpenAI のAPIキー。
    - `AZURE_OPENAI_ENDPOINT`: Azure OpenAI のエンドポイントURL。
2. スクリプトを実行します。
    ```bash
    docker build -t createindex:latest .
    docker run createindex:latest
    ```

## 注意事項

- このスクリプトは非同期処理を使用しており、`asyncio`を利用しています。
- 文書の処理には時間がかかる場合があります。特に、大量の文書を処理する場合や、文書のサイズが大きい場合です。
- Azure のリソースにアクセスするための認証情報は、環境変数を通じて提供する必要があります。
- このスクリプトは、Azure AI Search と Azure Blob Storage、Azure OpenAI の使用を前提としています。