# Equipment And Procurement Management

장비 운영 및 조달 관리 업무를 위한 **Streamlit UI 프로토타입**입니다.  
[GP2 MariaDB DDL](docs/GP2_Maria.pdf) 스키마를 기준으로 화면을 구성했으며, **mng_db** MariaDB에 SSH 터널로 연결해 조회·저장합니다.

## 실행 방법

### 1. 환경 준비

Python 3.9+ 권장. 프로젝트 루트에서 가상환경을 쓰는 것을 권장합니다.

```bash
cd streamlit-app
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. 앱 실행

```bash
streamlit run app.py
```

브라우저가 열리면 왼쪽 **사이드바**에서 홈(`app`)과 각 페이지로 이동할 수 있습니다.

### 3. DB 연결 설정

`db.ini.example`을 복사해 `db.ini`를 만들고 SSH·DB 계정을 입력합니다 (`*.ini`는 gitignore).

```bash
cp db.ini.example db.ini
# db.ini 편집
```

환경 변수로도 설정할 수 있습니다: `DB_SSH_HOST`, `DB_SSH_USER`, `DB_SSH_PASSWORD`, `DB_USER`, `DB_PASSWORD` 등.

연결 확인:

```bash
python connection_test.py
```

## 페이지 구성

사이드바 이름은 `pages/` 파일명에서 숫자 접두사(`01_` 등)를 뺀 뒤 표시됩니다. 각 페이지 상단 제목과 동일한 라벨을 사용합니다.

| 순서 | 사이드바 / 제목 | 테이블 | 주요 기능 |
|------|-----------------|--------|-----------|
| 홈 | app (Equipment And Procurement Management) | — | 업무 흐름 안내, 데이터 요약, 데모 초기화 |
| 01 | Business Location | `business_location` | 사업장 목록 조회, 등록·수정·삭제 (유형: Warehouse / Store / Site) |
| 02 | Contract | `contract` | 사업장별 계약 등록·수정 (기간, 상태, 회수 정보) |
| 03 | Machine | `machine`, `machine_contract_hst` | 장비 CRUD, 송장 연결, **계약 이력** 탭에서 장비–계약 이력 추가 |
| 04 | Order | `order` | 주문 목록 + 상세 폼 (주문/운송/기타 탭), 기술자·사업장 FK |
| 05 | Purchase Request | `purchase_request`, `purchase_request_item` | 구매 요청 헤더 + **동적 품목** (제품, 수량) |
| 06 | Purchase Order | `purchase_order`, `purchase_order_item` | 발주 헤더 + 품목(수량, 단가), **합계 금액** 자동 계산 |
| 07 | Invoice | `invoice`, `invoice_item` | 발주 선택 시 공급업체 자동 연동, 송장 품목·합계 |
| 08 | Vendor | `vendor` | 공급업체 마스터 CRUD |
| 09 | Product | `product` | 제품 마스터 CRUD |
| 10 | Technician | `technician` | 기술자 마스터 CRUD (주문 화면 FK용) |

## 권장 업무 흐름

1. **마스터**: Business Location → Vendor → Product → Technician  
2. **조달**: Purchase Request → Purchase Order → Invoice → Machine 등록  
3. **운영**: Contract → Machine + 계약 이력 → Order 처리  

## 프로젝트 구조

```
streamlit-app/
├── app.py                 # 진입점 (홈)
├── pages/                 # 멀티페이지 (01~10)
├── lib/
│   ├── repository/        # 도메인별 CRUD · FK 검증
│   ├── db.py / db_store.py # SSH 터널 + MariaDB
│   ├── labels.py          # 컬럼명 기반 UI 라벨
│   └── components/        # 공통 폼·품목 위젯
├── db.ini.example         # DB 연결 설정 예시
├── data/seed.json         # (참고용) 예전 목 데이터 샘플
├── docs/                  # ER/DDL PDF, 주문 UI 참고 이미지
└── tutorial/              # Streamlit 학습용 예제 (본 앱과 무관)
```

## 참고

- UI 라벨은 DB 컬럼명을 영문 Title Case로 표시합니다 (예: `location_id` → Location Id).  
- `order.memo` 등 DDL에 없는 필드는 UI에만 표시되며 DB에는 저장되지 않습니다.  
- `tutorial/` 폴더는 별도 학습 자료이며, 본 앱 실행에 필요하지 않습니다.
