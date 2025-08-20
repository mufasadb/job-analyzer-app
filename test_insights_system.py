#!/usr/bin/env python3
"""
Comprehensive test script for the Career Insights & Vector Search system.
Tests the complete flow from career categories to AI narrative generation.
"""

import os
import sys
import json
import requests
from datetime import datetime

# Add Django project to path
sys.path.append('backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_analyzer_backend.settings')

import django
django.setup()

from django.contrib.auth.models import User
from rest_framework.authtoken.models import Token
from jobs.models import SearchedJob, CareerCategory, PersonalInsight

# Test configuration
BASE_URL = 'http://127.0.0.1:5007/api'
TEST_USER = {
    'username': 'testuser',
    'password': 'testpass123',
    'email': 'test@example.com'
}

class InsightsSystemTester:
    """Test runner for the complete insights system"""
    
    def __init__(self):
        self.session = requests.Session()
        self.user = None
        self.token = None
        self.test_results = []
    
    def log_result(self, test_name, success, message="", data=None):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        
        return success
    
    def setup_test_user(self):
        """Create or get test user and authentication token"""
        try:
            # Get or create user
            self.user, created = User.objects.get_or_create(
                username=TEST_USER['username'],
                defaults={
                    'email': TEST_USER['email'],
                    'is_active': True
                }
            )
            
            if created:
                self.user.set_password(TEST_USER['password'])
                self.user.save()
            
            # Get or create token
            self.token, created = Token.objects.get_or_create(user=self.user)
            
            # Set session headers
            self.session.headers.update({
                'Authorization': f'Token {self.token.key}',
                'Content-Type': 'application/json'
            })
            
            return self.log_result("Setup Test User", True, f"User '{self.user.username}' ready")
            
        except Exception as e:
            return self.log_result("Setup Test User", False, f"Error: {str(e)}")
    
    def test_career_categories_api(self):
        """Test career categories listing"""
        try:
            response = self.session.get(f'{BASE_URL}/jobs/categories/')
            
            if response.status_code != 200:
                return self.log_result(
                    "Career Categories API", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
            
            data = response.json()
            categories = data.get('results', data) if 'results' in data else data
            
            if not isinstance(categories, list) or len(categories) == 0:
                return self.log_result(
                    "Career Categories API", 
                    False, 
                    "No categories found"
                )
            
            return self.log_result(
                "Career Categories API", 
                True, 
                f"Found {len(categories)} categories",
                [cat['name'] for cat in categories[:3]]
            )
            
        except Exception as e:
            return self.log_result("Career Categories API", False, f"Error: {str(e)}")
    
    def test_create_personal_insight(self):
        """Test creating a personal insight"""
        try:
            # Get CTO category
            cto_category = CareerCategory.objects.filter(name__icontains='CTO').first()
            if not cto_category:
                return self.log_result(
                    "Create Personal Insight", 
                    False, 
                    "CTO category not found"
                )
            
            insight_data = {
                'category': cto_category.id,
                'insight_type': 'leadership_style',
                'question': 'How do you approach team leadership and management?',
                'content': '''I believe in servant leadership combined with clear technical vision. My approach focuses on:

1. Empowering teams through clear goals and removing blockers
2. Building psychological safety where team members can take calculated risks
3. Balancing technical debt with feature delivery through transparent roadmapping
4. Fostering continuous learning through code reviews, architecture discussions, and knowledge sharing
5. Leading by example in code quality, documentation, and technical decision-making

I've successfully scaled engineering teams from 5 to 50+ people while maintaining high code quality and delivery velocity. My experience spans both startup environments requiring rapid iteration and enterprise contexts needing robust, scalable solutions.''',
                'tags': ['leadership', 'management', 'scaling', 'technical_vision']
            }
            
            response = self.session.post(f'{BASE_URL}/jobs/insights/', json=insight_data)
            
            if response.status_code not in [200, 201]:
                return self.log_result(
                    "Create Personal Insight", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
            
            insight = response.json()
            
            return self.log_result(
                "Create Personal Insight", 
                True, 
                f"Created insight: {insight.get('insight_type_display', 'Unknown')}",
                {'id': insight.get('id'), 'type': insight.get('insight_type')}
            )
            
        except Exception as e:
            return self.log_result("Create Personal Insight", False, f"Error: {str(e)}")
    
    def create_test_job(self):
        """Create a test job for matching"""
        try:
            job_data = {
                'user': self.user,
                'linkedin_url': 'https://www.linkedin.com/jobs/view/test-cto-role/',
                'job_title': 'Chief Technology Officer',
                'company_name': 'TechCorp Inc',
                'analysis_result': '''We are seeking an experienced Chief Technology Officer to lead our engineering organization. 

Key Requirements:
- 10+ years of software engineering experience with 5+ years in leadership roles
- Experience scaling engineering teams from startup to enterprise
- Strong background in cloud architecture, microservices, and DevOps practices
- Proven track record of building high-performing engineering cultures
- Experience with agile development methodologies and technical roadmap planning
- Strong communication skills for both technical and business stakeholders

Responsibilities:
- Define and execute technical strategy and architecture vision
- Build, mentor, and scale a world-class engineering team
- Collaborate with CEO and leadership team on product roadmap and business strategy
- Establish engineering best practices, processes, and quality standards
- Drive technical innovation while maintaining system reliability and security

This is a unique opportunity to shape the technical direction of a rapidly growing company in the fintech space.''',
                'recommendations': {
                    'analysis': 'This CTO role requires strong technical leadership and team scaling experience.',
                    'skills_match': ['leadership', 'scaling', 'architecture', 'team_building']
                }
            }
            
            job = SearchedJob.objects.create(**job_data)
            
            return self.log_result(
                "Create Test Job", 
                True, 
                f"Created job: {job.job_title} at {job.company_name}",
                {'id': job.id}
            ), job
            
        except Exception as e:
            return self.log_result("Create Test Job", False, f"Error: {str(e)}"), None
    
    def test_insight_matching(self, job):
        """Test vector similarity matching between job and insights"""
        if not job:
            return self.log_result("Insight Matching", False, "No job available for testing")
        
        try:
            match_data = {
                'top_k': 5,
                'min_similarity': 0.2
            }
            
            response = self.session.post(
                f'{BASE_URL}/jobs/{job.id}/match-insights/', 
                json=match_data
            )
            
            if response.status_code != 200:
                return self.log_result(
                    "Insight Matching", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
            
            data = response.json()
            matches = data.get('matches', [])
            
            if not matches:
                return self.log_result(
                    "Insight Matching", 
                    False, 
                    "No insight matches found (may need embeddings generated)"
                )
            
            return self.log_result(
                "Insight Matching", 
                True, 
                f"Found {len(matches)} matches with scores up to {matches[0].get('final_score', 0):.3f}",
                [{'type': m.get('insight_type'), 'score': m.get('final_score')} for m in matches[:3]]
            )
            
        except Exception as e:
            return self.log_result("Insight Matching", False, f"Error: {str(e)}")
    
    def test_narrative_generation(self, job):
        """Test AI narrative generation"""
        if not job:
            return self.log_result("Narrative Generation", False, "No job available for testing")
        
        try:
            narrative_data = {
                'narrative_type': 'cover_letter'
            }
            
            response = self.session.post(
                f'{BASE_URL}/jobs/{job.id}/generate-narrative/', 
                json=narrative_data
            )
            
            if response.status_code not in [200, 201]:
                return self.log_result(
                    "Narrative Generation", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
            
            data = response.json()
            narrative = data.get('narrative', {})
            content = narrative.get('content', '')
            
            if not content:
                return self.log_result(
                    "Narrative Generation", 
                    False, 
                    "No narrative content generated"
                )
            
            return self.log_result(
                "Narrative Generation", 
                True, 
                f"Generated {len(content)} character {narrative.get('narrative_type', 'narrative')}",
                {'preview': content[:100] + '...', 'insights_used': data.get('insights_used', 0)}
            )
            
        except Exception as e:
            return self.log_result("Narrative Generation", False, f"Error: {str(e)}")
    
    def test_job_with_insights_api(self, job):
        """Test enhanced job details with insights"""
        if not job:
            return self.log_result("Job with Insights API", False, "No job available for testing")
        
        try:
            response = self.session.get(f'{BASE_URL}/jobs/{job.id}/insights/')
            
            if response.status_code != 200:
                return self.log_result(
                    "Job with Insights API", 
                    False, 
                    f"HTTP {response.status_code}: {response.text}"
                )
            
            data = response.json()
            
            return self.log_result(
                "Job with Insights API", 
                True, 
                f"Retrieved job with {len(data.get('insight_matches', []))} matches and {len(data.get('generated_narratives', []))} narratives"
            )
            
        except Exception as e:
            return self.log_result("Job with Insights API", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run the complete test suite"""
        print("🚀 Starting Career Insights System Test Suite")
        print("=" * 60)
        
        # Setup
        if not self.setup_test_user():
            return False
        
        # API Tests
        self.test_career_categories_api()
        self.test_create_personal_insight()
        
        # Create test data
        success, job = self.create_test_job()
        
        # Advanced Tests
        self.test_insight_matching(job)
        self.test_narrative_generation(job)
        self.test_job_with_insights_api(job)
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 Failed Tests:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  - {result['test']}: {result['message']}")
        
        # Save detailed results
        with open('test_results.json', 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n📝 Detailed results saved to test_results.json")
        
        return failed_tests == 0


if __name__ == '__main__':
    tester = InsightsSystemTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed! The Career Insights system is working correctly.")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        sys.exit(1)