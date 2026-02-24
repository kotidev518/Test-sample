import React, { useEffect, useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { analyticsService } from '@/services/analyticsService';
import { Navbar } from '@/components/Navbar';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
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
import { TrendingUp, Target, Award, BookOpen, BarChart3, Sparkles, GraduationCap } from 'lucide-react';
import { Button } from '@/components/ui/button';

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
    if (score >= 80) return { label: 'PROFICIENT', color: 'bg-green-500/10 text-green-600 border-green-200' };
    if (score >= 60) return { label: 'ADVANCED', color: 'bg-indigo-500/10 text-indigo-600 border-indigo-200' };
    if (score >= 40) return { label: 'IN PROGRESS', color: 'bg-blue-500/10 text-blue-600 border-blue-200' };
    return { label: 'BEGINNER', color: 'bg-gray-500/10 text-gray-600 border-gray-200' };
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
      <div className="min-h-screen mesh-background">
        <Navbar />
        <div className="container mx-auto px-4 py-12">
          <div className="animate-pulse space-y-6">
            <div className="h-12 bg-muted rounded w-64" />
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-32 bg-muted rounded-3xl" />
              ))}
            </div>
            <div className="h-96 bg-muted rounded-3xl" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen mesh-background selection:bg-primary/20" data-testid="analytics-page">
      <Navbar />

      <div className="container mx-auto px-4 lg:px-12 py-12 max-w-7xl">
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-end justify-between mb-12 gap-6">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
          >
            <h1 className="text-4xl lg:text-5xl font-heading font-extrabold tracking-tight-more mb-3 text-gray-900">
              Learning Analytics
            </h1>
            <p className="text-gray-500 text-lg font-medium max-w-lg leading-relaxed">
              Personalized insights and mastery tracking for your educational journey.
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            className="flex items-center gap-2 px-4 py-2 bg-white/50 backdrop-blur-md rounded-full border border-white/50 shadow-sm self-start md:self-auto"
          >
            <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
            <span className="text-xs font-bold text-gray-700 tracking-wide">Live AI Analysis Active</span>
          </motion.div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {[
            {
              label: 'VIDEOS COMPLETED',
              value: progress?.completed_videos || 0,
              icon: BookOpen,
              color: 'bg-indigo-500/10 text-indigo-500',
              delay: 0.1
            },
            {
              label: 'OVERALL PROGRESS',
              value: `${Math.round(progress?.completion_percentage || 0)}%`,
              icon: TrendingUp,
              color: 'bg-emerald-500/10 text-emerald-500',
              delay: 0.2
            },
            {
              label: 'AVG QUIZ SCORE',
              value: `${Math.round(progress?.average_quiz_score || 0)}%`,
              icon: Award,
              color: 'bg-blue-500/10 text-blue-500',
              delay: 0.3
            },
            {
              label: 'QUIZZES TAKEN',
              value: progress?.total_quizzes || 0,
              icon: Target,
              color: 'bg-fuchsia-500/10 text-fuchsia-500',
              delay: 0.4
            }
          ].map((stat, idx) => (
            <motion.div
              key={idx}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: stat.delay }}
            >
              <Card className="border-0 shadow-[0_8px_30px_rgb(0,0,0,0.04)] bg-white/80 backdrop-blur-sm hover:shadow-[0_8px_30px_rgb(0,0,0,0.08)] transition-all duration-300 rounded-[2rem]">
                <CardContent className="p-8">
                  <div className={`w-12 h-12 rounded-2xl ${stat.color} flex items-center justify-center mb-6`}>
                    <stat.icon className="h-6 w-6" />
                  </div>
                  <div className="space-y-1">
                    <p className="text-4xl font-heading font-extrabold text-gray-900 tracking-tight">
                      {stat.value}
                    </p>
                    <p className="text-[10px] font-bold text-gray-400 tracking-[0.1em]">
                      {stat.label}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Charts Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          {/* Bar Chart */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5 }}
          >
            <Card className="border-0 shadow-[0_8px_30px_rgb(0,0,0,0.04)] bg-white/80 backdrop-blur-sm rounded-[2.5rem] overflow-hidden">
              <CardHeader className="p-8 pb-0 flex flex-row items-start justify-between">
                <div>
                  <CardTitle className="text-2xl font-heading font-extrabold text-gray-900 mb-1">Topic Mastery</CardTitle>
                  <CardDescription className="text-gray-400 font-medium">Proficiency levels per subject area</CardDescription>
                </div>
                <div className="p-2.5 bg-gray-50 rounded-xl">
                  <BarChart3 className="h-5 w-5 text-gray-400" />
                </div>
              </CardHeader>
              <CardContent className="p-8 pt-12">
                {chartData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={320}>
                    <BarChart data={chartData} barGap={12}>
                      <defs>
                        <linearGradient id="barGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#a78bfa" />
                          <stop offset="100%" stopColor="#6366f1" />
                        </linearGradient>
                      </defs>
                      <CartesianGrid vertical={false} strokeDasharray="3 3" stroke="#f0f0f0" />
                      <XAxis
                        dataKey="topic"
                        axisLine={false}
                        tickLine={false}
                        tick={{ fill: '#9ca3af', fontSize: 12, fontWeight: 500 }}
                        dy={10}
                      />
                      <Tooltip
                        cursor={{ fill: '#f9fafb' }}
                        contentStyle={{
                          borderRadius: '16px',
                          border: 'none',
                          boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1)',
                          fontSize: '12px',
                          fontWeight: '600'
                        }}
                      />
                      <Bar
                        dataKey="score"
                        fill="url(#barGradient)"
                        radius={[6, 6, 6, 6]}
                        barSize={20}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[320px] flex items-center justify-center text-gray-400 font-medium">
                    Start learning to see your mastery scores
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Radar Chart */}
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.6 }}
          >
            <Card className="border-0 shadow-[0_8px_30px_rgb(0,0,0,0.04)] bg-white/80 backdrop-blur-sm rounded-[2.5rem] overflow-hidden">
              <CardHeader className="p-8 pb-0 flex flex-row items-start justify-between">
                <div>
                  <CardTitle className="text-2xl font-heading font-extrabold text-gray-900 mb-1">Skill Overview</CardTitle>
                  <CardDescription className="text-gray-400 font-medium">Core competence vector analysis</CardDescription>
                </div>
                <div className="p-2.5 bg-gray-50 rounded-xl">
                  <Sparkles className="h-5 w-5 text-gray-400" />
                </div>
              </CardHeader>
              <CardContent className="p-8 pt-6 flex items-center justify-center">
                {radarData.length > 0 ? (
                  <ResponsiveContainer width="100%" height={320}>
                    <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="80%">
                      <defs>
                        <linearGradient id="radarGradient" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="0%" stopColor="#a78bfa" stopOpacity={0.8} />
                          <stop offset="100%" stopColor="#6366f1" stopOpacity={0.8} />
                        </linearGradient>
                      </defs>
                      <PolarGrid stroke="#f0f0f0" />
                      <PolarAngleAxis
                        dataKey="topic"
                        tick={{ fill: '#9ca3af', fontSize: 11, fontWeight: 500 }}
                      />
                      <Radar
                        name="Mastery"
                        dataKey="mastery"
                        stroke="#818cf8"
                        strokeWidth={2}
                        fill="url(#radarGradient)"
                        fillOpacity={0.6}
                      />
                    </RadarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="h-[320px] flex items-center justify-center text-gray-400 font-medium">
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
          <Card className="border-0 shadow-[0_8px_30px_rgb(0,0,0,0.04)] bg-white/80 backdrop-blur-sm rounded-[2.5rem] overflow-hidden">
            <CardHeader className="p-10 pb-6 flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div>
                <CardTitle className="text-3xl font-heading font-extrabold text-gray-900 mb-1">All Topics</CardTitle>
                <CardDescription className="text-gray-400 font-medium">Detailed mastery roadmap across your active curriculum</CardDescription>
              </div>
              <div className="flex items-center gap-3">
                <Button variant="outline" className="rounded-xl border-gray-100 text-gray-500 font-bold text-xs h-10 px-5 hover:bg-gray-50">
                  Sort by Mastery
                </Button>
                <Button className="rounded-xl bg-gradient-primary shadow-lg shadow-purple-500/20 text-xs font-bold h-10 px-5 hover:scale-105 transition-transform">
                  All Modules
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-10 pt-4">
              {masteryScores.length > 0 ? (
                <div className="space-y-10">
                  {masteryScores.map((mastery, index) => {
                    const level = getMasteryLevel(mastery.score);
                    const formattedIndex = (index + 1).toString().padStart(2, '0');
                    return (
                      <div key={index} className="relative group">
                        <div className="flex items-center justify-between mb-4">
                          <div className="flex items-center gap-6">
                            <span className="text-sm font-black text-indigo-300 tracking-tighter w-6">
                              {formattedIndex}
                            </span>
                            <div className="space-y-1">
                              <span className="text-xl font-heading font-extrabold text-gray-900 block">
                                {mastery.topic}
                              </span>
                              <span className={`inline-block px-2.5 py-0.5 rounded-full text-[9px] font-black border ${level.color}`}>
                                {level.label}
                              </span>
                            </div>
                          </div>
                          <div className="w-10 h-4 bg-gradient-primary rounded-sm opacity-80" />
                        </div>
                        <div className="relative h-2.5 w-full bg-gray-50 rounded-full overflow-hidden">
                          <motion.div
                            initial={{ width: 0 }}
                            animate={{ width: `${mastery.score}%` }}
                            transition={{ duration: 1, delay: 0.8 + (index * 0.1) }}
                            className="absolute h-full left-0 top-0 bg-gradient-primary rounded-full shadow-[0_0_10px_rgba(99,102,241,0.3)]"
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <div className="text-center py-20 text-gray-400 font-medium">
                  <p className="text-lg">No mastery data available yet</p>
                  <p className="text-sm mt-1 opacity-60">Start learning to build your skill profile</p>
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Footer info (matches image branding) */}
        <div className="mt-20 flex flex-col md:flex-row items-center justify-between pt-8 border-t border-gray-100/50 gap-6">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-lg bg-gradient-primary flex items-center justify-center">
              <GraduationCap className="w-3.5 h-3.5 text-white" />
            </div>
            <span className="text-sm font-black text-gray-900">SkillFlow AI</span>
          </div>
          <p className="text-[10px] font-bold text-gray-300 tracking-widest uppercase">
            © 2024 SKILLFLOW AI • PRECISION LEARNING ECOSYSTEM
          </p>
          <div className="flex items-center gap-6">
            {['Privacy', 'Terms', 'Support'].map(item => (
              <span key={item} className="text-[11px] font-bold text-gray-400 hover:text-gray-900 cursor-pointer transition-colors">
                {item}
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
