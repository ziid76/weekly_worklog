# 프로젝트 플랜: 비주얼 업무 프로세스 관리 시스템 (Visual BPM)

## 1. 프로젝트 개요
기존 Django 기반 시스템을 확장하여, 업무 프로세스를 다이어그램(Box & Line) 형태로 시각화하고 각 단계의 상세 정보(텍스트, 이미지, 문서) 및 변경 이력을 관리하는 모듈을 구축합니다.

## 2. 주요 기능 정의
- **Visual Flow Editor**: 노드(Node)와 엣지(Edge)를 드래그 앤 드롭으로 배치 및 연결
- **Content Management**: 각 노드별 상세 설명(Rich Text), 이미지 업로드, 첨부 파일 관리
- **Version Control**: 프로세스 수정 시 스냅샷 저장 및 버전별 이력 조회/복구
- **Existing System Integration**: 기존 Django Auth 및 네비게이션 메뉴와 통합

## 3. 기술 스택
- **Backend**: Python 3.x, Django, Django Rest Framework (DRF)
- **Frontend**: React (또는 Vue.js), React Flow (다이어그램 라이브러리)
- **Database**: 기존 시스템 DB (PostgreSQL 등)
- **Storage**: 로컬 미디어 스토리지를 활용한 파일 관리

## 4. 데이터 모델 설계 (Django Models)
- `Workflow`: 전체 프로세스의 메타 데이터 및 현재 버전 관리
- `Node`: 프로세스 내 개별 단계 (좌표, 타입, 레이블 정보 포함)
- `Edge`: 단계 간의 연결선 정보 (Source, Target)
- `NodeDetail`: 노드와 1:1 매칭되는 상세 정보 (HTML 본문, 파일 경로 등)
- `WorkflowHistory`: 버전별 다이어그램 상태를 JSON 형태로 스냅샷 저장

## 5. 개발 로드맵 (Vibe Coding Flow)

### Phase 1: Backend Infrastructure
1. `models.py` 정의: Workflow, Node, Edge, NodeDetail, History 모델 구현
2. `serializers.py` 작성: 다이어그램 데이터 구조를 위한 직렬화
3. `views.py` 엔드포인트 구축: CRUD API 및 버전 저장 로직 구현

### Phase 2: Frontend Editor Implementation
1. React Flow를 이용한 캔버스 환경 구축
2. 노드 생성/삭제/연결 기능 및 자동 레이아웃(선택 사항) 구현
3. 노드 클릭 시 상세 정보를 입력할 수 있는 Side Panel(또는 Modal) 개발

### Phase 3: Detailed Content & Versioning
1. 이미지 및 파일 업로드를 위한 Media API 연동
2. 변경 발생 시 `WorkflowHistory`에 자동으로 기록되는 Signal 또는 Save 로직 강화
3. 이전 버전으로 복구(Restore)하는 기능 구현

### Phase 4: Integration & UI/UX
1. 기존 Django 템플릿에 React 앱 임베딩
2. 권한(Admin/User)에 따른 편집/조회 기능 제한
3. Tailwind CSS를 활용한 UI 정교화