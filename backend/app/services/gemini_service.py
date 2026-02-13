"""
Gemini AI Service for generating video metadata
- Generate accurate topics from video titles
- Create clean transcripts/summaries from descriptions
"""
import aiohttp
import json
from typing import List, Optional
from app.database import db
from app.core.config import settings


class GeminiService:
    """Service to interact with Google Gemini API for AI-generated content"""
    
    BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
    
    async def generate_topics(self, video_title: str, video_description: str = "", transcript: str = "") -> List[str]:
        """
        Generate accurate topics from video title, description, and transcript using Gemini AI.
        Returns a list of 3-5 relevant topic keywords.
        """
        if not self.api_key:
            return self._fallback_topics(video_title)
        
        # Prefer transcript over description for better accuracy
        content_source = ""
        if transcript:
            content_source = f"Transcript: {transcript}"
        elif video_description:
            content_source = f"Description Preview: {video_description[:500]}"
        else:
            content_source = "No description or transcript available"
        
        prompt = f"""Analyze this educational video and extract 3-5 key topic keywords.
        
Video Title: {video_title}
{content_source}

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
    
    async def generate_transcript_summary(self, video_title: str, video_description: str, transcript: str = "") -> str:
        """
        Generate a clean, concise summary from the video title, description, and transcript.
        Prefers real transcript content over description when available.
        """
        if not self.api_key or (not video_description and not transcript):
            return self._clean_description(video_description or video_title)
        
        # Build the content section based on what's available
        if transcript:
            content_section = f"Video Transcript:\n{transcript}"
        else:
            content_section = f"Original Description:\n{video_description}"
        
        prompt = f"""Create a concise educational summary for this video. 
        
Video Title: {video_title}
{content_section}

Instructions:
- Write 2-3 sentences summarizing what the viewer will learn
- Remove all promotional links, social media handles, and contact info
- Focus only on the educational content
- Keep it under 200 characters
- Do NOT include any URLs or hashtags
"""
        
        try:
            result = await self._call_gemini(prompt, max_tokens=400)
            if result and len(result) > 10:
                return result.strip()[:500]  # Limit length
        except Exception as e:
            print(f"Gemini summary error: {e}")
        
        return self._clean_description(video_description)
    
    async def generate_quiz(self, video_title: str, video_transcript: str, topics: List[str], difficulty: str = "Medium", num_questions: int = 4) -> List[dict]:
        """
        Generate a quiz based on video title, transcript, and topics using Gemini AI.
        Returns a list of question objects with options and correct_answer index.
        
        Args:
            num_questions: Number of MCQ questions to generate (default: 4)
        """
        if not self.api_key:
            print(f"Quiz fallback: No Gemini API key configured")
            return self._fallback_quiz(video_title, topics, difficulty)[:num_questions]
        
        topic_str = ", ".join(topics) if topics else "General programming"
        
        # Use full transcript for richer quiz content
        content_text = video_transcript if video_transcript else f"Educational content about {video_title}"
        print(f"Generating quiz for '{video_title}' | Transcript length: {len(video_transcript)} chars | Questions: {num_questions}")
        
        prompt = f"""Generate exactly {num_questions} multiple choice quiz questions for an educational video.

Video Title: {video_title}
Topics: {topic_str}
Difficulty: {difficulty}
Video Transcript: {content_text}

Return ONLY a valid JSON array with exactly {num_questions} questions in this format:
[
  {{
    "question": "What is...",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": 0
  }}
]

Requirements:
- All questions MUST be directly based on specific facts, concepts, or explanations from the transcript
- Do NOT create generic or vague questions — each question should reference actual content from the video
- For {difficulty} difficulty, adjust complexity accordingly
- Each question must have exactly 4 options
- correct_answer is the index (0-3) of the correct option
- Questions should test understanding, not just memorization
- All questions and options must be related to the video content
- Return ONLY the JSON array, no other text
"""
        
        try:
            result = await self._call_gemini(prompt, max_tokens=1500)
            if result:
                # Clean the response - sometimes AI adds markdown code blocks
                clean_result = result.strip()
                if clean_result.startswith("```"):
                    # Handle ```json ... ``` format
                    parts = clean_result.split("```")
                    if len(parts) >= 2:
                        clean_result = parts[1]
                        if clean_result.startswith("json"):
                            clean_result = clean_result[4:]
                clean_result = clean_result.strip()
                
                questions = json.loads(clean_result)
                if isinstance(questions, list):
                    # Validate questions
                    valid_questions = []
                    for q in questions:
                        if (isinstance(q, dict) and 
                            "question" in q and 
                            "options" in q and 
                            "correct_answer" in q and
                            isinstance(q["options"], list) and len(q["options"]) == 4):
                            valid_questions.append(q)
                    
                    print(f"Quiz for '{video_title}': {len(valid_questions)} valid questions from {len(questions)} total")
                    
                    if len(valid_questions) >= num_questions - 1:
                        # Pad with fallback questions if we have fewer than requested
                        if len(valid_questions) < num_questions:
                            fallback = self._fallback_quiz(video_title, topics, difficulty)
                            while len(valid_questions) < num_questions and fallback:
                                valid_questions.append(fallback.pop(0))
                        return valid_questions[:num_questions]
                else:
                    print(f"Quiz parse error: Expected list, got {type(questions)}")
            else:
                print(f"Quiz error: Gemini returned empty result for '{video_title}'")
        except json.JSONDecodeError as e:
            print(f"Quiz JSON parse error for '{video_title}': {e}")
            print(f"Raw response: {result[:200] if result else 'None'}")
        except Exception as e:
            print(f"Gemini quiz generation error for '{video_title}': {e}")
        
        # Return empty list on failure instead of static fallback
        return []

    async def ask_video_chatbot(self, user_name: str, video_title: str, video_transcript: str, user_question: str) -> str:
        """
        Answering user questions about a specific video using Gemini AI.
        """
        if not self.api_key:
            return "I'm sorry, I cannot answer questions at the moment as the AI service is not configured."

        # Expanded greeting detection
        clean_question = user_question.lower().strip().rstrip('?')
        greetings = ['hi', 'hello', 'hey', 'greetings', 'how are you', 'howdy', 'hi there', 'hello there']
        if clean_question in greetings:
            return f"hi {user_name}. what would you like me to answer?"

        # Context-aware answering
        prompt = f"""You are an educational assistant chatbot for a video learning platform.
The user is watching a video titled: "{video_title}"

Transcript of the video:
{video_transcript}

User Question: "{user_question}"

Instructions:
1. Provide a clear, helpful answer based ONLY on the video content provided in the transcript.
2. If the answer is not in the transcript, politely say you don't have that information.
3. For content-related questions (e.g., "What is X?", "Explain Y"), your answer MUST be between 100-150 words.
4. For simple greetings or non-content conversational questions that weren't caught by the system, respond very briefly (under 20 words) like: "hi {user_name}. what would you like me to answer?"
5. Use a friendly, encouraging tone.
6. Do NOT include any filler text like "Based on the transcript..." or "Hi there!". Just answer the question directly.

Answer:
"""
        try:
            result = await self._call_gemini(prompt, max_tokens=600)
            if result:
                return result.strip()
        except Exception as e:
            print(f"Gemini chatbot error: {e}")
        
        return "I'm sorry, I'm having trouble processing your question right now. Please try again later."

    def _fallback_quiz(self, title: str, topics: List[str], difficulty: str) -> List[dict]:
        """Generate basic quiz if AI fails - DEPRECATED: Returns empty list now"""
        return []

    async def _call_gemini(self, prompt: str, max_tokens: int = 200) -> Optional[str]:
        """Make API call to Gemini with retry for rate limits"""
        import asyncio
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
        
        max_retries = 3
        for attempt in range(max_retries + 1):
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
                    elif response.status == 429 and attempt < max_retries:
                        wait_time = 2 ** (attempt + 1)  # 2s, 4s, 8s
                        print(f"Gemini rate limited, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries})")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        error = await response.text()
                        print(f"Gemini API error (status {response.status}): {error[:200]}")
            break
        
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
