"""
Gemini AI Service for generating video metadata
- Generate accurate topics from video titles
- Create clean transcripts/summaries from descriptions
"""
import aiohttp
import json
from typing import List, Optional
from .config import settings


class GeminiService:
    """Service to interact with Google Gemini API for AI-generated content"""
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent"
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
    
    async def generate_topics(self, video_title: str, video_description: str = "") -> List[str]:
        """
        Generate accurate topics from video title and description using Gemini AI.
        Returns a list of 3-5 relevant topic keywords.
        """
        if not self.api_key:
            return self._fallback_topics(video_title)
        
        prompt = f"""Analyze this educational video and extract 3-5 key topic keywords.
        
Video Title: {video_title}
Description Preview: {video_description[:500] if video_description else 'No description'}

Return ONLY a JSON array of topic strings, no explanation. Example: ["Python", "Programming", "Variables"]
Topics should be:
- Short (1-3 words each)
- Relevant to the video content
- Good for categorization and search
"""
        
        try:
            result = await self._call_gemini(prompt)
            # Parse JSON array from response
            topics = json.loads(result.strip())
            if isinstance(topics, list) and len(topics) > 0:
                return topics[:5]  # Limit to 5 topics
        except Exception as e:
            print(f"Gemini topics error: {e}")
        
        return self._fallback_topics(video_title)
    
    async def generate_transcript_summary(self, video_title: str, video_description: str) -> str:
        """
        Generate a clean, concise summary/transcript from the video title and description.
        Removes promotional content and clutter.
        """
        if not self.api_key or not video_description:
            return self._clean_description(video_description or video_title)
        
        prompt = f"""Create a concise educational summary for this video. 
        
Video Title: {video_title}
Original Description: {video_description}

Instructions:
- Write 2-3 sentences summarizing what the viewer will learn
- Remove all promotional links, social media handles, and contact info
- Focus only on the educational content
- Keep it under 200 characters
- Do NOT include any URLs or hashtags
"""
        
        try:
            result = await self._call_gemini(prompt)
            if result and len(result) > 10:
                return result.strip()[:500]  # Limit length
        except Exception as e:
            print(f"Gemini summary error: {e}")
        
        return self._clean_description(video_description)
    
    async def generate_quiz(self, video_title: str, video_transcript: str, topics: List[str], difficulty: str = "Medium") -> List[dict]:
        """
        Generate a 4-question quiz based on video title, transcript, and topics using Gemini AI.
        Returns a list of question objects with options and correct_answer index.
        """
        if not self.api_key:
            return self._fallback_quiz(video_title, topics, difficulty)
        
        topic_str = ", ".join(topics) if topics else "General programming"
        
        prompt = f"""Generate exactly 4 multiple choice quiz questions for an educational video.

Video Title: {video_title}
Topics: {topic_str}
Difficulty: {difficulty}
Video Content Summary: {video_transcript[:1000] if video_transcript else 'Educational content about ' + video_title}

Return ONLY a valid JSON array with exactly 4 questions in this format:
[
  {{
    "question": "What is...",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": 0
  }}
]

Requirements:
- Make questions relevant to the video content and topics
- For {difficulty} difficulty, adjust complexity accordingly
- Each question must have exactly 4 options
- correct_answer is the index (0-3) of the correct option
- Questions should test understanding, not just memorization
- Return ONLY the JSON array, no other text
"""
        
        try:
            result = await self._call_gemini(prompt, max_tokens=1000)
            if result:
                # Clean the response - sometimes AI adds markdown code blocks
                clean_result = result.strip()
                if clean_result.startswith("```"):
                    clean_result = clean_result.split("```")[1]
                    if clean_result.startswith("json"):
                        clean_result = clean_result[4:]
                clean_result = clean_result.strip()
                
                questions = json.loads(clean_result)
                if isinstance(questions, list) and len(questions) >= 4:
                    # Validate and return first 4 questions
                    valid_questions = []
                    for q in questions[:4]:
                        if (isinstance(q, dict) and 
                            "question" in q and 
                            "options" in q and 
                            "correct_answer" in q and
                            isinstance(q["options"], list) and len(q["options"]) == 4):
                            valid_questions.append(q)
                    
                    if len(valid_questions) == 4:
                        return valid_questions
        except Exception as e:
            print(f"Gemini quiz generation error: {e}")
        
        return self._fallback_quiz(video_title, topics, difficulty)
    
    def _fallback_quiz(self, title: str, topics: List[str], difficulty: str) -> List[dict]:
        """Generate basic quiz if AI fails"""
        primary_topic = topics[0] if topics else "this topic"
        
        return [
            {
                "question": f"What is the main subject covered in '{title}'?",
                "options": [primary_topic, "Unrelated Topic", "Random Subject", "None of the above"],
                "correct_answer": 0
            },
            {
                "question": f"This video is aimed at which audience level?",
                "options": ["Beginner", "Intermediate", "Advanced", difficulty],
                "correct_answer": 3
            },
            {
                "question": f"Which concept is primarily discussed in this video?",
                "options": [primary_topic, "General Science", "History", "Art"],
                "correct_answer": 0
            },
            {
                "question": f"What type of content is this video?",
                "options": ["Entertainment", "Tutorial/Educational", "News", "Documentary"],
                "correct_answer": 1
            }
        ]
    
    async def _call_gemini(self, prompt: str, max_tokens: int = 200) -> Optional[str]:
        """Make API call to Gemini"""
        url = f"{self.BASE_URL}?key={self.api_key}"
        
        payload = {
            "contents": [{
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": 0.3,
                "maxOutputTokens": max_tokens
            }
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    candidates = data.get("candidates", [])
                    if candidates:
                        content = candidates[0].get("content", {})
                        parts = content.get("parts", [])
                        if parts:
                            return parts[0].get("text", "")
                else:
                    error = await response.text()
                    print(f"Gemini API error: {error}")
        
        return None
    
    def _fallback_topics(self, title: str) -> List[str]:
        """Extract basic topics from title if AI fails"""
        # Common programming/tech keywords to look for
        keywords = {
            'python', 'java', 'javascript', 'react', 'node', 'sql', 'database',
            'machine learning', 'ai', 'web', 'api', 'css', 'html', 'coding',
            'programming', 'tutorial', 'beginner', 'advanced', 'data', 'science'
        }
        
        title_lower = title.lower()
        found = []
        
        for keyword in keywords:
            if keyword in title_lower:
                found.append(keyword.title())
        
        # Always add "Programming" if nothing found
        if not found:
            words = title.split()[:3]
            found = [w.title() for w in words if len(w) > 3]
        
        return found[:5] if found else ['Technology', 'Tutorial']
    
    def _clean_description(self, description: str) -> str:
        """Basic cleaning of description without AI"""
        if not description:
            return ""
        
        lines = description.split('\n')
        clean_lines = []
        
        for line in lines:
            line = line.strip()
            # Skip lines with URLs or social media
            if any(x in line.lower() for x in ['http', 'www.', '@', 'instagram', 'linkedin', 'twitter', 'whatsapp', 'discord', 'coupon']):
                continue
            # Skip short lines (likely hashtags or handles)
            if len(line) < 20:
                continue
            clean_lines.append(line)
            # Only take first 2 meaningful lines
            if len(clean_lines) >= 2:
                break
        
        result = ' '.join(clean_lines)
        return result[:300] if result else description[:100]


# Singleton instance
gemini_service = GeminiService()
