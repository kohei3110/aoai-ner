import warnings
import tiktoken
import os
import logging
import sys
from fastapi import FastAPI, Query
from langchain.text_splitter import RecursiveCharacterTextSplitter
from openai import AzureOpenAI
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

app = FastAPI()

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

# Azure AI Search のインデックス名と API キー
search_service_name = os.environ.get("AI_SEARCH_SERVICE_NAME")
index_name = os.environ.get("AI_SEARCH_INDEX_NAME")
api_version = "2023-11-01"
api_key = os.environ.get("AI_SEARCH_API_KEY")

# AI Search のエンドポイント
service_endpoint="https://{0}.search.windows.net/".format(search_service_name)

default_credential = DefaultAzureCredential()

text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    encoding_name='cl100k_base',
    chunk_size=1000, 
    chunk_overlap=50  # 一般的に、文書の長さの10%~15%が良いとされる
)
enc = tiktoken.get_encoding("cl100k_base")

@app.get('/health')
def healthcheck():
    # FIXME: Add more health checks
    return {'status': 'ok'}

"""
全文検索
"""
@app.get('/fulltext')
def fulltext(query: str = Query(..., title="Search query")):
    search_client = build_search_client()
    results = execute_fulltext_search(search_client, query)
    return process_results(results)

"""
ベクトル検索
"""
@app.get('/vector')
def vector(query: str = Query(..., title="Search query")):
    aoai_client, search_client = build_clients()
    response = get_embedding(aoai_client, query)
    results = execute_vector_search(search_client, response)
    return process_results(results)

"""
ハイブリッド検索
"""
@app.get('/hybrid')
def hybrid(query: str = Query(..., title="Search query")):
    aoai_client, search_client = build_clients()
    response = get_embedding(aoai_client, query)
    results = execute_hybrid_search(search_client, query, response)
    return process_results(results)

"""
セマンティック検索
"""
@app.get('/semantic')
def semantic(query: str = Query(..., title="Search query")):
    aoai_client, search_client = build_clients()
    response = get_embedding(aoai_client, query)
    results = execute_semantic_search(search_client, query, response)
    return process_semantic_results(results)

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

# 埋め込みを取得するメソッド
def get_embedding(client: AzureOpenAI, text: str):
    response = client.embeddings.create(
        input = text,
        model= "text-embedding-ada-002"
    )
    return response

def build_clients():
    aoai_client = build_aoai_client()
    search_client = build_search_client()
    return aoai_client, search_client

def build_aoai_client():
    return AzureOpenAI(
        api_key = os.getenv("AZURE_OPENAI_API_KEY"),  
        api_version = "2024-02-01",
        azure_endpoint =os.getenv("AZURE_OPENAI_ENDPOINT") 
    )

def build_search_client():
    return SearchClient(service_endpoint, index_name, AzureKeyCredential(api_key))

def execute_fulltext_search(search_client, query):
    return search_client.search(
        search_text=query,
        select=["sourcepage", "content"],
        top=5
    )

def execute_vector_search(search_client, embedding):
    return search_client.search(  
        search_text=None,  
        vector_queries=[
            VectorizedQuery(
                kind="vector", vector=embedding.data[0].embedding, k_nearest_neighbors=3, fields="contentVector"
            )
        ],
    )

def execute_hybrid_search(search_client, query, response):
    return search_client.search(  
        search_text=query,  
        vector_queries=[
            VectorizedQuery(
                kind="vector", vector=response.data[0].embedding, k_nearest_neighbors=3, fields="contentVector"
            )
        ],
        top=5
    )

def execute_semantic_search(search_client, query, response):
    return search_client.search(
        search_text=query,
        vector_queries=[
            VectorizedQuery(
                kind="vector", vector=response.data[0].embedding, k_nearest_neighbors=3, fields="contentVector"
            )
        ],
        query_type="semantic",
        semantic_configuration_name="config1",
        query_caption="extractive", 
        query_answer="extractive",
        select=["sourcepage", "content"],
        top=5
    )

def process_results(results):
    results_list = []
    for result in results:
        results_list.append(dict(result))
    return results_list

def process_semantic_results(results):
    semantic_answers = results.get_answers()
    for answer in semantic_answers:
        log_answer(answer)
    results_list = [dict(result) for result in results]
    return results_list

def log_answer(answer):
    if answer.highlights:
        logging.info(f"Semantic Answer: {answer.highlights}")
    else:
        logging.info(f"Semantic Answer: {answer.text}")
    logging.info(f"Semantic Answer Score: {answer.score}\n")