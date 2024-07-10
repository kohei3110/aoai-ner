# Azure AI Searchを使用した検索API

このAPIは、Azure AI Searchを利用して、全文検索、ベクトル検索、ハイブリッド検索、セマンティック検索を提供します。Azure OpenAIと組み合わせて、文書のベクトル埋め込みを生成し、より精度の高い検索結果を得ることができます。

## 機能

- **全文検索 (`/fulltext`)**: キーワードに基づいて文書を検索します。
- **ベクトル検索 (`/vector`)**: 文書のベクトル表現を使用して、クエリに最も近い文書を検索します。
- **ハイブリッド検索 (`/hybrid`)**: 全文検索とベクトル検索の結果を組み合わせて、より関連性の高い検索結果を提供します。
- **セマンティック検索 (`/semantic`)**: セマンティック順位付けを使用して、クエリの意味を理解し、より関連性の高い回答を提供します。

## 使用方法

1. 必要な環境変数を設定します。
    - `AI_SEARCH_SERVICE_NAME`: Azure AI Search のサービス名。
    - `AI_SEARCH_INDEX_NAME`: 作成または更新するインデックスの名前。
    - `AI_SEARCH_API_KEY`: Azure AI Search のAPIキー。
    - `AZURE_OPENAI_API_KEY`: Azure OpenAI のAPIキー。
    - `AZURE_OPENAI_ENDPOINT`: Azure OpenAI のエンドポイントURL。
2. FastAPIを起動します。
    ```bash
    uvicorn main:app --reload
    ```
3. ブラウザまたはAPIクライアントを使用して、以下のエンドポイントにアクセスします。
    - 全文検索: `http://localhost:8000/fulltext?query=your_query`
    - ベクトル検索: `http://localhost:8000/vector?query=your_query`
    - ハイブリッド検索: `http://localhost:8000/hybrid?query=your_query`
    - セマンティック検索: `http://localhost:8000/semantic?query=your_query`

## 注意事項

- Azure AI Search と Azure OpenAI の使用を前提としています。