from django.contrib.auth import get_user_model
from django.db import models

User = get_user_model()


class Workflow(models.Model):
    name = models.CharField(max_length=255, verbose_name="프로세스명")
    description = models.TextField(blank=True, verbose_name="설명")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="workflows")

    library_type = models.CharField(
        max_length=20,
        default="reactflow",
        choices=[("reactflow", "React Flow"), ("logicflow", "LogicFlow"), ("x6", "AntV X6")],
    )
    data_lf = models.JSONField(null=True, blank=True, verbose_name="LogicFlow 데이터")
    data_x6 = models.JSONField(null=True, blank=True, verbose_name="X6 데이터")

    class Meta:
        verbose_name = "워크플로우"
        verbose_name_plural = "워크플로우 목록"

    def __str__(self):
        return self.name

    @property
    def current_version(self):
        latest_history = self.history.order_by("-created_at", "-id").first()
        return latest_history.version if latest_history else "0.0"


class Node(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name="nodes")
    node_id = models.CharField(max_length=100)
    type = models.CharField(max_length=50, default="default")
    position_x = models.FloatField()
    position_y = models.FloatField()
    label = models.CharField(max_length=255)

    class Meta:
        unique_together = ("workflow", "node_id")
        verbose_name = "노드"
        verbose_name_plural = "노드 목록"

    def __str__(self):
        return f"{self.workflow.name} - {self.label}({self.node_id})"


class Edge(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name="edges")
    edge_id = models.CharField(max_length=100)
    source = models.CharField(max_length=100)
    target = models.CharField(max_length=100)

    class Meta:
        unique_together = ("workflow", "edge_id")
        verbose_name = "엣지"
        verbose_name_plural = "엣지 목록"


class NodeDetail(models.Model):
    node = models.OneToOneField(Node, on_delete=models.CASCADE, related_name="detail")
    content = models.TextField(blank=True, verbose_name="상세 내용")

    class Meta:
        verbose_name = "노드 상세"
        verbose_name_plural = "노드 상세 목록"


class NodeFile(models.Model):
    node_detail = models.ForeignKey(NodeDetail, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="vbpm/attachments/", verbose_name="첨부 파일")
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "노드 첨부파일"
        verbose_name_plural = "노드 첨부파일 목록"


class WorkflowHistory(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name="history")
    version = models.CharField(max_length=10, verbose_name="버전")
    snapshot = models.JSONField(verbose_name="스냅샷")
    description = models.TextField(blank=True, verbose_name="변경 설명")
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        verbose_name = "워크플로우 이력"
        verbose_name_plural = "워크플로우 이력 목록"


class LogicFlowNodeDetail(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name="lf_node_details")
    node_id = models.CharField(max_length=100)
    content = models.TextField(blank=True, verbose_name="상세 내용")

    class Meta:
        unique_together = ("workflow", "node_id")


class LogicFlowNodeFile(models.Model):
    node_detail = models.ForeignKey(LogicFlowNodeDetail, on_delete=models.CASCADE, related_name="files")
    file = models.FileField(upload_to="vbpm/lf_attachments/", verbose_name="첨부 파일")
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(auto_now_add=True)
