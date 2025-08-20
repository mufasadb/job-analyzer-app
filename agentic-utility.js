import OpenAI from 'openai';
import axios from 'axios';
import * as cheerio from 'cheerio';
import { readFileSync } from 'fs';
import 'dotenv/config';

class AgenticUtility {
  constructor(apiKey = process.env.OPENROUTER_API_KEY) {
    this.openai = new OpenAI({
      baseURL: "https://openrouter.ai/api/v1",
      apiKey: apiKey,
    });
    
    // Load the job extraction schema
    this.jobExtractionSchema = JSON.parse(
      readFileSync('./job-extraction-schema.json', 'utf8')
    );
  }

  async searchWeb(query, numResults = 3) {
    try {
      // Use DuckDuckGo Instant Answer API for search
      const searchUrl = `https://api.duckduckgo.com/?q=${encodeURIComponent(query)}&format=json&no_html=1`;
      const response = await axios.get(searchUrl);
      
      if (response.data.RelatedTopics && response.data.RelatedTopics.length > 0) {
        return response.data.RelatedTopics.slice(0, numResults).map(topic => ({
          title: topic.Text,
          url: topic.FirstURL,
          snippet: topic.Text
        }));
      }
      
      return [{ title: "No results", snippet: "Search did not return results", url: "" }];
    } catch (error) {
      return [{ title: "Search Error", snippet: error.message, url: "" }];
    }
  }

  async fetchPageContent(url) {
    try {
      const response = await axios.get(url, {
        headers: {
          'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
          'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
          'Accept-Language': 'en-US,en;q=0.5',
          'Accept-Encoding': 'gzip, deflate',
          'Connection': 'keep-alive'
        },
        timeout: 15000
      });
      
      const $ = cheerio.load(response.data);
      
      // Remove script and style elements
      $('script, style').remove();
      
      // Extract text content
      const title = $('title').text();
      const content = $('body').text().replace(/\s+/g, ' ').trim();
      
      return {
        title,
        content: content.substring(0, 2000), // Limit content length
        url
      };
    } catch (error) {
      return {
        title: "Fetch Error",
        content: `Unable to fetch content: ${error.message}`,
        url
      };
    }
  }

  async extractJobDetails(jobUrl, model = "openai/gpt-5-chat") {
    try {
      console.log(`🔍 Extracting job details from: ${jobUrl}`);
      
      // Fetch the job posting content
      const pageContent = await this.fetchPageContent(jobUrl);
      
      if (!pageContent.content || pageContent.content.includes('Unable to fetch content')) {
        throw new Error('Unable to fetch job posting content');
      }

      console.log(`📄 Fetched job content: ${pageContent.title}`);

      const response = await this.openai.chat.completions.create({
        model: model,
        messages: [
          {
            role: "system",
            content: "You are a job posting analyzer. Extract information from job postings and organize it into the specified structure. Only extract information that is explicitly stated in the content. If information is not available, leave fields empty or use appropriate default values."
          },
          {
            role: "user",
            content: `Please extract job details from this job posting content:

TITLE: ${pageContent.title}

CONTENT: ${pageContent.content}

Extract the information and organize it according to the function schema. Only include information that is explicitly mentioned in the content.`
          }
        ],
        tools: [
          {
            type: "function",
            function: this.jobExtractionSchema
          }
        ],
        tool_choice: { type: "function", function: { name: "extract_job_details" } },
        temperature: 0.1,
      });

      const toolCall = response.choices[0].message.tool_calls?.[0];
      if (!toolCall || toolCall.function.name !== 'extract_job_details') {
        throw new Error('Failed to extract structured job data');
      }

      const extractedData = JSON.parse(toolCall.function.arguments);

      return {
        success: true,
        jobData: extractedData,
        rawContent: {
          title: pageContent.title,
          url: jobUrl,
          content: pageContent.content
        },
        usage: response.usage,
        timestamp: new Date().toISOString()
      };

    } catch (error) {
      return {
        success: false,
        error: error.message,
        timestamp: new Date().toISOString()
      };
    }
  }

  async executeTask(config) {
    const { 
      systemMessage, 
      prompt, 
      goal, 
      input, 
      enableSearch = false,
      model = "openai/gpt-5-chat",
      useJobExtraction = false
    } = config;

    // If this is a job extraction task, use the dedicated method
    if (useJobExtraction && input.jobUrl) {
      return await this.extractJobDetails(input.jobUrl, model);
    }

    let searchResults = null;
    
    // If search is enabled, perform web search based on goal/prompt
    if (enableSearch) {
      const searchQuery = input.searchQuery || goal;
      console.log(`🔍 Processing: ${searchQuery}`);
      
      // Check if searchQuery is a direct URL
      if (searchQuery.startsWith('http')) {
        console.log(`📄 Fetching content directly from URL: ${searchQuery}`);
        const pageContent = await this.fetchPageContent(searchQuery);
        searchResults = [{
          title: pageContent.title,
          url: searchQuery,
          snippet: pageContent.content.substring(0, 200),
          fullContent: pageContent.content
        }];
      } else {
        searchResults = await this.searchWeb(searchQuery);
        
        // Fetch content from first result if available
        if (searchResults.length > 0 && searchResults[0].url) {
          console.log(`📄 Fetching content from: ${searchResults[0].url}`);
          const pageContent = await this.fetchPageContent(searchResults[0].url);
          searchResults[0].fullContent = pageContent.content;
        }
      }
    }

    try {
      const response = await this.openai.chat.completions.create({
        model: model,
        messages: [
          {
            role: "system",
            content: systemMessage || "You are a helpful research assistant that can analyze data and provide structured outputs. When provided with search results, incorporate them into your analysis."
          },
          {
            role: "user",
            content: `
GOAL: ${goal}

CONTEXT/PROMPT: ${prompt}

INPUT DATA: ${JSON.stringify(input, null, 2)}

${searchResults ? `
SEARCH RESULTS:
${JSON.stringify(searchResults, null, 2)}
` : ''}

Please complete the goal using the provided context, input data${searchResults ? ', and search results' : ''}. Provide a structured response with your findings and analysis.
            `.trim()
          }
        ],
        temperature: 0.7,
      });

      return {
        success: true,
        result: response.choices[0].message.content,
        usage: response.usage,
        searchResults: searchResults,
        timestamp: new Date().toISOString()
      };
    } catch (error) {
      return {
        success: false,
        error: error.message,
        searchResults: searchResults,
        timestamp: new Date().toISOString()
      };
    }
  }
}

export default AgenticUtility;