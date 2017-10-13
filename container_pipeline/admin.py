from django.contrib import admin

from container_pipeline.models import Project, Build, BuildPhase


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'created', 'last_updated')
    search_fields = ('name',)


@admin.register(Build)
class BuildAdmin(admin.ModelAdmin):
    list_display = ('uuid', 'project', 'status',
                    'notification_status', 'created', 'start_time',
                    'end_time', 'last_updated')
    search_fields = ('project', 'uuid')


@admin.register(BuildPhase)
class BuildPhase(admin.ModelAdmin):
    list_display = ('build', 'phase', 'status', 'created', 'start_time',
                    'end_time', 'last_updated')
    search_fields = ('build',)
