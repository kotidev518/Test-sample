import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import axios from 'axios';
import { Navbar } from '@/components/Navbar';
import { Footer } from '@/components/Footer';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { PlayCircle } from 'lucide-react';
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
      Easy: 'bg-[#10b981] text-white',
      Medium: 'bg-[#f59e0b] text-white',
      Hard: 'bg-[#ef4444] text-white'
    };
    return colors[difficulty] || colors.Medium;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-[#f8fafc]">
        <Navbar />
        <div className="container mx-auto px-4 py-20 text-center">
          <div className="animate-pulse space-y-8">
            <div className="h-4 bg-muted rounded w-32 mx-auto" />
            <div className="h-12 bg-muted rounded w-96 mx-auto" />
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mt-16">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i} className="h-[450px] bg-muted rounded-3xl" />
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f8fafc] pb-20" data-testid="courses-page">
      <Navbar />

      <div className="container mx-auto px-4 lg:px-8 py-16">
        {/* Hero Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center mb-20"
        >
          <span className="text-[10px] font-extrabold tracking-[0.3em] text-[#d946ef] uppercase mb-6 block">
            Knowledge Catalog
          </span>
          <h1 className="text-5xl lg:text-7xl font-heading font-black tracking-tighter mb-6 text-[#1e293b]">
            The Future of <span className="text-transparent bg-clip-text bg-gradient-to-r from-[#a855f7] to-[#6366f1]">Learning</span>
          </h1>
          <p className="text-gray-500 max-w-2xl mx-auto text-sm leading-relaxed font-medium">
            Choose from our curated collection of elite academic paths,<br />
            designed for precision and deep mastery.
          </p>
        </motion.div>

        {/* Courses Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-x-8 gap-y-12">
          {courses.map((course, index) => (
            <motion.div
              key={course.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.1 }}
            >
              <Card
                className="group border-0 bg-white rounded-[2rem] overflow-hidden course-card-shadow transition-all duration-500 hover:shadow-2xl hover:-translate-y-2 cursor-pointer flex flex-col h-full"
                onClick={() => navigate(`/course/${course.id}`)}
                data-testid={`course-card-${course.id}`}
              >
                {/* Image Container */}
                <div className="relative h-64 overflow-hidden m-4 mb-0 rounded-[1.5rem]">
                  <img
                    src={course.thumbnail}
                    alt={course.title}
                    onError={(e) => {
                      e.target.onerror = null;
                      e.target.src = 'https://images.unsplash.com/photo-1546410531-bb4caa6b424d?auto=format&fit=crop&q=80&w=1000';
                    }}
                    className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110"
                  />
                  <div className="absolute inset-0 bg-gradient-to-t from-black/20 to-transparent" />

                  {/* Badge */}
                  <Badge className={`absolute top-4 right-4 px-3 py-1 text-[9px] font-black border-0 rounded-full ${getDifficultyColor(course.difficulty)}`}>
                    {course.difficulty.toUpperCase()}
                  </Badge>

                  {/* Video Count Overlay (Optional but nice) */}
                  <div className="absolute bottom-4 left-4 flex items-center gap-1.5 text-white/90 text-[10px] font-bold">
                    <PlayCircle className="h-3 w-3" />
                    <span>{course.video_count} VIDEOS</span>
                  </div>
                </div>

                <CardContent className="p-8 pt-6 flex flex-col flex-grow">
                  <div className="flex items-center gap-1.5 text-[10px] font-extrabold text-blue-400 tracking-wider mb-3">
                    <PlayCircle className="h-3 w-3" />
                    <span>{course.video_count} VIDEOS</span>
                  </div>

                  <h3 className="text-2xl font-bold text-[#1e293b] mb-3 leading-tight group-hover:text-primary transition-colors">
                    {course.title}
                  </h3>

                  <p className="text-gray-400 text-[13px] leading-relaxed mb-6 line-clamp-3 font-medium">
                    {course.description}
                  </p>

                  <div className="flex flex-wrap gap-2 mb-8 mt-auto">
                    {course.topics.slice(0, 2).map((topic, idx) => (
                      <span
                        key={idx}
                        className="text-[9px] font-black tracking-widest text-gray-400 bg-gray-50 border border-gray-100 px-3 py-1 rounded-md uppercase"
                      >
                        {topic}
                      </span>
                    ))}
                  </div>

                  <Button
                    className="w-full h-12 rounded-2xl bg-gradient-to-r from-[#a855f7] to-[#6366f1] hover:from-[#9333ea] hover:to-[#4f46e5] text-white font-bold text-xs tracking-widest shadow-lg shadow-purple-200 transition-all duration-300"
                  >
                    VIEW COURSE
                  </Button>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </div>

        {courses.length === 0 && (
          <div className="text-center py-20">
            <p className="text-gray-400 font-medium">No courses available at the moment.</p>
          </div>
        )}
      </div>
      <Footer />
    </div>
  );
};

export default CoursesPage;