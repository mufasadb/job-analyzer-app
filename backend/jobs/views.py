from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from .models import SearchedJob, JobHistory, Experience, UserFeedback
from .serializers import (
    SearchedJobSerializer, JobAnalysisRequestSerializer,
    JobHistorySerializer, JobHistoryListSerializer, JobHistoryCreateSerializer,
    ExperienceSerializer, ExperienceCreateSerializer,
    UserFeedbackSerializer, UserFeedbackCreateSerializer, UserFeedbackUpdateSerializer
)
from .agentic_utility import AgenticUtility
import json
import re


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def analyze_job(request):
    serializer = JobAnalysisRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    linkedin_url = serializer.validated_data['linkedin_url']
    use_structured_extraction = request.data.get('use_structured_extraction', True)
    
    # Initialize agentic utility
    agent = AgenticUtility()
    
    try:
        if use_structured_extraction:
            # Use structured job extraction
            result = agent.extract_job_details(linkedin_url)
            
            if not result['success']:
                return Response({
                    'error': 'Failed to extract job details',
                    'details': result.get('error', 'Unknown error')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            job_data = result['job_data']
            job_title = job_data.get('job_title', 'Job Title Not Found')
            company_name = job_data.get('company_information', {}).get('company_name', 'Company Not Found')
            
            # Save the structured analysis to database
            searched_job = SearchedJob.objects.create(
                user=request.user,
                linkedin_url=linkedin_url,
                job_title=job_title,
                company_name=company_name,
                recommendations={
                    'structured_data': job_data,
                    'raw_content': result.get('raw_content', {}),
                    'usage': result.get('usage', {})
                },
                analysis_result=json.dumps(job_data, indent=2)
            )
            
            # Return structured response
            job_serializer = SearchedJobSerializer(searched_job)
            return Response({
                'job': job_serializer.data,
                'structured_data': job_data,
                'raw_content': result.get('raw_content', {}),
                'message': 'Structured job extraction completed successfully'
            }, status=status.HTTP_201_CREATED)
            
        else:
            # Use legacy analysis approach
            config = {
                'systemMessage': "You are an expert career advisor and resume consultant. Analyze job postings and provide specific, actionable resume recommendations.",
                'prompt': "Analyze this job posting and provide specific recommendations for what should be included in a resume to match this role. Focus on required skills, experience, keywords, and qualifications mentioned in the posting.",
                'goal': f"Tell me what things I should put in my resume for this job {linkedin_url}",
                'enableSearch': True,
                'input': {
                    'searchQuery': linkedin_url,
                    'jobUrl': linkedin_url,
                    'requestType': 'resume_optimization'
                }
            }
            
            # Execute the analysis
            result = agent.execute_task(config)
            
            if not result['success']:
                return Response({
                    'error': 'Failed to analyze job posting',
                    'details': result.get('error', 'Unknown error')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Extract job title and company from the analysis or URL
            job_title = extract_job_title_from_analysis(result['result'])
            company_name = extract_company_from_analysis(result['result'])
            
            # Save the analysis to database
            searched_job = SearchedJob.objects.create(
                user=request.user,
                linkedin_url=linkedin_url,
                job_title=job_title,
                company_name=company_name,
                recommendations={
                    'analysis': result['result'],
                    'searchResults': result.get('searchResults', []),
                    'usage': result.get('usage', {})
                },
                analysis_result=result['result']
            )
            
            # Return the response
            job_serializer = SearchedJobSerializer(searched_job)
            return Response({
                'job': job_serializer.data,
                'analysis': result['result'],
                'recommendations': extract_recommendations_list(result['result']),
                'message': 'Job analysis completed successfully'
            }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': 'An error occurred during analysis',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_history(request):
    jobs = SearchedJob.objects.filter(user=request.user)
    serializer = SearchedJobSerializer(jobs, many=True)
    return Response({
        'jobs': serializer.data,
        'count': jobs.count()
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_detail(request, job_id):
    try:
        job = SearchedJob.objects.get(id=job_id, user=request.user)
        serializer = SearchedJobSerializer(job)
        return Response({
            'job': serializer.data,
            'recommendations': extract_recommendations_list(job.analysis_result)
        })
    except SearchedJob.DoesNotExist:
        return Response({'error': 'Job not found'}, status=status.HTTP_404_NOT_FOUND)


def extract_job_title_from_analysis(analysis_text):
    """Extract job title from analysis text using regex patterns"""
    patterns = [
        r'(?:Job title|Position|Role):\s*([^\n\r]+)',
        r'(?:hiring|for)\s+([A-Z][^,\n\r]+?)(?:\s+in|\s+at|\s+\|)',
        r'(?:Chief Information Officer|CIO|Director|Manager|Engineer|Developer|Analyst)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, analysis_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()[:200]
    
    return "Job Title Not Found"


def extract_company_from_analysis(analysis_text):
    """Extract company name from analysis text using regex patterns"""
    patterns = [
        r'(?:Company|Employer):\s*([^\n\r]+)',
        r'(?:at|with)\s+([A-Z][A-Za-z\s&]+?)(?:\s+\(|$)',
        r'(?:CS Energy|OnTalent)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, analysis_text, re.IGNORECASE)
        if match:
            return match.group(1).strip()[:200]
    
    return "Company Not Found"


def extract_recommendations_list(analysis_text):
    """Extract key recommendations as a list from the analysis"""
    lines = analysis_text.split('\n')
    recommendations = []
    
    for line in lines:
        line = line.strip()
        # Look for bullet points, numbered lists, or key phrases
        if (line.startswith('- ') or line.startswith('• ') or 
            re.match(r'^\d+\.', line) or 
            'should include' in line.lower() or 
            'add to resume' in line.lower()):
            recommendations.append(line)
    
    return recommendations[:10]  # Limit to top 10 recommendations


# JobHistory CRUD Views
class JobHistoryListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['job_title', 'company']
    filterset_fields = ['is_current']
    ordering_fields = ['start_date', 'created_at']
    ordering = ['-start_date']

    def get_queryset(self):
        return JobHistory.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return JobHistoryCreateSerializer
        return JobHistoryListSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class JobHistoryRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = JobHistorySerializer

    def get_queryset(self):
        return JobHistory.objects.filter(user=self.request.user)


class JobHistoryExperiencesListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'impact', 'skills_used']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        job_id = self.kwargs.get('job_id')
        job_history = get_object_or_404(JobHistory, id=job_id, user=self.request.user)
        return Experience.objects.filter(job_history=job_history)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ExperienceCreateSerializer
        return ExperienceSerializer

    def perform_create(self, serializer):
        job_id = self.kwargs.get('job_id')
        job_history = get_object_or_404(JobHistory, id=job_id, user=self.request.user)
        serializer.save(job_history=job_history)


# Experience CRUD Views
class ExperienceListView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExperienceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'impact', 'skills_used']
    filterset_fields = ['job_history']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return Experience.objects.filter(job_history__user=self.request.user)


class ExperienceRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ExperienceSerializer

    def get_queryset(self):
        return Experience.objects.filter(job_history__user=self.request.user)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enhance_experience_with_ai(request):
    """Enhance experience description using AI"""
    try:
        # Get request data
        job_title = request.data.get('job_title', 'N/A')
        company = request.data.get('company', 'N/A')
        job_description = request.data.get('job_description', 'N/A')
        experience_description = request.data.get('experience_description', '')
        
        if not experience_description.strip():
            return Response({
                'error': 'Experience description is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Initialize agentic utility
        agent = AgenticUtility()
        
        # Construct the enhancement prompt
        prompt = f"""You are a professional resume writer. Rewrite the experience description below to be more professional and resume-appropriate. 

CRITICAL: Return ONLY the enhanced description text. No explanations, no markdown, no bullet points, no titles, no additional content - just the improved description text.

Job Title: {job_title}
Company: {company}
Job Description: {job_description}

Original Experience: {experience_description}

Enhanced description:"""

        # Execute AI enhancement
        config = {
            'systemMessage': 'You are a professional resume writer. Return ONLY the enhanced description text with no explanations, formatting, or additional content. Be concise and professional.',
            'prompt': prompt,
            'goal': 'Return only the enhanced experience description text',
            'input': {
                'job_title': job_title,
                'company': company,
                'job_description': job_description,
                'experience_description': experience_description
            },
            'enableSearch': False,
            'model': 'openai/gpt-5-chat'
        }
        
        result = agent.execute_task(config)
        
        if not result['success']:
            return Response({
                'error': 'AI enhancement failed',
                'details': result.get('error', 'Unknown error')
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        enhanced_description = result['result'].strip()
        
        return Response({
            'enhanced_description': enhanced_description,
            'original_description': experience_description
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Failed to enhance experience with AI',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# UserFeedback CRUD Views
class UserFeedbackListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'content', 'tags']
    filterset_fields = ['feedback_type', 'priority', 'is_implemented']
    ordering_fields = ['created_at', 'priority']
    ordering = ['-created_at']

    def get_queryset(self):
        return UserFeedback.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserFeedbackCreateSerializer
        return UserFeedbackSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserFeedbackRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserFeedback.objects.filter(user=self.request.user)
    
    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UserFeedbackUpdateSerializer
        return UserFeedbackSerializer


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def feedback_stats(request):
    """Get user feedback statistics"""
    user_feedback = UserFeedback.objects.filter(user=request.user)
    
    stats = {
        'total_feedback': user_feedback.count(),
        'by_type': {},
        'by_priority': {},
        'implemented_count': user_feedback.filter(is_implemented=True).count(),
        'pending_count': user_feedback.filter(is_implemented=False).count()
    }
    
    # Count by feedback type
    for choice in UserFeedback.FEEDBACK_TYPES:
        feedback_type = choice[0]
        count = user_feedback.filter(feedback_type=feedback_type).count()
        stats['by_type'][feedback_type] = count
    
    # Count by priority
    for choice in UserFeedback.PRIORITY_LEVELS:
        priority = choice[0]
        count = user_feedback.filter(priority=priority).count()
        stats['by_priority'][priority] = count
    
    return Response(stats)
