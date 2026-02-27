from django.db import models
from django.contrib.auth.models import User
import datetime

class Worklog(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='worklogs')
    year = models.IntegerField("년도")
    week_number = models.IntegerField("주차")
    this_week_work = models.TextField("이번 주 수행 업무", blank=True)
    next_week_plan = models.TextField("다음 주 계획", blank=True)
    display_order = models.IntegerField("표시 순서", default=0, help_text="주간보고서에서의 표시 순서 (낮은 숫자가 먼저 표시)")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('author', 'year', 'week_number')
        ordering = ['display_order', 'author__profile__last_name_ko', 'author__username']

    def __str__(self):
        return f'{self.author.username} - {self.year}년 {self.week_number}주차'

    @property
    def week_start_date(self):
        """ISO year, week number를 기반으로 해당 주의 월요일 날짜를 반환합니다."""
        return datetime.date.fromisocalendar(self.year, self.week_number, 1)

    @property
    def week_end_date(self):
        """해당 주의 금요일 날짜를 반환합니다."""
        return self.week_start_date + datetime.timedelta(days=4)

    @property
    def next_week_start_date(self):
        import datetime
        return self.week_start_date + datetime.timedelta(days=7)

    @property
    def next_week_end_date(self):
        import datetime
        return self.week_start_date + datetime.timedelta(days=11)

    @property
    def month_week_display(self):
        """'7월 1주차'와 같은 형식으로 월별 주차를 반환합니다."""
        start_date = self.week_start_date
        end_date = self.week_end_date
        
        # 주의 시작과 끝이 같은 달인 경우
        if start_date.month == end_date.month:
            # 해당 월의 첫 번째 월요일을 찾아서 몇 번째 주인지 계산
            first_monday = start_date.replace(day=1)
            while first_monday.weekday() != 0:  # 0 = 월요일
                first_monday += datetime.timedelta(days=1)
            
            week_diff = (start_date - first_monday).days // 7 + 1
            return f"{start_date.month}월 {week_diff}주차"
        else:
            # 주가 두 달에 걸쳐있는 경우, 더 많은 날이 포함된 달 기준
            if start_date.day <= 3:  # 월요일~수요일이 이전 달
                month = end_date.month
                first_monday = end_date.replace(day=1)
                while first_monday.weekday() != 0:
                    first_monday += datetime.timedelta(days=1)
                week_diff = (end_date - first_monday).days // 7 + 1
            else:  # 목요일~일요일이 다음 달
                month = start_date.month
                first_monday = start_date.replace(day=1)
                while first_monday.weekday() != 0:
                    first_monday += datetime.timedelta(days=1)
                week_diff = (start_date - first_monday).days // 7 + 1
            
            return f"{month}월 {week_diff}주차"

    @staticmethod
    def get_current_week_info():
        """현재 날짜의 연도와 ISO 주차를 반환합니다."""
        today = datetime.date.today()
        year, week_number, _ = today.isocalendar()
        return year, week_number


class WorklogFile(models.Model):
    worklog = models.ForeignKey(Worklog, on_delete=models.CASCADE, related_name='files')
    file = models.FileField("파일", upload_to='worklog_files/')
    original_name = models.CharField("원본 파일명", max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.original_name