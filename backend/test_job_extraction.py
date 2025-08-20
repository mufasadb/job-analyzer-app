#!/usr/bin/env python3

import os
import sys
import django

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'job_analyzer_backend.settings')
django.setup()

from jobs.agentic_utility import AgenticUtility

# Test the structured job extraction
agent = AgenticUtility()

# Use a test job URL
job_url = "https://www.linkedin.com/jobs/view/4286417322"

print("🚀 Testing Python structured job extraction...")
print(f"🎯 Job URL: {job_url}")

try:
    result = agent.extract_job_details(job_url, model='anthropic/claude-3.5-sonnet')
    
    if result['success']:
        print("✅ Job extraction completed!")
        print("\n📋 STRUCTURED JOB DATA:")
        print("=" * 60)
        
        job = result['job_data']
        
        print(f"\n🏢 JOB TITLE: {job.get('job_title', 'Not specified')}")
        
        if job.get('company_information'):
            company = job['company_information']
            print(f"\n🏢 COMPANY:")
            print(f"  Name: {company.get('company_name', 'Not specified')}")
            print(f"  Industry: {company.get('industry', 'Not specified')}")
            print(f"  Location: {company.get('location', 'Not specified')}")
        
        if job.get('requirements'):
            req = job['requirements']
            print(f"\n✅ REQUIREMENTS:")
            if req.get('must_have'):
                print("  Must Have:")
                for item in req['must_have']:
                    print(f"    • {item}")
            print(f"  Experience: {req.get('experience_level', 'Not specified')}")
            print(f"  Education: {req.get('education', 'Not specified')}")
        
        if job.get('salary_information'):
            salary = job['salary_information']
            print(f"\n💰 SALARY:")
            print(f"  Range: {salary.get('salary_range', 'Not specified')}")
            print(f"  Type: {salary.get('salary_type', 'not_specified')}")
        
        print("\n" + "=" * 60)
        
        if result.get('usage'):
            usage = result['usage']
            print(f"\n📊 Usage Stats:")
            print(f"- Prompt tokens: {usage.get('prompt_tokens', 0)}")
            print(f"- Completion tokens: {usage.get('completion_tokens', 0)}")
            print(f"- Total tokens: {usage.get('total_tokens', 0)}")
        
    else:
        print(f"❌ Job extraction failed: {result.get('error', 'Unknown error')}")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")