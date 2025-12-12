from django import template
from django.utils.safestring import mark_safe
import markdown

register = template.Library()

@register.filter(name='markdown')
def markdown_format(text):
    """Convert markdown text to HTML"""
    if not text:
        return ''
    
    # Configure markdown with extensions
    md = markdown.Markdown(extensions=[
        'markdown.extensions.fenced_code',
        'markdown.extensions.tables',
        'markdown.extensions.nl2br',
        'markdown.extensions.toc',
    ])
    
    return mark_safe(md.convert(text))
