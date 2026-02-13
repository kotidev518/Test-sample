from typing import List, Optional, Tuple, Dict
from motor.motor_asyncio import AsyncIOMotorDatabase
from app.services.embedding_service import embedding_service
from app.services.processing_queue_service import processing_worker

class VectorService:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def get_video_status(self, video_id: str) -> Optional[dict]:
        return await self.db.videos.find_one({"id": video_id})

    async def find_similar_videos(self, video_id: str, limit: int = 5, course_id: Optional[str] = None) -> List[dict]:
        source_video = await self.db.videos.find_one({"id": video_id})
        if not source_video:
            return None
            
        source_embedding = source_video.get("embedding")
        if not source_embedding:
            return []
            
        query = {"embedding": {"$exists": True, "$ne": None}, "id": {"$ne": video_id}}
        if course_id:
            query["course_id"] = course_id
            
        candidate_videos = await self.db.videos.find(
            query,
            {"id": 1, "title": 1, "embedding": 1, "course_id": 1, "thumbnail": 1, "_id": 0}
        ).to_list(length=1000)
        
        if not candidate_videos:
            return []
            
        candidates = [(v["id"], v["embedding"]) for v in candidate_videos]
        similar = await embedding_service.find_most_similar(source_embedding, candidates, top_k=limit)
        
        results = []
        for vid, score in similar:
            v_data = next((v for v in candidate_videos if v["id"] == vid), None)
            if v_data:
                results.append({
                    "video_id": vid,
                    "title": v_data["title"],
                    "similarity_score": round(score, 4),
                    "course_id": v_data["course_id"],
                    "thumbnail": v_data.get("thumbnail")
                })
        return results

    async def semantic_search(self, query_text: str, limit: int = 10, course_id: Optional[str] = None) -> List[dict]:
        query_embedding = await embedding_service.generate_embedding(query_text)
        if not query_embedding:
            return []
            
        # Search chunks
        chunk_query = {}
        if course_id:
            course_videos = await self.db.videos.find({"course_id": course_id}, {"id": 1}).to_list(length=1000)
            chunk_query["video_id"] = {"$in": [v["id"] for v in course_videos]}
        
        candidate_chunks = await self.db.video_chunks.find(
            chunk_query, {"video_id": 1, "text": 1, "embedding": 1, "_id": 0}
        ).to_list(length=2000)

        # Search videos
        video_query = {"embedding": {"$exists": True, "$ne": None}}
        if course_id: video_query["course_id"] = course_id
        candidate_videos = await self.db.videos.find(
            video_query, {"id": 1, "title": 1, "embedding": 1, "course_id": 1, "transcript": 1, "thumbnail": 1, "_id": 0}
        ).to_list(length=1000)
        
        search_candidates = []
        for c in candidate_chunks: search_candidates.append((c["video_id"], c["embedding"], "chunk", c["text"]))
        for v in candidate_videos: search_candidates.append((v["id"], v["embedding"], "full", v.get("transcript", "")))
        
        if not search_candidates: return []
        
        raw_candidates = [(f"{v_id}_{i}", emb) for i, (v_id, emb, t, txt) in enumerate(search_candidates)]
        similar = await embedding_service.find_most_similar(query_embedding, raw_candidates, top_k=limit * 2)
        
        grouped = {}
        for key, score in similar:
            idx = int(key.split('_')[-1])
            v_id, _, _, text = search_candidates[idx]
            if v_id not in grouped or score > grouped[v_id]["score"]:
                grouped[v_id] = {"score": score, "preview": text[:150] + "..." if len(text) > 150 else text}
        
        sorted_ids = sorted(grouped.items(), key=lambda x: x[1]["score"], reverse=True)[:limit]
        results = []
        for v_id, data in sorted_ids:
            v_info = next((v for v in candidate_videos if v["id"] == v_id), None)
            if not v_info: v_info = await self.db.videos.find_one({"id": v_id})
            if v_info:
                results.append({
                    "video_id": v_id,
                    "title": v_info["title"],
                    "similarity_score": round(data["score"], 4),
                    "course_id": v_info["course_id"],
                    "transcript_preview": data["preview"],
                    "thumbnail": v_info.get("thumbnail")
                })
        return results
