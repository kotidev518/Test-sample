import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { adminService } from '@/services/adminService';
import { toast } from 'sonner';
import { 
  Upload, 
  Loader2, 
  CheckCircle2, 
  XCircle, 
  Trash2, 
  Video,
  ArrowLeft,
  Youtube,
  BookOpen
} from 'lucide-react';

const AdminDashboardPage = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  const [playlistUrl, setPlaylistUrl] = useState('');
  const [difficulty, setDifficulty] = useState('Medium');
  const [isImporting, setIsImporting] = useState(false);
  const [courses, setCourses] = useState([]);
  const [loadingCourses, setLoadingCourses] = useState(true);
  const [importResult, setImportResult] = useState(null);

  // Check if user is admin
  useEffect(() => {
    if (user && user.role !== 'admin') {
      toast.error('Admin access required');
      navigate('/dashboard');
    }
  }, [user, navigate]);

  // Load courses on mount
  useEffect(() => {
    loadCourses();
  }, []);

  const loadCourses = async () => {
    try {
      setLoadingCourses(true);
      const data = await adminService.getCourses();
      setCourses(data);
    } catch (error) {
      console.error('Failed to load courses:', error);
      if (error.response?.status === 403) {
        toast.error('Admin access required');
        navigate('/dashboard');
      }
    } finally {
      setLoadingCourses(false);
    }
  };

  const handleImport = async (e) => {
    e.preventDefault();
    
    if (!playlistUrl.trim()) {
      toast.error('Please enter a YouTube playlist URL');
      return;
    }

    if (!playlistUrl.includes('youtube.com') && !playlistUrl.includes('youtu.be')) {
      toast.error('Please enter a valid YouTube URL');
      return;
    }

    setIsImporting(true);
    setImportResult(null);

    try {
      const result = await adminService.importPlaylist(playlistUrl, difficulty);
      setImportResult(result);
      toast.success(`Imported "${result.course_title}" with ${result.videos_imported} videos!`);
      setPlaylistUrl('');
      loadCourses(); // Refresh course list
    } catch (error) {
      const message = error.response?.data?.detail || 'Failed to import playlist';
      toast.error(message);
      setImportResult({ success: false, message });
    } finally {
      setIsImporting(false);
    }
  };

  const handleDeleteCourse = async (courseId, courseTitle) => {
    if (!window.confirm(`Are you sure you want to delete "${courseTitle}"? This will also delete all videos and quizzes.`)) {
      return;
    }

    try {
      await adminService.deleteCourse(courseId);
      toast.success(`Deleted "${courseTitle}"`);
      loadCourses();
    } catch (error) {
      toast.error('Failed to delete course');
    }
  };

  if (!user || user.role !== 'admin') {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
        <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900">
      {/* Header */}
      <header className="border-b border-gray-700/50 backdrop-blur-sm bg-gray-900/50 sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={() => navigate('/dashboard')}
                className="p-2 hover:bg-gray-800 rounded-lg transition-colors"
              >
                <ArrowLeft className="w-5 h-5 text-gray-400" />
              </button>
              <div>
                <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-pink-500 bg-clip-text text-transparent">
                  Admin Dashboard
                </h1>
                <p className="text-gray-400 text-sm">Manage courses and import YouTube playlists</p>
              </div>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-purple-500/10 rounded-lg border border-purple-500/30">
              <span className="text-purple-400 text-sm font-medium">Admin: {user.name}</span>
            </div>
          </div>
        </div>
      </header>

      <main className="container mx-auto px-6 py-8">
        {/* Import Section */}
        <section className="mb-12">
          <div className="bg-gradient-to-r from-gray-800/80 to-gray-800/50 rounded-2xl border border-gray-700/50 p-8 backdrop-blur-sm">
            <div className="flex items-center gap-3 mb-6">
              <div className="p-3 bg-red-500/20 rounded-xl">
                <Youtube className="w-6 h-6 text-red-400" />
              </div>
              <div>
                <h2 className="text-xl font-semibold text-white">Import YouTube Playlist</h2>
                <p className="text-gray-400 text-sm">Add a new course by importing a YouTube playlist</p>
              </div>
            </div>

            <form onSubmit={handleImport} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Playlist URL
                </label>
                <input
                  type="url"
                  value={playlistUrl}
                  onChange={(e) => setPlaylistUrl(e.target.value)}
                  placeholder="https://www.youtube.com/playlist?list=PLxxxxxx"
                  className="w-full px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-xl text-white placeholder-gray-500 focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 transition-all"
                  disabled={isImporting}
                />
              </div>

              <div className="flex flex-wrap gap-4 items-end">
                <div className="flex-1 min-w-[200px]">
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    Course Difficulty
                  </label>
                  <select
                    value={difficulty}
                    onChange={(e) => setDifficulty(e.target.value)}
                    className="w-full px-4 py-3 bg-gray-900/50 border border-gray-600 rounded-xl text-white focus:outline-none focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 transition-all"
                    disabled={isImporting}
                  >
                    <option value="Easy">Easy</option>
                    <option value="Medium">Medium</option>
                    <option value="Hard">Hard</option>
                  </select>
                </div>

                <button
                  type="submit"
                  disabled={isImporting}
                  className="px-8 py-3 bg-gradient-to-r from-purple-500 to-pink-500 rounded-xl font-semibold text-white flex items-center gap-2 hover:from-purple-600 hover:to-pink-600 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-purple-500/25"
                >
                  {isImporting ? (
                    <>
                      <Loader2 className="w-5 h-5 animate-spin" />
                      Importing...
                    </>
                  ) : (
                    <>
                      <Upload className="w-5 h-5" />
                      Import Playlist
                    </>
                  )}
                </button>
              </div>
            </form>

            {/* Import Result */}
            {importResult && (
              <div className={`mt-6 p-4 rounded-xl border ${
                importResult.success 
                  ? 'bg-green-500/10 border-green-500/30' 
                  : 'bg-red-500/10 border-red-500/30'
              }`}>
                <div className="flex items-center gap-3">
                  {importResult.success ? (
                    <CheckCircle2 className="w-5 h-5 text-green-400" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-400" />
                  )}
                  <div>
                    <p className={importResult.success ? 'text-green-400' : 'text-red-400'}>
                      {importResult.message}
                    </p>
                    {importResult.success && (
                      <p className="text-gray-400 text-sm mt-1">
                        {importResult.videos_imported} videos • {importResult.quizzes_generated} quizzes generated
                      </p>
                    )}
                  </div>
                </div>
              </div>
            )}
          </div>
        </section>

        {/* Courses List */}
        <section>
          <div className="flex items-center gap-3 mb-6">
            <div className="p-3 bg-blue-500/20 rounded-xl">
              <BookOpen className="w-6 h-6 text-blue-400" />
            </div>
            <div>
              <h2 className="text-xl font-semibold text-white">Imported Courses</h2>
              <p className="text-gray-400 text-sm">{courses.length} courses available</p>
            </div>
          </div>

          {loadingCourses ? (
            <div className="flex justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-purple-500" />
            </div>
          ) : courses.length === 0 ? (
            <div className="text-center py-12 bg-gray-800/30 rounded-2xl border border-gray-700/50">
              <Video className="w-12 h-12 text-gray-600 mx-auto mb-4" />
              <p className="text-gray-400">No courses yet. Import a YouTube playlist to get started!</p>
            </div>
          ) : (
            <div className="grid gap-4">
              {courses.map((course) => (
                <div
                  key={course.id}
                  className="bg-gray-800/50 rounded-xl border border-gray-700/50 p-4 hover:bg-gray-800/70 transition-colors"
                >
                  <div className="flex items-center gap-4">
                    <img
                      src={course.thumbnail || '/placeholder-course.jpg'}
                      alt={course.title}
                      className="w-32 h-20 object-cover rounded-lg flex-shrink-0"
                      onError={(e) => {
                        e.target.onerror = null;
                        e.target.src = 'https://via.placeholder.com/128x80?text=No+Image';
                      }}
                    />
                    <div className="flex-1 min-w-0">
                      <h3 className="text-white font-medium truncate">{course.title}</h3>
                      <p className="text-gray-400 text-sm truncate">{course.description}</p>
                      <div className="flex items-center gap-4 mt-2">
                        <span className="text-xs px-2 py-1 bg-purple-500/20 text-purple-400 rounded">
                          {course.difficulty}
                        </span>
                        <span className="text-gray-500 text-xs">
                          {course.video_count} videos
                        </span>
                        {course.channel && (
                          <span className="text-gray-500 text-xs">
                            by {course.channel}
                          </span>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => handleDeleteCourse(course.id, course.title)}
                      className="p-2 hover:bg-red-500/20 rounded-lg transition-colors group flex-shrink-0"
                      title="Delete course"
                    >
                      <Trash2 className="w-5 h-5 text-gray-500 group-hover:text-red-400" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </section>
      </main>
    </div>
  );
};

export default AdminDashboardPage;
