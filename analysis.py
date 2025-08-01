import pandas as pd
import matplotlib.pyplot as plt
from collections import Counter

def analyze_data():
    # Load scraped data
    df = pd.read_csv('jobs.csv')
    
    # 1. Top Job Titles
    print("\nTop 10 Job Titles:")
    print(df['Title'].value_counts().head(10))
    
    # 2. Most In-Demand Skills
    all_skills = [skill for skills in df['Skills'] 
                  for skill in str(skills).split(', ') 
                  if skill != 'None']
    skill_counts = Counter(all_skills).most_common(10)
    
    print("\nTop 10 Skills:")
    for skill, count in skill_counts:
        print(f"{skill}: {count}")
    
    # 3. Bonus: Skills by City
    if not df.empty:
        # Clean location data
        df['City'] = df['Location'].apply(lambda x: x.split(',')[0])
        
        # Get top 5 cities
        top_cities = df['City'].value_counts().head(5).index
        
        # Plot skills distribution
        plt.figure(figsize=(12, 8))
        for i, city in enumerate(top_cities, 1):
            city_skills = [skill for skills in df[df['City']==city]['Skills'] 
                           for skill in str(skills).split(', ') 
                           if skill != 'None']
            skill_counts = Counter(city_skills).most_common(5)
            
            plt.subplot(2, 3, i)
            plt.bar(*zip(*skill_counts))
            plt.title(f"Top Skills in {city}")
            plt.xticks(rotation=45)
        
        plt.tight_layout()
        plt.savefig('skills_by_city.png')
        print("\nSaved visualization: skills_by_city.png")

if __name__ == "__main__":
    analyze_data()