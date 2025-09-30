# pip install azure-search-documents openai azure-identity
import os

# from azure.identity import DefaultAzureCredential
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# 환경 변수 설정 (로컬 .env 추천)
SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
INDEX_NAME = os.getenv("INDEX_NAME")

client = SearchClient(
    endpoint=SEARCH_ENDPOINT,
    index_name=INDEX_NAME,
    credential=AzureKeyCredential(SEARCH_API_KEY),
)

query = input("질문을 입력하세요: ")

results = client.search(
    query_type="simple",
    search_text=query,
    select="keyphrases,locations,merged_content",
    include_total_count=True,
    # filter="@search.score gt 4",
    # order_by="@search.score desc",
)

#print("Total Documents Matching Query:", results.get_count())

docs = []
for r in results:
    docs.append(r["merged_content"])

client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY")
)

# 2) Azure OpenAI로 프롬프트 구성
prompt = f"""
너는 시스템 운영자들의 문의에 답변하는 챗봇이야.
다음 문서를 참고하여 사용자의 질문에 답해줘.

문서:
{docs}

질문: {query}
"""

response = client.chat.completions.create(
    model=os.getenv("AZURE_DEPLOYMENT_MODEL"),
    messages=[{"role": "user", "content": prompt}],
)

print(response.choices[0].message.content)
