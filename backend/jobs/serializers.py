from rest_framework import serializers
from .models import SearchedJob, JobHistory, Experience, UserFeedback


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