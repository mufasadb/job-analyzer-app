from django.urls import path
from . import views
from . import insights_views

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
    
    # Career Insights & Vector Search
    path('categories/', insights_views.CareerCategoryListCreateView.as_view(), name='career_categories'),
    path('categories/<int:pk>/', insights_views.CareerCategoryRetrieveUpdateDeleteView.as_view(), name='career_category_detail'),
    path('categories/<int:category_id>/questions/', insights_views.insight_questions, name='insight_questions'),
    
    # Personal Insights
    path('insights/', insights_views.PersonalInsightListCreateView.as_view(), name='personal_insights'),
    path('insights/<int:pk>/', insights_views.PersonalInsightRetrieveUpdateDeleteView.as_view(), name='personal_insight_detail'),
    
    # Job Insight Matching
    path('<int:job_id>/match-insights/', insights_views.match_insights_to_job, name='match_insights_to_job'),
    path('<int:job_id>/insights/', insights_views.job_with_insights, name='job_with_insights'),
    
    # Narrative Generation
    path('<int:job_id>/generate-narrative/', insights_views.generate_narrative, name='generate_narrative'),
    path('narratives/', insights_views.GeneratedNarrativeListView.as_view(), name='generated_narratives'),
    path('narratives/<int:pk>/', insights_views.GeneratedNarrativeRetrieveUpdateDeleteView.as_view(), name='generated_narrative_detail'),
]