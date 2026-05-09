import requests
from datetime import datetime

# Set your variables
api_key = "YOUR_API_KEY"
headers = {"Authorization": f"Bearer {api_key}"}

# 1. Get your subscription limit
sub = requests.get("https://api.openai.com/dashboard/billing/subscription", headers=headers).json()
hard_limit = sub.get("hard_limit_usd")

# 2. Get your usage
today = datetime.now().strftime("%Y-%m-%d")
usage = requests.get(f"https://api.openai.com/dashboard/billing/usage?end_date={today}&start_date={today}", headers=headers).json()
total_usage = usage.get("total_usage") / 100  # usage is often returned in cents

print(f"Remaining Balance: ${hard_limit - total_usage:.2f}")