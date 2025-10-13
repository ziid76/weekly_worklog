"""Service layer for miscellaneous application features."""

from .report_review import review_last_4_weeks, generate_writing_guide

__all__ = ["review_last_4_weeks", "generate_writing_guide"]
