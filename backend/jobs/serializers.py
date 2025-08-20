from rest_framework import serializers
from .models import (
    SearchedJob, JobHistory, Experience, UserFeedback,
    CareerCategory, PersonalInsight, JobInsightMatch, GeneratedNarrative
)


class SearchedJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchedJob
        fields = ['id', 'linkedin_url', 'job_title', 'company_name', 'recommendations', 'analysis_result', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class JobAnalysisRequestSerializer(serializers.Serializer):
    linkedin_url = serializers.URLField(max_length=500)
    
    def validate_linkedin_url(self, value):
        if 'linkedin.com/jobs' not in value:
            raise serializers.ValidationError("Please provide a valid LinkedIn job URL")
        return value


class ExperienceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = ['id', 'job_history', 'title', 'description', 'impact', 'skills_used', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ExperienceCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Experience
        fields = ['title', 'description', 'impact', 'skills_used']

    def create(self, validated_data):
        # job_history will be set in the view based on URL parameter
        return Experience.objects.create(**validated_data)


class JobHistorySerializer(serializers.ModelSerializer):
    experiences = ExperienceSerializer(many=True, read_only=True)
    experience_count = serializers.SerializerMethodField()

    class Meta:
        model = JobHistory
        fields = ['id', 'job_title', 'company', 'start_date', 'end_date', 'is_current', 
                 'alternative_names', 'experiences', 'experience_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_experience_count(self, obj):
        return obj.experiences.count()

    def validate(self, data):
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] <= data['start_date']:
                raise serializers.ValidationError("End date must be after start date")
        
        if data.get('end_date') and data.get('is_current'):
            raise serializers.ValidationError("Current job cannot have an end date")
        
        return data


class JobHistoryListSerializer(serializers.ModelSerializer):
    experience_count = serializers.SerializerMethodField()

    class Meta:
        model = JobHistory
        fields = ['id', 'job_title', 'company', 'start_date', 'end_date', 'is_current', 
                 'alternative_names', 'experience_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_experience_count(self, obj):
        return obj.experiences.count()


class JobHistoryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobHistory
        fields = ['job_title', 'company', 'start_date', 'end_date', 'is_current', 'alternative_names']

    def validate(self, data):
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] <= data['start_date']:
                raise serializers.ValidationError("End date must be after start date")
        
        if data.get('end_date') and data.get('is_current'):
            raise serializers.ValidationError("Current job cannot have an end date")
        
        return data


class UserFeedbackSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = UserFeedback
        fields = ['id', 'user', 'feedback_type', 'title', 'content', 'priority', 
                 'is_implemented', 'implementation_notes', 'tags', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class UserFeedbackCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFeedback
        fields = ['feedback_type', 'title', 'content', 'priority', 'tags']
        
    def validate_title(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters long")
        return value.strip()
    
    def validate_content(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Content must be at least 10 characters long")
        return value.strip()


class UserFeedbackUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFeedback
        fields = ['feedback_type', 'title', 'content', 'priority', 'is_implemented', 
                 'implementation_notes', 'tags']
        
    def validate_title(self, value):
        if len(value.strip()) < 5:
            raise serializers.ValidationError("Title must be at least 5 characters long")
        return value.strip()
    
    def validate_content(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Content must be at least 10 characters long")
        return value.strip()


# Career Insights Serializers

class CareerCategorySerializer(serializers.ModelSerializer):
    insight_count = serializers.SerializerMethodField()

    class Meta:
        model = CareerCategory
        fields = ['id', 'name', 'keywords', 'description', 'is_active', 
                 'insight_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_insight_count(self, obj):
        return obj.insights.filter(is_active=True).count()


class PersonalInsightSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    insight_type_display = serializers.CharField(source='get_insight_type_display', read_only=True)
    
    class Meta:
        model = PersonalInsight
        fields = ['id', 'category', 'category_name', 'insight_type', 'insight_type_display',
                 'question', 'content', 'tags', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class PersonalInsightCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonalInsight
        fields = ['category', 'insight_type', 'question', 'content', 'tags']
        
    def validate_content(self, value):
        if len(value.strip()) < 20:
            raise serializers.ValidationError("Content must be at least 20 characters long")
        return value.strip()


class JobInsightMatchSerializer(serializers.ModelSerializer):
    insight_content = serializers.CharField(source='matched_insight.content', read_only=True)
    insight_type = serializers.CharField(source='matched_insight.insight_type', read_only=True)
    insight_type_display = serializers.CharField(source='matched_insight.get_insight_type_display', read_only=True)
    category_name = serializers.CharField(source='matched_insight.category.name', read_only=True)

    class Meta:
        model = JobInsightMatch
        fields = ['id', 'matched_insight', 'insight_content', 'insight_type', 'insight_type_display',
                 'category_name', 'relevance_score', 'category_match_bonus', 'final_score', 
                 'is_used_in_narrative', 'created_at']
        read_only_fields = ['id', 'created_at']


class GeneratedNarrativeSerializer(serializers.ModelSerializer):
    narrative_type_display = serializers.CharField(source='get_narrative_type_display', read_only=True)
    insights_used_count = serializers.SerializerMethodField()
    job_title = serializers.CharField(source='searched_job.job_title', read_only=True)
    company_name = serializers.CharField(source='searched_job.company_name', read_only=True)

    class Meta:
        model = GeneratedNarrative
        fields = ['id', 'searched_job', 'job_title', 'company_name', 'narrative_type', 
                 'narrative_type_display', 'content', 'insights_used_count', 'ai_model_used',
                 'user_feedback', 'is_approved', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_insights_used_count(self, obj):
        return obj.insights_used.count()


class GeneratedNarrativeCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeneratedNarrative
        fields = ['narrative_type']


# Enhanced SearchedJob serializer with insight matching
class SearchedJobWithInsightsSerializer(serializers.ModelSerializer):
    insight_matches = JobInsightMatchSerializer(many=True, read_only=True)
    generated_narratives = GeneratedNarrativeSerializer(many=True, read_only=True)
    
    class Meta:
        model = SearchedJob
        fields = ['id', 'linkedin_url', 'job_title', 'company_name', 'recommendations', 
                 'analysis_result', 'insight_matches', 'generated_narratives', 
                 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


# API Request/Response Serializers

class InsightMatchingRequestSerializer(serializers.Serializer):
    """Request serializer for matching insights to a job"""
    top_k = serializers.IntegerField(default=10, min_value=1, max_value=50)
    min_similarity = serializers.FloatField(default=0.3, min_value=0.0, max_value=1.0)
    categories = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="List of category IDs to filter by"
    )


class NarrativeGenerationRequestSerializer(serializers.Serializer):
    """Request serializer for generating narrative content"""
    narrative_type = serializers.ChoiceField(choices=GeneratedNarrative.NARRATIVE_TYPES)
    use_insight_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        help_text="Specific insight IDs to use (optional)"
    )
    custom_prompt = serializers.CharField(
        required=False,
        max_length=2000,
        help_text="Custom instructions for narrative generation"
    )