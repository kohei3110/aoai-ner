# Azure OpenAI を活用した固有表現抽出

![Architecture](./infra/images/architecture.png "サンプルアプリアーキテクチャ")

## 0. 環境準備

### Bicep ファイルをデプロイするためのツール

まず、Bicep ファイルをデプロイするためのツールを準備します。

以下のいずれかの方法を使用できます。**用意する環境はいずれか１つで構いません。**

- **Visual Studio Code - Bicep 拡張機能**: 

Bicep 拡張機能をインストールして、Visual Studio Code で Bicep ファイルをデプロイします。

- **Azure CLI**: 

最新バージョンの Bicep CLI がインストールされていることを確認します。以下のコマンドでアップグレードできます：

```
az bicep upgrade  
```

- **PowerShell**: 

PowerShell を使用して Bicep ファイルをデプロイします。

### Azure Functions Core Tools

- [Azure Functions Core Tools](https://learn.microsoft.com/ja-jp/azure/azure-functions/functions-run-local?tabs=windows%2Cisolated-process%2Cnode-v4%2Cpython-v2%2Chttp-trigger%2Ccontainer-apps&pivots=programming-language-python#install-the-azure-functions-core-tools)をインストールします。

以下のコマンドで Azure Functions Core Tools のバージョンが出力されたらインストール完了です。

```
func -v
```

### Azure CLI

- [Windows での Azure CLI のインストール](https://learn.microsoft.com/ja-jp/cli/azure/install-azure-cli-windows?tabs=azure-cli)

以下のコマンドで Azure CLI のバージョンが出力されたらインストール完了です。

```
az --version
```

### Azurite

- [ローカルでの Azure Storage の開発に Azurite エミュレーターを使用する](https://learn.microsoft.com/ja-jp/azure/storage/common/storage-use-azurite?tabs=visual-studio-code%2Cblob-storage) の手順に従い、ローカル開発用のストレージをインストールします。


## 1. Azure リソース作成

### 1-1. パラメーターファイルのコピーと修正

`main.bicepparam` ファイルのコピーを作成し、パラメータの値を指定するように修正します。

デプロイ前に値を指定する必要があるパラメータは以下の通りです：

- environmentName: 作成されるリソースに使用される一意の名前。
- location: アセットが作成される場所。利用可能なリージョンは以下の通りです。

    - `australiaeast`
    - `eastasia`
    - `eastus`
    - `eastus2`
    - `northeurope`
    - `southcentralus`
    - `southeastasia`
    - `swedencentral`
    - `uksouth`
    - `westus2`

※ これらのリージョンは、パブリックプレビューの早期アクセス時に利用可能です。

以下はコピー・修正後の `main.bicepparam` のサンプルです。

```
using 'main.bicep'
param environmentName = 'myflexconsumptionapp'
param location = 'eastasia'
```

### 1-２. デプロイ実行

例えば、`maincopy.bicepparam` を作成し、East US リージョンにデプロイする際、以下のコマンドを実行します。

```
cd infra
az deployment sub create --name fcthibicep1 --location eastus --template-file main.bicep --parameters maincopy.bicepparam
```

デプロイが完了すると、以下のようなリソースが作成されます。

![Azure Resources](./infra/images/resources.png "作成される Azure リソース一覧")

## 2. アプリケーションのデプロイ

### 2-1. Entra ID へのアプリケーション登録（サービスプリンシパル作成）

アプリケーション（インデックス作成ジョブ）で使用する認証情報を登録するため、Entra ID のアプリケーションを登録し、サービスプリンシパルを作成します。

まず、[クラウド アプリケーション管理者](https://learn.microsoft.com/ja-jp/entra/identity/role-based-access-control/permissions-reference#cloud-application-administrator)以上のユーザーで[Microsoft Entra 管理センター](https://entra.microsoft.com/)にサインインします。

![Entra 管理センター](./infra/images/entra_1.png "Entra 管理センター")

[ID]、[アプリケーション]、[アプリ登録] の順に進み、**[新規登録]** を選択します。

![Entra 管理センター](./infra/images/entra_2.png "Entra 管理センター")

アプリケーションに以下の設定をします。

- **名前**: 任意の名前（`app-NamedEntityRecognition-demo-001` など）。
- **サポートされているアカウントの種類**: この組織ディレクトリのみに含まれるアカウント。
- **リダイレクトURI**: 
    - **プラットフォーム**: `Web`
    - **値**: `http://localhost`

![Entra 管理センター](./infra/images/entra_3.png "Entra 管理センター")

**登録**ボタンを押下し、アプリケーションを登録します。

### 2-2. 作成したサービスプリンシパルにロールを割り当てる

上記で作成したサービスプリンシパルに対し、ストレージアカウントに保存されたファイルを読み取るための権限を付与します。

まず、Azure Portal で対象となるストレージアカウントに遷移し、**[アクセス制御（IAM）]**、**[ロールの割り当ての追加]**の順に選択します。

![ストレージアカウントへの権限付与](./infra/images/entra_4.png "ストレージアカウントへの権限付与")

**ストレージ BLOB データ閲覧者** を選択し、**次へ**を押下。

![ストレージアカウントへの権限付与](./infra/images/entra_5.png "ストレージアカウントへの権限付与")

`メンバー`にて、作成したアプリケーション名（`app-NamedEntityRecognition-demo-001` など）を選択し、**レビューと割り当て**を押下。

![ストレージアカウントへの権限付与](./infra/images/entra_6.png "ストレージアカウントへの権限付与")

再度**レビューと割り当て**を押下し、権限を付与。

**参考**

- [Microsoft Entra アプリを登録し、サービス プリンシパルを作成する](https://learn.microsoft.com/ja-jp/entra/identity-platform/howto-create-service-principal-portal)
- [DefaultAzureCredential では環境変数を使うと便利です（Java on Azure）](https://qiita.com/kk31108424/items/a2b2d8079f9faae49721)

### 2-3. サービスプリンシパルの資格情報発行

プログラムでサインインするときは、認証要求でディレクトリ (テナント) ID とアプリケーション (クライアント) ID を渡します。 証明書または認証キーも必要です。 

[Microsoft Entra 管理センター](https://entra.microsoft.com/)にサインインします。

![Entra 管理センター](./infra/images/entra_1.png "Entra 管理センター")

[ID]、[アプリケーション]、[アプリ登録] の順に進み、作成したアプリケーション（`app-NamedEntityRecognition-demo-001` など）を選択します。

表示されている **アプリケーション（クライアント）ID**、**ディレクトリ（テナント）ID**をメモ帳にコピーします。

![Entra 管理センター](./infra/images/entra_7.png "Entra 管理センター")

[証明書とシークレット] にて **+新しいクライアント シークレット**を選択し、シークレットを発行し、メモ帳にコピーします。シークレットは１度しか表示されないので、コピーし忘れに注意してください。

![Entra 管理センター](./infra/images/entra_8.png "Entra 管理センター")

メモ帳にコピーした値は、**2-4-2. 検索インデックス作成日次ジョブ用コンテナ** にて使用します。

### 2-4. ローカル環境での動作確認

ローカル環境で動作検証をします。

#### 2-4-1. アノテーション付与用関数アプリ

`app/fn/local.settings.sample.json` ファイルを同じディレクトリに `local.settings.json` というファイル名でコピーし、以下の値を編集します。

- **AZURE_OPENAI_API_KEY**: Azure OpenAI のキー
- **AZURE_OPENAI_ENDPOINT**: Azure OpenAI のエンドポイント
- **MODEL_ID**: Azure OpenAI に展開したデプロイ名

```
cd app/fn
func start
```

以下のように出力され、ローカル環境で関数アプリが起動する。

```
Functions:

        create_annotations: [POST] http://localhost:7071/api/annotations

        create_annotations_enrich: [POST] http://localhost:7071/api/annotations/enrich

        daily_sync_records: timerTrigger
```

#### 2-4-2. 検索インデックス作成用コンテナ（日次ジョブ）

`Dockerfile.sample` を同じディレクトリに `Dockerfile` というファイル名でコピーし、以下の値を編集します。

- **AZURE_OPENAI_ENDPOINT**: Azure OpenAI のエンドポイント
- **AZURE_OPENAI_API_KEY**: Azure OpenAI のキー
- **AI_SEARCH_SERVICE_NAME**: AI Search のリソース名
- **AI_SEARCH_API_KEY**: AI Search の API キー
- **STORAGE_ACCOUNT_NAME**: インデックス作成対象の文書が保管されるストレージアカウント名（`docs`で終わる値）
- **AZURE_TENANT_ID**: Entra ID テナント名（メモ帳にコピーした値）
- **AZURE_CLIENT_ID**: Entra ID アプリケーション ID（メモ帳にコピーした値）
- **AZURE_CLIENT_SECRET**: Entra ID アプリケーションシークレット（メモ帳にコピーした値）

`Dockerfile` 作成後、`app/createindex` ディレクトリに移動し、以下のコマンドでコンテナをビルド・実行します。

```
cd ../createindex
docker build -t createindex:0.0.1 --platform linux/x86_64 .  
docker run createindex:0.0.1
```

以下のログが出力されれば、コンテナは正常終了しています。

```
202x-xx-xx xx:xx:xx,xxx - root - INFO - Index created and documents uploaded successfully.
```

その他のログが出力されている場合は、コンテナは異常終了しています。データが Blob ストレージにアップロードされているか、`Dockerfile` に設定した環境変数が間違っていないか等を確認します。

#### 2-4-3. 検索クエリ処理用コンテナ

`Dockerfile.sample` を同じディレクトリに `Dockerfile` というファイル名でコピーし、以下の値を編集します。

- **AZURE_OPENAI_ENDPOINT**: Azure OpenAI のエンドポイント
- **AZURE_OPENAI_API_KEY**: Azure OpenAI のキー
- **AI_SEARCH_SERVICE_NAME**: AI Search のリソース名
- **AI_SEARCH_API_KEY**: AI Search の API キー
- **AZURE_TENANT_ID**: Entra ID テナント名（メモ帳にコピーした値）
- **AZURE_CLIENT_ID**: Entra ID アプリケーション ID（メモ帳にコピーした値）
- **AZURE_CLIENT_SECRET**: Entra ID アプリケーションシークレット（メモ帳にコピーした値）

`Dockerfile` 作成後、`app/search` ディレクトリに移動し、以下のコマンドでコンテナをビルド・実行します。

```
cd ../search
docker build -t search:0.0.1 --platform linux/x86_64 .  
docker run -p 8000:8000 search:0.0.1
```

検索クエリを実行します。ブラウザを開いて以下の URL を入力し、全文検索・ベクトル検索・ハイブリッド検索・セマンティックランク付けを試します。

`query` パラメータに、検索キーワードを入力します。

```
http://localhost:8000/fulltext?query=xxxxxxxxx

http://localhost:8000/vector?query=xxxxxxxxx

http://localhost:8000/hybrid?query=xxxxxxxxx

http://localhost:8000/semantic?query=xxxxxxxxx
```

### 2-5. Azure にアプリケーションをデプロイ

#### 2-5-1. アノテーション付与用関数アプリ

`app/fn` ディレクトリに作成した関数アプリを Azure にデプロイします。

以下のコマンドで Azure に関数アプリをデプロイします。

```
cd ../fn
func azure functionapp publish <APP_NAME>
```

関数アプリの環境変数に、それぞれ以下の値を設定します。

| 環境変数 | 値 |
| :--- | :--- |
| AZURE_OPENAI_API_KEY | Azure OpenAI の API キー |
| AZURE_OPENAI_ENDPOINT | Azure OpenAI のエンドポイント |

![AOAI 環境変数](./infra/images/openai_environment_variables.png "作成される Azure リソース一覧")

以下のコマンドを使って、動作確認をします。

```bash
curl -X POST -H "Content-Type: application/json" -d '{"text":"ここにテキストを入力"}' http://<関数アプリのURL>/api/annotations
```

#### 2-5-2. 検索インデックス作成用コンテナ（日次ジョブ）

`app/createindex` ディレクトリに作成したコンテナアプリ（日次ジョブ）を Azure にデプロイします。

以下のコマンドで Azure に `createindex` という名前のコンテナアプリ（ジョブ）をデプロイします。

日次ジョブとして、日本時間深夜0時に実行するためには、CRON式で `0 9 * * *` を指定します。

```
cd ../createindex
az acr login --name <YOUR_CONTAINER_REGISTRY_NAME>
docker tag createindex:0.0.1 <YOUR_CONTAINER_REGISTRY_NAME>.azurecr.io/createindex:0.0.1
docker push <YOUR_CONTAINER_REGISTRY_NAME>.azurecr.io/createindex:0.0.1

az containerapp job create --name "createindex" --resource-group "リソースグループ名"  --environment "Container Apps 環境名" --trigger-type "Schedule" --replica-timeout 1800 --image "<YOUR_CONTAINER_REGISTRY_NAME>.azurecr.io/createindex:0.0.1" --cpu "0.25" --memory "0.5Gi" --cron-expression "0 9 * * *"
```

#### 2-5-3. 検索クエリ処理用コンテナ

`app/search` ディレクトリに作成したコンテナアプリ（検索用 API）を Azure にデプロイします。

以下のコマンドで Azure にコンテナアプリをデプロイします。

```
cd ../search
az containerapp up --name <Container Apps 名> --source . --ingress external
```

検索クエリを実行します。ブラウザを開いて以下の URL を入力し、全文検索・ベクトル検索・ハイブリッド検索・セマンティックランク付けを試します。

`query` パラメータに、検索キーワードを入力します。

```
http://<Container Apps の URL>/fulltext?query=xxxxxxxxx

http://<Container Apps の URL>/vector?query=xxxxxxxxx

http://<Container Apps の URL>/hybrid?query=xxxxxxxxx

http://<Container Apps の URL>/semantic?query=xxxxxxxxx
```
