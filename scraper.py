"""
RMIT Policy Scraper
===================
Automatically scrapes policies from https://policies.rmit.edu.au/
and converts them to the JSON format required by the chatbot.

Usage:
    from scraper import scrape_all_policies
    scrape_all_policies()
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
from datetime import datetime
from typing import List, Dict, Any
import re

# Configuration
BASE_URL = "https://policies.rmit.edu.au"
BROWSE_URL = f"{BASE_URL}/browse.php"
OUTPUT_DIR = "./data/policies"

def get_all_policy_links() -> List[str]:
    """
    Scrape the browse page to get all policy document links.
    
    Returns:
        List of policy document URLs
    """
    print(f"🔍 Fetching policy links from {BROWSE_URL}...")
    
    try:
        response = requests.get(BROWSE_URL, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Error fetching browse page: {e}")
        return []
    
    soup = BeautifulSoup(response.content, 'html.parser')
    policy_links = []
    
    # Find all links that point to policy documents
    for link in soup.find_all('a', href=True):
        href = link['href']
        
        # Look for document view links
        if 'document/view' in href or 'view.php' in href:
            # Make absolute URL
            if href.startswith('http'):
                full_url = href
            elif href.startswith('/'):
                full_url = f"{BASE_URL}{href}"
            else:
                full_url = f"{BASE_URL}/{href}"
            
            policy_links.append(full_url)
    
    # Remove duplicates
    policy_links = list(set(policy_links))
    print(f"✓ Found {len(policy_links)} policy documents")
    
    return policy_links


def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    if not text:
        return ""
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    # Remove common artifacts
    text = text.replace('\xa0', ' ')
    text = text.replace('\u200b', '')
    
    return text


def extract_clauses_from_list(ol_element) -> List[Dict[str, Any]]:
    """Extract numbered clauses from an ordered list."""
    clauses = []
    
    for i, li in enumerate(ol_element.find_all('li', recursive=False)):
        text = clean_text(li.get_text())
        
        if len(text) < 20:  # Skip very short items
            continue
        
        # Check for subclauses (nested lists)
        subclauses = []
        nested_list = li.find(['ol', 'ul'])
        if nested_list:
            for sub_li in nested_list.find_all('li'):
                sub_text = clean_text(sub_li.get_text())
                if len(sub_text) >= 20:
                    subclauses.append(sub_text)
        
        clauses.append({
            "clause_number": str(i + 1),
            "text": text,
            "subclauses": subclauses
        })
    
    return clauses


def scrape_policy_document(url: str) -> Dict[str, Any]:
    """
    Scrape an individual policy document and convert to JSON format.
    
    Args:
        url: URL of the policy document
        
    Returns:
        Dictionary in the chatbot's expected JSON format
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  ❌ Error fetching {url}: {e}")
        return None
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract metadata
    title = "Unknown Policy"
    title_elem = soup.find('h1')
    if title_elem:
        title = clean_text(title_elem.get_text())
    
    # Try to find approval/review dates
    approval_date = ""
    review_date = ""
    date_pattern = r'\d{1,2}[-/]\d{1,2}[-/]\d{4}'
    
    for text in soup.stripped_strings:
        if 'approval date' in text.lower() or 'approved' in text.lower():
            match = re.search(date_pattern, text)
            if match:
                approval_date = match.group()
        if 'review date' in text.lower() or 'reviewed' in text.lower():
            match = re.search(date_pattern, text)
            if match:
                review_date = match.group()
    
    # Extract content sections
    sections = []
    
    # Find main content area (adjust selectors based on actual page structure)
    content_area = soup.find('div', class_='content') or soup.find('main') or soup.body
    
    if content_area:
        # Look for section headings (h2, h3)
        for heading in content_area.find_all(['h2', 'h3']):
            section_title = clean_text(heading.get_text())
            
            if not section_title or len(section_title) < 3:
                continue
            
            clauses = []
            
            # Collect content until next heading
            for sibling in heading.find_next_siblings():
                # Stop at next heading of same or higher level
                if sibling.name in ['h2', 'h3'] and sibling != heading:
                    break
                
                # Extract clauses from ordered lists
                if sibling.name == 'ol':
                    clauses.extend(extract_clauses_from_list(sibling))
                
                # Extract clauses from paragraphs
                elif sibling.name == 'p':
                    text = clean_text(sibling.get_text())
                    if len(text) >= 20:
                        clauses.append({
                            "clause_number": str(len(clauses) + 1),
                            "text": text,
                            "subclauses": []
                        })
            
            # Only add section if it has clauses
            if clauses:
                sections.append({
                    "section_title": section_title,
                    "clauses": clauses
                })
    
    # Build final JSON structure
    policy_json = {
        "metadata": {
            "title": title,
            "approval_date": approval_date,
            "review_date": review_date or datetime.now().strftime("%Y-%m-%d"),
            "source_path": url,
            "scraped_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "structure": [
            {
                "part_title": "Main Content",
                "sections": sections
            }
        ],
        "qa_index": []
    }
    
    return policy_json


def save_policy_json(policy: Dict[str, Any], output_dir: str = OUTPUT_DIR) -> str:
    """
    Save policy JSON to file.
    
    Args:
        policy: Policy dictionary
        output_dir: Directory to save files
        
    Returns:
        Filepath of saved JSON
    """
    os.makedirs(output_dir, exist_ok=True)
    
    # Create filename from title
    title = policy['metadata']['title']
    filename = re.sub(r'[^\w\s-]', '', title)  # Remove special chars
    filename = re.sub(r'[-\s]+', '_', filename)  # Replace spaces/hyphens with underscore
    filename = filename[:80]  # Limit length
    filename = f"{filename}.json"
    
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(policy, f, indent=2, ensure_ascii=False)
    
    return filepath


def scrape_all_policies(output_dir: str = OUTPUT_DIR, max_policies: int = None) -> Dict[str, Any]:
    """
    Scrape all policies from RMIT policies website.
    
    Args:
        output_dir: Directory to save JSON files
        max_policies: Maximum number of policies to scrape (None = all)
        
    Returns:
        Dictionary with scraping statistics
    """
    print("=" * 60)
    print("🚀 RMIT Policy Scraper")
    print("=" * 60)
    
    # Get all policy links
    policy_links = get_all_policy_links()
    
    if not policy_links:
        print("❌ No policy links found")
        return {"success": 0, "failed": 0, "total": 0}
    
    # Limit number if specified
    if max_policies:
        policy_links = policy_links[:max_policies]
    
    print(f"\n📥 Scraping {len(policy_links)} policies...\n")
    
    success_count = 0
    failed_count = 0
    
    for i, url in enumerate(policy_links, 1):
        print(f"[{i}/{len(policy_links)}] Scraping: {url}")
        
        try:
            # Scrape the policy
            policy = scrape_policy_document(url)
            
            if policy and policy['structure'][0]['sections']:
                # Save to file
                filepath = save_policy_json(policy, output_dir)
                print(f"  ✓ Saved: {os.path.basename(filepath)}")
                success_count += 1
            else:
                print(f"  ⚠️  Skipped: No content extracted")
                failed_count += 1
        
        except Exception as e:
            print(f"  ❌ Error: {e}")
            failed_count += 1
        
        # Rate limiting to be respectful
        time.sleep(1)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Scraping Summary")
    print("=" * 60)
    print(f"✓ Successfully scraped: {success_count}")
    print(f"✗ Failed: {failed_count}")
    print(f"📁 Files saved to: {output_dir}")
    print("=" * 60)
    
    return {
        "success": success_count,
        "failed": failed_count,
        "total": len(policy_links)
    }


if __name__ == "__main__":
    # Run scraper when executed directly
    scrape_all_policies()
