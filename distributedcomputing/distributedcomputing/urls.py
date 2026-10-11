from django.contrib import admin
from django.urls import path
from rollback_recovery import views


urlpatterns = [
    path('admin/', admin.site.urls),

    # Dashboard
    path("", views.dashboard, name="dashboard"),

    # Create process
    path("process/create/", views.create_process, name="create_process"),

    # Send message
    path("message/send/", views.send_message, name="send_message" ),

    # Create checkpoint
    path("process/<int:process_id>/checkpoint/", views.create_checkpoint, name="create_checkpoint" ),

    # Fail process
    path( "process/<int:process_id>/fail/", views.fail_process, name="fail_process" ),

    # Rollback process
    path( "process/<int:process_id>/rollback/", views.rollback_process, name="rollback_process" ),

    # Reset process
    path( "process/<int:process_id>/reset/", views.reset_process, name="reset_process" ),
]