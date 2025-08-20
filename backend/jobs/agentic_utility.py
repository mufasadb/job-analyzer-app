import openai
import requests
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AgenticUtility:
    def __init__(self, api_key=None):
        if not api_key:
            api_key = os.getenv('OPENROUTER_API_KEY')
        
        self.client = openai.OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )
        
        # Load the job extraction schema
        schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'job-extraction-schema.json')
        with open(schema_path, 'r') as f:
            self.job_extraction_schema = json.load(f)

    def search_web(self, query, num_results=3):
        try:
            # Use DuckDuckGo Instant Answer API for search
            search_url = f"https://api.duckduckgo.com/?q={requests.utils.quote(query)}&format=json&no_html=1"
            response = requests.get(search_url)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('RelatedTopics') and len(data['RelatedTopics']) > 0:
                    return [
                        {
                            'title': topic.get('Text', ''),
                            'url': topic.get('FirstURL', ''),
                            'snippet': topic.get('Text', '')
                        }
                        for topic in data['RelatedTopics'][:num_results]
                    ]
            
            return [{'title': 'No results', 'snippet': 'Search did not return results', 'url': ''}]
        except Exception as error:
            return [{'title': 'Search Error', 'snippet': str(error), 'url': ''}]

    def fetch_page_content(self, url):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Extract text content
            title = soup.find('title').get_text() if soup.find('title') else ''
            content = soup.get_text()
            
            # Clean up whitespace
            content = ' '.join(content.split())
            
            return {
                'title': title,
                'content': content[:2000],  # Limit content length
                'url': url
            }
        except Exception as error:
            return {
                'title': 'Fetch Error',
                'content': f'Unable to fetch content: {str(error)}',
                'url': url
            }

    def extract_job_details(self, job_url, model='openai/gpt-5-chat'):
        """Extract structured job details using function calling"""
        try:
            print(f"🔍 Extracting job details from: {job_url}")
            
            # Fetch the job posting content
            page_content = self.fetch_page_content(job_url)
            
            if not page_content['content'] or 'Unable to fetch content' in page_content['content']:
                raise Exception('Unable to fetch job posting content')

            print(f"📄 Fetched job content: {page_content['title']}")

            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a job posting analyzer. Extract information from job postings and organize it into the specified structure. Only extract information that is explicitly stated in the content. If information is not available, leave fields empty or use appropriate default values.'
                    },
                    {
                        'role': 'user',
                        'content': f"""Please extract job details from this job posting content:

TITLE: {page_content['title']}

CONTENT: {page_content['content']}

Extract the information and organize it according to the function schema. Only include information that is explicitly mentioned in the content."""
                    }
                ],
                tools=[
                    {
                        'type': 'function',
                        'function': self.job_extraction_schema
                    }
                ],
                tool_choice={'type': 'function', 'function': {'name': 'extract_job_details'}},
                temperature=0.1
            )

            tool_call = response.choices[0].message.tool_calls[0] if response.choices[0].message.tool_calls else None
            if not tool_call or tool_call.function.name != 'extract_job_details':
                raise Exception('Failed to extract structured job data')

            extracted_data = json.loads(tool_call.function.arguments)

            return {
                'success': True,
                'job_data': extracted_data,
                'raw_content': {
                    'title': page_content['title'],
                    'url': job_url,
                    'content': page_content['content']
                },
                'usage': response.usage.model_dump() if response.usage else None,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as error:
            return {
                'success': False,
                'error': str(error),
                'timestamp': datetime.now().isoformat()
            }

    def execute_task(self, config):
        system_message = config.get('systemMessage', 'You are a helpful research assistant that can analyze data and provide structured outputs.')
        prompt = config.get('prompt', '')
        goal = config.get('goal', '')
        input_data = config.get('input', {})
        enable_search = config.get('enableSearch', False)
        model = config.get('model', 'openai/gpt-5-chat')
        
        search_results = None
        
        # If search is enabled, perform web search based on goal/prompt
        if enable_search:
            search_query = input_data.get('searchQuery') or goal
            print(f"🔍 Processing: {search_query}")
            
            # Check if searchQuery is a direct URL
            if search_query.startswith('http'):
                print(f"📄 Fetching content directly from URL: {search_query}")
                page_content = self.fetch_page_content(search_query)
                search_results = [{
                    'title': page_content['title'],
                    'url': search_query,
                    'snippet': page_content['content'][:200],
                    'fullContent': page_content['content']
                }]
            else:
                search_results = self.search_web(search_query)
                
                # Fetch content from first result if available
                if search_results and len(search_results) > 0 and search_results[0].get('url'):
                    print(f"📄 Fetching content from: {search_results[0]['url']}")
                    page_content = self.fetch_page_content(search_results[0]['url'])
                    search_results[0]['fullContent'] = page_content['content']

        try:
            messages = [
                {
                    'role': 'system',
                    'content': system_message
                },
                {
                    'role': 'user',
                    'content': f"""
GOAL: {goal}

CONTEXT/PROMPT: {prompt}

INPUT DATA: {json.dumps(input_data, indent=2)}

{f'''
SEARCH RESULTS:
{json.dumps(search_results, indent=2)}
''' if search_results else ''}

Please complete the goal using the provided context, input data{', and search results' if search_results else ''}. Provide a structured response with your findings and analysis.
                    """.strip()
                }
            ]
            
            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.7
            )

            return {
                'success': True,
                'result': response.choices[0].message.content,
                'usage': response.usage.model_dump() if response.usage else None,
                'searchResults': search_results,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as error:
            return {
                'success': False,
                'error': str(error),
                'searchResults': search_results,
                'timestamp': datetime.now().isoformat()
            }