# File: update_activity.py
import os
import re # Import the regular expression module
import requests
from datetime import datetime

# --- Configuration ---
USERNAME = "CongLeSolutionX"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
MAX_ITEMS = 5

# The fetch_github_events, format_relative_time, and process_events functions remain the same
# ... (You can copy them from the previous response or use the full script below) ...
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
            num_commits = len(event['payload']['commits'])
            plural_s = "s" if num_commits > 1 else ""
            commit_url = f"https://github.com/{repo_name}/commits?author={USERNAME}"
            activity['commits'].append(f"Pushed [{num_commits} commit{plural_s}]({commit_url}) to **{repo_name}** - *{event_time}*")
            committed_repos.add(repo_name)
        elif event['type'] == 'PullRequestEvent' and event['payload']['action'] == 'opened' and len(activity['pull_requests']) < MAX_ITEMS:
            pr = event['payload']['pull_request']
            activity['pull_requests'].append(f"Opened PR [#{pr['number']}]({pr['html_url']}) in **{repo_name}** - *{event_time}*")
        elif event['type'] == 'IssuesEvent' and event['payload']['action'] == 'opened' and len(activity['issues']) < MAX_ITEMS:
            issue = event['payload']['issue']
            activity['issues'].append(f"Opened Issue [#{issue['number']}]({issue['html_url']}) in **{repo_name}** - *{event_time}*")
        elif event['type'] == 'WatchEvent' and event['payload']['action'] == 'started' and len(activity['stars']) < MAX_ITEMS:
            activity['stars'].append(f"Starred [{repo_name}](https://github.com/{repo_name}) - *{event_time}*")
    return activity
# --- END of unchanged functions ---


def generate_markdown_snippet(activity):
    """Generates the activity list portion of the Markdown content."""
    md = [f"*Last updated: {datetime.now().strftime('%d %B %Y')}*\n"] # Use a list to build parts
    
    if activity['commits']:
        md.append("#### 📝 Latest Pushes")
        md.extend([f"- {c}" for c in activity['commits']])
        md.append("") # Add a blank line for spacing
        
    if activity['pull_requests']:
        md.append("#### 🔧 Recent Pull Requests")
        md.extend([f"- {pr}" for pr in activity['pull_requests']])
        md.append("")
        
    if activity['issues']:
        md.append("#### 🎯 Newly Opened Issues")
        md.extend([f"- {i}" for i in activity['issues']])
        md.append("")
        
    if activity['stars']:
        md.append("#### ⭐ Recently Starred")
        md.extend([f"- {s}" for s in activity['stars']])
        
    return "\n".join(md).strip()


def main():
    """Main function to run the script."""
    if not os.getenv("GITHUB_TOKEN"):
        print("❗ GITHUB_TOKEN environment variable not set. API requests are limited.")
    
    events = fetch_github_events()
    if not events:
        print("No events fetched. Exiting.")
        return
        
    processed_activity = process_events(events)
    markdown_snippet = generate_markdown_snippet(processed_activity)
    
    # --- The ✨ New Logic ✨ ---
    readme_path = "README.md"
    try:
        with open(readme_path, "r", encoding="utf-8") as f:
            readme_content = f.read()
    except FileNotFoundError:
        print(f"❌ '{readme_path}' not found. Cannot update.")
        return

    # Use regex to find and replace the content between markers
    start_marker = "<!--START_ACTIVITY_LIST-->"
    end_marker = "<!--END_ACTIVITY_LIST-->"
    
    # Safely construct the new content to be injected
    new_content_block = f"{start_marker}\n{markdown_snippet}\n{end_marker}"
    
    # Regex pattern to find the block to replace
    pattern = re.compile(f"{re.escape(start_marker)}.*?{re.escape(end_marker)}", re.DOTALL)
    
    # Replace the block
    new_readme, replacements = pattern.subn(new_content_block, readme_content)

    if replacements > 0:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(new_readme)
        print("📄 README.md has been successfully updated with new activity.")
    else:
        print(f"❗ Markers '{start_marker}' and '{end_marker}' not found in README.md. No changes made.")


if __name__ == "__main__":
    main()