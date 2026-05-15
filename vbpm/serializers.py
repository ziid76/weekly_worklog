from django.utils import timezone
from rest_framework import serializers

from .models import Workflow, Node, Edge, NodeDetail, NodeFile, WorkflowHistory, LogicFlowNodeDetail, LogicFlowNodeFile

class NodeFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NodeFile
        fields = ['id', 'file', 'filename', 'uploaded_at']

class NodeDetailSerializer(serializers.ModelSerializer):
    files = NodeFileSerializer(many=True, read_only=True)
    
    class Meta:
        model = NodeDetail
        fields = ['id', 'content', 'files']

class NodeSerializer(serializers.ModelSerializer):
    detail = NodeDetailSerializer(read_only=True)
    
    class Meta:
        model = Node
        fields = ['id', 'node_id', 'type', 'position_x', 'position_y', 'label', 'detail']

class EdgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Edge
        fields = ['id', 'edge_id', 'source', 'target']

class WorkflowSerializer(serializers.ModelSerializer):
    nodes = NodeSerializer(many=True, read_only=True)
    edges = EdgeSerializer(many=True, read_only=True)
    current_version = serializers.CharField(read_only=True)
    
    class Meta:
        model = Workflow
        fields = ['id', 'name', 'description', 'created_at', 'updated_at', 'created_by', 'current_version', 'nodes', 'edges']

class WorkflowHistorySerializer(serializers.ModelSerializer):
    created_at = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = WorkflowHistory
        fields = ['id', 'workflow', 'version', 'snapshot', 'description', 'created_at', 'created_by', 'created_by_name']

    def get_created_at(self, obj):
        if not obj.created_at:
            return ""
        return timezone.localtime(obj.created_at).strftime("%Y-%m-%d %H:%M")

    def get_created_by_name(self, obj):
        if not obj.created_by:
            return ''
        profile = getattr(obj.created_by, "profile", None)
        if profile and getattr(profile, "display_name", None):
            return profile.display_name
        return obj.created_by.get_full_name() or obj.created_by.username

class LogicFlowNodeFileSerializer(serializers.ModelSerializer):
    class Meta:
        model = LogicFlowNodeFile
        fields = ['id', 'file', 'filename', 'uploaded_at']

class LogicFlowNodeDetailSerializer(serializers.ModelSerializer):
    files = LogicFlowNodeFileSerializer(many=True, read_only=True)
    class Meta:
        model = LogicFlowNodeDetail
        fields = ['id', 'node_id', 'content', 'files']
