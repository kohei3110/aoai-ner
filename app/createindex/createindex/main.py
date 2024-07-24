import os
import pandas as pd
import asyncio
import datetime
import warnings
import logging
import sys
import glob
import base64
import requests
import json as JSON
import shutil
from azure.identity import DefaultAzureCredential
from azure.storage.blob import BlobServiceClient
from langchain_text_splitters import RecursiveCharacterTextSplitter
from openai import AzureOpenAI

"""
- 日次のインデックス作成(https://learn.microsoft.com/ja-jp/azure/search/vector-search-how-to-create-index?tabs=config-2023-11-01%2Crest-2023-11-01%2Cpush%2Cportal-check-index)
   - 多くの場合、既存のフィールドの更新と削除には、削除と再構築が必要です。
   - ただし、再構築しなくても、次の変更を加えて既存のスキーマを更新できます。
      - Fields コレクションに新しいフィールドを追加します。
      - 新しいベクトル構成を追加します。新しいフィールドには割り当てられますが、既にベクトル化されている既存のフィールドには割り当てられません。
      - 既存のフィールドの "retrievable" (値は true または false) を変更します。 ベクトル フィールドは検索可能で取得可能である必要がありますが、削除と再構築が不可能な状況でベクトル フィールドへのアクセスを無効にする場合は、retrievable を false に設定できます。
- チャンク化の単位は？ファイルごとにチャンク化する？既定のまま？
   - まずは Recursive Character でチャンク化してみる方針にします。
   - 意味のある単位が出なかったら、Semantic Splitting でチャンク化することも検討します。
"""

# すべての警告を表示させない
warnings.filterwarnings('ignore')

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # 標準出力へのハンドラーを追加
    ]
)

# Azure Cognitive Search のインデックス名と API キー
search_service_name = os.environ.get("AI_SEARCH_SERVICE_NAME")
index_name = os.environ.get("AI_SEARCH_INDEX_NAME")
api_version = "2023-11-01"
api_key = os.environ.get("AI_SEARCH_API_KEY")

# インデックス作成の REST API の URL
createindex_url = "https://{0}.search.windows.net/indexes/{1}?api-version={2}".format(search_service_name, index_name, api_version)

# データをアップロードするための REST API の URL
base_url = "https://{0}.search.windows.net/indexes/{1}/docs/index?api-version={2}".format(search_service_name, index_name, api_version)

# Blob ストレージの URL
account_url = "https://{0}.blob.core.windows.net".format(os.environ.get("STORAGE_ACCOUNT_NAME"))

default_credential = DefaultAzureCredential()

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    encoding_name='cl100k_base',
    chunk_size=1000, 
    chunk_overlap=50  # 文書の長さの10%~15%が良いとされる
)

# 一日ごとにインデックスを作成する(Push型)
async def schedule():
    while True:
        blob_service_client = build_blob_client()
        process_blobs(blob_service_client, os.environ.get("STORAGE_CONTAINER_NAME"))
        # チャンク分割済みテキストファイルを DataFrame の行としてロード
        df = await load_and_transform_data()
        if await is_dataframe_empty(df):
            logging.info("Dataframe is empty. Skip the process.")
            sys.exit(0)
        client = build_aoai_client()
        if 'contentVector' not in df.columns:
            df['contentVector'] = pd.Series(dtype='object')
        for i, row in df.iterrows():
            response = get_embedding(client, row['content'])
            df.at[i, 'contentVector'] = response.data[0].embedding
        df = await get_embeddings_and_update_df(df)
        try:
            await create_index(createindex_url, api_key)
            await upload_documents(base_url, api_key, df)
            await cleanup_downloads()
            sys.exit(0)
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP error occurred: {http_err}")
            sys.exit(1)
        except Exception as err:
            logging.error(f"Other error occurred: {err}")
            sys.exit(1)

def build_blob_client():
    return BlobServiceClient(account_url, credential=default_credential)

def process_blobs(blob_service_client: BlobServiceClient, storage_container_name):
    """Blobの処理を行うメイン関数"""
    container_client = blob_service_client.get_container_client(storage_container_name)
    recent_blobs = get_recent_blobs(container_client)
    for blob in recent_blobs:
        logging.info(f"Blob name: {blob.name}")
        file_path = download_blob(container_client, blob)
        split_chunk_file(file_path)

async def load_and_transform_data():
    results = []
    for p in glob.glob('./download/output/*.txt'):
        result = make_dataframe(p)
        results.append(result)
    df = pd.DataFrame(results, columns=['id', 'content', 'sourcepage'])
    return df

async def is_dataframe_empty(df):
    if df.empty:
        logging.info("Dataframe is empty. Skip the process.")
        return True
    return False

def build_aoai_client():
    return AzureOpenAI(
        api_key = os.getenv("AZURE_OPENAI_API_KEY"),  
        api_version = "2024-02-01",
        azure_endpoint =os.getenv("AZURE_OPENAI_ENDPOINT") 
    )

async def get_embeddings(df):
    client = build_aoai_client()
    if 'contentVector' not in df.columns:
        df['contentVector'] = pd.Series(dtype='object')
    for i, row in df.iterrows():
        response = get_embedding(client, row['content'])
        df.at[i, 'contentVector'] = response.data[0].embedding
    return df

def get_embedding(client: AzureOpenAI, text: str):
    response = client.embeddings.create(
        input = text,
        model= "text-embedding-ada-002"
    )
    return response

async def get_embeddings_and_update_df(df):
    client = build_aoai_client()
    if 'contentVector' not in df.columns:
        df['contentVector'] = pd.Series(dtype='object')
    for i, row in df.iterrows():
        response = get_embedding(client, row['content'])
        df.at[i, 'contentVector'] = response.data[0].embedding
    return df

async def create_index(url, api_key):
    try:
        with open("./requests/create_vector_index_with_semantic.json", 'r', encoding="utf-8") as f:
            jsondata = JSON.load(f)
            response = requests.put(url, headers={"Content-Type": "application/json", "api-key": api_key}, json=jsondata)
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"Other error occurred: {err}")
    else:
        logging.info(f"Index created successfully: {response.status_code}")
    return response.status_code

async def upload_documents(url, api_key, df):
    jsondata = {
        "value": JSON.loads(df.to_json(orient='records'))
    }
    try:
        response = requests.post(url, headers={"Content-Type": "application/json", "api-key": api_key}, json=jsondata)
    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        logging.error(f"Other error occurred: {err}")
    else:
        logging.info(f"Data uploaded successfully: {response.status_code}")
    return response.status_code

async def cleanup_downloads():
    for p in glob.glob('./download/*'):
        if os.path.isdir(p):
            shutil.rmtree(p)
        else:
            os.remove(p)

def get_recent_blobs(container_client, hours=24):
    """指定された時間内に更新されたBlobのリストを取得する"""
    recent_blobs = []
    blob_list = container_client.list_blobs()
    for blob in blob_list:
        if blob.last_modified.date() >= (datetime.datetime.now() - datetime.timedelta(hours=hours)).date():
            recent_blobs.append(blob)
    return recent_blobs

def download_blob(container_client, blob, download_path="./download/"):
    """Blobをダウンロードする"""
    file_path = os.path.join(download_path, blob.name)
    blob_client = container_client.get_blob_client(blob)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "wb") as file:
        file.write(blob_client.download_blob().readall())
    return file_path

#ファイルを読み込んで、指定のトークン数のチャンクファイルに分割するメソッド
def split_chunk_file(filepath):
    logging.info('splitting chunk file: ' + filepath)
    f = open(filepath, 'r', encoding='UTF-8')
    data = f.read()
    chunk = text_splitter.split_text(data)
    for i, chunkedtext in enumerate(chunk):
        dirname = os.path.dirname(filepath)
        basename = os.path.splitext(os.path.basename(filepath))[0]
        outputfilepath = dirname + "/output/" + basename + "-" + str(i) + ".txt"
        os.makedirs(os.path.dirname(outputfilepath), exist_ok=True)
        with open(outputfilepath, 'w', encoding='UTF-8') as fo:
            fo.write(chunkedtext)
        fo.close()
    f.close()
    return

# 必要なデータフレームを作成するメソッド
def make_dataframe(filepath):
    f = open(filepath, 'r', encoding='UTF-8')
    data = f.read()
    content = " ".join(data.splitlines())
    
    filename = os.path.basename(filepath)
    enc_id = base64.urlsafe_b64encode(filename.encode())
    
    return {'id': enc_id.decode(), 'content': content, 'sourcepage': filename}

async def main():
    await schedule()
    sys.exit()

if __name__ == "__main__":
    asyncio.run(main())