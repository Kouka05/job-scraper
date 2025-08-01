from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import time

def scrape_jobs():
    # Configure Selenium
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')  # Run in background
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    
    # Scrape 3 pages of Indeed "data analyst" jobs
    all_jobs = []
    for page in range(0, 31, 10):  # Pages 0, 10, 20
        url = f"https://www.indeed.com/jobs?q=data+analyst&start={page}"
        driver.get(url)
        time.sleep(3)  # Wait for page load
        
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        jobs = soup.find_all('div', class_='job_seen_beacon')
        
        for job in jobs:
            try:
                title = job.find('h2', class_='jobTitle').text.strip()
                company = job.find('span', class_='companyName').text.strip()
                location = job.find('div', class_='companyLocation').text.strip()
                date = job.find('span', class_='date').text.strip()
                
                # Extract skills from description
                description = job.find('div', class_='job-snippet').text.lower()
                skills = []
                for skill in ['sql', 'python', 'excel', 'tableau', 'power bi']:
                    if skill in description:
                        skills.append(skill)
                
                all_jobs.append({
                    'Title': title,
                    'Company': company,
                    'Location': location,
                    'Posted': date,
                    'Skills': ', '.join(skills) if skills else 'None'
                })
            except AttributeError:
                continue
    
    driver.quit()
    return pd.DataFrame(all_jobs)

if __name__ == "__main__":
    df = scrape_jobs()
    df.to_csv('jobs.csv', index=False)
    print(f"Scraped {len(df)} jobs. Data saved to jobs.csv")