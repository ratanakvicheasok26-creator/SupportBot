import re
from typing import Dict, Any, List

def analyze_customer_message(text: str, history: List[str] = None) -> Dict[str, Any]:
    """
    Analyzes customer messages to observe their intent, urgency, and topic (Supports both Khmer & English).
    """
    if not text:
        return {
            "topic": "📎 Media / Attachment",
            "sentiment": "Neutral",
            "urgency": "Normal",
            "entities": []
        }

    lower = text.lower()

    # 1. Topic & Intent Analysis (Khmer & English)
    topics = []
    
    # Workflow & Architecture keywords
    workflow_keywords = [
        "workflow", "pipeline", "how it works", "process", "architecture", "edge", "server", "local", "privacy", "gpu", "cpu", "specs",
        "ដំណើរការ", "លំហូរ", "ស្ថាបត្យកម្ម", "របៀបដើរ", "របៀបដំណើរការ", "កុំព្យូទ័រ", "ផ្នែករឹង", "សុវត្ថិភាព"
    ]
    if any(w in lower for w in workflow_keywords):
        topics.append("🔄 Workflow & Architecture")
    
    # Camera & RTSP Compatibility keywords
    camera_keywords = [
        "rtsp", "onvif", "ip camera", "cctv", "hikvision", "dahua", "tapo", "uniview", "ezviz", "stream", "stream1", "port", "554", "lan", "wifi",
        "កាមេរ៉ា", "ភ្ជាប់", "ខ្សែ", "ភ្ជាប់កាមេរ៉ា", "ម៉ាក"
    ]
    if any(w in lower for w in camera_keywords):
        topics.append("📹 Camera & RTSP Compatibility")
        
    # AI Detection & Vision Features keywords
    ai_keywords = [
        "ai", "yolo", "detect", "detection", "tracking", "person", "vehicle", "car", "face", "face id", "loitering", "dwell", "roi", "zone", "absence",
        "ចាប់មនុស្ស", "ចាប់ឡាន", "ស្គាល់មុខ", "វត្តមាន", "តំបន់ហាមឃាត់", "ចលនា", "មុខងារ"
    ]
    if any(w in lower for w in ai_keywords):
        topics.append("🧠 AI Capabilities & Features")
        
    # Alerts & Telegram Integration keywords
    alert_keywords = [
        "alert", "telegram", "notification", "snapshot", "hud", "dashboard", "message", "log", "report",
        "ដាស់តឿន", "សារ", "តេឡេក្រាម", "រូបថត", "របាយការណ៍", "ផ្ញើសារ"
    ]
    if any(w in lower for w in alert_keywords):
        topics.append("📲 Alerts & Notifications")
        
    # Technical Support keywords
    support_keywords = [
        "help", "error", "problem", "broken", "issue", "cannot", "can't", "fix", "setup", "install", "not working", "support",
        "ជួយ", "ខូច", "មិនដំណើរការ", "អត់ដើរ", "មើលអត់កើត", "ជួសជុល", "បញ្ហា", "ដាច់", "សេវាអន់"
    ]
    if any(w in lower for w in support_keywords):
        topics.append("🛠️ Technical Support")
        
    # Greetings keywords
    greeting_keywords = [
        "hi", "hello", "hey", "good morning", "good afternoon", "good evening", "yo", "start",
        "សួស្តី", "ជំរាបសួរ", "ជម្រាបសួរ", "បាទ", "ចាស", "ចា៎"
    ]
    if any(w in lower for w in greeting_keywords):
        if not topics:
            topics.append("👋 Greeting & Intro")

    topic_str = " | ".join(topics) if topics else "💬 General Inquiry"

    # 2. Urgency Detection
    urgent_words = [
        "urgent", "asap", "immediately", "emergency", "fast", "right now", "please reply", "quick",
        "បន្ទាន់", "លឿន", "ឥឡូវ", "ប្រញាប់"
    ]
    is_urgent = any(w in lower for w in urgent_words)
    urgency_str = "🚨 High Priority" if is_urgent else "Normal"

    # 3. Sentiment Analysis
    frustrated_words = [
        "angry", "bad", "terrible", "worst", "hate", "scam", "waste", "waiting", "disappointed",
        "ខឹង", "យឺត", "បោក", "មិនល្អ", "ខកចិត្ត", "រង់ចាំយូរ"
    ]
    happy_words = [
        "thanks", "thank you", "great", "awesome", "good", "perfect", "love", "nice",
        "អរគុណ", "ល្អ", "សេវាកម្មល្អ", "ពេញចិត្ត", "ស្រលាញ់", "សប្បាយចិត្ត"
    ]

    if any(w in lower for w in frustrated_words):
        sentiment_str = "⚠️ Frustrated"
    elif any(w in lower for w in happy_words):
        sentiment_str = "😊 Friendly"
    else:
        sentiment_str = "Neutral"

    # 4. Extract Key Entities (Phone numbers, emails)
    phones = re.findall(r'(?:\+?855|0)\d{2,3}[\s-]?\d{3}[\s-]?\d{3,4}', text)
    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    
    entities = []
    if phones:
        entities.append(f"📞 Phone: {', '.join(phones)}")
    if emails:
        entities.append(f"📧 Email: {', '.join(emails)}")

    return {
        "topic": topic_str,
        "sentiment": sentiment_str,
        "urgency": urgency_str,
        "entities": entities
    }
