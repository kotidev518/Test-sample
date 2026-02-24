import React, { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { analyticsService } from '@/services/analyticsService';
import { Navbar } from '@/components/Navbar';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, Target, Award, BookOpen } from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Legend
} from 'recharts';

const AnalyticsPage = () => {
  const [masteryScores, setMasteryScores] = useState([]);
  const [progress, setProgress] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      const [masteryData, progressData] = await Promise.all([
        analyticsService.getMasteryScores(),
        analyticsService.getOverallProgress()
      ]);
      setMasteryScores(masteryData);
      setProgress(progressData);
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
      toast.error('Failed to load analytics');
    } finally {
      setLoading(false);
    }
  };

  const getMasteryLevel = (score) => {
    if (score >= 80) return { label: 'Expert', color: 'text-green-600' };
    if (score >= 60) return { label: 'Proficient', color: 'text-blue-600' };
    if (score >= 40) return { label: 'Learning', color: 'text-yellow-600' };
    return { label: 'Beginner', color: 'text-gray-600' };
  };

  const chartData = masteryScores.map((m) => ({
    topic: m.topic,
    score: Math.round(m.score)
  }));

  const radarData = masteryScores.slice(0, 6).map((m) => ({
    topic: m.topic.length > 10 ? m.topic.substring(0, 10) + '...' : m.topic,
    mastery: Math.round(m.score)
  }));

  if (loading) {
    return (
      <div>
        <Navbar />
        <div className="container mx-auto px-4 py-12">
          <div className="animate-pulse space-y-6">
            <div className="h-12 bg-muted rounded w-64" />
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-32 bg-muted rounded-lg" />
              ))}
            </div>
            <div className="h-96 bg-muted rounded-lg" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" data-testid="analytics-page">
      <Navbar />
      
      <div className="container mx-auto px-4 lg:px-8 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl lg:text-4xl font-heading font-bold tracking-tight-more mb-2">
            Learning Analytics
          </h1>
          <p className="text-muted-foreground">
            Track your progress and master new topics
          </p>
        </motion.div>

        {/* Stats Overview */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card data-testid="completed-videos-stat">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 rounded-lg bg-primary/10">
                    <BookOpen className="h-5 w-5 text-primary" />
                  </div>
                </div>
                <p className="text-3xl font-heading font-bold">
                  {progress?.completed_videos || 0}
                </p>
                <p className="text-sm text-muted-foreground">Videos Completed</p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card data-testid="completion-percentage-stat">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 rounded-lg bg-accent/50">
                    <TrendingUp className="h-5 w-5 text-accent-foreground" />
                  </div>
                </div>
                <p className="text-3xl font-heading font-bold">
                  {Math.round(progress?.completion_percentage || 0)}%
                </p>
                <p className="text-sm text-muted-foreground">Overall Progress</p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Card data-testid="quiz-score-stat">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 rounded-lg bg-blue-500/10">
                    <Award className="h-5 w-5 text-blue-600" />
                  </div>
                </div>
                <p className="text-3xl font-heading font-bold">
                  {Math.round(progress?.average_quiz_score || 0)}%
                </p>
                <p className="text-sm text-muted-foreground">Avg Quiz Score</p>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Card data-testid="quizzes-taken-stat">
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-3">
                  <div className="p-2 rounded-lg bg-purple-500/10">
                    <Target className="h-5 w-5 text-purple-600" />
                  </div>
                </div>
                <p className="text-3xl font-heading font-bold">
                  {progress?.total_quizzes || 0}
                </p>
                <p className="text-sm text-muted-foreground">Quizzes Taken</p>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Bar Chart */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
          >
            <Card className="h-full">
              <CardHeader>
                <CardTitle className="font-heading">Topic Mastery Scores</CardTitle>
                <CardDescription>Your proficiency across different topics</CardDescription>
              </CardHeader>
              <CardContent>
                {chartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={chartData}>
                      <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
                      <XAxis
                        dataKey="topic"
                        angle={-45}
                        textAnchor="end"
                        height={80}
                        fontSize={12}
                      />
                      <YAxis domain={[0, 100]} />
                      <Tooltip />
                      <Bar dataKey="score" fill="hsl(var(--primary))" radius={[8, 8, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                    Start learning to see your mastery scores
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Radar Chart */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6 }}
          >
            <Card className="h-full">
              <CardHeader>
                <CardTitle className="font-heading">Skill Overview</CardTitle>
                <CardDescription>Comparative view of your top skills</CardDescription>
              </CardHeader>
              <CardContent>
                {radarData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={300}>
                    <RadarChart data={radarData}>
                      <PolarGrid />
                      <PolarAngleAxis dataKey="topic" fontSize={12} />
                      <PolarRadiusAxis domain={[0, 100]} />
                      <Radar
                        name="Mastery"
                        dataKey="mastery"
                        stroke="hsl(var(--primary))"
                        fill="hsl(var(--primary))"
                        fillOpacity={0.6}
                      />
                      <Legend />
                    </RadarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[300px] flex items-center justify-center text-muted-foreground">
                    Complete videos to build your skill profile
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Detailed Mastery List */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.7 }}
        >
          <Card>
            <CardHeader>
              <CardTitle className="font-heading">All Topics</CardTitle>
              <CardDescription>Complete breakdown of your mastery levels</CardDescription>
            </CardHeader>
            <CardContent>
              {masteryScores.length > 0 ? (
                <div className="space-y-6">
                  {masteryScores.map((mastery, index) => {
                    const level = getMasteryLevel(mastery.score);
                    return (
                      <div key={index} className="space-y-2">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <span className="font-medium">{mastery.topic}</span>
                            <Badge variant="outline" className={level.color}>
                              {level.label}
                            </Badge>
                          </div>
                          <span className="text-2xl font-heading font-bold text-primary">
                            {Math.round(mastery.score)}%
                          </span>
                        </div>
                        <Progress value={mastery.score} className="h-2" />
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-12 text-muted-foreground">
                  <p>No mastery data available yet</p>
                  <p className="text-sm mt-2">Start learning to build your skill profile</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
