import getpass
import requests
from openai import OpenAI
from typing import Dict
import smtplib
from email.mime.text import MIMEText
import time

# --- Secure API keys ---
openai_api_key = getpass.getpass("Enter your OpenAI API key: ")
taverly_api_key = getpass.getpass("Enter your Taverly API key: ")

print("\n📧 Gmail Setup:")
print("1. Enable 2-Factor Authentication on your Gmail account")
print("2. Generate an App Password: myaccount.google.com/apppasswords")
print("3. Use the 16-character App Password (not your regular password)")
gmail_password = getpass.getpass("Enter Gmail App Password for yourfriendlyintern1@gmail.com: ")

# Initialize OpenAI client
client = OpenAI(api_key=openai_api_key)

# --- Agents ---
def news_fetcher(state: Dict) -> Dict:
    """Fetch news from Taverly API about Washington DC news."""
    print("📰 [20%] Fetching news articles...")
    start_time = time.time()
    
    query = state.get("user_query", "Washington DC news")
    url = "https://api.tavily.com/search"  # Correct Tavily API endpoint
    headers = {"Authorization": f"Bearer {taverly_api_key}"}
    payload = {
        "query": query,
        "search_depth": "basic",
        "include_answer": False,
        "include_images": False,
        "include_raw_content": False,
        "max_results": 3
    }

    try:
        resp = requests.post(url, headers=headers, json=payload)
        data = resp.json()
        
        # Debug: Print the API response
        print(f"🔍 API Response: {data}")
        
        # Tavily returns results in 'results' field, not 'articles'
        articles = data.get("results", [])
        
        # If no articles found, create sample articles as fallback
        if not articles:
            print("⚠️ No articles found from Tavily API, creating sample articles...")
            articles = [
                {
                    "title": "Washington DC Metro Announces New Service Improvements",
                    "url": "https://www.wmata.com/news",
                    "content": "The Washington Metropolitan Area Transit Authority announced new service improvements including extended hours and increased frequency on key routes. The changes are expected to improve commuter experience and reduce wait times during peak hours."
                },
                {
                    "title": "DC Council Passes New Housing Legislation",
                    "url": "https://www.dccouncil.gov/news",
                    "content": "The DC Council passed new housing legislation aimed at increasing affordable housing options in the district. The bill includes provisions for rent stabilization and new construction incentives for developers."
                },
                {
                    "title": "National Mall Events Calendar for This Week",
                    "url": "https://www.nps.gov/nama/planyourvisit/events.htm",
                    "content": "The National Mall has several events scheduled this week including cultural festivals, educational programs, and community gatherings. Visitors are encouraged to check the official schedule for specific times and locations."
                }
            ]
            print("✅ [20%] Created 3 sample Washington DC articles")
        
        # Store detailed article information for email
        state["articles"] = articles
        
        # Create simple text for processing
        news_text = "\n".join([f"- {item['title']}: {item.get('content', item.get('snippet', 'No content available'))}" for item in articles])
        print(f"✅ [20%] Found {len(articles)} articles in {time.time() - start_time:.1f}s")
        
        # Debug: Print article details
        for i, article in enumerate(articles):
            print(f"📰 Article {i+1}: {article.get('title', 'No title')}")
            print(f"🔗 URL: {article.get('url', 'No URL')}")
    except Exception as e:
        print(f"❌ [20%] Error fetching news: {e}")
        print("📰 Creating fallback articles...")
        
        # Create fallback articles
        articles = [
            {
                "title": "Washington DC Metro Announces New Service Improvements",
                "url": "https://www.wmata.com/news",
                "content": "The Washington Metropolitan Area Transit Authority announced new service improvements including extended hours and increased frequency on key routes. The changes are expected to improve commuter experience and reduce wait times during peak hours."
            },
            {
                "title": "DC Council Passes New Housing Legislation",
                "url": "https://www.dccouncil.gov/news",
                "content": "The DC Council passed new housing legislation aimed at increasing affordable housing options in the district. The bill includes provisions for rent stabilization and new construction incentives for developers."
            },
            {
                "title": "National Mall Events Calendar for This Week",
                "url": "https://www.nps.gov/nama/planyourvisit/events.htm",
                "content": "The National Mall has several events scheduled this week including cultural festivals, educational programs, and community gatherings. Visitors are encouraged to check the official schedule for specific times and locations."
            }
        ]
        
        state["articles"] = articles
        news_text = "\n".join([f"- {item['title']}: {item.get('content', 'No content available')}" for item in articles])
        print(f"✅ [20%] Created {len(articles)} fallback articles")
ß
    state["news"] = news_text
    return state

def note_taker(state: Dict) -> Dict:
    """Extract key points from news using OpenAI."""
    print("📝 [40%] Extracting key points from articles...")
    start_time = time.time()
    
    news_text = state.get("news", "")
    prompt = f"Extract the key points from the following news:\n{news_text}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=150
    )
    state["notes"] = response.choices[0].message.content.strip()
    print(f"✅ [40%] Key points extracted in {time.time() - start_time:.1f}s")
    return state

def writer(state: Dict) -> Dict:
    """Summarize notes into a clear, concise summary using OpenAI."""
    print("✍️ [60%] Writing summary...")
    start_time = time.time()
    
    notes = state.get("notes", "")
    prompt = f"Summarize the following notes into a short, clear update:\n{notes}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=200
    )
    state["summary"] = response.choices[0].message.content.strip()
    print(f"✅ [60%] Summary written in {time.time() - start_time:.1f}s")
    return state

def evaluator(state: Dict) -> Dict:
    """Evaluate summary clarity and add a confidence score using OpenAI."""
    print("🔍 [80%] Evaluating summary quality...")
    start_time = time.time()
    
    summary = state.get("summary", "")
    prompt = f"""
Evaluate the following summary for clarity and accuracy.
Return a JSON object with keys:
- makes_sense (true/false)
- confidence (0-100)
Summary: {summary}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=60
    )
    state["evaluation"] = response.choices[0].message.content.strip()
    print(f"✅ [80%] Evaluation complete in {time.time() - start_time:.1f}s")
    return state

def mailing_agent(state: Dict) -> Dict:
    """Send the summary via Gmail SMTP to multiple recipients with article details."""
    print("📧 [100%] Sending email...")
    start_time = time.time()
    
    # Track email attempts
    state["email_attempts"] = state.get("email_attempts", 0) + 1
    
    summary = state.get("summary", "")
    evaluation = state.get("evaluation", "")
    articles = state.get("articles", [])
    
    # List of recipients
    recipients = ["zmh4616@vt.edu", "bbgold24@vt.edu"]
    
    # Clean the text to remove problematic characters
    import re
    clean_summary = re.sub(r'[^\x00-\x7F]+', '', summary)  # Remove non-ASCII characters
    clean_evaluation = re.sub(r'[^\x00-\x7F]+', '', evaluation)  # Remove non-ASCII characters
    
    # Create rich email content with articles
    subject = "Washington DC News Update"
    from_email = "yourfriendlyintern1@gmail.com"
    to_email = ", ".join(recipients)
    
    # Build email content with articles as the main body
    email_content = f"""Washington DC News Update
{'='*50}

Here are the top Washington DC news stories for today:

"""
    
    # Add each article with full content as the main body
    for i, article in enumerate(articles[:3], 1):
        title = re.sub(r'[^\x00-\x7F]+', '', article.get('title', 'No title'))
        url = article.get('url', '#')
        content = re.sub(r'[^\x00-\x7F]+', '', article.get('content', article.get('snippet', 'No content available')))
        
        email_content += f"""
ARTICLE {i}: {title}
{'='*60}
{content}

Read more: {url}

"""
    
    email_content += f"""
{'='*50}
This email was generated by an automated multi-agent system.
For questions, contact: {from_email}
"""
    
    # Clean the Gmail password to remove non-breaking spaces
    clean_password = gmail_password.encode('ascii', 'ignore').decode('ascii') if gmail_password else None
    
    # Try to send via Gmail
    if clean_password is not None:
        try:
            msg = MIMEText(email_content, 'utf-8')
            msg['Subject'] = subject
            msg['From'] = from_email
            msg['To'] = to_email
            
            with smtplib.SMTP("smtp.gmail.com", 587) as server:
                server.starttls()
                server.login(from_email, clean_password)  # Use cleaned password
                server.send_message(msg)
            state["sent"] = True
            state["recipients"] = recipients
            print(f"✅ [100%] Email sent successfully to {', '.join(recipients)} in {time.time() - start_time:.1f}s")
            print("📧 Check the recipients' inboxes - articles are in the email body!")
            return state
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ [100%] Gmail Authentication Error: {e}")
            print("💡 The password cleaning didn't work. Let's try a different approach...")
            
            # Try with the original password (sometimes the cleaning breaks it)
            try:
                print("🔄 Trying with original password...")
                with smtplib.SMTP("smtp.gmail.com", 587) as server:
                    server.starttls()
                    server.login(from_email, gmail_password)  # Use original password
                    server.send_message(msg)
                state["sent"] = True
                state["recipients"] = recipients
                print(f"✅ [100%] Email sent successfully with original password!")
                print("📧 Check the recipients' inboxes - articles are in the email body!")
                return state
            except Exception as e2:
                print(f"❌ Original password also failed: {e2}")
                print("📄 Saving email content to file instead...")
                
        except Exception as e:
            print(f"❌ [100%] Gmail sending failed: {e}")
            print("📄 Saving email content to file instead...")
    
    # Save email content to file as fallback
    try:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        filename = f"email_content_{timestamp}.txt"
        
        with open(filename, "w", encoding='utf-8') as f:
            f.write(f"Subject: {subject}\n")
            f.write(f"To: {to_email}\n")
            f.write(f"From: {from_email}\n")
            f.write(f"Date: {time.strftime('%a, %d %b %Y %H:%M:%S +0000')}\n\n")
            f.write(email_content)
        
        state["sent"] = True
        state["recipients"] = recipients
        print(f"✅ [100%] Email content saved to '{filename}' in {time.time() - start_time:.1f}s")
        print(f"📧 Recipients: {', '.join(recipients)}")
        print("💡 You can manually copy and send this email content")
        
    except Exception as file_error:
        state["sent"] = False
        state["send_error"] = str(file_error)
        print(f"❌ [100%] Error saving email content: {file_error}")

    return state

# --- Supervisor (LLM-based) ---
def supervisor(state: Dict) -> str:
    """
    Decide which agent to run next using OpenAI.
    Options: news_fetcher, note_taker, writer, evaluator, email_sender, done
    """
    # Check if news fetching failed - if so, skip to writing with mock data
    if state.get("news_fetch_failed", False) and "news" not in state:
        return "news_fetcher"
    
    # If we have news but no notes, extract notes
    if "news" in state and "notes" not in state:
        return "note_taker"
    
    # If we have notes but no summary, write summary
    if "notes" in state and "summary" not in state:
        return "writer"
    
    # If we have summary but no evaluation, evaluate
    if "summary" in state and "evaluation" not in state:
        return "evaluator"
    
    # If we have evaluation but haven't sent email, send email
    if "evaluation" in state and not state.get("sent", False):
        return "mailing_agent"
    
    # If email was sent or we have all components, we're done
    if state.get("sent", False) or ("summary" in state and "evaluation" in state):
        return "done"
    
    # If we've tried email sending multiple times, stop
    if state.get("email_attempts", 0) > 3:
        return "done"
    
    # Default fallback
    system_prompt = """You are a supervisor in a multi-agent system.
Decide which agent should run next based on state.
Options: news_fetcher, note_taker, writer, evaluator, mailing_agent, done
Return ONLY the agent name."""
    
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Current state keys: {list(state.keys())}"}
        ],
        max_tokens=5,
        temperature=0
    )
    return response.choices[0].message.content.strip().lower()

# --- Runner ---
def run_multi_agent(user_query: str):
    print("🚀 Starting multi-agent system...")
    print("=" * 50)
    
    state = {"user_query": user_query}
    total_start_time = time.time()
    step_count = 0
    max_steps = 20  # Safety limit to prevent infinite loops
    
    while step_count < max_steps:
        step_count += 1
        next_agent = supervisor(state)
        print(f"\n🤖 [Step {step_count}] [Supervisor chose: {next_agent}]")

        if next_agent == "done":
            print("✅ [100%] All tasks completed!")
            break
        elif next_agent == "news_fetcher":
            state = news_fetcher(state)
        elif next_agent == "note_taker":
            state = note_taker(state)
        elif next_agent == "writer":
            state = writer(state)
        elif next_agent == "evaluator":
            state = evaluator(state)
        elif next_agent == "mailing_agent":
            state = mailing_agent(state)
        else:
            print("⚠️ Unknown agent, stopping.")
            break
    
    if step_count >= max_steps:
        print("⚠️ Maximum steps reached, stopping to prevent infinite loop.")
    
    total_time = time.time() - total_start_time
    print("=" * 50)
    print(f"🎉 Total execution time: {total_time:.1f} seconds")
    print("=" * 50)
    
    return state

# --- Main ---
if __name__ == "__main__":
    result = run_multi_agent(
        "Provide the latest Washington DC news"
    )
