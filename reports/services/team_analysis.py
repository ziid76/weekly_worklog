"""Backward-compatible import for the moved AI team analysis service."""

from app.services.team_analysis import TeamPerformanceAnalyzer

__all__ = ["TeamPerformanceAnalyzer"]
