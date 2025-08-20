from django.contrib import admin
from .models import (
    SearchedJob, JobHistory, Experience, UserFeedback,
    CareerCategory, PersonalInsight, JobInsightMatch, GeneratedNarrative
)


@admin.register(SearchedJob)
class SearchedJobAdmin(admin.ModelAdmin):
    list_display = ['job_title', 'company_name', 'user', 'created_at']
    list_filter = ['created_at', 'company_name']
    search_fields = ['job_title', 'company_name', 'user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(JobHistory)
class JobHistoryAdmin(admin.ModelAdmin):
    list_display = ['job_title', 'company', 'user', 'start_date', 'end_date', 'is_current']
    list_filter = ['is_current', 'start_date']
    search_fields = ['job_title', 'company', 'user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ['title', 'job_history', 'created_at']
    list_filter = ['created_at', 'job_history__company']
    search_fields = ['title', 'description', 'job_history__job_title']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = ['title', 'feedback_type', 'priority', 'user', 'is_implemented', 'created_at']
    list_filter = ['feedback_type', 'priority', 'is_implemented', 'created_at']
    search_fields = ['title', 'content', 'user__username']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(CareerCategory)
class CareerCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(PersonalInsight)
class PersonalInsightAdmin(admin.ModelAdmin):
    list_display = ['user', 'category', 'insight_type', 'is_active', 'created_at']
    list_filter = ['category', 'insight_type', 'is_active', 'created_at']
    search_fields = ['user__username', 'content', 'question']
    readonly_fields = ['created_at', 'updated_at', 'embedding']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'category')


@admin.register(JobInsightMatch)
class JobInsightMatchAdmin(admin.ModelAdmin):
    list_display = ['searched_job', 'matched_insight', 'final_score', 'is_used_in_narrative', 'created_at']
    list_filter = ['is_used_in_narrative', 'created_at']
    search_fields = ['searched_job__job_title', 'matched_insight__user__username']
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'searched_job', 'matched_insight', 'matched_insight__user'
        )


@admin.register(GeneratedNarrative)
class GeneratedNarrativeAdmin(admin.ModelAdmin):
    list_display = ['searched_job', 'narrative_type', 'user', 'is_approved', 'created_at']
    list_filter = ['narrative_type', 'is_approved', 'ai_model_used', 'created_at']
    search_fields = ['searched_job__job_title', 'user__username', 'content']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'searched_job')
