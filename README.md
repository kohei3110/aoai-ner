# Azure OpenAI を活用した固有表現抽出

![Architecture](./infra/images/architecture.png "サンプルアプリアーキテクチャ")

## 0. 環境準備

プロジェクトを開始する前に、以下のツールがインストールされていることを確認してください。

- [Git](https://git-scm.com/download/win) - 本リポジトリをクローンするために必要です。

- [Azure CLI](https://learn.microsoft.com/ja-jp/cli/azure/install-azure-cli-windows?tabs=azure-cli) - Azure リソース展開時に必要です。

- [Azure Developer CLI](https://learn.microsoft.com/ja-jp/azure/developer/azure-developer-cli/install-azd?tabs=winget-windows%2Cbrew-mac%2Cscript-linux&pivots=os-windows) - Azure リソースを管理するために必要です。

- [Docker](https://docs.docker.com/engine/install/) - コンテナを展開するために必要です。

以下のリソースがデプロイされます:

- **Resource Group**: リソースを管理するためのコンテナ（リソースグループ）。
- **Azure Monitor**: アプリケーションの監視とログ収集を行います。
- **Azure Functions**: サーバーレスアプリケーションをホストします。
- **Azure OpenAI**: OpenAIモデルのホスティングと管理を行います。
- **Azure Container Apps**: コンテナベースのアプリケーションをホストします。
- **Azure Container Registry**: Dockerコンテナイメージの管理を行います。

リポジトリをローカル環境にクローンします。

```
git clone https://github.com/kohei3110/aoai-ner.git
cd aoai-ner
```

## 1. Azure リソース作成

### 1-1. パラメーターファイルのコピーと修正

`infra/main.bicepparam` ファイルのパラメータの値を指定するように修正します。

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

例えば、East US リージョンにデプロイする際、`infra/main.bicepparam` を以下のように書き換えます。

```
using 'main.bicep'
param environmentName = 'dev'
param location = 'eastus'
```

### 1-２. デプロイ実行

以下のコマンドを実行します。

```
az login
azd auth login
azd init
```

環境名を聞かれるので、任意の値（`dev`など）を入力し、Enter を押します。

```
Initializing an app to run on Azure (azd init)

Enter a new environment name: dev
```

`SUCCESS: New project initiated` と表示されたら成功です。

Azure リソースを展開します。

```
azd up
```

※ Windows で実行時、エラーが出た場合は以下のコマンドにより `pwsh` に PATH を通してください。

```
dotnet tool update --global PowerShell
```

**デプロイ先のサブスクリプション・リージョン**を Enter で選択します。本ハンズオンでは、リージョンを `East US` にすることを推奨します。

デプロイが完了すると、以下のようなリソースが作成されます。

![Azure Resources](./infra/images/resources.png "作成される Azure リソース一覧")

## 2. サービスプリンシパル登録・権限付与

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

**ストレージ Blob データ共同作成者** を選択し、**次へ**を押下。

![ストレージアカウントへの権限付与](./infra/images/entra_5.png "ストレージアカウントへの権限付与")

`メンバー`にて、作成したアプリケーション名（`app-NamedEntityRecognition-demo-001` など）を選択し、**レビューと割り当て**を押下。

![ストレージアカウントへの権限付与](./infra/images/entra_6.png "ストレージアカウントへの権限付与")

再度**レビューと割り当て**を押下し、権限を付与。

**参考**

- [Microsoft Entra アプリを登録し、サービス プリンシパルを作成する](https://learn.microsoft.com/ja-jp/entra/identity-platform/howto-create-service-principal-portal)
- [DefaultAzureCredential では環境変数を使うと便利です（Java on Azure）](https://qiita.com/kk31108424/items/a2b2d8079f9faae49721)

### 2-3. Azure 上のアプリケーションの動作確認

Azure にデプロイ済みのアプリケーションを動作確認します。

#### 2-3-1. アノテーション付与用コンテナ（日次ジョブ）

Azure Portal から**コンテナー アプリ ジョブ**を検索します。

**cajannot** から始まるジョブを選択します。

**▷Run now** を押下し、アノテーション付与ジョブを実行します。

![ジョブ実行](./infra/images/job_1.png "ジョブ実行")

#### 2-3-2. 検索インデックス作成用コンテナ（日次ジョブ）

Azure Portal から**コンテナー アプリ ジョブ**を検索します。

**cajindex** から始まるジョブを選択します。

**▷Run now** を押下し、アノテーション付与ジョブを実行します。

![ジョブ実行](./infra/images/job_2.png "ジョブ実行")

#### 2-3-3. 検索クエリ処理用コンテナ

検索クエリを実行します。ブラウザを開いて以下の URL を入力し、全文検索・ベクトル検索・ハイブリッド検索・セマンティックランク付けを試します。

`query` パラメータに、検索キーワードを入力します。

```
http://<Container Apps の URL>/fulltext?query=xxxxxxxxx

http://<Container Apps の URL>/vector?query=xxxxxxxxx

http://<Container Apps の URL>/hybrid?query=xxxxxxxxx

http://<Container Apps の URL>/semantic?query=xxxxxxxxx
```