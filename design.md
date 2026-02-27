# ITMS 디자인 가이드 (Tailwind CSS)

이 문서는 ITMS 프로젝트의 일관된 사용자 경험(UX)과 시각적 아이덴티티를 유지하기 위한 디자인 원칙 및 UI 컴포넌트 사용 가이드를 설명합니다.

## 1. 컬러 팔레트 (Color Palette)
- **주요 색상 (Primary)**: `#0077C8` (Pantone 3005C) - 주요 액션 버튼, 활성 상태, 하이라이트에 사용합니다.
- **배경색 (Background)**: `#F8FAFC` (Slate 50) - 전체적인 콘텐츠 영역의 배경입니다.
- **표면색 (Surface)**: `#FFFFFF` (White) - 카드, 모달, 사이드바의 배경입니다.
- **텍스트 (Text)**:
  - 기본 (Primary): `slate-900` (#0f172a) - 제목 및 주요 본문.
  - 보조 (Secondary): `slate-500` (#64748b) - 설명 및 라벨.
  - 약하게 (Muted): `slate-400` (#94a3b8) - 홀더 텍스트 및 보조 라벨.
- **상태 색상 (Status Colors)**:
  - 성공/완료: `emerald-500` / `bg-emerald-50`
  - 대기/경고: `amber-500` / `bg-amber-50`
  - 에러/긴급: `rose-500` / `bg-rose-50`
  - 정보/진행중: `blue-500` / `bg-blue-50`

## 2. 타이포그래피 (Typography)
- **기본 폰트**: `Manrope` (Sans-serif)
- **계층 구조**:
  - 페이지 제목: `text-3xl font-extrabold tracking-tight`
  - 카드 제목: `text-lg font-bold`
  - 본문 텍스트: `text-sm font-medium`
  - 소형/라벨: `text-xs font-bold uppercase tracking-wider`

## 3. 레이아웃 및 간격 (Layout & Spacing)
- **메인 컨테이너**: `max-w-[1400px] mx-auto p-4 md:p-8 flex flex-col gap-8`
- **섹션 간격**: 주요 섹션 간에는 `gap-8`, 관련 그룹 내에서는 `gap-4`를 사용합니다.
- **섹션 헤더**: 왼쪽에는 제목과 설명을, 오른쪽에는 액션 버튼을 배치하는 Flex 컨테이너 구조를 권장합니다.

## 4. 컴포넌트 (Components)

### 카드 (Cards)
- **표준 카드**: `bg-white rounded-[2rem] border border-slate-200 shadow-sm overflow-hidden`
- **대시보드/리스트 카드**: `bg-white rounded-[2rem] border border-slate-200 p-6 hover:shadow-xl hover:border-primary/20 transition-all`
- **반경 (Radius)**: 큰 반경(`2rem` 또는 `rounded-[2rem]`)은 ITMS의 핵심 아이덴티티입니다. 작은 아이템에는 `rounded-xl`을 사용합니다.

### 버튼 (Buttons)
- **기본 버튼 (Primary)**: `rounded-full bg-primary text-white font-bold px-6 py-2.5 hover:bg-primary/90 transition-all shadow-lg shadow-primary/20`
- **보조 버튼 (Secondary/Ghost)**: `rounded-full bg-slate-50 text-slate-600 font-bold px-6 py-2.5 hover:bg-slate-100 transition-all`
- **아이콘 버튼**: 원형 또는 모서리가 약간 둥근 사각형 안에 아이콘을 중앙 배치합니다.

### 관리 테이블 (Management Tables)
- **컨테이너**: `bg-white`, `rounded-[2.5rem]`, `border border-slate-200`, `shadow-sm`, `overflow-hidden`.
- **헤더**: `bg-slate-50/50`, `px-8`, `py-5`, `text-xs font-black text-slate-400 uppercase tracking-widest border-b border-slate-100`.
- **행 호버**: `hover:bg-slate-50/50 transition-colors`.
- **셀 콘텐츠**:
  - 제목: `text-sm font-bold text-slate-900`.
  - ID/부제목: `text-[11px] text-slate-400 font-medium`.
- **액션 버튼**: `size-9`, `rounded-lg`, `bg-slate-50`, `text-slate-400`, `hover:bg-primary/10 hover:text-primary transition-all`.

### 상태 배지 (Status Badges)
- **공통**: `px-3 py-1 rounded-full text-[10px] font-black uppercase tracking-wider border`.
- **기본/정보**: `bg-blue-50 text-blue-600 border-blue-100`.
- **성공/활성**: `bg-emerald-50 text-emerald-600 border-emerald-100`.
- **경고/대기**: `bg-amber-50 text-amber-600 border-amber-100`.
- **위험/지연**: `bg-rose-50 text-rose-600 border-rose-100`.
- **보조/비활성**: `bg-slate-50 text-slate-400 border-slate-200`.

### 통계 및 대시보드 (Stats & Cards)
- **통계 카드**: `bg-white rounded-[2rem] border border-slate-200 p-8 shadow-sm flex flex-col gap-4`.
- **통계 라벨**: `text-xs font-bold uppercase tracking-wider text-slate-400`.
- **통계 수치**: `text-4xl font-black text-slate-900`.
- **AI 인사이트 카드**: `bg-slate-900 rounded-[2.5rem] p-8 md:p-12 shadow-2xl relative overflow-hidden`.

## 5. 시각 효과 (Visual Effects)
- **그림자 (Shadows)**: 주요 요소에는 부드러운 컬러 그림자(`shadow-primary/20`)를 사용합니다.
- **애니메이션 (Transitions)**: 호버 효과 시 `transition-all duration-200`을 적용합니다.
- **아이콘 (Icons)**: `Material Symbols Outlined` 라이브러리를 사용합니다.
