# File: update_activity.py
import os
import requests
from datetime import datetime

# --- Configuration ---
USERNAME = "CongLeSolutionX"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
MAX_ITEMS = 5

def fetch_github_events():
    """Fetches public events for the specified user from the GitHub API."""
    url = f"https://api.github.com/users/{USERNAME}/events/public"
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "Authorization": f"token {GITHUB_TOKEN}"
    }
    
    print(f"🔗 Fetching events for user: {USERNAME}")
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("✅ Events fetched successfully.")
        return response.json()
    else:
        print(f"❌ Error fetching events: {response.status_code} - {response.text}")
        return None

def format_relative_time(dt_str):
    """Formats a datetime string into a human-readable relative time."""
    event_time = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    now = datetime.now(event_time.tzinfo)
    delta = now - event_time
    
    if delta.days > 1:
        return f"{delta.days} days ago"
    elif delta.days == 1:
        return "yesterday"
    elif delta.seconds >= 3600:
        return f"{delta.seconds // 3600} hours ago"
    elif delta.seconds >= 60:
        return f"{delta.seconds // 60} minutes ago"
    else:
        return "just now"

def process_events(events):
    """Processes the raw event data into structured lists for Markdown generation."""
    activity = {
        "commits": [], "pull_requests": [], "issues": [], "stars": []
    }
    if not events: return activity

    committed_repos = set()

    for event in events:
        repo_name = event['repo']['name']
        event_time = format_relative_time(event['created_at'])

        if event['type'] == 'PushEvent' and repo_name not in committed_repos and len(activity['commits']) < MAX_ITEMS:
            # Group all commits in a single push to one line item
            num_commits = len(event['payload']['commits'])
            plural_s = "s" if num_commits > 1 else ""
            commit_url = f"https://github.com/{repo_name}/commits?author={USERNAME}"
            activity['commits'].append(
                f"Pushed [{num_commits} commit{plural_s}]({commit_url}) to **{repo_name}** - *{event_time}*"
            )
            committed_repos.add(repo_name) # Avoid listing the same repo push multiple times

        elif event['type'] == 'PullRequestEvent' and event['payload']['action'] == 'opened' and len(activity['pull_requests']) < MAX_ITEMS:
            pr = event['payload']['pull_request']
            activity['pull_requests'].append(f"Opened PR [#{pr['number']}]({pr['html_url']}) in **{repo_name}** - *{event_time}*")

        elif event['type'] == 'IssuesEvent' and event['payload']['action'] == 'opened' and len(activity['issues']) < MAX_ITEMS:
            issue = event['payload']['issue']
            activity['issues'].append(f"Opened Issue [#{issue['number']}]({issue['html_url']}) in **{repo_name}** - *{event_time}*")

        elif event['type'] == 'WatchEvent' and event['payload']['action'] == 'started' and len(activity['stars']) < MAX_ITEMS:
            activity['stars'].append(f"Starred [{repo_name}](https://github.com/{repo_name}) - *{event_time}*")

    return activity

def generate_markdown(activity):
    """Generates the full Markdown content from the processed activity."""
    md = f"# ✨ My Recent GitHub Activity\n\n*Last updated: {datetime.now().strftime('%d %B %Y')}*\n\n"
    if activity['commits']:
        md += "### 📝 Latest Pushes\n\n" + "\n".join([f"- {c}" for c in activity['commits']]) + "\n\n"
    if activity['pull_requests']:
        md += "### 🔧 Recent Pull Requests\n\n" + "\n".join([f"- {pr}" for pr in activity['pull_requests']]) + "\n\n"
    if activity['issues']:
        md += "### 🎯 Newly Opened Issues\n\n" + "\n".join([f"- {i}" for i in activity['issues']]) + "\n\n"
    if activity['stars']:
        md += "### ⭐ Recently Starred\n\n" + "\n".join([f"- {s}" for s in activity['stars']]) + "\n\n"
    return md

if __name__ == "__main__":
    if not os.getenv("GITHUB_TOKEN"):
        print("❗ GITHUB_TOKEN environment variable not set.")
    events = fetch_github_events()
    if events:
        processed_activity = process_events(events)
        markdown_content = generate_markdown(processed_activity)
        with open("README.md", "w") as f:
            f.write(markdown_content)
        print("📄 README.md has been successfully updated.")