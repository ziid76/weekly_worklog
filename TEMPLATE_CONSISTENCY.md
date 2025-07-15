# 템플릿 일관성 가이드

## 개요
모든 템플릿 페이지에서 일관된 디자인과 사용자 경험을 제공하기 위한 가이드입니다.

## 페이지 구조 표준

### 1. 페이지 헤더
모든 페이지는 다음과 같은 표준 헤더 구조를 사용합니다:

```html
<div class="page-header">
    <div class="d-flex justify-content-between align-items-center">
        <div>
            <h1 class="page-title">
                <i class="fas fa-icon me-3"></i>페이지 제목
            </h1>
            <p class="page-subtitle mb-0">페이지 설명</p>
        </div>
        <div class="page-actions">
            <button class="btn btn-primary">
                <i class="fas fa-plus me-2"></i>주요 액션
            </button>
        </div>
    </div>
</div>
```

### 2. 카드 헤더
카드 내부의 제목은 다음 구조를 사용합니다:

```html
<div class="card-header">
    <h5 class="card-title mb-0">
        <i class="fas fa-icon me-2"></i>카드 제목
    </h5>
</div>
```

### 3. 빈 상태 표시
데이터가 없을 때는 일관된 빈 상태를 표시합니다:

```html
<div class="empty-state">
    <div class="empty-icon">
        <i class="fas fa-icon"></i>
    </div>
    <h6 class="empty-title">제목</h6>
    <p class="empty-description">설명</p>
    <a href="#" class="btn btn-primary">
        <i class="fas fa-plus me-2"></i>액션
    </a>
</div>
```

## 타이틀 크기 표준

### 페이지 레벨
- **페이지 제목**: `page-title` 클래스 (28px, font-weight: 700)
- **페이지 부제목**: `page-subtitle` 클래스 (16px, font-weight: 400)

### 섹션 레벨
- **섹션 제목**: `section-title` 클래스 (24px, font-weight: 700)
- **서브섹션 제목**: `subsection-title` 클래스 (20px, font-weight: 600)
- **카드 제목**: `card-title` 클래스 (18px, font-weight: 600)

### 컨텐츠 레벨
- **일반 제목**: `h6` 태그 (16px, font-weight: 600)
- **작은 제목**: `small` 태그 (14px, font-weight: 500)

## 패딩 및 마진 표준

### 페이지 레벨
- **페이지 헤더**: `padding: 24px 32px`, `margin-bottom: 32px`
- **메인 컨텐츠**: `padding: 24px` (카드 내부)

### 컴포넌트 레벨
- **카드 헤더**: `padding: 20px 24px`
- **카드 바디**: `padding: 24px`
- **리스트 아이템**: `padding: 16px`
- **작은 컴포넌트**: `padding: 12px 16px`

### 간격
- **섹션 간격**: `margin-bottom: 32px`
- **카드 간격**: `margin-bottom: 24px`
- **요소 간격**: `margin-bottom: 16px`
- **작은 간격**: `margin-bottom: 8px`

## 아이콘 사용 표준

### 페이지별 아이콘
- **대시보드**: `fa-tachometer-alt`
- **업무 관리**: `fa-tasks`
- **워크로그**: `fa-calendar-week`
- **리포트**: `fa-chart-line`
- **카테고리**: `fa-tags`
- **사용자**: `fa-user-circle`
- **설정**: `fa-cog`

### 액션별 아이콘
- **추가/생성**: `fa-plus`
- **수정/편집**: `fa-edit`
- **삭제**: `fa-trash`
- **보기/상세**: `fa-eye`
- **검색**: `fa-search`
- **필터**: `fa-filter`
- **새로고침**: `fa-sync-alt`
- **저장**: `fa-save`
- **취소**: `fa-times`
- **확인**: `fa-check`

### 상태별 아이콘
- **성공**: `fa-check-circle` (녹색)
- **경고**: `fa-exclamation-triangle` (주황색)
- **오류**: `fa-times-circle` (빨간색)
- **정보**: `fa-info-circle` (파란색)
- **로딩**: `fa-spinner fa-spin`

### 우선순위별 아이콘
- **긴급**: `fa-exclamation-triangle` (빨간색)
- **높음**: `fa-arrow-up` (주황색)
- **보통**: `fa-minus` (노란색)
- **낮음**: `fa-arrow-down` (녹색)

## 색상 사용 표준

### 브랜드 색상
- **주 색상**: `var(--naver-green)` (#03C75A)
- **보조 색상**: `var(--naver-dark-green)` (#00B04F)
- **배경 색상**: `var(--naver-light-green)` (#E8F5E8)

### 상태 색상
- **성공**: `#4CAF50`
- **경고**: `#FF9800`
- **오류**: `#F44336`
- **정보**: `#2196F3`

### 우선순위 색상
- **긴급**: `#FF4757`
- **높음**: `#FF6B35`
- **보통**: `#FFA726`
- **낮음**: `#66BB6A`

### 그레이 스케일
- **텍스트**: `var(--naver-gray-800)` (#333333)
- **보조 텍스트**: `var(--naver-gray-600)` (#777777)
- **비활성 텍스트**: `var(--naver-gray-500)` (#999999)
- **테두리**: `var(--naver-gray-300)` (#DDDDDD)
- **배경**: `var(--naver-gray-100)` (#F5F5F5)

## 반응형 디자인 표준

### 브레이크포인트
- **모바일**: `< 576px`
- **태블릿**: `576px - 768px`
- **데스크톱**: `> 768px`

### 모바일 최적화
- 페이지 헤더 패딩: `16px`
- 카드 패딩: `16px`
- 버튼 크기: 최소 44px 높이
- 터치 영역: 최소 44px × 44px

## 접근성 표준

### 키보드 네비게이션
- 모든 인터랙티브 요소는 키보드로 접근 가능
- 포커스 인디케이터 제공
- 논리적인 탭 순서

### 색상 대비
- 텍스트와 배경 간 최소 4.5:1 대비율
- 중요한 정보는 색상에만 의존하지 않음

### 스크린 리더
- 의미 있는 alt 텍스트
- 적절한 헤딩 구조
- ARIA 레이블 사용

## 성능 최적화

### 이미지
- 적절한 크기와 포맷 사용
- 지연 로딩 적용
- WebP 포맷 우선 사용

### CSS/JS
- 중요하지 않은 CSS는 지연 로딩
- JavaScript는 필요시에만 로드
- 압축 및 최소화

## 테스트 가이드

### 브라우저 테스트
- Chrome, Firefox, Safari, Edge 최신 버전
- 모바일 브라우저 (iOS Safari, Chrome Mobile)

### 기능 테스트
- 모든 링크와 버튼 동작 확인
- 폼 유효성 검사 확인
- 반응형 레이아웃 확인

### 접근성 테스트
- 키보드 네비게이션 테스트
- 스크린 리더 테스트
- 색상 대비 검사

이 가이드를 따라 모든 템플릿을 일관되게 유지하여 사용자에게 통일된 경험을 제공합니다.
