import re
import sys
from dotenv import load_dotenv
from TextToSpeech.Fast_DF_TTS import speak

load_dotenv()

# Keyless search library
try:
    from ddgs import DDGS
except ImportError:
    DDGS = None

try:
    from webscout import FreeAI
except ImportError:
    FreeAI = None

NEWS_PATTERNS = [
    r'\b(what(\'?s|\s+is)\s+happening\s+in\s+the\s+news)\b',
    r'\b(what(\'?s|\s+is)\s+in\s+the\s+news)\b',
    r'\b(what(\'?s|\s+is)\s+(the\s+)?news)\b',
    r'\b(tell\s+me\s+today(\'?s)?\s+news)\b',
    r'\b(give\s+me\s+today(\'?s)?\s+news)\b',
    r'\b(latest\s+news)\b',
    r'\b(today(\'?s)?\s+news)\b',
    r'\b(what(\'?s|\s+is)\s+the\s+latest\s+news)\b',
    r'\b(what\s+happened\s+today)\b',
    r'\b(today(\'?s)?\s+headlines)\b',
    r'\b(what\s+are\s+today(\'?s)?\s+headlines)\b',
    r'\b(give\s+me\s+today(\'?s)?\s+headlines)\b',
    r'\b(news\s+update)\b',
    r'\b(give\s+me\s+a\s+news\s+update)\b',
    r'\bnews\b',
    r'\bheadlines\b'
]

def safe_print(msg: str):
    """Safely print text to Windows console without charmap encoding issues."""
    try:
        print(msg)
    except (UnicodeEncodeError, Exception):
        try:
            print(str(msg).encode("ascii", errors="replace").decode("ascii"))
        except Exception:
            pass

def is_news_query(text: str) -> bool:
    """Detect if the speech input is requesting today's or latest news."""
    lower = text.lower().strip()
    
    # Avoid intercepting explicit browser or app opening commands
    if "open edge" in lower or "open browser" in lower:
        return False
        
    for pattern in NEWS_PATTERNS:
        if re.search(pattern, lower):
            return True
    return False

def extract_news_topic(text: str) -> str:
    """Extract topic or return default 'latest news today'."""
    cleaned = re.sub(r'^(hey\s+|hello\s+|hi\s+|ok\s+)?jarvis[,:\s]*', '', text, flags=re.IGNORECASE).strip()
    lower = cleaned.lower()
    
    # Detect category news, e.g. "tech news", "sports news", "world news"
    m = re.search(r'\b([a-zA-Z\s]+?)\s+news\b', lower)
    if m:
        topic = m.group(1).strip()
        topic = re.sub(r'\b(today|latest|current|the|any|what|give|tell|me|is|in)\b', '', topic).strip()
        if topic and len(topic) > 2:
            return f"{topic} news"
            
    return "latest news today"

def fetch_todays_news(query: str = "latest news today", max_results: int = 5) -> list:
    """
    Perform programmatic keyless news search using the DDGS library.
    Filters out duplicates and extracts title, source, date, body, and URL.
    """
    results = []
    if not DDGS:
        return results

    try:
        with DDGS() as ddgs:
            raw_news = list(ddgs.news(query=query, timelimit="d", max_results=max_results))
            seen_titles = set()
            for item in raw_news:
                title = item.get("title", "").strip()
                # Clean trailing source tags from title (e.g. ' - Reuters')
                clean_title = re.sub(r'\s+[-|]\s+.*$', '', title).strip()
                if clean_title and clean_title.lower() not in seen_titles:
                    seen_titles.add(clean_title.lower())
                    results.append({
                        "title": clean_title,
                        "source": item.get("source", "").strip(),
                        "date": item.get("date", "").strip(),
                        "body": item.get("body", "").strip(),
                        "url": item.get("url", "")
                    })
    except Exception as e:
        safe_print(f"[Jarvis - News Error]: {e}")
        
    return results

def summarize_news(news_items: list) -> str:
    """Synthesize news stories into a clear, spoken summary."""
    if not news_items:
        return "I couldn't find recent news at the moment."

    # Try AI synthesis for fluid spoken narrative
    if FreeAI:
        try:
            ai = FreeAI()
            context = "\n".join([f"- {n['title']} (Source: {n['source']}): {n['body']}" for n in news_items[:3]])
            prompt = (
                "You are Jarvis, a voice assistant. Summarize these top news stories into 2 or 3 concise, spoken sentences "
                "for voice readout. Start with 'Here are today's top stories:'. "
                "Do not use markdown, asterisks, citations, or bullet points.\n\n"
                f"{context}"
            )
            res = ai.chat(prompt)
            if isinstance(res, str) and res.strip() and len(res.strip()) > 30:
                summary = res.strip().replace("*", "").replace('"', '').strip()
                clean_summary = re.sub(r'[^\x00-\x7F]+', ' ', summary).strip()
                return clean_summary
        except Exception:
            pass

    # Extractive structured fallback
    headlines = []
    for item in news_items[:3]:
        t = item["title"]
        src = item.get("source")
        if src:
            headlines.append(f"{t}, from {src}")
        else:
            headlines.append(t)
            
    intro = "Here are today's top headlines: "
    body = ". Also, ".join(headlines) + "."
    body = re.sub(r'[^\x00-\x7F]+', ' ', body).strip()
    return intro + body

def get_news_response(text: str) -> str:
    """Perform news search and return summarized text without speaking."""
    topic = extract_news_topic(text)
    safe_print(f"\n[Jarvis - News Search]: Query = '{topic}' (timelimit = 'd')")
    
    try:
        news_items = fetch_todays_news(query=topic, max_results=5)
        if not news_items and topic != "latest news today":
            news_items = fetch_todays_news(query="latest news today", max_results=5)
                
        if not news_items:
            response = "I couldn't find recent news at the moment."
        else:
            safe_print(f"[Jarvis - Retrieved {len(news_items)} news stories]:")
            for i, item in enumerate(news_items[:3], 1):
                safe_print(f"  {i}. {item['title']} ({item.get('source')})")
                safe_print(f"     {item['body'][:100]}...")
            response = summarize_news(news_items)
            
    except Exception as e:
        safe_print(f"[Jarvis - News Retrieval Error]: {e}")
        response = "Sorry, I couldn't retrieve today's news right now."

    return response

def handle_news_command(text: str) -> str:
    """
    Complete workflow for NEWS requests:
    """
    response = get_news_response(text)

    # Display in terminal
    safe_print(f"\n[Jarvis - News Summary]: {response}\n")

    # Log to file
    try:
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(f"\nYou : {text}\njarvis : {response}\n")
    except Exception:
        pass

    # Speak aloud via existing TTS
    speak(response)
    return response

if __name__ == "__main__":
    handle_news_command("what is happening in the news today")
