## Azure Function (Python)

Azure OpenAI と Azure Functions を活用し、固有表現抽出を行うサンプルである。

テキストの注釈付け（アノテーション）を行う Web API のサンプルとして作成された。

| HTTP メソッド | パス | 関数名 | 説明 |
| :-- | :-- | :-- | :-- |
| POST | `/annotations/enrich/enable` | `create_annotations_enrich` | Azure OpenAI を使用してチャットの完了を作成し、アノテーションを作成する。その後、Wikipedia を探索してレスポンスをエンリッチする。 |
| POST | `/annotations` | `create_annotations` | Azure OpenAI を使用してチャットの完了を作成し、アノテーションを作成する。|