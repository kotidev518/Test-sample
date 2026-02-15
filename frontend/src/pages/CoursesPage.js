import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import axios from 'axios';
import { Navbar } from '@/components/Navbar';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { BookOpen, Clock } from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CoursesPage = () => {
  const { getAxiosConfig } = useAuth();
  const navigate = useNavigate();
  const [courses, setCourses] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchCourses();
  }, []);

  const fetchCourses = async () => {
    try {
      const response = await axios.get(`${API}/courses`, getAxiosConfig());
      setCourses(response.data);
    } catch (error) {
      console.error('Failed to fetch courses:', error);
      toast.error('Failed to load courses');
    } finally {
      setLoading(false);
    }
  };

  const getDifficultyColor = (difficulty) => {
    const colors = {
      Easy: 'bg-green-500/10 text-green-700 dark:text-green-400',
      Medium: 'bg-yellow-500/10 text-yellow-700 dark:text-yellow-400',
      Hard: 'bg-red-500/10 text-red-700 dark:text-red-400'
    };
    return colors[difficulty] || colors.Medium;
  };

  if (loading) {
    return (
      <div>
        <Navbar />
        <div className="container mx-auto px-4 py-12">
          <div className="animate-pulse space-y-6">
            <div className="h-12 bg-muted rounded w-64" />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="h-80 bg-muted rounded-lg" />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" data-testid="courses-page">
      <Navbar />
      
      <div className="container mx-auto px-4 lg:px-8 py-8">
        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-3xl lg:text-4xl font-heading font-bold tracking-tight-more mb-2">
            All Courses
          </h1>
          <p className="text-muted-foreground">
            Choose from our curated collection of courses
          </p>
        </motion.div>

        {/* Courses Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {courses.map((course, index) => (
            <motion.div
              key={course.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card
                className="h-full hover:-translate-y-1 hover:shadow-lg transition-all cursor-pointer border group"
                onClick={() => navigate(`/course/${course.id}`)}
                data-testid={`course-card-${course.id}`}
              >
                <div className="aspect-video overflow-hidden rounded-t-lg">
                  <img
                    src={course.thumbnail}
                    alt={course.title}
                    onError={(e) => {
                      e.target.onerror = null;
                      e.target.src = 'https://images.unsplash.com/photo-1546410531-bb4caa6b424d?auto=format&fit=crop&q=80&w=1000';
                    }}
                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                  />
                </div>
                <CardHeader>
                  <div className="flex items-center gap-2 mb-2">
                    <Badge className={getDifficultyColor(course.difficulty)}>
                      {course.difficulty}
                    </Badge>
                    <div className="flex items-center gap-1 text-xs text-muted-foreground">
                      <BookOpen className="h-3 w-3" />
                      <span>{course.video_count} videos</span>
                    </div>
                  </div>
                  <CardTitle className="text-xl font-heading line-clamp-2">
                    {course.title}
                  </CardTitle>
                  <CardDescription className="line-clamp-2">
                    {course.description}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {course.topics.slice(0, 3).map((topic, idx) => (
                      <span
                        key={idx}
                        className="text-xs bg-secondary text-secondary-foreground px-2 py-1 rounded-full"
                      >
                        {topic}
                      </span>
                    ))}
                    {course.topics.length > 3 && (
                      <span className="text-xs text-muted-foreground px-2 py-1">
                        +{course.topics.length - 3} more
                      </span>
                    )}
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {courses.length === 0 && (
          <div className="text-center py-16">
            <p className="text-muted-foreground">No courses available</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default CoursesPage;
