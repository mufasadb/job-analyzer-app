from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from pgvector.django import VectorField


class SearchedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='searched_jobs')
    linkedin_url = models.URLField(max_length=500)
    job_title = models.CharField(max_length=200, blank=True)
    company_name = models.CharField(max_length=200, blank=True)
    recommendations = models.JSONField(default=dict)
    analysis_result = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.job_title} at {self.company_name} - {self.user.username}"


class JobHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='job_history')
    job_title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)  # null for current job
    is_current = models.BooleanField(default=False)
    alternative_names = models.JSONField(default=list, blank=True)  # List of alternative job titles
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-start_date']
        verbose_name_plural = "Job Histories"

    def clean(self):
        if self.end_date and self.start_date and self.end_date <= self.start_date:
            raise ValidationError('End date must be after start date')
        
        if self.end_date and self.is_current:
            raise ValidationError('Current job cannot have an end date')

    def save(self, *args, **kwargs):
        # Auto-set is_current based on end_date
        if self.end_date:
            self.is_current = False
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.job_title} at {self.company} - {self.user.username}"


class Experience(models.Model):
    job_history = models.ForeignKey(JobHistory, on_delete=models.CASCADE, related_name='experiences')
    title = models.CharField(max_length=300)  # Brief title of the experience/achievement
    description = models.TextField()  # Detailed description
    impact = models.TextField(blank=True)  # Quantifiable impact/results
    skills_used = models.JSONField(default=list)  # List of skills/technologies
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.job_history.job_title}"


class UserFeedback(models.Model):
    FEEDBACK_TYPES = [
        ('resume', 'Resume'),
        ('cover_letter', 'Cover Letter'),
        ('general', 'General'),
    ]
    
    PRIORITY_LEVELS = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedback')
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPES, default='general')
    title = models.CharField(max_length=200)
    content = models.TextField()
    priority = models.CharField(max_length=10, choices=PRIORITY_LEVELS, default='medium')
    is_implemented = models.BooleanField(default=False)
    implementation_notes = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)  # For categorizing feedback
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = "User Feedback"

    def __str__(self):
        return f"{self.title} - {self.user.username} ({self.feedback_type})"


class CareerCategory(models.Model):
    """Categories for different types of roles/career paths"""
    name = models.CharField(max_length=100, unique=True)  # "CTO", "Head of IT", "Technical Leadership"
    keywords = models.JSONField(default=list, blank=True)  # Alternative job titles that match
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Career Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class PersonalInsight(models.Model):
    """User's personal insights and motivations for different career contexts"""
    INSIGHT_TYPES = [
        ('company_motivation', 'Why This Company'),
        ('career_motivation', 'Career Motivation'), 
        ('leadership_style', 'Leadership Approach'),
        ('work_values', 'Professional Values'),
        ('unique_value', 'Unique Value Proposition'),
        ('industry_knowledge', 'Industry Insights'),
        ('problem_solving', 'Problem Solving Approach'),
        ('team_building', 'Team Building Philosophy'),
        ('change_management', 'Change Management Style'),
        ('technical_vision', 'Technical Vision'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='personal_insights')
    category = models.ForeignKey(CareerCategory, on_delete=models.CASCADE, related_name='insights')
    insight_type = models.CharField(max_length=50, choices=INSIGHT_TYPES)
    question = models.TextField()  # The question that was answered
    content = models.TextField()  # User's response
    embedding = VectorField(dimensions=1536, null=True, blank=True)  # OpenAI embedding
    tags = models.JSONField(default=list, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'category', 'insight_type']  # One insight per type per category per user

    def __str__(self):
        return f"{self.user.username} - {self.category.name} - {self.get_insight_type_display()}"


class JobInsightMatch(models.Model):
    """Tracks which insights match well with which jobs"""
    searched_job = models.ForeignKey(SearchedJob, on_delete=models.CASCADE, related_name='insight_matches')
    matched_insight = models.ForeignKey(PersonalInsight, on_delete=models.CASCADE, related_name='job_matches')
    relevance_score = models.FloatField()  # Cosine similarity score (0-1)
    category_match_bonus = models.FloatField(default=0.0)  # Additional bonus for category alignment
    final_score = models.FloatField()  # Combined score for ranking
    is_used_in_narrative = models.BooleanField(default=False)  # Whether this insight was used in generated content
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-final_score']
        unique_together = ['searched_job', 'matched_insight']

    def __str__(self):
        return f"{self.searched_job.job_title} <- {self.matched_insight.insight_type} (Score: {self.final_score:.3f})"


class GeneratedNarrative(models.Model):
    """AI-generated narrative content for job applications"""
    NARRATIVE_TYPES = [
        ('cover_letter', 'Cover Letter'),
        ('summary', 'Professional Summary'),
        ('motivation', 'Motivation Statement'),
        ('value_proposition', 'Value Proposition'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='generated_narratives')
    searched_job = models.ForeignKey(SearchedJob, on_delete=models.CASCADE, related_name='generated_narratives')
    narrative_type = models.CharField(max_length=30, choices=NARRATIVE_TYPES)
    content = models.TextField()
    insights_used = models.ManyToManyField(PersonalInsight, through='NarrativeInsightUsage')
    generation_prompt = models.TextField(blank=True)  # Store the prompt used for generation
    ai_model_used = models.CharField(max_length=100, default='openai/gpt-5-chat')
    user_feedback = models.TextField(blank=True)  # User's notes/edits
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['searched_job', 'narrative_type']  # One narrative per type per job

    def __str__(self):
        return f"{self.searched_job.job_title} - {self.get_narrative_type_display()}"


class NarrativeInsightUsage(models.Model):
    """Through table tracking how insights were used in narratives"""
    narrative = models.ForeignKey(GeneratedNarrative, on_delete=models.CASCADE)
    insight = models.ForeignKey(PersonalInsight, on_delete=models.CASCADE)
    usage_weight = models.FloatField()  # How heavily this insight influenced the narrative (0-1)
    specific_content = models.TextField(blank=True)  # Specific text that came from this insight
    
    class Meta:
        unique_together = ['narrative', 'insight']

    def __str__(self):
        return f"{self.narrative} uses {self.insight.insight_type} (Weight: {self.usage_weight:.2f})"
