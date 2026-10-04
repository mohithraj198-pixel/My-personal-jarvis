import os
import re
from dotenv import load_dotenv
from TextToSpeech.Fast_DF_TTS import speak
from search_service import perform_web_search

load_dotenv()

try:
    from webscout import FreeAI
except ImportError:
    FreeAI = None

# Session memory to track the active project discussed
CURRENT_PROJECT = {
    "topic": "smart queue management",
    "description": ""
}

PROJECT_PATTERNS = [
    r'\b(project|projects)\b',
    r'\b(waste segregation)\b',
    r'\b(queue management)\b',
    r'\b(explain this project)\b',
    r'\b(explain the project)\b',
    r'\b(similar projects)\b',
    r'\b(what technologies can be used for this project)\b',
    r'\b(technologies (used|for) this project)\b',
    r'\b(existing solutions for this project)\b'
]

def is_project_query(text: str) -> bool:
    """Check if the text is asking about project ideas, technologies, or details."""
    lower = text.lower().strip()
    for pattern in PROJECT_PATTERNS:
        if re.search(pattern, lower):
            return True
    return False

def extract_project_topic(text: str) -> str:
    """Extract project topic or resolve 'this project' using session memory."""
    cleaned = re.sub(r'^(hey\s+|hello\s+|hi\s+|ok\s+)?jarvis[,:\s]*', '', text, flags=re.IGNORECASE).strip()
    lower = cleaned.lower()
    
    # Check for references to current project
    if any(k in lower for k in ["this project", "the project", "similar projects", "existing solutions"]):
        if CURRENT_PROJECT["topic"]:
            return CURRENT_PROJECT["topic"]
            
    # Remove prefix phrases
    prefixes = [
        r'^(?:please\s+)?tell\s+me\s+about\s+',
        r'^(?:please\s+)?search\s+for\s+projects\s+related\s+to\s+',
        r'^(?:please\s+)?search\s+the\s+web\s+for\s+',
        r'^(?:please\s+)?search\s+for\s+information\s+about\s+my\s+project\s*',
        r'^(?:please\s+)?search\s+for\s+information\s+about\s+',
        r'^(?:please\s+)?search\s+for\s+',
        r'^(?:please\s+)?find\s+information\s+about\s+',
        r'^(?:please\s+)?what\s+are\s+some\s+'
    ]
    for p in prefixes:
        cleaned = re.sub(p, '', cleaned, flags=re.IGNORECASE)
        
    cleaned = re.sub(r'\b(project|projects)\b', '', cleaned, flags=re.IGNORECASE).strip()
    cleaned = cleaned.rstrip('?.!').strip()
    
    if cleaned and len(cleaned) > 2:
        CURRENT_PROJECT["topic"] = cleaned
        return cleaned
        
    return CURRENT_PROJECT["topic"] or "artificial intelligence project"

def explain_project(topic: str, query_type: str = "overview") -> str:
    """Explain project aspects using web search and AI synthesis."""
    search_query = f"{topic} project"
    if query_type == "tech":
        search_query = f"technologies tools tech stack used for {topic} project"
    elif query_type == "solutions":
        search_query = f"existing solutions and implementations for {topic} project"
    elif query_type == "similar":
        search_query = f"similar project ideas to {topic}"

    # Perform web search to get real external data
    snippets = perform_web_search(search_query, max_results=3)
    combined = " ".join(snippets[:2])

    if FreeAI:
        try:
            ai = FreeAI()
            if query_type == "tech":
                prompt = (
                    f"In 2 clear and concise spoken sentences, explain what technologies, libraries, or hardware "
                    f"can be used to build a {topic} project. No markdown or bullet points."
                )
            elif query_type == "similar":
                prompt = (
                    f"In 2 concise spoken sentences, mention 2 or 3 similar project ideas related to {topic}. "
                    f"No markdown or bullet points."
                )
            elif query_type == "solutions":
                prompt = (
                    f"In 2 concise spoken sentences, explain existing real-world solutions or approaches for {topic}. "
                    f"No markdown or bullet points."
                )
            else:
                prompt = (
                    f"In 2 concise spoken sentences, explain the {topic} project, its purpose, and how it works. "
                    f"Use this context if helpful: {combined[:300]}. No markdown or bullet points."
                )
            res = ai.chat(prompt)
            if isinstance(res, str) and res.strip() and len(res.strip()) > 20:
                return res.strip().replace("*", "").replace('"', '').strip()
        except Exception:
            pass

    # Fallback to search snippets if AI is unavailable
    if snippets:
        return f"For the {topic} project, here is what I found: " + snippets[0][:200]
        
    return f"The {topic} project involves designing an automated system using software and hardware to solve real-world problems efficiently."

def handle_project_command(text: str) -> str:
    """Handle project-related queries, log, and speak via TTS."""
    lower = text.lower()
    
    # Determine aspect of the question
    if "technolog" in lower:
        query_type = "tech"
    elif "similar" in lower:
        query_type = "similar"
    elif "existing solution" in lower or "solutions" in lower:
        query_type = "solutions"
    else:
        query_type = "overview"

    topic = extract_project_topic(text)
    print(f"\n[Jarvis - Project Info]: Processing '{topic}' (aspect: {query_type})...")
    
    try:
        response = explain_project(topic, query_type)
    except Exception:
        response = "Sorry, I couldn't retrieve project information right now."

    print(f"[Jarvis - Project Explanation]: {response}")
    try:
        with open("log.txt", "a", encoding="utf-8") as f:
            f.write(f"\nYou : {text}\njarvis : {response}\n")
    except Exception:
        pass

    speak(response)
    return response

if __name__ == "__main__":
    handle_project_command("Jarvis, tell me about AI-based waste segregation.")
