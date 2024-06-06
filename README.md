# Azure OpenAI を活用した固有表現抽出

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

### 2-1. ローカル環境での動作確認

ローカル環境で動作検証をします。`app/python/local.settings.sample.json` ファイルを同じディレクトリに `local.settings.json` というファイル名でコピーし、以下の値を編集します。

- **AZURE_OPENAI_API_KEY**: Azure OpenAI のキー
- **AZURE_OPENAI_ENDPOINT**: Azure OpenAI のエンドポイント
- **MODEL_ID**: Azure OpenAI に展開したデプロイ名

```
cd app/python
func start
```

以下のように出力され、ローカル環境で関数アプリが起動する。

```
Functions:

        create_annotations: [POST] http://localhost:7071/api/annotations

        create_annotations_enrich: [POST] http://localhost:7071/api/annotations/enrich

        daily_sync_records: timerTrigger
```

### 2-2. Azure に関数アプリを展開

以下のコマンドで Azure に関数アプリを展開する。

```
func azure functionapp publish <APP_NAME>
```

関数アプリの環境変数に、それぞれ以下の値を設定する。

| 環境変数 | 値 |
| :--- | :--- |
| AZURE_OPENAI_API_KEY | Azure OpenAI の API キー |
| AZURE_OPENAI_ENDPOINT | Azure OpenAI のエンドポイント |

![AOAI 環境変数](./infra/images/openai_environment_variables.png "作成される Azure リソース一覧")

以下のコマンドを使って、動作確認をします。

```bash
curl -X POST -H "Content-Type: application/json" -d '{"text":"ここにテキストを入力"}' http://<関数アプリのURL>/api/annotations
```