import os
import google.generativeai as genai
import requests
from supabase import create_client
from datetime import datetime
from dotenv import load_dotenv
import json
import time

class InfoAgent:
    """
    Agent for collecting and analyzing financial news using Brave Search and Gemini AI.
    Stores processed information in Supabase database.
    """

    def __init__(self):
        """Initialize the InfoAgent with necessary API clients and configurations"""
        load_dotenv(override=True)
        
        # Validate environment variables
        self.required_vars = {
            'SUPABASE_URL': os.getenv('SUPABASE_URL'),
            'SUPABASE_KEY': os.getenv('SUPABASE_KEY'),
            'SUPABASE_EMAIL': os.getenv('SUPABASE_EMAIL'),
            'SUPABASE_PASSWORD': os.getenv('SUPABASE_PASSWORD'),
            'BRAVE_API_KEY': os.getenv('BRAVE_API_KEY'),
            'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY')
        }
        
        if not all(self.required_vars.values()):
            raise ValueError("Missing required environment variables")

        # Initialize API clients
        self.supabase = create_client(self.required_vars['SUPABASE_URL'], self.required_vars['SUPABASE_KEY'])
        genai.configure(api_key=self.required_vars['GEMINI_API_KEY'])
        self.model = genai.GenerativeModel("gemini-1.5-flash-8b")

        # Define Gemini function for Brave Search
        self.tools = [{
            "function_declarations": [{
                "name": "brave_search",
                "description": "Search for latest financial news using Brave Search API",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The search query for financial news"
                        }
                    },
                    "required": ["query"]
                }
            }]
        }]

    def authenticate(self):
        """Authenticate with Supabase"""
        try:
            self.supabase.auth.sign_in_with_password({
                "email": self.required_vars['SUPABASE_EMAIL'],
                "password": self.required_vars['SUPABASE_PASSWORD']
            })
            print("Successfully authenticated with Supabase")
            return True
        except Exception as e:
            print(f"Authentication error: {e}")
            return False

    def search_news(self, query, max_retries=3, base_delay=5):
        """
        Perform a search using Brave Search API with rate limiting and retries
        Args:
            query (str): Search query string
            max_retries (int): Maximum number of retry attempts
            base_delay (int): Base delay between retries in seconds
        Returns:
            dict: Search results or None if error
        """
        for attempt in range(max_retries):
            try:
                url = "https://api.search.brave.com/res/v1/web/search"
                headers = {
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "X-Subscription-Token": self.required_vars['BRAVE_API_KEY']
                }
                params = {
                    "q": query,
                    "search_lang": "en",
                    "country": "us",
                    "freshness": "pd"  # Past day
                }
                
                response = requests.get(url, headers=headers, params=params)
                
                # Handle rate limiting
                if response.status_code == 429:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    print(f"Rate limited. Waiting {delay} seconds before retry...")
                    time.sleep(delay)
                    continue
                    
                response.raise_for_status()
                results = response.json()
                print(f"Successfully retrieved {len(results.get('web', {}).get('results', []))} news articles")
                return results
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:  # Last attempt
                    print(f"Search error after {max_retries} attempts: {e}")
                    return None
                delay = base_delay * (2 ** attempt)
                print(f"Request failed. Retrying in {delay} seconds...")
                time.sleep(delay)
                continue

    def extract_function_args(self, completion):
        """Extract search query from Gemini function call response"""
        try:
            parts = completion.candidates[0].content.parts
            for part in parts:
                if hasattr(part, 'function_call'):
                    args_map = part.function_call.args
                    if 'query' in args_map:
                        return {"query": args_map['query'].strip('"')}
            return None
        except Exception as e:
            print(f"Error extracting function args: {e}")
            return None

    def store_news(self, info):
        """Store processed news in Supabase"""
        try:
            data = {
                "info": info,
                "timestamp": datetime.utcnow().isoformat()
            }
            self.supabase.table('finance_info').insert(data).execute()
            print("Successfully stored news summary in database")
            return True
        except Exception as e:
            print(f"Error storing news: {e}")
            return False

    def process_articles(self, search_results):
        """Process and format search results into articles"""
        if not search_results or "web" not in search_results:
            return None

        web = search_results.get("web", {})
        web_results = web.get("results", [])
        
        articles = []
        for i, result in enumerate(web_results):
            if i >= 5:  # Limit to top 5 articles
                break
                
            title = result.get('title', '')
            description = result.get('description', '')
            url = result.get('url', '')
            
            if title or description:
                articles.append({
                    'title': title or 'No title',
                    'description': description or 'No description',
                    'url': url or 'No URL'
                })
        
        return articles

    def run(self):
        """Main execution function"""
        if not self.authenticate():
            return

        queries = [
            "latest bitcoin cryptocurrency news today",
            "major macroeconomic news finance today",
            "bitcoin market analysis latest",
            "global financial markets news today"
        ]

        print(f"\nStarting news processing for {len(queries)} topics...")
        successful_queries = 0

        for query in queries:
            try:
                print(f"\nProcessing topic: {query}")
                # Get optimized search query from Gemini
                search_prompt = f"""You are a financial news researcher. Your task is to help find and analyze 
                the latest important financial news. Be concise and specific in your search query.
                Find the latest news about: {query}"""
                
                completion = self.model.generate_content(
                    search_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.5,
                        candidate_count=1,
                        top_k=10,
                        top_p=0.8,
                    ),
                    tools=self.tools,
                    tool_config={"function_calling_config": {"mode": "ANY"}}
                )

                search_args = self.extract_function_args(completion)
                if not search_args:
                    continue

                # Search for news articles
                search_results = self.search_news(search_args["query"])
                articles = self.process_articles(search_results)
                
                if not articles:
                    continue

                # Format articles for analysis
                articles_text = "\n\n".join([
                    f"Title: {article['title']}\nURL: {article['url']}\nDescription: {article['description']}" 
                    for article in articles
                ])

                # Get analysis from Gemini
                analysis_prompt = """Analyze these financial news articles and provide a concise, 
                fact-focused summary in a single paragraph. Focus on key market movements, important 
                announcements, and potential impact on Bitcoin and crypto markets.

                Articles:\n""" + articles_text

                analysis = self.model.generate_content(
                    analysis_prompt,
                    generation_config=genai.types.GenerationConfig(
                        temperature=0.5,
                        candidate_count=1,
                        top_k=10,
                        top_p=0.8,
                        max_output_tokens=200
                    )
                )

                if analysis:
                    if self.store_news(analysis.text):
                        successful_queries += 1
                
                # Increase delay between queries to avoid rate limiting
                time.sleep(5)  # Wait 5 seconds between queries

            except Exception as e:
                print(f"Error processing query '{query}': {e}")
                time.sleep(5)  # Wait even after errors
                continue

        print(f"\nCompleted processing with {successful_queries} out of {len(queries)} topics successfully analyzed")


if __name__ == "__main__":
    """Initialize and run the InfoAgent"""
    print("Starting InfoAgent...")
    agent = InfoAgent()
    agent.run()