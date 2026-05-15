import json
from decimal import Decimal, InvalidOperation

from django.shortcuts import get_object_or_404, render
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.response import Response

from .models import (
    Edge,
    LogicFlowNodeDetail,
    LogicFlowNodeFile,
    Node,
    NodeDetail,
    Workflow,
    WorkflowHistory,
)
from .serializers import (
    EdgeSerializer,
    LogicFlowNodeDetailSerializer,
    NodeDetailSerializer,
    NodeSerializer,
    WorkflowHistorySerializer,
    WorkflowSerializer,
)


def _parse_graph_payload(value, fallback):
    if value in (None, ""):
        return fallback
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return fallback
        return parsed if parsed is not None else fallback
    return value


def _legacy_to_x6(workflow):
    nodes = []
    edges = []

    for node in workflow.nodes.all():
        label = node.label or "Node"
        node_type = (node.type or "").lower()
        shape = "rect"
        width = 120
        height = 60
        body_attrs = {
            "stroke": "#0077C8",
            "strokeWidth": 2,
            "fill": "#f0f9ff",
            "rx": 8,
            "ry": 8,
        }

        if "circle" in node_type:
            shape = "circle"
            width = 80
            height = 80
            body_attrs = {
                "stroke": "#0077C8",
                "strokeWidth": 2,
                "fill": "#f0f9ff",
            }
        elif "diamond" in node_type or "polygon" in node_type:
            shape = "polygon"
            width = 100
            height = 100
            body_attrs = {
                "stroke": "#0077C8",
                "strokeWidth": 2,
                "fill": "#f0f9ff",
                "refPoints": "0,10 10,0 20,10 10,20",
            }

        nodes.append(
            {
                "id": node.node_id,
                "shape": shape,
                "x": node.position_x,
                "y": node.position_y,
                "width": width,
                "height": height,
                "attrs": {
                    "body": body_attrs,
                    "label": {
                        "text": label,
                        "fill": "#334155",
                        "fontSize": 14,
                        "fontWeight": "bold",
                    },
                },
            }
        )

    for edge in workflow.edges.all():
        edges.append(
            {
                "id": edge.edge_id,
                "shape": "edge",
                "source": {"cell": edge.source},
                "target": {"cell": edge.target},
                "router": {"name": "orth"},
                "connector": {"name": "rounded", "args": {"radius": 8}},
                "attrs": {
                    "line": {
                        "stroke": "#94a3b8",
                        "strokeWidth": 2,
                        "targetMarker": {
                            "name": "block",
                            "width": 12,
                            "height": 8,
                        },
                    },
                },
            }
        )

    return {"cells": [*nodes, *edges]}


def _legacy_to_logicflow(workflow):
    nodes = []
    edges = []

    for node in workflow.nodes.all():
        node_type = (node.type or "rect").lower()
        lf_type = "rect"
        if "circle" in node_type:
            lf_type = "ellipse"
        elif "diamond" in node_type or "polygon" in node_type:
            lf_type = "diamond"

        nodes.append(
            {
                "id": node.node_id,
                "type": lf_type,
                "x": node.position_x,
                "y": node.position_y,
                "text": node.label or "Node",
            }
        )

    for edge in workflow.edges.all():
        edges.append(
            {
                "id": edge.edge_id,
                "type": "polyline",
                "sourceNodeId": edge.source,
                "targetNodeId": edge.target,
            }
        )

    return {"nodes": nodes, "edges": edges}


def _get_x6_graph_data(workflow):
    parsed = _parse_graph_payload(workflow.data_x6, None)
    if parsed:
        return parsed
    return _legacy_to_x6(workflow)


def _get_logicflow_graph_data(workflow):
    parsed = _parse_graph_payload(workflow.data_lf, None)
    if parsed:
        return parsed
    return _legacy_to_logicflow(workflow)


def _calculate_next_version(last_version, is_major_update=False):
    if not last_version:
        return "1.0" if is_major_update else "0.1"

    try:
        version_number = Decimal(str(last_version))
    except (InvalidOperation, TypeError, ValueError):
        version_number = Decimal("0.0")

    major_part = int(version_number)
    minor_part = int((version_number - major_part) * 10)

    if is_major_update:
        return f"{major_part + 1}.0"

    return f"{major_part}.{minor_part + 1}"


def _create_workflow_history(workflow, snapshot, request, default_description):
    description = (request.data.get("history_description") or "").strip() or default_description
    raw_major_flag = request.data.get("is_major_update", False)
    is_major_update = str(raw_major_flag).lower() in {"1", "true", "yes", "on"}
    last_history = workflow.history.order_by("-created_at", "-id").first()
    version = _calculate_next_version(
        last_history.version if last_history else None,
        is_major_update=is_major_update,
    )

    WorkflowHistory.objects.create(
        workflow=workflow,
        version=version,
        snapshot=snapshot,
        description=description,
        created_by=request.user if request.user.is_authenticated else None,
    )
    return version


class WorkflowViewSet(viewsets.ModelViewSet):
    queryset = Workflow.objects.all().order_by("-updated_at", "-created_at")
    serializer_class = WorkflowSerializer
    parser_classes = [JSONParser, FormParser, MultiPartParser]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user if self.request.user.is_authenticated else None)

    @action(detail=True, methods=["post"])
    def save_diagram(self, request, pk=None):
        workflow = self.get_object()
        nodes_data = request.data.get("nodes", [])
        edges_data = request.data.get("edges", [])

        existing_nodes = {n.node_id: n for n in workflow.nodes.all()}

        new_node_ids = set()
        for node_data in nodes_data:
            node_id = node_data["id"]
            new_node_ids.add(node_id)

            position = node_data.get("position", {"x": 0, "y": 0})
            label = node_data.get("data", {}).get("label", "")

            if node_id in existing_nodes:
                node = existing_nodes[node_id]
                node.position_x = position["x"]
                node.position_y = position["y"]
                node.label = label
                node.type = node_data.get("type", "default")
                node.save()
            else:
                Node.objects.create(
                    workflow=workflow,
                    node_id=node_id,
                    type=node_data.get("type", "default"),
                    position_x=position["x"],
                    position_y=position["y"],
                    label=label,
                )

        for node_id, node in existing_nodes.items():
            if node_id not in new_node_ids:
                node.delete()

        workflow.edges.all().delete()
        for edge_data in edges_data:
            Edge.objects.create(
                workflow=workflow,
                edge_id=edge_data["id"],
                source=edge_data["source"],
                target=edge_data["target"],
            )

        version = _create_workflow_history(
            workflow=workflow,
            snapshot=request.data,
            request=request,
            default_description="변경 사항 저장",
        )

        return Response({"status": "diagram saved", "version": version})

    @action(detail=True, methods=["post"])
    def restore_version(self, request, pk=None):
        workflow = self.get_object()
        version_id = request.data.get("version_id")
        try:
            history = workflow.history.get(id=version_id)
            return Response({"status": "restored", "version": history.version})
        except WorkflowHistory.DoesNotExist:
            return Response({"error": "Version not found"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=True, methods=["post"])
    def save_logicflow(self, request, pk=None):
        workflow = self.get_object()
        snapshot = _parse_graph_payload(request.data.get("graphData"), {})
        workflow.data_lf = snapshot
        workflow.save()

        version = _create_workflow_history(
            workflow=workflow,
            snapshot=snapshot,
            request=request,
            default_description="LogicFlow 변경 사항 저장",
        )
        return Response({"status": "logicflow saved", "version": version})

    @action(detail=True, methods=["post"])
    def save_x6(self, request, pk=None):
        workflow = self.get_object()
        snapshot = _parse_graph_payload(request.data.get("graphData"), {"cells": []})
        workflow.data_x6 = snapshot
        workflow.save()

        version = _create_workflow_history(
            workflow=workflow,
            snapshot=snapshot,
            request=request,
            default_description="X6 변경 사항 저장",
        )
        return Response({"status": "x6 saved", "version": version})

    @action(detail=True, methods=["get", "post"])
    def lf_node_detail(self, request, pk=None):
        workflow = self.get_object()
        node_id = request.query_params.get("node_id") or request.data.get("node_id")
        if not node_id:
            return Response({"error": "node_id is required"}, status=400)

        detail, _ = LogicFlowNodeDetail.objects.get_or_create(workflow=workflow, node_id=node_id)

        if request.method == "GET":
            serializer = LogicFlowNodeDetailSerializer(detail)
            return Response(serializer.data)

        detail.content = request.data.get("content", detail.content)
        detail.save()

        files = request.FILES.getlist("files")
        for uploaded_file in files:
            LogicFlowNodeFile.objects.create(
                node_detail=detail,
                file=uploaded_file,
                filename=uploaded_file.name,
            )

        serializer = LogicFlowNodeDetailSerializer(detail)
        return Response(serializer.data)


class NodeViewSet(viewsets.ModelViewSet):
    queryset = Node.objects.all()
    serializer_class = NodeSerializer

    @action(detail=True, methods=["get", "post"])
    def detail_info(self, request, pk=None):
        node = self.get_object()
        if request.method == "GET":
            detail, _ = NodeDetail.objects.get_or_create(node=node)
            serializer = NodeDetailSerializer(detail)
            return Response(serializer.data)

        detail, _ = NodeDetail.objects.get_or_create(node=node)
        detail.content = request.data.get("content", detail.content)
        detail.save()
        serializer = NodeDetailSerializer(detail)
        return Response(serializer.data)


class WorkflowHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WorkflowHistory.objects.all()
    serializer_class = WorkflowHistorySerializer

    def get_queryset(self):
        queryset = super().get_queryset().select_related("workflow", "created_by")
        workflow_id = self.request.query_params.get("workflow")
        if workflow_id:
            queryset = queryset.filter(workflow_id=workflow_id)
        return queryset


def workflow_list(request):
    workflows = Workflow.objects.all().order_by("-updated_at", "-created_at")
    return render(request, "vbpm/workflow_list.html", {"workflows": workflows})


def workflow_editor(request, pk):
    workflow = get_object_or_404(Workflow, pk=pk)
    return render(request, "vbpm/editor.html", {"workflow": workflow})


def workflow_editor_v2(request, pk):
    workflow = get_object_or_404(Workflow, pk=pk)
    return render(
        request,
        "vbpm/logicflow_editor.html",
        {
            "workflow": workflow,
            "initial_lf_data": _get_logicflow_graph_data(workflow),
        },
    )


def workflow_editor_v3(request, pk):
    workflow = get_object_or_404(Workflow, pk=pk)
    return render(
        request,
        "vbpm/x6_editor.html",
        {
            "workflow": workflow,
            "initial_x6_data": _get_x6_graph_data(workflow),
        },
    )


def workflow_viewer_v3(request, pk):
    workflow = get_object_or_404(Workflow, pk=pk)
    return render(
        request,
        "vbpm/x6_viewer.html",
        {
            "workflow": workflow,
            "initial_x6_data": _get_x6_graph_data(workflow),
        },
    )
