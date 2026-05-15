from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    WorkflowViewSet, 
    NodeViewSet, 
    WorkflowHistoryViewSet, 
    workflow_list, 
    workflow_editor, 
    workflow_editor_v2,
    workflow_editor_v3,
    workflow_viewer_v3
)

router = DefaultRouter()
router.register(r'workflows', WorkflowViewSet)
router.register(r'nodes', NodeViewSet)
router.register(r'history', WorkflowHistoryViewSet)

urlpatterns = [
    path('', workflow_list, name='workflow_list'),
    path('<int:pk>/editor/', workflow_editor, name='workflow_editor'),
    path('<int:pk>/editor_v2/', workflow_editor_v2, name='workflow_editor_v2'),
    path('<int:pk>/editor_v3/', workflow_editor_v3, name='workflow_editor_v3'),
    path('<int:pk>/viewer_v3/', workflow_viewer_v3, name='workflow_viewer_v3'),
    path('api/', include(router.urls)),
]
