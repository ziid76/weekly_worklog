import uuid
from django.db import models
from django.contrib.auth.models import User

class ReviewHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    input_code = models.TextField(verbose_name="Input Code")
    business_context = models.TextField(blank=True, null=True, verbose_name="Business Context")
    core_review_point = models.TextField(blank=True, null=True, verbose_name="Core Review Point")
    program_name = models.CharField(max_length=255, blank=True, null=True, verbose_name="Program Name")
    review_result = models.TextField(verbose_name="Review Result")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Created At")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Created By")

    class Meta:
        verbose_name = "Review History"
        verbose_name_plural = "Review Histories"
        ordering = ['-created_at']

    def __str__(self):
        name = self.program_name if self.program_name else self.id
        return f"Review {name} at {self.created_at}"
