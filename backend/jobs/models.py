from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError


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
