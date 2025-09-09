# 첨부파일 기능 개선 요약

## 구현된 기능

### 1. 업무 첨부파일 삭제 기능
- **위치**: task_detail.html 사이드바 첨부파일 섹션
- **권한**: 파일 업로드자 또는 업무 작성자만 삭제 가능
- **구현 내용**:
  - 각 첨부파일 옆에 삭제 버튼 추가
  - 삭제 확인 다이얼로그 표시
  - 실제 파일과 DB 레코드 모두 삭제

### 2. 댓글 첨부파일 업로드 기능
- **위치**: task_detail.html 댓글 작성 폼
- **기능**:
  - 댓글 작성 시 파일 첨부 가능
  - 첨부된 파일은 댓글과 함께 표시
  - 파일 다운로드 링크 제공

## 수정된 파일

### 1. 모델 (task/models.py)
```python
class TaskComment(models.Model):
    # 기존 필드들...
    file = models.FileField("첨부파일", upload_to='comment_files/', blank=True, null=True)
```

### 2. 폼 (task/forms.py)
```python
class TaskCommentForm(forms.ModelForm):
    class Meta:
        model = TaskComment
        fields = ['content', 'file']  # file 필드 추가
```

### 3. 뷰 (task/views.py)
- `add_comment()`: 파일 업로드 처리 추가
- `delete_file()`: 새로운 파일 삭제 뷰 추가

### 4. URL (task/urls.py)
```python
path('file/<int:file_id>/delete/', views.delete_file, name='delete_file'),
```

### 5. 템플릿 (task/templates/task/task_detail.html)
- 첨부파일 목록에 삭제 버튼 추가
- 댓글 표시 시 첨부파일 링크 추가
- 댓글 작성 폼에 파일 업로드 필드 추가

## 데이터베이스 마이그레이션
```bash
python manage.py makemigrations task
python manage.py migrate
```

## 사용법

### 첨부파일 삭제
1. 업무 상세 페이지 접속
2. 사이드바 "첨부파일" 섹션에서 삭제할 파일 찾기
3. 파일 옆 휴지통 아이콘 클릭
4. 확인 다이얼로그에서 "확인" 클릭

### 댓글에 파일 첨부
1. 업무 상세 페이지 하단 댓글 작성 폼
2. 댓글 내용 입력
3. "첨부파일 (선택사항)" 필드에서 파일 선택
4. "댓글 작성" 버튼 클릭

## 보안 및 권한
- **파일 삭제**: 파일 업로드자 또는 업무 작성자만 가능
- **댓글 작성**: 업무 작성자 또는 담당자만 가능
- **파일 다운로드**: 기존 권한 체계 유지

## 파일 저장 위치
- 업무 첨부파일: `media/task_files/`
- 댓글 첨부파일: `media/comment_files/`
