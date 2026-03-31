import os
import requests
from dotenv import load_dotenv

# 1. .env file se humara secret GITHUB_TOKEN load karna
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

if not GITHUB_TOKEN:
    print("❌ Error: GITHUB_TOKEN nahi mila! .env file aur uska naam check karo.")
    exit()

# 2. GitHub API ke liye ID card (Headers) setup karna
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}

def fetch_repo_contents(owner, repo):
    """Repo ki root files fetch karne ka function"""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        files = response.json()
        print(f"\n📁 Repo: {owner}/{repo} ki files:")
        for file in files:
            # Hum print kar rahe hain ki file ka naam kya hai aur wo file hai ya folder(dir)
            print(f"  - {file['name']} ({file['type']})")
    else:
        print(f"❌ Error fetching files: {response.status_code}")
        print(response.json())

def fetch_recent_commits(owner, repo):
    """Repo ke latest 3 commits fetch karne ka function"""
    # Hum API ko bol rahe hain ki sirf aakhri 3 commits hi do (?per_page=3)
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?per_page=3"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 200:
        commits = response.json()
        print(f"\n📝 Latest Commits in {owner}/{repo}:")
        for commit in commits:
            author = commit['commit']['author']['name']
            message = commit['commit']['message'].split('\n')[0] # Message ki sirf pehli line lene ke liye
            date = commit['commit']['author']['date'][:10] # Sirf YYYY-MM-DD dikhane ke liye
            
            print(f"  [{date}] {author}: {message}")
    else:
        print(f"❌ Error fetching commits: {response.status_code}")

# 3. Yahan se humara program run hona start hoga
if __name__ == "__main__":
    # GitHub ki official test repository use kar rahe hain
    TARGET_OWNER = "DonaChoudhury"
    TARGET_REPO = "rag-demo"
    
    print("🚀 Fetcher script start ho raha hai GitHub API se connect karne ke liye...")
    fetch_repo_contents(TARGET_OWNER, TARGET_REPO)
    fetch_recent_commits(TARGET_OWNER, TARGET_REPO)
    print("\n✅ Script Successfully Run! Connection perfect hai.")