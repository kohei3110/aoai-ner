# Flex Consumption app - Bicep

この Bicep ファイルは、以下の Azure コンポーネントを作成するために使用されます。

- **Function App**: 

サーバーレスの Flex Consumption アプリで、ここに関数コードをデプロイします。この Function App は Application Insights と Storage Account で構成されています。

- **Function App Plan**: 

Flex Consumption アプリに関連付けられた Azure Functions のアプリプランです。Flex Consumption ではプランごとに1つのアプリのみ許可されますが、それでもプランは作成されます。

- **Application Insights**: 

Flex Consumption アプリに関連付けられたテレメトリーサービスで、ライブアプリケーションの監視、パフォーマンス異常の検出、テレメトリーログの確認、アプリの動作理解に役立ちます。

- **Log Analytics Workspace**: 

Application Insights がアプリのテレメトリーに使用するワークスペースです。

- **Storage Account**: 

Azure Functions インスタンスを作成する際に必要な Microsoft Azure ストレージアカウントです。

