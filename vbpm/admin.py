from django.contrib import admin
from .models import Workflow, Node, Edge, NodeDetail, NodeFile, WorkflowHistory

@admin.register(Workflow)
class WorkflowAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at', 'updated_at', 'created_by')
    search_fields = ('name', 'description')

@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ('workflow', 'node_id', 'label', 'type')
    list_filter = ('workflow', 'type')

@admin.register(Edge)
class EdgeAdmin(admin.ModelAdmin):
    list_display = ('workflow', 'edge_id', 'source', 'target')
    list_filter = ('workflow',)

@admin.register(NodeDetail)
class NodeDetailAdmin(admin.ModelAdmin):
    list_display = ('node', 'content')

@admin.register(NodeFile)
class NodeFileAdmin(admin.ModelAdmin):
    list_display = ('node_detail', 'filename', 'uploaded_at')

@admin.register(WorkflowHistory)
class WorkflowHistoryAdmin(admin.ModelAdmin):
    list_display = ('workflow', 'version', 'created_at', 'created_by')
    list_filter = ('workflow',)
