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
    <div className="min-h-screen" data-testid="dashboard-page">
      <Navbar />
      
      <div className="container mx-auto px-4 lg:px-8 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl lg:text-4xl font-heading font-bold tracking-tight-more mb-2">
            Your Learning Dashboard
          </h1>
          <p className="text-muted-foreground">
            Track your progress and continue your learning journey
          </p>
        </motion.div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Next Best Video - Featured */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
            className="lg:col-span-2 lg:row-span-2"
          >
            <Card className="h-full border-2 border-primary/20 hover:border-primary/40 transition-colors">
              <CardHeader>
                <div className="flex items-center gap-2 mb-2">
                  <Sparkles className="h-5 w-5 text-accent" />
                  <span className="text-sm font-medium text-accent-foreground bg-accent px-2 py-1 rounded-full">
                    Next Best Video
                  </span>
                </div>
                <CardTitle className="text-2xl font-heading">
                  {recommendation?.video?.title}
                </CardTitle>
                <CardDescription className="text-base">
                  {recommendation?.reason}
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="aspect-video bg-muted rounded-lg overflow-hidden relative group">
                  <img
                    src={recommendation?.video?.thumbnail || "https://images.unsplash.com/photo-1546410531-bb4caa6b424d?auto=format&fit=crop&q=80&w=1000"}
                    alt={recommendation?.video?.title}
                    onError={(e) => {
                      e.target.onerror = null;
                      e.target.src = 'https://images.unsplash.com/photo-1546410531-bb4caa6b424d?auto=format&fit=crop&q=80&w=1000';
                    }}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-black/50 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                    <Play className="h-16 w-16 text-white" />
                  </div>
                </div>

                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Difficulty</span>
                    <span className="font-medium">{recommendation?.video?.difficulty}</span>
                  </div>
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-muted-foreground">Duration</span>
                    <span className="font-medium">
                      {Math.floor((recommendation?.video?.duration || 0) / 60)} min
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2 pt-2">
                    {recommendation?.video?.topics?.map((topic, idx) => (
                      <span
                        key={idx}
                        className="text-xs bg-secondary text-secondary-foreground px-2 py-1 rounded-full"
                      >
                        {topic}
                      </span>
                    ))}
                  </div>
                </div>

                <Button
                  onClick={handleWatchVideo}
                  className="w-full gap-2"
                  size="lg"
                  data-testid="watch-video-btn"
                >
                  <Play className="h-4 w-4" />
                  Start Learning
                </Button>
              </CardContent>
            </Card>
          </motion.div>

          {/* Stats Cards */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
            className="lg:col-span-2"
          >
            <div className="grid grid-cols-2 gap-4 h-full">
              {/* Completed Videos */}
              <Card data-testid="completed-videos-card">
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-2 rounded-lg bg-primary/10">
                      <BookOpen className="h-5 w-5 text-primary" />
                    </div>
                  </div>
                  <div>
                    <p className="text-3xl font-heading font-bold">
                      {progress?.completed_videos || 0}
                    </p>
                    <p className="text-sm text-muted-foreground">Videos Completed</p>
                  </div>
                </CardContent>
              </Card>

              {/* Quiz Score */}
              <Card data-testid="quiz-score-card">
                <CardContent className="p-6">
                  <div className="flex items-center gap-3 mb-3">
                    <div className="p-2 rounded-lg bg-accent/50">
                      <Award className="h-5 w-5 text-accent-foreground" />
                    </div>
                  </div>
                  <div>
                    <p className="text-3xl font-heading font-bold">
                      {Math.round(progress?.average_quiz_score || 0)}%
                    </p>
                    <p className="text-sm text-muted-foreground">Avg Quiz Score</p>
                  </div>
                </CardContent>
              </Card>

              {/* Completion Progress */}
              <Card className="col-span-2" data-testid="completion-progress-card">
                <CardContent className="p-6">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <TrendingUp className="h-4 w-4 text-primary" />
                      <span className="text-sm font-medium">Overall Progress</span>
                    </div>
                    <span className="text-2xl font-heading font-bold">
                      {Math.round(progress?.completion_percentage || 0)}%
                    </span>
                  </div>
                  <Progress value={progress?.completion_percentage || 0} className="h-2" />
                  <p className="text-xs text-muted-foreground mt-2">
                    {progress?.completed_videos || 0} of {progress?.total_videos || 0} videos
                  </p>
                </CardContent>
              </Card>
            </div>
          </motion.div>

          {/* Mastery Scores */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
            className="lg:col-span-2"
          >
            <Card className="h-full">
              <CardHeader>
                <CardTitle className="text-lg font-heading">Topic Mastery</CardTitle>
                <CardDescription>Your current mastery levels</CardDescription>
              </CardHeader>
              <CardContent>
                {recommendation?.mastery_scores &&
                Object.keys(recommendation.mastery_scores).length > 0 ? (
                  <div className="space-y-4">
                    {Object.entries(recommendation.mastery_scores)
                      .slice(0, 4)
                      .map(([topic, score]) => (
                        <div key={topic} className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="font-medium">{topic}</span>
                            <span className="text-muted-foreground">
                              {Math.round(score)}%
                            </span>
                          </div>
                          <Progress value={score} className="h-2" />
                        </div>
                      ))}
                    <Button
                      variant="outline"
                      className="w-full mt-4"
                      onClick={() => navigate('/analytics')}
                      data-testid="view-analytics-btn"
                    >
                      View Detailed Analytics
                    </Button>
                  </div>
                ) : (
                  <div className="text-center py-8 text-muted-foreground">
                    <p>Start learning to build your mastery scores</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Quick Actions */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.4 }}
          className="mt-8"
        >
          <Card>
            <CardContent className="p-6">
              <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
                <div>
                  <h3 className="font-heading font-semibold text-lg mb-1">
                    Explore More Courses
                  </h3>
                  <p className="text-sm text-muted-foreground">
                    Browse our full catalog of courses and videos
                  </p>
                </div>
                <Button
                  onClick={() => navigate('/courses')}
                  variant="outline"
                  data-testid="browse-courses-btn"
                >
                  Browse Courses
                </Button>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
};

export default DashboardPage;
