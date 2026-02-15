import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { courseService } from '@/services/courseService';
import { Navbar } from '@/components/Navbar';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Play, Clock, ArrowLeft } from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';

const CourseDetailPage = () => {
  const { courseId } = useParams();
  const navigate = useNavigate();
  const [course, setCourse] = useState(null);
  const [videos, setVideos] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCourseData();
  }, [courseId]);

  const fetchCourseData = async () => {
    try {
      const [courseData, videosData] = await Promise.all([
        courseService.getCourseById(courseId),
        courseService.getVideos(courseId)
      ]);
      setCourse(courseData);
      setVideos(videosData);
    } catch (error) {
      console.error('Failed to fetch course data:', error);
      toast.error('Failed to load course');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div>
        <Navbar />
        <div className="container mx-auto px-4 py-12">
          <div className="animate-pulse space-y-6">
            <div className="h-64 bg-muted rounded-lg" />
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="h-24 bg-muted rounded-lg" />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!course) {
    return (
      <div>
        <Navbar />
        <div className="container mx-auto px-4 py-12 text-center">
          <p className="text-muted-foreground">Course not found</p>
          <Button onClick={() => navigate('/courses')} className="mt-4">
            Back to Courses
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" data-testid="course-detail-page">
      <Navbar />
      
      <div className="container mx-auto px-4 lg:px-8 py-8">
        {/* Back Button */}
        <Button
          variant="ghost"
          onClick={() => navigate('/courses')}
          className="mb-6 gap-2"
          data-testid="back-to-courses-btn"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Courses
        </Button>

        {/* Course Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <Card className="border-2">
            <div className="grid md:grid-cols-2 gap-6">
              <div className="aspect-video overflow-hidden rounded-l-lg">
                <img
                  src={course.thumbnail}
                  alt={course.title}
                  onError={(e) => {
                    e.target.onerror = null;
                    e.target.src = 'https://images.unsplash.com/photo-1546410531-bb4caa6b424d?auto=format&fit=crop&q=80&w=1000';
                  }}
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="p-6 flex flex-col justify-center">
                <div className="flex items-center gap-2 mb-4">
                  <Badge
                    className={`${
                      course.difficulty === 'Easy'
                        ? 'bg-green-500/10 text-green-700'
                        : course.difficulty === 'Medium'
                        ? 'bg-yellow-500/10 text-yellow-700'
                        : 'bg-red-500/10 text-red-700'
                    }`}
                  >
                    {course.difficulty}
                  </Badge>
                  <span className="text-sm text-muted-foreground">
                    {course.video_count} videos
                  </span>
                </div>
                <h1 className="text-3xl font-heading font-bold tracking-tight-more mb-3">
                  {course.title}
                </h1>
               {/* <p className="text-muted-foreground mb-6">{course.description}</p> */}
                <div className="flex flex-wrap gap-2">
                  {course.topics.map((topic, idx) => (
                    <span
                      key={idx}
                      className="text-xs bg-secondary text-secondary-foreground px-3 py-1 rounded-full"
                    >
                      {topic}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </Card>
        </motion.div>

        {/* Videos List */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
        >
          <h2 className="text-2xl font-heading font-bold mb-4">Course Videos</h2>
          <div className="space-y-4">
            {videos.map((video, index) => (
              <motion.div
                key={video.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card
                  className="hover:-translate-y-0.5 hover:shadow-md transition-all cursor-pointer group"
                  onClick={() => navigate(`/video/${video.id}`)}
                  data-testid={`video-card-${video.id}`}
                >
                  <CardContent className="p-6">
                    <div className="flex items-start gap-4">
                      <div className="flex-shrink-0 w-16 h-16 rounded-lg bg-primary/10 flex items-center justify-center group-hover:bg-primary/20 transition-colors">
                        <Play className="h-6 w-6 text-primary" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-2">
                          <span className="text-sm font-medium text-muted-foreground">
                            Video {video.order}
                          </span>
                          <Badge variant="outline" className="text-xs">
                            {video.difficulty}
                          </Badge>
                        </div>
                        <h3 className="text-lg font-heading font-semibold mb-2 group-hover:text-primary transition-colors">
                          {video.title}
                        </h3>
                        {/* <p className="text-sm text-muted-foreground mb-3 line-clamp-2">
                          {video.description}
                        </p> */}
                        <div className="flex items-center gap-4 text-xs text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            <span>{Math.floor(video.duration / 60)} min</span>
                          </div>
                          <div className="flex gap-2">
                            {video.topics.slice(0, 2).map((topic, idx) => (
                              <span key={idx} className="px-2 py-0.5 bg-secondary rounded-full">
                                {topic}
                              </span>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            ))}
          </div>

          {videos.length === 0 && (
            <Card>
              <CardContent className="p-12 text-center">
                <p className="text-muted-foreground">No videos available in this course</p>
              </CardContent>
            </Card>
          )}
        </motion.div>
      </div>
    </div>
  );
};

export default CourseDetailPage;
