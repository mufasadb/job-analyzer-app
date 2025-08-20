"""
Views for career insights and vector similarity matching.
Handles career categories, personal insights, job matching, and narrative generation.
"""

from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from pgvector.django import CosineDistance
from django.db import transaction
import logging
import re

from .models import (
    SearchedJob, CareerCategory, PersonalInsight, 
    JobInsightMatch, GeneratedNarrative, NarrativeInsightUsage
)
from .serializers import (
    CareerCategorySerializer, PersonalInsightSerializer, PersonalInsightCreateSerializer,
    JobInsightMatchSerializer, GeneratedNarrativeSerializer, GeneratedNarrativeCreateSerializer,
    SearchedJobWithInsightsSerializer, InsightMatchingRequestSerializer,
    NarrativeGenerationRequestSerializer
)
from .embedding_service import get_embedding_service
from .agentic_utility import AgenticUtility

logger = logging.getLogger(__name__)


# Career Categories Views

class CareerCategoryListCreateView(generics.ListCreateAPIView):
    """List and create career categories"""
    permission_classes = [IsAuthenticated]
    serializer_class = CareerCategorySerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    filterset_fields = ['is_active']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']

    def get_queryset(self):
        return CareerCategory.objects.filter(is_active=True)


class CareerCategoryRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a career category"""
    permission_classes = [IsAuthenticated]
    serializer_class = CareerCategorySerializer
    
    def get_queryset(self):
        return CareerCategory.objects.all()


# Personal Insights Views

class PersonalInsightListCreateView(generics.ListCreateAPIView):
    """List and create personal insights"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['content', 'question']
    filterset_fields = ['category', 'insight_type', 'is_active']
    ordering_fields = ['created_at', 'insight_type']
    ordering = ['-created_at']

    def get_queryset(self):
        return PersonalInsight.objects.filter(user=self.request.user, is_active=True)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return PersonalInsightCreateSerializer
        return PersonalInsightSerializer

    def perform_create(self, serializer):
        """Create insight and generate embedding"""
        insight = serializer.save(user=self.request.user)
        
        # Generate embedding asynchronously (in a real app, use Celery)
        self._generate_embedding_for_insight(insight)

    def _generate_embedding_for_insight(self, insight):
        """Generate and save embedding for an insight"""
        try:
            embedding_service = get_embedding_service()
            
            # Combine question and content for better semantic representation
            combined_text = f"Question: {insight.question}\nAnswer: {insight.content}"
            embedding = embedding_service.generate_embedding(combined_text)
            
            if embedding:
                insight.embedding = embedding
                insight.save(update_fields=['embedding'])
                logger.info(f"Generated embedding for insight {insight.id}")
            else:
                logger.error(f"Failed to generate embedding for insight {insight.id}")
                
        except Exception as e:
            logger.error(f"Error generating embedding for insight {insight.id}: {str(e)}")


class PersonalInsightRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a personal insight"""
    permission_classes = [IsAuthenticated]
    serializer_class = PersonalInsightSerializer

    def get_queryset(self):
        return PersonalInsight.objects.filter(user=self.request.user)

    def perform_update(self, serializer):
        """Update insight and regenerate embedding if content changed"""
        old_content = self.get_object().content
        insight = serializer.save()
        
        # Regenerate embedding if content changed
        if insight.content != old_content:
            self._generate_embedding_for_insight(insight)

    def _generate_embedding_for_insight(self, insight):
        """Generate and save embedding for an insight"""
        try:
            embedding_service = get_embedding_service()
            combined_text = f"Question: {insight.question}\nAnswer: {insight.content}"
            embedding = embedding_service.generate_embedding(combined_text)
            
            if embedding:
                insight.embedding = embedding
                insight.save(update_fields=['embedding'])
                logger.info(f"Regenerated embedding for insight {insight.id}")
                
        except Exception as e:
            logger.error(f"Error regenerating embedding for insight {insight.id}: {str(e)}")


# Job Insight Matching Views

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def match_insights_to_job(request, job_id):
    """Find and rank insights that match a specific job"""
    try:
        # Get the job
        job = get_object_or_404(SearchedJob, id=job_id, user=request.user)
        
        # Validate request
        serializer = InsightMatchingRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        params = serializer.validated_data
        top_k = params.get('top_k', 10)
        min_similarity = params.get('min_similarity', 0.3)
        category_ids = params.get('categories', [])
        
        # Get job description for embedding
        job_description = job.analysis_result or job.recommendations.get('analysis', '')
        if not job_description:
            return Response({
                'error': 'No job description available for matching'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate embedding for job description
        embedding_service = get_embedding_service()
        job_embedding = embedding_service.generate_embedding(job_description)
        
        if not job_embedding:
            return Response({
                'error': 'Failed to generate job embedding'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Get user's insights
        insights_query = PersonalInsight.objects.filter(
            user=request.user,
            is_active=True,
            embedding__isnull=False  # Only insights with embeddings
        )
        
        if category_ids:
            insights_query = insights_query.filter(category_id__in=category_ids)
        
        insights = list(insights_query)
        
        if not insights:
            return Response({
                'matches': [],
                'message': 'No insights available for matching'
            }, status=status.HTTP_200_OK)
        
        # Calculate similarities and create matches
        matches_created = []
        
        with transaction.atomic():
            # Clear existing matches for this job
            JobInsightMatch.objects.filter(searched_job=job).delete()
            
            for insight in insights:
                try:
                    # Calculate cosine similarity
                    similarity = embedding_service.calculate_similarity(
                        job_embedding, insight.embedding
                    )
                    
                    if similarity >= min_similarity:
                        # Calculate category match bonus
                        category_bonus = _calculate_category_match_bonus(job, insight)
                        final_score = similarity + category_bonus
                        
                        # Create match record
                        match = JobInsightMatch.objects.create(
                            searched_job=job,
                            matched_insight=insight,
                            relevance_score=similarity,
                            category_match_bonus=category_bonus,
                            final_score=final_score
                        )
                        matches_created.append(match)
                        
                except Exception as e:
                    logger.error(f"Error calculating similarity for insight {insight.id}: {str(e)}")
                    continue
        
        # Sort by final score and limit to top_k
        matches_created.sort(key=lambda m: m.final_score, reverse=True)
        top_matches = matches_created[:top_k]
        
        # Serialize and return
        serializer = JobInsightMatchSerializer(top_matches, many=True)
        
        return Response({
            'job_id': job_id,
            'job_title': job.job_title,
            'matches_found': len(matches_created),
            'top_matches': len(top_matches),
            'matches': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error matching insights to job {job_id}: {str(e)}")
        return Response({
            'error': 'Failed to match insights to job',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _calculate_category_match_bonus(job, insight):
    """Calculate bonus score for category alignment between job and insight"""
    try:
        # Get job title and description
        job_text = f"{job.job_title} {job.analysis_result}".lower()
        
        # Check if insight category keywords match the job
        category_keywords = [kw.lower() for kw in insight.category.keywords]
        
        bonus = 0.0
        for keyword in category_keywords:
            if keyword in job_text:
                bonus += 0.1  # 10% bonus per matching keyword
        
        # Cap the bonus at 30%
        return min(bonus, 0.3)
        
    except Exception as e:
        logger.error(f"Error calculating category bonus: {str(e)}")
        return 0.0


# Generated Narratives Views

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def generate_narrative(request, job_id):
    """Generate AI narrative content using matched insights"""
    try:
        # Get the job
        job = get_object_or_404(SearchedJob, id=job_id, user=request.user)
        
        # Validate request
        serializer = NarrativeGenerationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        params = serializer.validated_data
        narrative_type = params['narrative_type']
        use_insight_ids = params.get('use_insight_ids', [])
        custom_prompt = params.get('custom_prompt', '')
        
        # Get insights to use
        if use_insight_ids:
            # Use specific insights
            insights = PersonalInsight.objects.filter(
                id__in=use_insight_ids,
                user=request.user,
                is_active=True
            )
        else:
            # Use top-matched insights
            matches = JobInsightMatch.objects.filter(
                searched_job=job
            ).order_by('-final_score')[:5]
            insights = [match.matched_insight for match in matches]
        
        if not insights:
            return Response({
                'error': 'No insights available for narrative generation'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate narrative using AI
        narrative_content = _generate_narrative_content(
            job, insights, narrative_type, custom_prompt
        )
        
        if not narrative_content:
            return Response({
                'error': 'Failed to generate narrative content'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Save the generated narrative
        with transaction.atomic():
            # Delete existing narrative of this type for this job
            GeneratedNarrative.objects.filter(
                searched_job=job,
                narrative_type=narrative_type
            ).delete()
            
            # Create new narrative
            narrative = GeneratedNarrative.objects.create(
                user=request.user,
                searched_job=job,
                narrative_type=narrative_type,
                content=narrative_content,
                generation_prompt=_build_generation_prompt(job, insights, narrative_type, custom_prompt)
            )
            
            # Link insights used
            for i, insight in enumerate(insights):
                NarrativeInsightUsage.objects.create(
                    narrative=narrative,
                    insight=insight,
                    usage_weight=max(0.1, 1.0 - (i * 0.2))  # Decreasing weight for lower-ranked insights
                )
                
                # Mark insight matches as used
                JobInsightMatch.objects.filter(
                    searched_job=job,
                    matched_insight=insight
                ).update(is_used_in_narrative=True)
        
        # Return the generated narrative
        narrative_serializer = GeneratedNarrativeSerializer(narrative)
        
        return Response({
            'narrative': narrative_serializer.data,
            'insights_used': len(insights),
            'message': 'Narrative generated successfully'
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        logger.error(f"Error generating narrative for job {job_id}: {str(e)}")
        return Response({
            'error': 'Failed to generate narrative',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _generate_narrative_content(job, insights, narrative_type, custom_prompt=""):
    """Generate narrative content using AI"""
    try:
        agent = AgenticUtility()
        
        # Build the generation prompt
        full_prompt = _build_generation_prompt(job, insights, narrative_type, custom_prompt)
        
        config = {
            'systemMessage': 'You are a professional career advisor and expert writer. Create compelling, personalized narrative content that authentically represents the candidate while being professional and engaging.',
            'prompt': full_prompt,
            'goal': f'Generate a professional {narrative_type.replace("_", " ")} based on the provided context',
            'enableSearch': False,
            'model': 'openai/gpt-5-chat'
        }
        
        result = agent.execute_task(config)
        
        if result['success']:
            return result['result'].strip()
        else:
            logger.error(f"AI generation failed: {result.get('error', 'Unknown error')}")
            return None
            
    except Exception as e:
        logger.error(f"Error in narrative generation: {str(e)}")
        return None


def _build_generation_prompt(job, insights, narrative_type, custom_prompt=""):
    """Build the prompt for AI narrative generation"""
    
    # Job context
    job_context = f"""
JOB INFORMATION:
- Title: {job.job_title}
- Company: {job.company_name}
- Description/Requirements: {job.analysis_result[:1000]}
"""
    
    # Insights context
    insights_text = ""
    for i, insight in enumerate(insights, 1):
        insights_text += f"""
INSIGHT {i} - {insight.get_insight_type_display()} ({insight.category.name}):
Question: {insight.question}
Response: {insight.content}
"""
    
    # Type-specific instructions
    type_instructions = {
        'cover_letter': 'Write a compelling cover letter that tells a cohesive story connecting the candidate\'s background to this specific role and company. Be engaging, professional, and authentic.',
        'summary': 'Create a professional summary that positions the candidate as an ideal fit for this role, highlighting the most relevant qualifications and motivations.',
        'motivation': 'Write a motivation statement explaining why the candidate is passionate about this role and company, drawing on their personal insights.',
        'value_proposition': 'Create a value proposition statement that clearly articulates the unique value the candidate would bring to this role and organization.'
    }
    
    instruction = type_instructions.get(narrative_type, 'Create professional narrative content')
    
    prompt = f"""
{job_context}

CANDIDATE INSIGHTS:
{insights_text}

TASK: {instruction}

{f"ADDITIONAL INSTRUCTIONS: {custom_prompt}" if custom_prompt else ""}

REQUIREMENTS:
- Use the insights naturally and authentically
- Make specific connections between the candidate's background and the job requirements
- Be professional but personable
- Avoid generic language or clichés
- Keep it concise and impactful (aim for 200-400 words for cover letters, shorter for other types)
- Return ONLY the narrative content, no explanations or meta-text

Generate the {narrative_type.replace('_', ' ')}:
"""
    
    return prompt


class GeneratedNarrativeListView(generics.ListAPIView):
    """List generated narratives for a user"""
    permission_classes = [IsAuthenticated]
    serializer_class = GeneratedNarrativeSerializer
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['narrative_type', 'is_approved']
    ordering_fields = ['created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return GeneratedNarrative.objects.filter(user=self.request.user)


class GeneratedNarrativeRetrieveUpdateDeleteView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a generated narrative"""
    permission_classes = [IsAuthenticated]
    serializer_class = GeneratedNarrativeSerializer

    def get_queryset(self):
        return GeneratedNarrative.objects.filter(user=self.request.user)


# Enhanced Job Detail with Insights

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def job_with_insights(request, job_id):
    """Get job details with insight matches and generated narratives"""
    try:
        job = get_object_or_404(SearchedJob, id=job_id, user=request.user)
        serializer = SearchedJobWithInsightsSerializer(job)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error retrieving job with insights {job_id}: {str(e)}")
        return Response({
            'error': 'Failed to retrieve job details',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Utility Views

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def insight_questions(request, category_id):
    """Get suggested questions for a specific career category"""
    try:
        category = get_object_or_404(CareerCategory, id=category_id)
        
        # Get existing insight types for this user/category
        existing_types = set(
            PersonalInsight.objects.filter(
                user=request.user,
                category=category,
                is_active=True
            ).values_list('insight_type', flat=True)
        )
        
        # Suggested questions for each insight type
        questions_map = {
            'company_motivation': [
                f"What specifically interests you about working for companies in the {category.name} space?",
                f"What industry trends in {category.name} roles excite you most?",
                "What type of company culture do you thrive in?"
            ],
            'career_motivation': [
                f"What drives you to pursue {category.name} positions?",
                "What are your long-term career goals in this field?",
                "What aspects of leadership/management motivate you?"
            ],
            'leadership_style': [
                "How do you approach team leadership and management?",
                "Describe your philosophy for building and developing teams.",
                "How do you handle conflict resolution and difficult conversations?"
            ],
            'work_values': [
                "What work environment helps you perform at your best?",
                "What professional values are most important to you?",
                "How do you balance technical work with business strategy?"
            ],
            'unique_value': [
                f"What makes you uniquely qualified for {category.name} roles?",
                "What's your competitive advantage over other candidates?",
                "What unique perspective do you bring to technical leadership?"
            ],
            'industry_knowledge': [
                f"What industry challenges do you see in the {category.name} space?",
                "What emerging technologies excite you most?",
                "How do you stay current with industry trends?"
            ],
            'problem_solving': [
                "Describe your approach to solving complex technical problems.",
                "How do you handle ambiguous or undefined requirements?",
                "What's your process for making difficult technical decisions?"
            ],
            'team_building': [
                "How do you build trust and rapport with new team members?",
                "What's your approach to hiring and onboarding?",
                "How do you foster collaboration across different teams?"
            ],
            'change_management': [
                "How do you lead teams through organizational change?",
                "Describe your approach to implementing new processes or technologies.",
                "How do you handle resistance to change?"
            ],
            'technical_vision': [
                "How do you develop and communicate technical vision?",
                "What's your approach to technical debt and architectural decisions?",
                "How do you balance innovation with stability?"
            ]
        }
        
        # Build response with available question types
        available_questions = {}
        for insight_type, questions in questions_map.items():
            if insight_type not in existing_types:
                available_questions[insight_type] = {
                    'display_name': dict(PersonalInsight.INSIGHT_TYPES)[insight_type],
                    'questions': questions
                }
        
        return Response({
            'category': category.name,
            'available_types': available_questions,
            'completed_types': list(existing_types)
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error getting questions for category {category_id}: {str(e)}")
        return Response({
            'error': 'Failed to get questions',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)