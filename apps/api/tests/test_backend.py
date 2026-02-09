import urllib.request
import json
import time

def test_health():
    url = "http://localhost:8080/health"
    print(f"Testing {url}...")
    try:
        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                print(f"FAILED: Status code {response.status}")
                return False
            
            data = json.loads(response.read().decode())
            print(f"Response: {data}")
            
            if data.get("status") == "ok":
                print("SUCCESS: Health check passed")
                return True
            else:
                print(f"FAILED: Unexpected status in body: {data.get('status')}")
                return False
    except Exception as e:
        print(f"FAILED: Error connecting to {url}: {e}")
        return False

def test_courses():
    url = "http://localhost:8080/courses"
    print(f"Testing {url}...")
    try:
        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                print(f"FAILED: Status code {response.status}")
                return False
            
            data = json.loads(response.read().decode())
            print(f"Response: {data}")
            
            if isinstance(data, list):
                print("SUCCESS: Courses list retrieved")
                return True
            else:
                print("FAILED: Response is not a list")
                return False
    except Exception as e:
        print(f"FAILED: Error connecting to {url}: {e}")
        return False

def test_search():
    url = "http://localhost:8080/search?q=test"
    print(f"Testing {url}...")
    try:
        with urllib.request.urlopen(url) as response:
            if response.status != 200:
                print(f"FAILED: Status code {response.status}")
                return False
            
            data = json.loads(response.read().decode())
            print(f"Response: {data}")
            
            # Check for expected keys in SearchResult
            if "courses" in data and "lessons" in data and "plans" in data:
                print("SUCCESS: Search results retrieved")
                return True
            else:
                print("FAILED: Invalid search result format")
                return False
    except Exception as e:
        print(f"FAILED: Error connecting to {url}: {e}")
        return False

if __name__ == "__main__":
    tests = [test_health, test_courses, test_search]
    failed = False
    
    for test in tests:
        if not test():
            failed = True
            
    if failed:
        exit(1)
    else:
        exit(0)
