import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { analyticsService } from '@/services/analyticsService';
import { Navbar } from '@/components/Navbar';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Sparkles, Play, TrendingUp, Award, BookOpen } from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';

const DashboardPage = () => {
  const navigate = useNavigate();
  const [recommendation, setRecommendation] = useState(null);
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const { recommendation, progress } = await analyticsService.getDashboardData();
      setRecommendation(recommendation);
      setProgress(progress);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
      toast.error('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleWatchVideo = () => {
    if (recommendation?.video) {
      navigate(`/video/${recommendation.video.id}`);
    }
  };

  if (loading) {
    return (
      <div>
        <Navbar />
        <div className="container mx-auto px-4 py-12">
          <div className="animate-pulse space-y-6">
            <div className="h-64 bg-muted rounded-lg" />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="h-32 bg-muted rounded-lg" />
              <div className="h-32 bg-muted rounded-lg" />
              <div className="h-32 bg-muted rounded-lg" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="relative min-h-screen">

      {/* ================= FORCE BACKGROUND ================= */}
      <div className="fixed inset-0 -z-50">

        {/* Base */}
        <div className="absolute inset-0 bg-gradient-to-br from-purple-100 via-white to-pink-100" />

        {/* Orbs */}
        <div className="absolute -top-40 -left-40 w-[500px] h-[500px] bg-purple-400/40 rounded-full blur-[180px]" />
        <div className="absolute -bottom-40 -right-40 w-[500px] h-[500px] bg-pink-400/40 rounded-full blur-[180px]" />



      </div>


      {/* ================= CONTENT ================= */}
      <div className="relative z-10">

        <Navbar />


        <main className="max-w-7xl mx-auto px-6 py-8">
          {/* ===== DASHBOARD HEADER ===== */}
          <div className="mb-8">

            <h1 className="text-3xl md:text-4xl font-bold mb-2">
              Your Learning Dashboard
            </h1>

            <p className="text-slate-500">
              Track your progress and continue your learning journey
            </p>

          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">


            {/* LEFT */}
            <div className="lg:col-span-7">

              <div className="bg-white/80 backdrop-blur-xl border border-white/50 rounded-3xl p-6 shadow-xl flex flex-col">

                {/* Badge */}
                <span className="inline-block bg-purple-100 text-purple-700 text-xs font-bold px-3 py-1 rounded-full mb-3 w-fit">
                  ⭐ Next Best Video
                </span>

                {/* Title */}
                <h1 className="text-2xl font-bold leading-snug mb-1 line-clamp-2">
                  {recommendation?.video?.title || "No Recommendation"}
                </h1>

                {/* Subtitle */}
                <p className="text-slate-500 text-sm mb-4 line-clamp-1">
                  {recommendation?.reason}
                </p>


                {/* Video */}
                <div className="relative aspect-video max-h-[260px] rounded-2xl overflow-hidden mb-4 shadow-lg">

                  <img
                    src="https://images.unsplash.com/photo-1741699427799-3fbb70fce948"
                    className="w-full h-full object-cover"
                    alt="video"
                  />

                  <div className="absolute inset-0 bg-black/20 flex items-center justify-center">

                    <button
                      onClick={handleWatchVideo}
                      className="w-16 h-16 bg-white/30 rounded-full text-white text-2xl backdrop-blur"
                    >
                      ▶
                    </button>

                  </div>

                </div>


                {/* Info */}
                <div className="grid grid-cols-2 gap-3 mb-4">

                  <div className="p-3 bg-slate-50 rounded-xl border">

                    <p className="text-[11px] text-slate-400 uppercase">Difficulty</p>

                    <p className="font-semibold text-sm">
                      {recommendation?.video?.difficulty}
                    </p>

                  </div>


                  <div className="p-3 bg-slate-50 rounded-xl border">

                    <p className="text-[11px] text-slate-400 uppercase">Duration</p>

                    <p className="font-semibold text-sm">
                      {Math.floor((recommendation?.video?.duration || 0) / 60)} min
                    </p>

                  </div>

                </div>


                {/* Button */}
                <Button
                  onClick={handleWatchVideo}
                  className="w-full py-3 bg-gradient-to-r from-purple-600 to-violet-500 text-white rounded-xl font-bold text-sm mt-auto"
                >
                  ▶ Start Learning
                </Button>

              </div>

            </div>



            {/* RIGHT */}
            <div className="lg:col-span-5 space-y-8">


              <div className="grid grid-cols-2 gap-4">

                <div className="bg-white/80 backdrop-blur-xl p-6 rounded-3xl border shadow">

                  <p className="text-4xl font-black">

                    {progress?.completed_videos || 0}

                  </p>

                  <p className="text-xs text-slate-400">

                    Videos Completed

                  </p>

                </div>


                <div className="bg-white/80 backdrop-blur-xl p-6 rounded-3xl border shadow">

                  <p className="text-4xl font-black">

                    {Math.round(progress?.average_quiz_score || 0)}%

                  </p>

                  <p className="text-xs text-slate-400">

                    Avg Quiz Score

                  </p>

                </div>

              </div>



              <div className="bg-white/80 backdrop-blur-xl p-6 rounded-3xl border shadow">

                <div className="flex justify-between mb-3">

                  <p className="font-bold">Overall Progress</p>

                  <p className="text-purple-600 font-bold">

                    {Math.round(progress?.completion_percentage || 0)}%

                  </p>

                </div>


                <div className="h-3 bg-slate-100 rounded-full overflow-hidden mb-2">

                  <div
                    className="h-full bg-purple-600"
                    style={{
                      width: `${progress?.completion_percentage || 0}%`,
                    }}
                  />

                </div>

              </div>



              <div className="bg-white/80 backdrop-blur-xl p-8 rounded-3xl border shadow">

                <h3 className="text-xl font-bold mb-4">

                  Topic Mastery

                </h3>


                {recommendation?.mastery_scores ? (

                  Object.entries(recommendation.mastery_scores)
                    .slice(0, 3)
                    .map(([topic, score]) => (

                      <div key={topic} className="mb-4">

                        <div className="flex justify-between mb-1 text-sm font-semibold">

                          <span>{topic}</span>

                          <span>{Math.round(score)}%</span>

                        </div>

                        <Progress value={score} className="h-2" />

                      </div>

                    ))

                ) : (

                  <p className="text-center text-slate-500">

                    No Data Available

                  </p>

                )}

              </div>

            </div>

          </div>



          {/* FOOTER */}

          <div className="mt-10 bg-white/80 backdrop-blur-xl p-8 rounded-3xl border shadow flex justify-between items-center">

            <div>

              <h2 className="text-2xl font-bold">
                Explore More Courses
              </h2>

              <p className="text-slate-500">
                Browse our full curriculum
              </p>

            </div>


            <Button
              onClick={() => navigate("/courses")}
              className="bg-slate-900 text-white px-8 py-4 rounded-2xl font-bold"
            >
              Browse Full Catalog
            </Button>

          </div>

        </main>

      </div>

    </div>
  );


}
export default DashboardPage;
