import streamlit as st

# 브라우저 탭 타이틀 설정
st.set_page_config(page_title="ktt 운영자 매뉴얼")
import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

SEARCH_ENDPOINT = os.getenv("AZURE_SEARCH_ENDPOINT")
SEARCH_API_KEY = os.getenv("AZURE_SEARCH_API_KEY")
INDEX_NAME = os.getenv("INDEX_NAME")

search_client = SearchClient(
    endpoint=SEARCH_ENDPOINT,
    index_name=INDEX_NAME,
    credential=AzureKeyCredential(SEARCH_API_KEY),
)

def get_search_results(query):
    results = search_client.search(
        query_type="simple",
        search_text=query,
        select="keyphrases,locations,merged_content",
        include_total_count=True,
    )
    docs = []
    for r in results:
        docs.append(r["merged_content"])
    return docs

openai_client = AzureOpenAI(
    api_version=os.getenv("AZURE_OPENAI_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY")
)

def get_answer(docs, query):
    prompt = f"""
너는 시스템 운영자들의 문의에 답변하는 챗봇이야.
다음 문서를 참고하여 사용자의 질문에 답해줘.

문서:
{docs}

질문: {query}
"""
    response = openai_client.chat.completions.create(
        model=os.getenv("AZURE_DEPLOYMENT_MODEL"),
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content

def get_history():
    if "history" not in st.session_state:
        st.session_state["history"] = []
    return st.session_state["history"]

st.markdown('<h1 style="text-align: center;">kt telecop 운영자 매뉴얼</h1>', unsafe_allow_html=True)


# 채팅 UI
chat_history = get_history()


# 채팅 메시지 출력 및 anchor 생성
for idx, chat in enumerate(chat_history):
    anchor = f"q{idx}"
    st.markdown(f'<div id="{anchor}"></div>', unsafe_allow_html=True)
    with st.chat_message("user"):
        st.markdown(chat["질문"])
    with st.chat_message("assistant"):
        st.markdown(chat["답변"])
    # 스크롤 이동 처리
    if "scroll_to" in st.session_state and st.session_state["scroll_to"] == anchor:
        st.markdown(f"<script>document.getElementById('{anchor}').scrollIntoView({{behavior: 'smooth'}});</script>", unsafe_allow_html=True)
        del st.session_state["scroll_to"]

user_input = st.chat_input("질문을 입력하세요...")

if user_input:
    with st.chat_message("user"):
        st.markdown(user_input)
    with st.spinner("검색 중..."):
        docs = get_search_results(user_input)
        answer = get_answer(docs, user_input)
    with st.chat_message("assistant"):
        st.markdown(answer)
        with st.expander("참고 문서"):
            for i, doc in enumerate(docs, 1):
                st.markdown(f"**문서 {i}:**\n{doc}")
    # 기록 저장
    chat_history.append({"질문": user_input, "답변": answer})
    st.session_state["history"] = chat_history



# 초기화면에 주의 메시지 및 예시 질문 추가
if not chat_history:
    st.warning("여기서 제공하는 정보는 100% 정확하지 않을 수 있습니다. 중요한 업무는 반드시 관련 부서나 공식 문서를 통해 재확인 후 진행해 주세요.")
    st.markdown("""
    <div style='border-radius:10px; padding:20px; margin-bottom:20px; border:1px solid #e0e0e0;'>
    <h3>예시 질문</h3>
    <ul>
        <li>고객통합앱 WEB서버 재기동 방법을 알려줘</li>
        <li>OC연동 서비스 실행 방법을 알려줘</li>
        <li>각 서비스 별 백업 정책을 알고싶어</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)


# 왼쪽 사이드바에 질문 목록 및 클릭 이동 기능
#if chat_history:
st.sidebar.title("질문 목록")
for idx, chat in enumerate(chat_history):
    # 각 질문에 고유 anchor 생성
    anchor = f"q{idx}"
    if st.sidebar.button(chat["질문"], key=f"sidebar_q{idx}"):
        st.session_state["scroll_to"] = anchor
