from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import json

def get_leetcode_solutions_selenium(url):
    driver = webdriver.Safari()
    
    try:
        driver.get(url)
        time.sleep(3)  # Wait for initial load
        
        solutions_set = set()

        # Get all visible solution links
        solution_links = driver.find_elements(
            By.CSS_SELECTOR, 
            'a.no-underline.hover\\:text-blue-s.dark\\:hover\\:text-dark-blue-s.truncate.w-full'
        )
        
        # Add new links to set
        current_solutions = {link.get_attribute('href') for link in solution_links}
        solutions_set.update(current_solutions)
        
        print(f"Currently found {len(solutions_set)} solutions")
            
        return list(solutions_set)
        
    except Exception as e:
        print(f"Error: {e}")
        return []
        
    finally:
        driver.quit()