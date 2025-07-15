# 네이버 스타일 디자인 시스템 적용

## 개요
업무관리시스템의 전반적인 디자인을 네이버의 깔끔하고 직관적인 디자인 철학을 참고하여 개선했습니다.

## 주요 변경사항

### 1. 색상 시스템
- **네이버 그린**: `#03C75A` (메인 브랜드 컬러)
- **다크 그린**: `#00B04F` (호버 상태)
- **라이트 그린**: `#E8F5E8` (배경 강조)
- **그레이 스케일**: 9단계 그레이 시스템 적용
- **우선순위 색상**: 직관적인 색상 구분 (긴급: 빨강, 높음: 주황, 보통: 노랑, 낮음: 초록)

### 2. 타이포그래피
- **폰트**: Noto Sans KR (한글 최적화)
- **기본 크기**: 14px (가독성 향상)
- **라인 높이**: 1.6 (읽기 편한 간격)
- **폰트 웨이트**: 300, 400, 500, 700 (다양한 강조 레벨)

### 3. 레이아웃 개선
- **헤더**: 그라데이션 배경의 네이버 그린 컬러
- **사이드바**: 깔끔한 흰색 배경, 활성 메뉴 강조
- **카드**: 부드러운 그림자와 호버 효과
- **반응형**: 모바일 친화적 레이아웃

### 4. 컴포넌트 스타일링

#### 버튼
- 그라데이션 배경
- 호버 시 상승 효과
- 클릭 피드백 애니메이션

#### 카드
- 8px 둥근 모서리
- 미묘한 그림자 효과
- 호버 시 상승 애니메이션

#### 폼 요소
- 네이버 그린 포커스 컬러
- 부드러운 테두리 전환
- 아이콘 통합 디자인

#### 테이블
- 깔끔한 헤더 스타일
- 행 호버 효과
- 반응형 스크롤

### 5. 아이콘 시스템
- **Font Awesome 6.4.0** 사용
- 일관된 아이콘 스타일
- 의미에 맞는 아이콘 선택:
  - 대시보드: `fa-tachometer-alt`
  - 업무: `fa-tasks`
  - 워크로그: `fa-calendar-week`
  - 리포트: `fa-chart-line`
  - 카테고리: `fa-tags`

### 6. 인터랙션 개선
- 부드러운 전환 효과 (0.2s ease)
- 호버 상태 피드백
- 로딩 상태 표시
- 키보드 단축키 지원

### 7. 접근성 향상
- 충분한 색상 대비
- 키보드 네비게이션 지원
- 스크린 리더 친화적 마크업
- 포커스 인디케이터 개선

## 파일 구조

```
templates/
├── base.html (메인 레이아웃)
├── base_simple.html (간단한 레이아웃)
├── dashboard/
│   └── dashboard.html (대시보드)
└── registration/
    └── login.html (로그인 페이지)

static/
├── css/
│   └── naver-style.css (추가 스타일)
└── js/
    └── app.js (통합 스크립트)
```

## 주요 기능

### CSS 변수 시스템
```css
:root {
    --naver-green: #03C75A;
    --naver-dark-green: #00B04F;
    --naver-light-green: #E8F5E8;
    /* ... 기타 색상 변수 */
}
```

### JavaScript 클래스
```javascript
class NaverStyleUI {
    // 통합 UI 관리 클래스
    // 애니메이션, 인터랙션, 유틸리티 메서드 제공
}
```

### 반응형 브레이크포인트
- **모바일**: < 576px
- **태블릿**: 576px - 768px
- **데스크톱**: > 768px

## 성능 최적화
- CSS 변수 활용으로 일관성 유지
- 트랜지션 최적화 (GPU 가속)
- 이미지 지연 로딩
- 자동 저장 기능

## 브라우저 지원
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## 다크 모드 지원
- `prefers-color-scheme` 미디어 쿼리 활용
- 자동 색상 전환
- 사용자 선호도 반영

## 사용법

### 새로운 컴포넌트 추가
```html
<div class="card">
    <div class="card-header">
        <h5><i class="fas fa-icon me-2"></i>제목</h5>
    </div>
    <div class="card-body">
        내용
    </div>
</div>
```

### 알림 표시
```javascript
naverUI.showNotification('메시지', 'success');
naverUI.showToast('제목', '내용', 'info');
```

### 로딩 상태
```javascript
naverUI.loadingOverlay(true);  // 표시
naverUI.loadingOverlay(false); // 숨김
```

## 향후 개선 계획
1. 다크 모드 토글 기능
2. 사용자 테마 커스터마이징
3. 애니메이션 성능 최적화
4. PWA 지원
5. 오프라인 모드

## 참고 자료
- [네이버 디자인 시스템](https://naver.design/)
- [Bootstrap 5.3 문서](https://getbootstrap.com/)
- [Font Awesome 아이콘](https://fontawesome.com/)
- [Noto Sans KR 폰트](https://fonts.google.com/noto/specimen/Noto+Sans+KR)
