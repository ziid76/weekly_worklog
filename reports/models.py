from django.db import models
from django.contrib.auth.models import User
from teams.models import Team
from worklog.models import Worklog


class WeeklyReport(models.Model):
    """주간 집계 리포트"""
    year = models.IntegerField("년도")
    week_number = models.IntegerField("주차")
    title = models.CharField("리포트 제목", max_length=200)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='weekly_reports', null=True, blank=True, verbose_name="대상 팀")
    editable = models.BooleanField("입력마감 여부", default=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('year', 'week_number', 'team')
        ordering = ['-year', '-week_number']

    def __str__(self):
        team_name = self.team.name if self.team else "전체"
        return f"{self.year}년 {self.week_number}주차 주간 리포트 ({team_name})"

    @property
    def get_worklog_count(self):
        """리포트에 작성된 주간업무 수"""        
        return Worklog.objects.filter(year=self.year, week_number=self.week_number).count


    @property
    def week_start_date(self):
        """해당 주의 월요일 날짜"""
        import datetime
        return datetime.date.fromisocalendar(self.year, self.week_number, 1)

    @property
    def week_end_date(self):
        """해당 주의 일요일 날짜"""
        import datetime
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
    def month_week_display_with_year(self):
        return f"{self.month_week_display} ({self.year}년 {self.week_number}주차)"

    @property
    def month_week_display(self):
        """'7월 1주차'와 같은 형식으로 월별 주차를 반환합니다."""
        import datetime
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

class WeeklyReportComment(models.Model):
    """주간 리포트 코멘트"""
    report = models.ForeignKey(WeeklyReport, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField("코멘트 내용")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.report} - {self.author.username}"


class WeeklyReportPersonalComment(models.Model):
    """담당자별 업무 코멘트"""
    report = models.ForeignKey(WeeklyReport, on_delete=models.CASCADE, related_name='personal_comments')
    target_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personal_report_comments')
    content = models.TextField("업무 코멘트")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_personal_report_comments')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"{self.report} - {self.target_user.username}"


class TeamWeeklyReport(models.Model):
    """팀별 주간 리포트"""
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='team_weekly_reports')
    year = models.IntegerField("년도")
    week_number = models.IntegerField("주차")
    title = models.CharField("리포트 제목", max_length=200)
    summary = models.TextField("주간 요약", blank=True)
    achievements = models.TextField("주요 성과", blank=True)
    issues = models.TextField("이슈 및 문제점", blank=True)
    next_week_plan = models.TextField("다음 주 계획", blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_team_reports')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('team', 'year', 'week_number')
        ordering = ['-year', '-week_number']

    def __str__(self):
        return f"{self.team.name} - {self.year}년 {self.week_number}주차"

    @property
    def week_start_date(self):
        """해당 주의 월요일 날짜"""
        import datetime
        return datetime.date.fromisocalendar(self.year, self.week_number, 1)

    @property
    def week_end_date(self):
        """해당 주의 일요일 날짜"""
        import datetime
        return self.week_start_date + datetime.timedelta(days=6)

    @property
    def month_week_display_with_year(self):
        return f"{self.month_week_display} ({self.year}년 {self.week_number}주차)"

    @property
    def month_week_display(self):
        """'7월 1주차'와 같은 형식으로 월별 주차를 반환합니다."""
        import datetime
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
