from django.urls import path
from . import views

urlpatterns = [
    # Job Analysis (existing)
    path('analyze/', views.analyze_job, name='analyze_job'),
    path('history/', views.job_history, name='job_history'),
    path('<int:job_id>/', views.job_detail, name='job_detail'),
    
    # Job History CRUD
    path('job-history/', views.JobHistoryListCreateView.as_view(), name='job_history_list_create'),
    path('job-history/<int:pk>/', views.JobHistoryRetrieveUpdateDeleteView.as_view(), name='job_history_detail'),
    
    # Nested Experience URLs under specific job
    path('job-history/<int:job_id>/experiences/', views.JobHistoryExperiencesListCreateView.as_view(), name='job_history_experiences'),
    
    # Global Experience CRUD
    path('experiences/', views.ExperienceListView.as_view(), name='experience_list'),
    path('experiences/<int:pk>/', views.ExperienceRetrieveUpdateDeleteView.as_view(), name='experience_detail'),
    
    # AI Enhancement
    path('experiences/enhance/', views.enhance_experience_with_ai, name='enhance_experience'),
    
    # User Feedback
    path('feedback/', views.UserFeedbackListCreateView.as_view(), name='user_feedback_list_create'),
    path('feedback/<int:pk>/', views.UserFeedbackRetrieveUpdateDeleteView.as_view(), name='user_feedback_detail'),
    path('feedback/stats/', views.feedback_stats, name='feedback_stats'),
]