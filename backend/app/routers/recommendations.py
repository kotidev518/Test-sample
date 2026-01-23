from fastapi import APIRouter, Depends, HTTPException
import numpy as np

from ..database import db, sbert_model
from ..schemas import Video, NextVideoRecommendation
from ..dependencies import get_current_user
from ..utils import get_video_url

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.get("/next-video", response_model=NextVideoRecommendation)
async def get_next_video_recommendation(user = Depends(get_current_user)):
    """AI-based recommendation using SBERT embeddings and mastery scores"""
    
    # Get user's mastery scores
    mastery_list = await db.mastery_scores.find({"user_id": user['id']}, {"_id": 0}).to_list(1000)
    mastery_dict = {m['topic']: m['score'] for m in mastery_list}
    
    # Get user's progress
    progress_list = await db.user_progress.find({"user_id": user['id']}, {"_id": 0}).to_list(1000)
    watched_videos = {p['video_id']: p for p in progress_list}
    
    # Get all videos
    all_videos = await db.videos.find({}, {"_id": 0}).sort("order", 1).to_list(1000)
    
    if not all_videos:
        raise HTTPException(status_code=404, detail="No videos available")
    
    # Get user's last watched video for semantic similarity
    last_watched_video = None
    if progress_list:
        sorted_progress = sorted(progress_list, key=lambda x: x.get('timestamp', ''), reverse=True)
        if sorted_progress:
            last_watched_video = await db.videos.find_one({"id": sorted_progress[0]['video_id']}, {"_id": 0})
    
    # Calculate scores for each unwatched video
    candidate_videos = []
    
    for video in all_videos:
        video_id = video['id']
        
        # Skip completed videos
        if video_id in watched_videos and watched_videos[video_id].get('completed', False):
            continue
        
        # Prioritize partially watched videos
        if video_id in watched_videos and not watched_videos[video_id].get('completed', False):
            candidate_videos.append({
                'video': video,
                'score': 1000,  # Highest priority
                'reason': f"Continue watching '{video['title']}' ({watched_videos[video_id]['watch_percentage']:.0f}% completed)"
            })
            continue
        
        # Calculate recommendation score
        score = 0
        reasons = []
        
        # 1. Mastery-based scoring (40% weight)
        video_topics = video.get('topics', [])
        if video_topics and mastery_dict:
            topic_scores = [mastery_dict.get(topic, 0) for topic in video_topics]
            avg_mastery = sum(topic_scores) / len(topic_scores) if topic_scores else 0
            
            # Prefer topics with 40-70% mastery (optimal learning zone)
            if 40 <= avg_mastery <= 70:
                score += 40
                reasons.append(f"Optimal challenge level for {video_topics[0]}")
            elif avg_mastery < 40:
                score += 30
                reasons.append(f"Build foundation in {video_topics[0]}")
            else:
                score += 20
        else:
            # No mastery data yet - prioritize easier content
            if video['difficulty'] == user.get('initial_level', 'Easy'):
                score += 35
                reasons.append(f"Matches your {user.get('initial_level', 'Easy')} level")
        
        # 2. Difficulty progression (20% weight)
        difficulty_map = {'Easy': 1, 'Medium': 2, 'Hard': 3}
        user_level = difficulty_map.get(user.get('initial_level', 'Easy'), 2)
        video_level = difficulty_map.get(video['difficulty'], 2)
        
        if video_level == user_level:
            score += 20
        elif video_level == user_level + 1:
            score += 15  # Slightly harder is good
            reasons.append("Next difficulty level")
        elif video_level == user_level - 1:
            score += 10
        
        # 3. Semantic similarity (30% weight)
        if last_watched_video:
            try:
                # Get embeddings - assuming sbert_model is loaded
                if sbert_model:
                    if 'embedding' not in video:
                        # Generate embedding on-the-fly
                        video_embedding = sbert_model.encode(video.get('transcript', video['description']))
                    else:
                        video_embedding = np.array(video['embedding'])
                    
                    if 'embedding' not in last_watched_video:
                        last_embedding = sbert_model.encode(last_watched_video.get('transcript', last_watched_video['description']))
                    else:
                        last_embedding = np.array(last_watched_video['embedding'])
                    
                    # Cosine similarity
                    similarity = np.dot(video_embedding, last_embedding) / (
                        np.linalg.norm(video_embedding) * np.linalg.norm(last_embedding)
                    )
                    similarity_score = float(similarity) * 30
                    score += similarity_score
                    
                    if similarity > 0.7:
                        reasons.append(f"Related to '{last_watched_video['title']}'")
            except Exception as e:
                # print(f"Error in similarity calculation: {e}")
                pass
        
        # 4. Sequential ordering (10% weight)
        if video.get('order', 0) < 10:  # Early videos in sequence
            score += 10 - video.get('order', 0)
        
        # 5. Course consistency (High priority)
        if last_watched_video and video['course_id'] == last_watched_video['course_id']:
            score += 100
            reasons.append(f"Continue in '{last_watched_video.get('course_id', 'this course')}'")
        
        candidate_videos.append({
            'video': video,
            'score': score,
            'reason': reasons[0] if reasons else f"Learn {video['title']}"
        })
    
    if not candidate_videos:
        # All videos completed - recommend from start
        recommended = all_videos[0]
        reason = "Congratulations! Review from the beginning"
    else:
        # Sort by score and return top recommendation
        candidate_videos.sort(key=lambda x: x['score'], reverse=True)
        best = candidate_videos[0]
        recommended = best['video']
        reason = best['reason']
    
    recommended_video = Video(**recommended)
    if hasattr(recommended_video, 'url'):
        recommended_video.url = get_video_url(recommended_video.url)

    return NextVideoRecommendation(
        video=recommended_video,
        reason=reason,
        mastery_scores=mastery_dict
    )
