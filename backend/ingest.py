#!/usr/bin/env python3
"""
Text extraction and vector loading for the Physical AI and Humanoid Robotics book.
Extracts content from https://agreeable-sand-0efbb301e.4.azurestaticapps.net/ and loads into Qdrant.
"""

import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urljoin, urlparse

from dotenv import load_dotenv

# Get the directory where ingest.py is located
base_dir = Path(__file__).resolve().parent
env_path = base_dir / ".env"

# Explicitly load the .env file from the backend folder
load_dotenv(dotenv_path=env_path)

# Verify they are loaded (Add these print statements for debugging)
print(f"Loading .env from: {env_path}")
print(f"COHERE_API_KEY found: {'Yes' if os.getenv('COHERE_API_KEY') else 'No'}")
import cohere
import requests
from bs4 import BeautifulSoup
from qdrant_client import QdrantClient
from qdrant_client.http import models


class WebExtractor:
    """Extracts content from the target website."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
        )

    def get_page_content(self, url: str) -> str:
        """Fetch HTML content from a URL."""
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            logging.error(f"Failed to fetch {url}: {e}")
            return ""

    def extract_all_pages(self) -> List[Dict[str, Any]]:
        """Extract content from all pages on the site by crawling."""
        visited = set()
        pages = []
        urls_to_visit = [self.base_url]

        while urls_to_visit:
            current_url = urls_to_visit.pop(0)

            # Skip if already visited
            if current_url in visited:
                continue

            visited.add(current_url)
            logging.info(f"Processing: {current_url}")

            content = self.get_page_content(current_url)
            if not content:
                continue

            soup = BeautifulSoup(content, "html.parser")

            # Extract content from the <article> tag (Docusaurus standard)
            article_content = soup.find('article')
            if article_content:
                # Get text from article tag specifically
                text_content = article_content.get_text(separator=" ", strip=True)
                html_content = str(article_content)
            else:
                # Fallback to full content if no article tag found
                # Remove script and style elements
                for script in soup(["script", "style"]):
                    script.decompose()
                text_content = soup.get_text(separator=" ", strip=True)
                html_content = str(soup)

            # Add the page data
            pages.append({
                "url": current_url,
                "title": soup.title.string.strip()
                if soup.title and soup.title.string
                else "No Title",
                "content": text_content,
                "html": html_content,
            })

            # Find all links on the page that start with /docs/ or are within the same domain
            from urllib.parse import urljoin, urlparse
            base_domain = f"{urlparse(self.base_url).scheme}://{urlparse(self.base_url).netloc}"
            links = soup.find_all('a', href=True)

            # Also look for Docusaurus sidebar/navigation links
            sidebar_selectors = ['nav', '.sidebar', '[role="navigation"]', '.menu__link', '.nav-link']
            for selector in sidebar_selectors:
                sidebar_elements = soup.select(selector)
                for elem in sidebar_elements:
                    for link in elem.find_all('a', href=True):
                        if link['href']:
                            links.append(link)

            for link in links:
                href = link.get('href', '')

                # Skip external links, empty hrefs, and anchor-only links
                if not href or href.startswith('#') or href.startswith('mailto:') or href.startswith('tel:') or href.startswith('http://') or href.startswith('https://'):
                    continue

                # Convert relative URLs to absolute URLs
                absolute_url = urljoin(current_url, href)

                # Only follow links within the same domain
                if absolute_url.startswith(base_domain):
                    # Get the path portion
                    path = urlparse(absolute_url).path

                    # Follow all internal links but skip API and static asset paths
                    excluded_patterns = ['/api/', '.json', '.xml', '.css', '.js', '.ico', '.png', '.jpg', '.svg', '.woff']
                    should_skip = any(pattern in absolute_url.lower() for pattern in excluded_patterns)

                    if not should_skip and absolute_url not in visited:
                        urls_to_visit.append(absolute_url)

            # Add small delay to avoid being blocked by Azure
            import time
            time.sleep(0.5)

        return pages


class ContentParser:
    """Parses HTML content and extracts structured text."""

    def parse_content(self, html: str, url: str) -> List[Dict[str, Any]]:
        """Parse HTML and extract content by headers."""
        soup = BeautifulSoup(html, "html.parser")

        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Find all headers (h1, h2, h3)
        headers = soup.find_all(["h1", "h2", "h3"])

        chunks = []

        if not headers:
            # If no headers found, use the entire content as one chunk
            text_content = soup.get_text(separator=" ", strip=True)
            if text_content:
                chunks.append(
                    {
                        "url": url,
                        "header": "Main Content",
                        "content": text_content,
                        "header_type": "none",
                    }
                )
        else:
            # Process content under each header
            for i, header in enumerate(headers):
                header_text = header.get_text(strip=True)
                header_type = header.name

                # Find the next header to determine content boundaries
                next_header = None
                if i + 1 < len(headers):
                    next_header = headers[i + 1]

                # Get content between this header and the next
                content_elements = []
                current = header.next_sibling

                while current:
                    if current == next_header:
                        break
                    if hasattr(current, "name") and current.name in ["h1", "h2", "h3"]:
                        break
                    if hasattr(current, "get_text"):
                        content_elements.append(
                            current.get_text(separator=" ", strip=True)
                        )
                    elif isinstance(current, str) and current.strip():
                        content_elements.append(current.strip())
                    current = current.next_sibling

                content = " ".join(content_elements).strip()

                # Combine header text with content
                full_content = f"{header_text} {content}".strip()

                if full_content:
                    chunks.append(
                        {
                            "url": url,
                            "header": header_text,
                            "content": full_content,
                            "header_type": header_type,
                        }
                    )

        return chunks


class Chunker:
    """Chunks content based on header hierarchy."""

    def chunk_content(self, pages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process pages and create content chunks."""
        all_chunks = []

        for page in pages:
            parser = ContentParser()
            chunks = parser.parse_content(page.get("html", ""), page.get("url", ""))
            all_chunks.extend(chunks)

        return all_chunks


class EmbeddingService:
    """Generates embeddings using Cohere API."""

    def __init__(self, api_key: str):
        self.client = cohere.Client(api_key)
        self.model = "embed-english-v3.0"  # Using model that produces 1024-dim vectors to match existing collection

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        # The issue is that Cohere API has changed and there's a version/model compatibility issue
        # Let's try the approach that handles the API differences properly

        # First, try with input_type as this is required for v3.0 model
        try:
            response = self.client.embed(
                model=self.model,
                texts=texts,
                input_type="search_document"
            )
            return response.embeddings
        except TypeError as e:
            if "input_type" in str(e):
                # The parameter is not accepted in this version of the library
                # This suggests we need to use the older API approach
                logging.warning(f"input_type parameter not supported: {e}")

                # For Cohere versions that don't support input_type as parameter,
                # we may need to use embed_jobs (async approach) or different model
                try:
                    # Try with a model that might not require input_type
                    response = self.client.embed(
                        model="small",  # Try a simpler model name
                        texts=texts
                    )
                    self.model = "small"
                    return response.embeddings
                except Exception:
                    # If that doesn't work, let's try to see if we can call embed with different parameters
                    try:
                        # Try the original model without input_type (will likely fail for v3.0 but worth trying)
                        response = self.client.embed(texts=texts, model=self.model)
                        return response.embeddings
                    except Exception:
                        logging.error("All embedding attempts failed")
                        return [[] for _ in texts]
            else:
                logging.error(f"Unexpected TypeError: {e}")
                return [[] for _ in texts]
        except Exception as e:
            # Handle the case where input_type is required but not provided properly
            if "input_type must be provided" in str(e):
                logging.error(f"Model {self.model} requires input_type but API format is incompatible: {e}")

                # Try with a different model that might be compatible with our library version
                fallback_models = ["small", "medium", "large", "embed-english-v2.0"]

                for fallback_model in fallback_models:
                    try:
                        logging.info(f"Trying fallback model: {fallback_model}")
                        response = self.client.embed(
                            model=fallback_model,
                            texts=texts
                        )
                        self.model = fallback_model
                        logging.info(f"Successfully used fallback model: {self.model}")
                        return response.embeddings
                    except Exception as fallback_error:
                        logging.warning(f"Fallback model {fallback_model} failed: {fallback_error}")
                        continue

                logging.error("All fallback models failed")
                return [[] for _ in texts]
            else:
                logging.error(f"Unexpected error during embedding: {e}")
                return [[] for _ in texts]


class VectorStore:
    """Manages storage in Qdrant."""

    def __init__(
        self, url: str, api_key: str, collection_name: str = "humanoid_robotics_docs"
    ):
        self.client = QdrantClient(url=url, api_key=api_key, prefer_grpc=False)
        self.collection_name = collection_name

    def create_collection(self):
        """Create the collection if it doesn't exist."""
        try:
            # Check if collection exists
            collection_info = self.client.get_collection(self.collection_name)
            print(f"Collection '{self.collection_name}' already exists.")
            # Note: We're not recreating the collection to avoid dimension mismatch
            # If you need to change dimensions, you'd need to delete and recreate the collection
        except Exception as e:
            # Collection doesn't exist, create it
            print(f"Collection '{self.collection_name}' does not exist. Creating it...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=1024,  # Cohere embed-english-v3.0 produces 1024-dim vectors
                    distance=models.Distance.COSINE,
                ),
            )
            print(f"Collection '{self.collection_name}' created successfully.")

    def store_chunks(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]]):
        """Store chunks with embeddings in Qdrant using batching to prevent timeouts."""
        points = []

        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            if not embedding:  # Skip chunks that failed to embed
                continue

            point = models.PointStruct(
                id=i,
                vector=embedding,
                payload={
                    "url": chunk["url"],
                    "header": chunk["header"],
                    "content": chunk["content"][:10000],  # Limit content size
                    "header_type": chunk["header_type"],
                    "module": "humanoid_robotics",
                    "content_type": "documentation",
                },
            )
            points.append(point)

        if points:
            # Batch upsert to prevent timeouts - Qdrant performs better with smaller batches
            batch_size = 20  # As specified in requirements to prevent timeouts
            for i in range(0, len(points), batch_size):
                batch = points[i : i + batch_size]
                self.client.upsert(collection_name=self.collection_name, points=batch)

                # Add small delay between batches to prevent overwhelming Qdrant
                time.sleep(0.5)

                logging.info(f"Upserted batch of {len(batch)} points, batch {(i // batch_size) + 1}/{(len(points) - 1) // batch_size + 1}")


def main():
    """Main ingestion pipeline."""
    logging.basicConfig(level=logging.INFO)

    # Configuration - in a real app, these would come from environment variables
    BASE_URL = os.getenv(
        "BASE_URL", "https://agreeable-sand-0efbb301e.4.azurestaticapps.net/"
    )
    COHERE_API_KEY = os.getenv("COHERE_API_KEY")
    QDRANT_URL = os.getenv("QDRANT_URL")
    QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

    if not all([COHERE_API_KEY, QDRANT_URL, QDRANT_API_KEY]):
        raise ValueError(
            "Missing required environment variables: COHERE_API_KEY, QDRANT_URL, QDRANT_API_KEY"
        )

    # Initialize components
    extractor = WebExtractor(BASE_URL)
    chunker = Chunker()
    embedding_service = EmbeddingService(COHERE_API_KEY)
    vector_store = VectorStore(QDRANT_URL, QDRANT_API_KEY)

    logging.info("Starting content extraction...")
    pages = extractor.extract_all_pages()

    if not pages:
        logging.error("No pages extracted, exiting.")
        return

    logging.info(f"Extracted {len(pages)} pages")

    logging.info("Chunking content...")
    chunks = chunker.chunk_content(pages)
    logging.info(f"Created {len(chunks)} content chunks")

    # Prepare texts for embedding (limit the number to avoid rate limits)
    texts = [chunk["content"] for chunk in chunks]

    # Batch process to avoid rate limits
    batch_size = 96  # Cohere's max batch size is 96
    all_embeddings = []

    logging.info("Generating embeddings...")
    for i in range(0, len(texts), batch_size):
        batch_texts = texts[i : i + batch_size]
        batch_embeddings = embedding_service.generate_embeddings(batch_texts)
        all_embeddings.extend(batch_embeddings)

        # Add a small delay to respect rate limits
        time.sleep(1)

        logging.info(f"Processed embedding batch {(i // batch_size) + 1}/{(len(texts) - 1) // batch_size + 1}, batch size: {len(batch_texts)}")

    logging.info("Creating Qdrant collection...")
    vector_store.create_collection()

    # Print total chunks before sending to Qdrant
    print(f"Total chunks to be stored in Qdrant: {len(chunks)}")
    logging.info("Storing embeddings in Qdrant...")
    vector_store.store_chunks(chunks, all_embeddings)

    logging.info(f"Ingestion pipeline completed successfully! Stored {len([e for e in all_embeddings if e])} embeddings for {len(chunks)} content chunks.")


if __name__ == "__main__":
    main()
