from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import json
import time

def scrape_question_lists(name):
    chrome_options = Options()
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920x1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    print("Setting up ChromeDriver...")
    service = Service(ChromeDriverManager().install())

    print("Initializing WebDriver...")
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        print("Navigating to LeetCode...")
        driver.get(f"https://leetcode.com/tag/{name}/")

        print("Waiting for problem list to load...")
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CLASS_NAME, "reactable-data"))
        )

        print("Extracting problem links...")
        reactable_data = driver.find_element(By.CLASS_NAME, "reactable-data")
        problem_links = reactable_data.find_elements(By.CSS_SELECTOR, "a[href^='/problems/']")

        problems = []
        for link in problem_links:
            problem = {
                'title': link.text.strip(),
                'link': link.get_attribute("href")
            }
            problems.append(problem)

        return problems

    except Exception as e:
        print(f"An error occurred: {e}")
        print("Current URL:", driver.current_url)
        print("Page source:")
        print(driver.page_source[:500])  # Print first 500 characters of page source
        return None

    finally:
        print("Closing WebDriver...")
        driver.quit()

if __name__ == "__main__":
    names = [
        "array", "string", "hash-table", "dynamic-programming", "math", "sorting", 
        "greedy", "depth-first-search", "database", "binary-search", 
        "breadth-first-search", "tree", "matrix", "bit-manipulation", 
        "two-pointers", "binary-tree", "heap-priority-queue", "prefix-sum", 
        "stack", "simulation", "graph", "counting", "design", "sliding-window", 
        "backtracking", "enumeration", "union-find", "linked-list", 
        "ordered-set", "monotonic-stack", "number-theory", "trie", 
        "segment-tree", "divide-and-conquer", "queue", "recursion", "bitmask", 
        "binary-search-tree", "geometry", "memoization", "binary-indexed-tree", 
        "hash-function", "combinatorics", "topological-sort", "string-matching", 
        "shortest-path", "rolling-hash", "game-theory", "interactive", 
        "data-stream", "brainteaser", "monotonic-queue", "randomized", 
        "merge-sort", "iterator", "doubly-linked-list", "concurrency", 
        "probability-and-statistics", "quickselect", "suffix-array", 
        "counting-sort", "bucket-sort", "minimum-spanning-tree", "shell", 
        "line-sweep", "reservoir-sampling", "strongly-connected-component", 
        "eulerian-circuit", "radix-sort", "rejection-sampling", 
        "biconnected-component"
    ]
    
    for name in names:
        array_problems = scrape_question_lists(name)
        
        if array_problems:
            with open(f"{name}_problems.json", "w") as file:
                json.dump(array_problems, file, indent=4)
            print(f"Found {len(array_problems)} array problems:")
            for problem in array_problems:
                print(f"Title: {problem['title']}, Link: {problem['link']}")
        else:
            print("Failed to scrape array problems from LeetCode.")