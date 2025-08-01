import pandas as pd
import time
import random
import re
import logging
import os
import json
from bs4 import BeautifulSoup
import cloudscraper  # Specialized library for bypassing Cloudflare

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("indeed_scraper.log"),
        logging.StreamHandler()
    ]
)

# Create cache directory
os.makedirs('cache', exist_ok=True)

def get_cached_page(url, cache_time=3600):
    """Cache pages to avoid repeated requests"""
    cache_file = f"cache/{re.sub(r'\W+', '_', url)}.html"
    
    # Use cache if available and recent
    if os.path.exists(cache_file) and (time.time() - os.path.getmtime(cache_file)) < cache_time:
        logging.info(f"Using cached version of {url}")
        with open(cache_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    # Use cloudscraper to bypass anti-bot protection
    scraper = cloudscraper.create_scraper()
    logging.info(f"Fetching: {url}")
    
    try:
        # Set a random user agent
        user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0"
        ]
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        # Add random delay before request
        time.sleep(random.uniform(1.0, 3.0))
        
        response = scraper.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Save to cache
        with open(cache_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        return response.text
    except Exception as e:
        logging.error(f"Error fetching {url}: {str(e)}")
        return None

def extract_job_data(job_element):
    """Extract job details from a job card element"""
    try:
        # Extract title
        title_elem = job_element.find('h2', class_='jobTitle')
        title = title_elem.text.strip() if title_elem else "Title not found"
        
        # Extract company
        company_elem = job_element.find('span', class_='companyName')
        company = company_elem.text.strip() if company_elem else "Company not specified"
        
        # Extract location
        location_elem = job_element.find('div', class_='companyLocation')
        location = location_elem.text.strip() if location_elem else "Location not specified"
        
        # Extract salary if available
        salary_elem = job_element.find('div', class_='salary-snippet')
        salary = salary_elem.text.strip() if salary_elem else "Salary not specified"
        
        # Extract date
        date_elem = job_element.find('span', class_='date')
        date = date_elem.text.strip() if date_elem else "Date not specified"
        
        # Extract job snippet
        snippet_elem = job_element.find('div', class_='job-snippet')
        snippet = snippet_elem.text.strip() if snippet_elem else ""
        
        # Extract job ID for detail link
        job_id = job_element.get('data-jk', '')
        detail_link = f"https://www.indeed.com/viewjob?jk={job_id}" if job_id else ""
        
        return {
            'Title': title,
            'Company': company,
            'Location': location,
            'Salary': salary,
            'Posted': date,
            'Snippet': snippet,
            'Detail_Link': detail_link
        }
        
    except Exception as e:
        logging.error(f"Error extracting job data: {str(e)}")
        return None

def find_job_cards(soup):
    """Find job cards using multiple strategies"""
    # Strategy 1: Look for standard job cards
    job_cards = soup.find_all('div', class_='job_seen_beacon')
    if job_cards:
        logging.info(f"Found {len(job_cards)} job cards using standard method")
        return job_cards
    
    # Strategy 2: Look for alternative job cards
    job_cards = soup.find_all('div', class_='jobsearch-SerpJobCard')
    if job_cards:
        logging.info(f"Found {len(job_cards)} job cards using alternative method")
        return job_cards
    
    # Strategy 3: Look for cards with job titles
    job_cards = []
    for h2 in soup.find_all('h2', class_='jobTitle'):
        card = h2.find_parent('div')
        if card and card not in job_cards:
            job_cards.append(card)
    if job_cards:
        logging.info(f"Found {len(job_cards)} job cards using parent method")
        return job_cards
    
    # Strategy 4: Look for cards with company names
    job_cards = []
    for span in soup.find_all('span', class_='companyName'):
        card = span.find_parent('div')
        if card and card not in job_cards:
            job_cards.append(card)
    if job_cards:
        logging.info(f"Found {len(job_cards)} job cards using company method")
        return job_cards
    
    logging.warning("No job cards found using any strategy")
    return []

def scrape_indeed_jobs(query="data analyst", location="", pages=2):
    """Scrape job listings from Indeed"""
    all_jobs = []
    
    try:
        base_url = "https://www.indeed.com"
        
        for page in range(0, pages):
            # Build URL with query parameters
            url = f"{base_url}/jobs?q={query.replace(' ', '+')}&l={location}&start={page*10}"
            logging.info(f"Scraping page {page+1}: {url}")
            
            # Get page content
            html_content = get_cached_page(url)
            if not html_content:
                logging.warning(f"Skipping page {page+1} due to fetch error")
                continue
                
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Find job cards
            job_cards = find_job_cards(soup)
            logging.info(f"Found {len(job_cards)} job cards on page {page+1}")
            
            # Process each job card
            for card in job_cards:
                job_data = extract_job_data(card)
                if job_data:
                    all_jobs.append(job_data)
            
            # Add random delay between pages
            time.sleep(random.uniform(2.0, 5.0))
    
    except Exception as e:
        logging.error(f"Scraping failed: {str(e)}")
    
    return pd.DataFrame(all_jobs)

def enrich_with_skills(df):
    """Enrich job data with skills extracted from snippets"""
    if df.empty:
        return df
    
    # Common skills to look for
    common_skills = [
        'sql', 'python', 'excel', 'tableau', 'power bi', 'r', 'aws', 
        'azure', 'google cloud', 'spark', 'hadoop', 'java', 'scala',
        'sas', 'statistics', 'machine learning', 'deep learning', 'nlp',
        'tensorflow', 'pytorch', 'scikit-learn', 'pandas', 'numpy', 'matplotlib',
        'seaborn', 'powerpoint', 'word', 'looker', 'qlik', 'snowflake', 'redshift',
        'bigquery', 'mysql', 'postgresql', 'mongodb', 'nosql', 'git', 'docker',
        'kubernetes', 'airflow', 'dbt', 'etl', 'elt', 'api', 'rest', 'json', 'xml'
    ]
    
    # Extract skills from snippets
    skills_list = []
    for snippet in df['Snippet']:
        found_skills = []
        snippet_lower = str(snippet).lower()
        for skill in common_skills:
            # Use regex to find whole words only
            if re.search(rf'\b{re.escape(skill)}\b', snippet_lower):
                found_skills.append(skill)
        skills_list.append(', '.join(found_skills) if found_skills else 'None')
    
    df['Skills'] = skills_list
    return df

def run_analysis(df):
    """Run analysis on the scraped data"""
    if df.empty:
        logging.warning("No data to analyze")
        return
    
    # Basic analysis
    print(f"\nTotal jobs scraped: {len(df)}")
    print("\nTop 10 job titles:")
    print(df['Title'].value_counts().head(10))
    
    # Skills analysis
    all_skills = [skill for skills in df['Skills'] for skill in skills.split(', ') if skill != 'None']
    if all_skills:
        from collections import Counter
        skill_counts = Counter(all_skills).most_common(10)
        print("\nTop 10 skills:")
        for skill, count in skill_counts:
            print(f"{skill}: {count}")
    else:
        print("\nNo skills data found")

if __name__ == "__main__":
    logging.info("Starting Indeed job scraper with Cloudflare bypass")
    
    # Scrape jobs
    job_df = scrape_indeed_jobs(query="data analyst", pages=2)
    
    if not job_df.empty:
        logging.info(f"Scraped {len(job_df)} jobs from Indeed")
        
        # Enrich with skills
        job_df = enrich_with_skills(job_df)
        
        # Save to CSV
        job_df.to_csv('indeed_jobs.csv', index=False)
        logging.info("Saved job data to indeed_jobs.csv")
        
        # Run basic analysis
        run_analysis(job_df)
        
        # Save sample as JSON for inspection
        sample = job_df.head(3).to_dict(orient='records')
        with open('sample_jobs.json', 'w') as f:
            json.dump(sample, f, indent=2)
        logging.info("Saved sample data to sample_jobs.json")
        
        # Print sample
        print("\nSample of scraped jobs:")
        print(job_df[['Title', 'Company', 'Location']].head(3))
    else:
        logging.warning("No jobs scraped. Check the logs for issues.")