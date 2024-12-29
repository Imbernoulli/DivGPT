from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import json
import time

def get_code_blocks(driver):
    """Extract all code blocks from the page"""
    code_blocks = []
    try:
        selectors = [
            'div.ReactCodeMirror',
            'div[class*="CodeMirror"]',
            'pre[class*="language-"]',
            'code[class*="language-"]'
        ]
        
        for selector in selectors:
            elements = driver.find_elements(By.CSS_SELECTOR, selector)
            for element in elements:
                try:
                    textarea = element.find_element(By.TAG_NAME, 'textarea')
                    code = textarea.get_attribute('value')
                except:
                    code = element.text
                
                if code and len(code.strip()) > 0:
                    code_blocks.append(code.strip())
        
        print(f"Found {len(code_blocks)} code blocks")
        
        print("Code block preview:")
        for i, code_block in enumerate(code_blocks[:3], 1):
            print(f"\nCode block {i}:\n{code_block[:200]}")
        
        return code_blocks
    except Exception as e:
        print(f"Error extracting code blocks: {str(e)}")
        return []

def get_solution_details(url):
    """Get detailed information for a single solution"""
    driver = webdriver.Safari()
    try:
        driver.set_window_size(1920, 1080)
        driver.get(url)
        wait = WebDriverWait(driver, 30)
        
        time.sleep(5)
        
        content_selectors = [
            'div[class*="break-words"]',
            'article',
            'div[class*="description"]',
            '//div[contains(@class, "markdown")]'
        ]
        
        content = None
        for selector in content_selectors:
            try:
                if selector.startswith('//'):
                    content = wait.until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                else:
                    content = wait.until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                if content and content.text.strip():
                    break
            except:
                continue
        
        article_text = content.text.strip() if content else ""
        
        code_blocks = get_code_blocks(driver)
        
        if not article_text and not code_blocks:
            print(f"No content found for {url}")
            return None
            
        result = {
            'url': url,
            'content': article_text,
            'code_blocks': code_blocks
        }
        
        print(f"Found {len(code_blocks)} code blocks")
        print(f"Content length: {len(article_text)}")
        
        return result
        
    except Exception as e:
        print(f"Error getting details for {url}: {str(e)}")
        return None
    finally:
        driver.quit()

def crawl_details():
    options = webdriver.SafariOptions()
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36')
    
    try:
        with open('solution_urls.json', 'r') as f:
            solutions = json.load(f)
    except FileNotFoundError:
        print("solution_urls.json not found. Please run get_leetcode_solutions.py first.")
        return
    
    print("\nGetting solution details...")
    all_solutions = []
    
    for index, solution_url in enumerate(solutions, 1):
        print(f"\nProcessing solution {index}/{len(solutions)}: {solution_url}")
        details = get_solution_details(solution_url)
        if details:
            all_solutions.append(details)
            print("\nPreview of extracted content:")
            print("Article text preview:", details['content'][:200] + "..." if details['content'] else "No article text")
            print("\nFirst code block preview:", details['code_blocks'][0][:200] + "..." if details['code_blocks'] else "No code blocks")
        time.sleep(3)
    
    with open('solution_details.json', 'w', encoding='utf-8') as f:
        json.dump(all_solutions, f, ensure_ascii=False, indent=2)
    
    print(f"\nTotal solutions processed: {len(all_solutions)}")
    print("Solution details have been saved to solution_details.json")