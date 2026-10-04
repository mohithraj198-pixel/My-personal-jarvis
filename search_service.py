import os
import re
from dotenv import load_dotenv
from TextToSpeech.Fast_DF_TTS import speak

load_dotenv()

# Keyless search library
try:
    from ddgs import DDGS
except ImportError:
    DDGS = None

# Resilient fallback search providers
try:
    from webscout import DuckDuckGoSearch, FreeAI
except ImportError:
    DuckDuckGoSearch = None
    FreeAI = None

try:
    import wikipedia
except ImportError:
    wikipedia = None

# Command detection patterns for search
SEARCH_PATTERNS = [
    r'\b(search\s+for\s+information\s+about)\b',
    r'\b(search\s+the\s+web\s+for)\b',
    r'\b(search\s+online\s+for)\b',
    r'\b(find\s+information\s+about)\b',
    r'\b(find\s+information\s+on)\b',
    r'\b(find\s+out\s+about)\b',
    r'\b(look\s+up)\b',
    r'\b(what\s+are\s+the\s+latest\s+developments\s+in)\b',
    r'\b(what\s+are\s+the\s+latest)\b',
    r'\b(search\s+the\s+latest\s+information\s+about)\b',
    r'\b(search\s+latest\s+information\s+about)\b',
    r'\b(search\s+for)\b',
    r'\b(search\s+about)\b',
    r'\b(find\s+similar\s+projects)\b',
    r'\b(existing\s+solutions\s+to\s+this\s+problem)\b',
    r'\b(existing\s+solutions\s+for\s+this\s+project)\b'
]

# Simple in-memory cache for repeated searches
SEARCH_CACHE = {}

def is_search_query(text: str) -> bool:
    """Check if the text is a web search command."""
    lower = text.lower().strip()
    
    # Do not intercept explicit browser opening commands
    if "open edge" in lower or "open microsoft edge" in lower or "open browser" in lower:
        return False
        
    for pattern in SEARCH_PATTERNS:
        if re.search(pattern, lower):
            return True
            
    if lower.startswith("search ") and not lower.startswith("search in google"):
        return True
        
    return False

def requires_fresh_search(text: str) -> bool:
    """Detect if the user is asking for current/latest information."""
    lower = text.lower()
    time_markers = ["latest", "today", "current", "recent", "this week", "now", "breaking", "new"]
    return any(marker in lower for marker in time_markers)

def clean_query_text(text: str) -> str:
    """Extract the clean subject query from user speech."""
    cleaned = text.strip()
    # Strip wake word prefixes
    cleaned = re.sub(r'^(hey\s+|hello\s+|hi\s+|ok\s+)?jarvis[,:\s]*', '', cleaned, flags=re.IGNORECASE).strip()
    
    prefixes = [
        r'^(?:please\s+)?search\s+the\s+latest\s+information\s+about\s+',
        r'^(?:please\s+)?search\s+latest\s+information\s+about\s+',
        r'^(?:please\s+)?search\s+for\s+information\s+about\s+',
        r'^(?:please\s+)?search\s+for\s+information\s+on\s+',
        r'^(?:please\s+)?search\s+the\s+web\s+for\s+',
        r'^(?:please\s+)?search\s+online\s+for\s+',
        r'^(?:please\s+)?find\s+information\s+about\s+',
        r'^(?:please\s+)?find\s+information\s+on\s+',
        r'^(?:please\s+)?find\s+out\s+about\s+',
        r'^(?:please\s+)?search\s+for\s+',
        r'^(?:please\s+)?search\s+about\s+',
        r'^(?:please\s+)?search\s+',
        r'^(?:please\s+)?what\s+are\s+the\s+latest\s+developments\s+in\s+',
        r'^(?:please\s+)?what\s+are\s+the\s+latest\s+',
        r'^(?:please\s+)?look\s+up\s+',
        r'^(?:please\s+)?tell\s+me\s+about\s+'
    ]
    for p in prefixes:
        cleaned = re.sub(p, '', cleaned, flags=re.IGNORECASE)
        
    cleaned = cleaned.rstrip('?.!').strip()
    return cleaned

def web_search(query: str, max_results: int = 5) -> list:
    """
    Perform programmatic keyless web search using the DDGS library.
    Extracts title, URL, and body/snippet for each result.
    Does NOT launch Edge, Chrome, or Selenium.
    """
    results = []
    
    # 1. Primary: ddgs package (zero API key)
    if DDGS:
        try:
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(query, max_results=max_results))
                for item in raw_results:
                    title = item.get("title", "").strip()
                    href = item.get("href", "").strip()
                    body = item.get("body", "").strip()
                    if title or body:
                        results.append({
                            "title": title,
                            "href": href,
                            "body": body
                        })
                if results:
                    return results
        except Exception:
            pass

    # 2. Resilient fallback: webscout DuckDuckGo text search
    if not results and DuckDuckGoSearch:
        try:
            ddg = DuckDuckGoSearch()
            raw_res = ddg.text(query, max_results=max_results)
            for r in raw_res:
                title = getattr(r, "title", "").strip()
                href = getattr(r, "href", "").strip()
                body = getattr(r, "body", "").strip()
                if title or body:
                    results.append({
                        "title": title,
                        "href": href,
                        "body": body
                    })
            if results:
                return results
        except Exception:
            pass

    # 3. Third fallback: Wikipedia for encyclopedic concepts
    if not results and wikipedia:
        try:
            summary = wikipedia.summary(query, sentences=3)
            if summary:
                results.append({
                    "title": query.title(),
                    "href": "https://en.wikipedia.org",
                    "body": summary.strip()
                })
                return results
        except Exception:
            pass

    return results

perform_web_search = web_search

def summarize_search_results(query: str, results: list) -> str:
    """
    Create a concise, spoken-friendly summary from extracted search results.
    Does not dump raw response into TTS.
    """
    if not results:
        return "Sorry, I couldn't search the web right now."

    # Extract clean text snippets from top results
    snippets = []
    for r in results[:3]:
        snippet = r.get("body", "").strip()
        if snippet:
            snippets.append(snippet)

    combined_text = " ".join(snippets)

    # Use AI synthesis if available for fluid natural speech
    if FreeAI:
        try:
            ai = FreeAI()
            prompt = (
                f"You are the voice assistant Jarvis. Based on these search results for '{query}', "
                f"provide a natural, concise 1 to 2 sentence spoken summary answering the user. "
                f"Start directly with the answer (e.g. 'I found several...', 'According to current information...'). "
                f"Do not use markdown, asterisks, bullet points, or URLs.\n\n"
                f"Results:\n{combined_text[:600]}"
            )
            res = ai.chat(prompt)
            if isinstance(res, str) and res.strip() and len(res.strip()) > 20:
                summary = res.strip().replace("*", "").replace('"', '').strip()
                return summary
        except Exception:
            pass

    # Clean extractive fallback
    sentences = re.split(r'(?<=[.!?])\s+', combined_text)
    meaningful = [s.strip() for s in sentences if len(s.strip()) > 15]
    summary = " ".join(meaningful[:2]).strip()
    
    # Strip any unprintable or non-ASCII characters so TTS engines and terminal prints never fail
    clean_summary = re.sub(r'[^\x00-\x7F]+', ' ', summary).strip()
    clean_summary = re.sub(r'\s+', ' ', clean_summary)
    
    if clean_summary:
        return f"According to current search results, {clean_summary}"
    elif results[0].get("body"):
        fallback_body = re.sub(r'[^\x00-\x7F]+', ' ', results[0]['body'][:200]).strip()
        return f"I found the following information: {fallback_body}"
    
    return "Sorry, I couldn't search the web right now."

def safe_print(msg: str):
    """Safely print to console on Windows without charmap encoding issues."""
    try:
        print(msg)
    except (UnicodeEncodeError, Exception):
        try:
            print(str(msg).encode("ascii", errors="replace").decode("ascii"))
        except Exception:
            pass

def get_search_response(text: str) -> str:
    """Perform web search and return summarized text without speaking."""
    query = clean_query_text(text)
    fresh = requires_fresh_search(text)
    
    safe_print(f"\n[Jarvis - Web Search]: Query = '{query}' (Fresh Search: {fresh})")

    # Check cache if not requiring fresh search
    if not fresh and query in SEARCH_CACHE:
        response = SEARCH_CACHE[query]
        safe_print(f"[Jarvis - Cached Result]: {response}")
    else:
        try:
            results = web_search(query, max_results=5)
            
            if not results:
                response = "Sorry, I couldn't search the web right now."
            else:
                # Display extracted results in terminal
                safe_print(f"[Jarvis - Retrieved {len(results)} results]:")
                for i, r in enumerate(results[:3], 1):
                    safe_print(f"  {i}. {r['title']} -> {r['href']}")
                    safe_print(f"     {r['body'][:120]}...")
                
                response = summarize_search_results(query, results)
                if response != "Sorry, I couldn't search the web right now.":
                    SEARCH_CACHE[query] = response
                    
        except Exception as e:
            safe_print(f"[Jarvis - Search Error]: {e}")
            response = "Sorry, I couldn't search the web right now."

    return response

def handle_search_command(text: str) -> str:
    """
    Search workflow that speaks the response.
    """
    response = get_search_response(text)
    safe_print(f"\n[Jarvis - Search Answer]: {response}\n")

    # Log interaction
    try:
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(f"\nYou : {text}\njarvis : {response}\n")
    except Exception:
        pass

    # 6. Speak the answer using existing TTS
    speak(response)
    return response

if __name__ == "__main__":
    handle_search_command("Jarvis, search for AI project ideas")
