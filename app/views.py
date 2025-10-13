"""Application level views."""

from __future__ import annotations

import logging
from datetime import date
from typing import Optional

from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
import markdown
import os

from .services import review_last_4_weeks

logger = logging.getLogger(__name__)


def review_me(request: HttpRequest) -> JsonResponse:
    """Return Gemini-based review JSON for a user."""
    if not request.user.is_authenticated:
        return JsonResponse({"error": "authentication_required"}, status=401)

    if request.method != "GET":
        return JsonResponse({"error": "method_not_allowed"}, status=405)

    target_user_id = request.GET.get("user_id")
    target_user: User

    if target_user_id:
        # Basic permission check: only staff/superusers can view others' reports, or users can view their own.
        if (
            not request.user.is_staff
            and not request.user.is_superuser
            and str(request.user.id) != target_user_id
        ):
            return JsonResponse({"error": "permission_denied"}, status=403)

        try:
            target_user = User.objects.get(pk=target_user_id)
        except User.DoesNotExist:
            return JsonResponse(
                {"error": f"User with id {target_user_id} not found."},
                status=404,
            )
    else:
        target_user = request.user

    as_of_param = request.GET.get("as_of")
    as_of_date: Optional[date] = None
    if as_of_param:
        try:
            as_of_date = date.fromisoformat(as_of_param)
        except ValueError:
            logger.warning("Invalid as_of parameter received: %s", as_of_param)
            return JsonResponse({"error": "invalid_as_of"}, status=400)

    logger.info(
        "review_me invoked by user=%s for target_user=%s as_of=%s",
        request.user.pk,
        target_user.pk,
        as_of_date,
    )
    payload = review_last_4_weeks(target_user, as_of=as_of_date)
    return JsonResponse(payload, json_dumps_params={"ensure_ascii": False})


def user_manual(request: HttpRequest):
    """Display the user manual."""
    user_manual_files = [
        "USER_MANUAL.md",
    ]
    
    combined_md = ""
    for md_file in user_manual_files:
        combined_md += f"\n# {os.path.basename(md_file)}\n\n"
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                combined_md += f.read() + "\n\n---\n\n"
        except FileNotFoundError:
            combined_md += f"### 파일을 찾을 수 없습니다: {md_file}\n\n"

    md = markdown.Markdown(extensions=['extra', 'toc', 'codehilite'])
    user_manual_html = md.convert(combined_md)
    toc_html = md.toc

    return render(request, "manuals/user_manual.html", {
        "user_manual_html": user_manual_html,
        "toc_html": toc_html
    })

def developer_manual(request: HttpRequest):
    """Display the developer manual."""
    developer_manual_files = [
        "ADMIN_GUIDE.md",
    ]

    combined_md = ""
    for md_file in developer_manual_files:
        combined_md += f"\n# {os.path.basename(md_file)}\n\n"
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                combined_md += f.read() + "\n\n---\n\n"
        except FileNotFoundError:
            combined_md += f"### 파일을 찾을 수 없습니다: {md_file}\n\n"
            
    md = markdown.Markdown(extensions=['extra', 'toc', 'codehilite'])
    developer_manual_html = md.convert(combined_md)
    toc_html = md.toc

    return render(request, "manuals/developer_manual.html", {
        "developer_manual_html": developer_manual_html,
        "toc_html": toc_html
    })
