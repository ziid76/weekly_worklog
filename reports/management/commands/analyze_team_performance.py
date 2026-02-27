from django.core.management.base import BaseCommand
from reports.services.team_analysis import TeamPerformanceAnalyzer
from teams.models import Team
import logging
from datetime import date

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Analyze team performance based on last 4 weeks of worklogs.'

    def add_arguments(self, parser):
        parser.add_argument('team_id', type=int, help='Target Team ID')
        parser.add_argument('--year', type=int, help='ISO year anchor for analysis')
        parser.add_argument('--week', type=int, help='ISO week anchor for analysis')

    def handle(self, *args, **options):
        team_id = options['team_id']
        try:
            team = Team.objects.get(id=team_id)
        except Team.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Team with ID {team_id} not found.'))
            return

        self.stdout.write(f"Starting analysis for team: {team.name}")

        anchor_year = options.get('year')
        anchor_week = options.get('week')
        if bool(anchor_year) ^ bool(anchor_week):
            self.stdout.write(self.style.ERROR('Both --year and --week must be provided together.'))
            return
        if not anchor_year and not anchor_week:
            anchor_year, anchor_week, _ = date.today().isocalendar()
        else:
            try:
                date.fromisocalendar(anchor_year, anchor_week, 1)
            except ValueError:
                self.stdout.write(self.style.ERROR('Invalid --year/--week combination.'))
                return

        analyzer = TeamPerformanceAnalyzer(team_id)
        result = analyzer.analyze_last_4_weeks(anchor_year=anchor_year, anchor_week=anchor_week)
        
        if 'error' in result:
             self.stdout.write(self.style.ERROR(f"Analysis failed: {result['error']}"))
        else:
             self.stdout.write(self.style.SUCCESS(f"Analysis completed successfully for {team.name}"))
