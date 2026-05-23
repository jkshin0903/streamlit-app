"""장비 운영 및 조달 관리 시스템 — 홈."""

import streamlit as st

from lib import repository

st.set_page_config(
    page_title="장비 운영 · 조달 관리",
    page_icon="🏭",
    layout="wide",
)

repository.init_if_needed()

st.title("장비 운영 및 조달 관리 시스템")
st.caption("Equipment & Procurement Management — 목 데이터 데모")

st.markdown(
    """
이 앱은 **GP2 MariaDB DDL** 기반 UI 프로토타입입니다.  
데이터는 `data/seed.json`에서 로드된 **in-memory 목 저장소**에 유지됩니다.
"""
)

if st.button("데모 데이터 초기화"):
    repository.reset_demo_data()
    st.success("seed.json 기준으로 데이터를 복원했습니다.")
    st.experimental_rerun()

st.divider()

st.subheader("권장 업무 흐름")

col1, col2 = st.columns(2)

with col1:
    st.markdown(
        """
**① 마스터 데이터**  
1. 사업장 관리  
2. 공급업체 · 제품 · 기술자  

**② 조달 프로세스**  
구매 요청 → 구매 발주 → 송장 → 장비 등록
"""
    )

with col2:
    st.markdown(
        """
**③ 장비 운영**  
계약 등록 → 장비 등록 → 계약 이력 연결  

**④ 주문 처리**  
주문 생성(대기) → 기술자 배정 → 완료 처리
"""
    )

st.subheader("사이드바 메뉴")
st.markdown(
    "왼쪽 사이드바에서 각 화면으로 이동하세요. 번호 순서가 업무 흐름과 대응합니다."
)

with st.expander("현재 데이터 요약"):
    st.write(
        {
            "사업장": len(repository.list_locations()),
            "공급업체": len(repository.list_vendors()),
            "제품": len(repository.list_products()),
            "기술자": len(repository.list_technicians()),
            "구매 요청": len(repository.list_purchase_requests()),
            "구매 발주": len(repository.list_purchase_orders()),
            "송장": len(repository.list_invoices()),
            "계약": len(repository.list_contracts()),
            "장비": len(repository.list_machines()),
            "주문": len(repository.list_orders()),
        }
    )
