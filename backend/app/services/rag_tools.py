# tools/rag_tools.py

import os
import requests
from bs4 import BeautifulSoup
import time
import json
import uuid
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
import logging
from pathlib import Path
import shutil
from datetime import datetime
from .file_system import FileSystemService
from collections import deque
from urllib.parse import urljoin, urlparse
from google import genai 

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Optional: Import sentence_transformers for semantic search if available
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    import numpy as np
    SEMANTIC_SEARCH_AVAILABLE = True
except ImportError:
    SEMANTIC_SEARCH_AVAILABLE = False
    logger.warning("sentence-transformers not installed. Semantic search will not be available.")

try: 
    from google import genai 
    genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
    
    result = genai_client.models.embed_content(
        model="gemini-embedding-001",
        contents="Hello, world!"
    )
    print(result.embeddings)
except Exception as e:
    logger.error(f"Error initializing Gemini client: {e}")
    genai_client = None

@dataclass
class WebPage:
    """Represents a web page with its content"""
    url: str
    title: str
    text_content: str
    html_content: str
    metadata: Dict[str, Any]
    timestamp: str




class WebScraperTool:
    """Tool for scraping web content, including basic crawling."""
    
    def __init__(self, file_system_service: FileSystemService = None):
        """
        Initialize the web scraper tool
        
        Args:
            file_system_service: Service for file management
        """
        self.fs = file_system_service or FileSystemService()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        self.visited_urls = set()
        self.scraped_data = []
        logger.info("WebScraperTool initialized")
    
    def fetch_url(self, url: str, timeout: int = 10) -> Optional[requests.Response]:
        """
        Fetch content from a URL
        
        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
            
        Returns:
            Response object or None if failed
        """
        try:
            response = requests.get(url, headers=self.headers, timeout=timeout)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.error(f"Error fetching URL {url}: {str(e)}")
            return None
    
    def extract_text_from_html(self, html_content: str) -> str:
        """
        Extract readable text from HTML content
        
        Args:
            html_content: HTML content
            
        Returns:
            Extracted text
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean up whitespace
        text = soup.get_text(separator=' ')
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)
        
        return text
    
    def extract_title(self, html_content: str) -> str:
        """
        Extract title from HTML content
        
        Args:
            html_content: HTML content
            
        Returns:
            Page title
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
        return "No title found"
    
    def extract_metadata(self, html_content: str) -> Dict[str, str]:
        """
        Extract metadata from HTML content
        
        Args:
            html_content: HTML content
            
        Returns:
            Dictionary of metadata
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        metadata = {}
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            name = meta.get('name')
            property = meta.get('property')
            content = meta.get('content')
            
            if name and content:
                metadata[name] = content
            elif property and content:
                metadata[property] = content
        
        return metadata
    
    def scrape_page(self, url: str) -> Optional[WebPage]:
        """
        Scrape a web page
        
        Args:
            url: URL to scrape
            
        Returns:
            WebPage object or None if failed
        """
        response = self.fetch_url(url)
        if not response:
            return None
        
        html_content = response.text
        text_content = self.extract_text_from_html(html_content)
        title = self.extract_title(html_content)
        metadata = self.extract_metadata(html_content)
        timestamp = datetime.now().isoformat()
        
        return WebPage(
            url=url,
            title=title,
            text_content=text_content,
            html_content=html_content,
            metadata=metadata,
            timestamp=timestamp
        )
    
    def save_scraped_page(self, agent_id: str, workspace_id: str, page: WebPage) -> Dict[str, str]:
        """
        Save a scraped page to the workspace
        
        Args:
            agent_id: The ID of the agent (for permissions)
            workspace_id: ID of the workspace (Note: FileSystemService uses agent_id for base path)
            page: WebPage object
            
        Returns:
            Dictionary with paths to saved files
        """
        # Generate a filename from the page title relative path for FileSystemService
        safe_title = re.sub(r'[^\w\s-]', '', page.title).strip().lower()
        safe_title = re.sub(r'[-\s]+', '-', safe_title)
        # Ensure workspace_id (agent_id) is part of the path if needed, 
        # but FileSystemService prepends agent_id automatically based on its base_path logic.
        # We need a relative path *within* the agent's implicit workspace.
        relative_base_filename = os.path.join(workspace_id, f"{safe_title}_{int(time.time())}") # Construct path relative to agent base

        # Save the text content using write_file
        text_filename = f"{relative_base_filename}.txt"
        # Note: write_file prepends the base path + agent_id internally
        self.fs.write_file(
            agent_id, 
            text_filename, 
            page.text_content
        )
        
        # Save the HTML content using write_file
        html_filename = f"{relative_base_filename}.html"
        self.fs.write_file(
            agent_id, 
            html_filename, 
            page.html_content
        )
        
        # Save metadata using write_file
        metadata = {
            "url": page.url,
            "title": page.title,
            "timestamp": page.timestamp,
            "metadata": page.metadata
        }
        metadata_filename = f"{relative_base_filename}.json"
        self.fs.write_file(
            agent_id,
            metadata_filename,
            json.dumps(metadata, indent=2) # Convert dict to JSON string
        )
        
        # Return relative paths for reference
        return {
            "text_path": text_filename,
            "html_path": html_filename,
            "metadata_path": metadata_filename,
            "base_filename": os.path.basename(relative_base_filename) # Just the filename part
        }
    
    def scrape_and_save(self, agent_id: str, url: str) -> Optional[Dict[str, str]]:
        """
        Scrape a URL and save the content to the agent's workspace
        
        Args:
            agent_id: ID of the agent performing the action
            url: URL to scrape
            
        Returns:
            Dictionary with file paths if successful, None otherwise
        """
        page = self.scrape_page(url)
        if not page:
            return None
        
        # Pass agent_id, using agent_id also as the relative directory name within base_path
        return self.save_scraped_page(agent_id, agent_id, page)

    def crawl_and_scrape(self, agent_id: str, start_url: str, max_pages: int = 10, allowed_prefix: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Crawls a website starting from a URL, scrapes pages, and saves them.

        Args:
            agent_id: ID of the agent performing the action.
            start_url: The initial URL to start crawling from.
            max_pages: Maximum number of pages to scrape.
            allowed_prefix: If set, only URLs starting with this prefix will be followed and scraped.

        Returns:
            A list of dictionaries, where each dictionary contains the paths to the saved files for a scraped page.
        """
        logger.info(f"Agent '{agent_id}' starting crawl from '{start_url}'. Max pages: {max_pages}, Prefix: '{allowed_prefix}'")
        
        queue = deque([(start_url, 0)]) # Queue of (url, depth)
        visited_urls = set()
        scraped_page_results = []
        scraped_count = 0

        # Ensure prefix ends with / if provided, for accurate startswith check
        normalized_prefix = None
        if allowed_prefix:
            normalized_prefix = allowed_prefix if allowed_prefix.endswith('/') else allowed_prefix + '/'
        
        # Check if start_url is valid according to the prefix
        if normalized_prefix:
            # Allow if start_url starts with the prefix OR if start_url exactly matches the prefix base
            start_url_normalized = start_url if start_url.endswith('/') else start_url + '/'
            prefix_base = normalized_prefix.rstrip('/')
            
            if not start_url_normalized.startswith(normalized_prefix) and start_url != prefix_base:
                logger.warning(f"Start URL '{start_url}' does not match allowed prefix '{allowed_prefix}' (normalized: '{normalized_prefix}'). Aborting crawl.")
                return []

        while queue and scraped_count < max_pages:
            current_url, depth = queue.popleft()

            if current_url in visited_urls:
                continue

            # Optional: Add depth limit if needed (e.g., if depth >= max_depth: continue)

            logger.info(f"Crawling [D:{depth}, {scraped_count+1}/{max_pages}]: {current_url}")
            visited_urls.add(current_url)

            page = self.scrape_page(current_url)
            if page:
                # Save the scraped page
                try:
                    save_result = self.save_scraped_page(agent_id, agent_id, page)
                    scraped_page_results.append(save_result)
                    scraped_count += 1
                    logger.info(f"Successfully scraped and saved: {current_url}")
                except Exception as save_e:
                    logger.error(f"Failed to save page {current_url} for agent {agent_id}: {save_e}")
                    # Optionally continue crawling even if saving fails for one page

                # Extract and enqueue new links
                soup = BeautifulSoup(page.html_content, 'html.parser')
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    # Create absolute URL
                    absolute_url = urljoin(current_url, href)
                    
                    # Basic filtering (ignore fragments, ensure http/https)
                    parsed_url = urlparse(absolute_url)
                    if parsed_url.fragment or parsed_url.scheme not in ['http', 'https']:
                        continue
                        
                    # Check against allowed prefix
                    if allowed_prefix and not absolute_url.startswith(allowed_prefix):
                        # logger.debug(f"Skipping URL (prefix mismatch): {absolute_url}")
                        continue

                    if absolute_url not in visited_urls and scraped_count + len(queue) < max_pages * 2 : # Avoid overly large queue
                        # Add new valid URL to the queue
                        queue.append((absolute_url, depth + 1))
            else:
                logger.warning(f"Failed to scrape page: {current_url}")

            # --- Be polite --- 
            time.sleep(0.5) # Add a delay between requests

        logger.info(f"Crawl finished for agent '{agent_id}'. Scraped {scraped_count} pages.")
        return scraped_page_results

    def get_weather_data(self, location: str, units: str = 'metric') -> Dict[str, Any]:
        """
        Fetches current weather data for a given location using OpenWeatherMap API.

        Args:
            location: The city name (e.g., "London", "London,UK").
            units: Units for temperature ('metric' for Celsius, 'imperial' for Fahrenheit).

        Returns:
            A dictionary containing weather data or an error message.
        """
        api_key = os.environ.get("OPENWEATHERMAP_API_KEY")
        if not api_key:
            logging.error("OPENWEATHERMAP_API_KEY environment variable not set.")
            return {"error": "Weather API key not configured."}

        base_url = "http://api.openweathermap.org/data/2.5/weather"
        params = {
            "q": location,
            "appid": api_key,
            "units": units,
        }

        try:
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

            data = response.json()

            if data.get("cod") != 200:
                logging.error(f"OpenWeatherMap API error for {location}: {data.get('message')}")
                return {"error": f"Could not fetch weather data for {location}. Reason: {data.get('message', 'Unknown API error')}"}

            # Extract relevant information
            main_weather = data.get('weather', [{}])[0].get('main', 'N/A')
            description = data.get('weather', [{}])[0].get('description', 'N/A')
            temp = data.get('main', {}).get('temp', 'N/A')
            feels_like = data.get('main', {}).get('feels_like', 'N/A')
            humidity = data.get('main', {}).get('humidity', 'N/A')
            wind_speed = data.get('wind', {}).get('speed', 'N/A')
            city_name = data.get('name', location)
            country = data.get('sys', {}).get('country', '')

            temp_unit = "°C" if units == 'metric' else "°F"

            result = {
                "location": f"{city_name}, {country}",
                "temperature": f"{temp}{temp_unit}",
                "feels_like": f"{feels_like}{temp_unit}",
                "humidity": f"{humidity}%",
                "condition": main_weather,
                "description": description.capitalize(),
                "wind_speed": f"{wind_speed} m/s" # API default is m/s regardless of units param
            }
            logging.info(f"Successfully fetched weather for {location}: {result}")
            return result

        except requests.exceptions.RequestException as e:
            logging.error(f"Network error fetching weather for {location}: {e}")
            return {"error": f"Network error fetching weather: {e}"}
        except Exception as e:
            logging.exception(f"Unexpected error fetching weather for {location}: {e}")
            return {"error": f"An unexpected error occurred: {e}"}


class RAGRetrieverTool:
    """Tool for retrieving information from stored documents"""
    
    def __init__(self, file_system_service: FileSystemService = None):
        """
        Initialize the RAG retriever tool
        
        Args:
            file_system_service: Service for file management
        """
        self.fs = file_system_service or FileSystemService()
        self.genai_client = genai_client
        self.embedding_model = "gemini-embedding-exp-03-07"
        
        logger.info("RAGRetrieverTool initialized")
    
    def _split_text_into_chunks(self, text: str, max_chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to split
            max_chunk_size: Maximum size of each chunk
            overlap: Overlap between chunks
            
        Returns:
            List of text chunks
        """
        # Simple splitting by paragraphs first
        paragraphs = [p for p in text.split('\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            if len(current_chunk) + len(paragraph) < max_chunk_size:
                current_chunk += paragraph + "\n"
            else:
                # If the current chunk is not empty, add it to chunks
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # Start a new chunk
                current_chunk = paragraph + "\n"
        
        # Add the last chunk if not empty
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        # Apply overlap between chunks
        overlapped_chunks = []
        for i, chunk in enumerate(chunks):
            if i > 0:
                # Add the end of the previous chunk to the current chunk
                prev_chunk = chunks[i-1]
                overlap_text = prev_chunk[-overlap:] if len(prev_chunk) > overlap else prev_chunk
                chunks[i] = overlap_text + "\n" + chunks[i]
            
            overlapped_chunks.append(chunks[i])
        
        return overlapped_chunks
    
    def _get_document_chunks(self, workspace_id: str, filename: str) -> List[Dict[str, Any]]:
        """
        Get chunks from a document
        
        Args:
            workspace_id: ID of the workspace
            filename: Name of the file
            
        Returns:
            List of dictionaries with chunk text and metadata
        """
        try:
            text_content = self.fs.read_text_file(workspace_id, filename)
            
            # Get metadata if available
            metadata = {}
            metadata_filename = filename.replace('.txt', '.json')
            if metadata_filename in self.fs.list_files(workspace_id):
                try:
                    metadata = self.fs.read_json_file(workspace_id, metadata_filename)
                except Exception as e:
                    logger.warning(f"Error reading metadata for {filename}: {str(e)}")
            
            # Split text into chunks
            text_chunks = self._split_text_into_chunks(text_content)
            
            # Create chunk objects
            chunks = []
            for i, chunk_text in enumerate(text_chunks):
                chunks.append({
                    "text": chunk_text,
                    "metadata": metadata,
                    "source": filename,
                    "chunk_id": i
                })
            
            return chunks
        
        except Exception as e:
            logger.error(f"Error processing document {filename}: {str(e)}")
            return []
    
    def search_by_keywords(self, workspace_id: str, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search documents by keywords
        
        Args:
            workspace_id: ID of the workspace
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results
        """
        # Get all text files
        txt_files = [f for f in self.fs.list_files(workspace_id) if f.endswith('.txt')]
        if not txt_files:
            return []
        
        # Prepare keywords
        keywords = query.lower().split()
        
        all_results = []
        
        # Search in each file
        for filename in txt_files:
            chunks = self._get_document_chunks(workspace_id, filename)
            
            for chunk in chunks:
                chunk_text = chunk["text"].lower()
                
                # Calculate a simple relevance score based on keyword frequency
                score = sum(1 for keyword in keywords if keyword in chunk_text)
                
                if score > 0:
                    result = {
                        "text": chunk["text"],
                        "metadata": chunk.get("metadata", {}),
                        "source": chunk["source"],
                        "score": score,
                        "chunk_id": chunk.get("chunk_id")
                    }
                    all_results.append(result)
        
        # Sort by score and limit results
        sorted_results = sorted(all_results, key=lambda x: x["score"], reverse=True)
        return sorted_results[:max_results]
    
    def search_by_semantic(self, workspace_id: str, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search documents by semantic similarity
        
        Args:
            workspace_id: ID of the workspace
            query: Search query
            max_results: Maximum number of results to return
            
        Returns:
            List of search results
        """
        if not SEMANTIC_SEARCH_AVAILABLE or not self.genai_client:
            logger.warning("Semantic search unavailable, falling back to keyword search")
            return self.search_by_keywords(workspace_id, query, max_results)
        
        # Get all text files
        txt_files = [f for f in self.fs.list_files(workspace_id) if f.endswith('.txt')]
        if not txt_files:
            return []
        
        # Encode query
        query_embedding = self.genai_client.models.embed_content(
            model=self.embedding_model,
            contents=query
        ).embeddings
        
        all_chunks = []
        chunk_texts = []
        
        # Collect chunks from all files
        for filename in txt_files:
            chunks = self._get_document_chunks(workspace_id, filename)
            all_chunks.extend(chunks)
            chunk_texts.extend([chunk["text"] for chunk in chunks])
        
        if not chunk_texts:
            return []
        
        # Generate embeddings for all chunks
        try:
            chunk_embeddings = self.genai_client.models.embed_content(
                model=self.embedding_model,
                contents=chunk_texts
            ).embeddings
            
            # Calculate similarity
            similarities = cosine_similarity([query_embedding], chunk_embeddings)[0]
            
            # Add similarity scores to results
            results = []
            for i, chunk in enumerate(all_chunks):
                if similarities[i] > 0.3:  # Threshold for relevant results
                    results.append({
                        "text": chunk["text"],
                        "metadata": chunk.get("metadata", {}),
                        "source": chunk["source"],
                        "score": float(similarities[i]),
                        "chunk_id": chunk.get("chunk_id")
                    })
            
            # Sort by score and limit results
            sorted_results = sorted(results, key=lambda x: x["score"], reverse=True)
            return sorted_results[:max_results]
            
        except Exception as e:
            logger.error(f"Error in semantic search: {str(e)}")
            return self.search_by_keywords(workspace_id, query, max_results)
    
    def search(self, workspace_id: str, query: str, use_semantic: bool = True, max_results: int = 5) -> List[Dict[str, Any]]:
        """
        Search for information in the workspace
        
        Args:
            workspace_id: ID of the workspace
            query: Search query
            use_semantic: Whether to use semantic search if available
            max_results: Maximum number of results to return
            
        Returns:
            List of search results
        """
        if use_semantic and SEMANTIC_SEARCH_AVAILABLE and self.genai_client:
            return self.search_by_semantic(workspace_id, query, max_results)
        else:
            return self.search_by_keywords(workspace_id, query, max_results)
    
    def format_results_as_context(self, results: List[Dict[str, Any]]) -> str:
        """
        Format search results as context for an LLM
        
        Args:
            results: Search results
            
        Returns:
            Formatted context
        """
        if not results:
            return "No relevant information found."
        
        context = "Here is the relevant information:\n\n"
        
        for i, result in enumerate(results, 1):
            source = result.get("source", "Unknown source")
            url = result.get("metadata", {}).get("url", "")
            title = result.get("metadata", {}).get("title", source)
            
            context += f"[{i}] From: {title}\n"
            if url:
                context += f"Source: {url}\n"
            context += f"Content: {result['text']}\n\n"
        
        return context


class RAGSystem:
    """
    Complete RAG system combining web scraping and retrieval
    """
    
    def __init__(self, base_path: str = "agent_workspaces"):
        """
        Initialize the RAG system
        
        Args:   
            base_path: The base directory for agent workspaces
        """
        self.fs_service = FileSystemService(base_path=base_path)
        self.scraper = WebScraperTool(self.fs_service)
        self.retriever = RAGRetrieverTool(self.fs_service)
        logger.info("RAGSystem initialized")
    
    def create_workspace(self, workspace_id: str = None) -> str:
        """
        Create a new workspace
        
        Args:
            workspace_id: Optional ID for the workspace
            
        Returns:
            ID of the created workspace
        """
        workspace_path = self.fs_service.create_workspace(workspace_id)
        return os.path.basename(workspace_path)
    
    def scrape_url(self, workspace_id: str, url: str) -> Dict[str, Any]:
        """
        Scrape a URL and store its content
        
        Args:
            workspace_id: ID of the workspace
            url: URL to scrape
            
        Returns:
            Information about the scraped content
        """
        result = self.scraper.scrape_and_save(workspace_id, url)
        if not result:
            return {"status": "error", "message": f"Failed to scrape URL: {url}"}
        
        return {
            "status": "success",
            "url": url,
            "files": result
        }
    
    def scrape_multiple_urls(self, workspace_id: str, urls: List[str]) -> List[Dict[str, Any]]:
        """
        Scrape multiple URLs
        
        Args:
            workspace_id: ID of the workspace
            urls: List of URLs to scrape
            
        Returns:
            List of results for each URL
        """
        results = []
        for url in urls:
            result = self.scrape_url(workspace_id, url)
            results.append(result)
            # Add a small delay to avoid overwhelming the server
            time.sleep(0.5)
        
        return results
    
    def retrieve_information(self, workspace_id: str, query: str, use_semantic: bool = True, max_results: int = 5) -> Dict[str, Any]:
        """
        Retrieve information based on a query
        
        Args:
            workspace_id: ID of the workspace
            query: Search query
            use_semantic: Whether to use semantic search
            max_results: Maximum number of results
            
        Returns:
            Retrieved information
        """
        results = self.retriever.search(workspace_id, query, use_semantic, max_results)
        
        if not results:
            return {
                "status": "no_results",
                "message": "No relevant information found for the query.",
                "results": []
            }
        
        # Format the results
        formatted_context = self.retriever.format_results_as_context(results)
        
        return {
            "status": "success",
            "result_count": len(results),
            "results": results,
            "formatted_context": formatted_context
        }
    
    def list_workspace_files(self, workspace_id: str) -> Dict[str, Any]:
        """
        List files in a workspace
        
        Args:
            workspace_id: ID of the workspace
            
        Returns:
            Information about the files
        """
        files = self.fs_service.list_files(workspace_id)
        
        # Group files by their base name
        file_groups = {}
        for file in files:
            base_name = os.path.splitext(file)[0]
            if "." in base_name:
                parts = base_name.split(".")
                if parts[-1].isdigit():  # This is likely a timestamp
                    base_name = ".".join(parts[:-1])
            
            if base_name not in file_groups:
                file_groups[base_name] = []
            
            file_groups[base_name].append(file)
        
        return {
            "status": "success",
            "workspace_id": workspace_id,
            "file_count": len(files),
            "files": files,
            "file_groups": file_groups
        }
    
    def delete_workspace(self, workspace_id: str) -> Dict[str, Any]:
        """
        Delete a workspace
        
        Args:
            workspace_id: ID of the workspace
            
        Returns:
            Status of the operation
        """
        success = self.fs_service.delete_workspace(workspace_id)
        
        if success:
            return {
                "status": "success",
                "message": f"Workspace {workspace_id} deleted successfully"
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to delete workspace {workspace_id}"
            }