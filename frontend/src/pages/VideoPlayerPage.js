import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import { courseService } from '@/services/courseService';
import { analyticsService } from '@/services/analyticsService';
import { Navbar } from '@/components/Navbar';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { ArrowLeft, CheckCircle2, XCircle } from 'lucide-react';
import { motion } from 'framer-motion';
import { toast } from 'sonner';

// Helper function to extract YouTube video ID from URL
const extractYouTubeId = (url) => {
  if (!url) return '';
  
  // Handle youtu.be short URLs
  const shortMatch = url.match(/youtu\.be\/([a-zA-Z0-9_-]+)/);
  if (shortMatch) return shortMatch[1];
  
  // Handle youtube.com URLs (watch?v=ID or embed/ID)
  const longMatch = url.match(/(?:youtube\.com\/(?:watch\?v=|embed\/))([a-zA-Z0-9_-]+)/);
  if (longMatch) return longMatch[1];
  
  // Handle just the video ID
  if (/^[a-zA-Z0-9_-]{11}$/.test(url)) return url;
  
  return '';
};

// Custom YouTube Player Wrapper with branded play button and end screen overlay
const YouTubePlayerWrapper = ({ videoId, thumbnail, title, onVideoEnd }) => {
  const [playerState, setPlayerState] = React.useState('idle'); // idle, playing, ended
  const iframeRef = React.useRef(null);
  const playerRef = React.useRef(null);
  
  // Load YouTube IFrame API
  React.useEffect(() => {
    if (playerState !== 'playing') return;
    
    // Load YouTube API script if not already loaded
    if (!window.YT) {
      const tag = document.createElement('script');
      tag.src = 'https://www.youtube.com/iframe_api';
      const firstScriptTag = document.getElementsByTagName('script')[0];
      firstScriptTag.parentNode.insertBefore(tag, firstScriptTag);
    }
    
    // Initialize player when API is ready
    const initPlayer = () => {
      if (playerRef.current) return;
      
      playerRef.current = new window.YT.Player(`youtube-player-${videoId}`, {
        events: {
          onStateChange: (event) => {
            // 0 = ended
            if (event.data === 0) {
              setPlayerState('ended');
              if (onVideoEnd) onVideoEnd();
            }
          }
        }
      });
    };
    
    if (window.YT && window.YT.Player) {
      initPlayer();
    } else {
      window.onYouTubeIframeAPIReady = initPlayer;
    }
    
    return () => {
      if (playerRef.current) {
        playerRef.current.destroy();
        playerRef.current = null;
      }
    };
  }, [playerState, videoId, onVideoEnd]);
  
  const handleReplay = () => {
    if (playerRef.current && playerRef.current.seekTo) {
      playerRef.current.seekTo(0);
      playerRef.current.playVideo();
      setPlayerState('playing');
    } else {
      setPlayerState('idle');
      setTimeout(() => setPlayerState('playing'), 100);
    }
  };
  
  // Show custom thumbnail before play
  if (playerState === 'idle') {
    return (
      <div 
        className="w-full h-full cursor-pointer group relative"
        onClick={() => setPlayerState('playing')}
      >
        {/* Custom Thumbnail */}
        <img 
          src={thumbnail || `https://img.youtube.com/vi/${videoId}/maxresdefault.jpg`}
          alt={title}
          className="w-full h-full object-cover"
          onError={(e) => {
            e.target.src = `https://img.youtube.com/vi/${videoId}/hqdefault.jpg`;
          }}
        />
        
        {/* Gradient Overlay */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-black/30" />
        
        {/* Custom Play Button */}
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-pink-500 rounded-full flex items-center justify-center shadow-2xl transform group-hover:scale-110 transition-transform duration-300">
            <svg 
              className="w-8 h-8 text-white ml-1" 
              fill="currentColor" 
              viewBox="0 0 24 24"
            >
              <path d="M8 5v14l11-7z" />
            </svg>
          </div>
        </div>
        
        {/* Video Title Overlay */}
        <div className="absolute bottom-0 left-0 right-0 p-4">
          <p className="text-white font-semibold text-lg truncate">{title}</p>
          <p className="text-white/70 text-sm">Click to play</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="w-full h-full relative">
      {/* YouTube Player */}
      <iframe
        id={`youtube-player-${videoId}`}
        ref={iframeRef}
        src={`https://www.youtube-nocookie.com/embed/${videoId}?autoplay=1&enablejsapi=1&rel=0&modestbranding=1&showinfo=0&iv_load_policy=3`}
        className="w-full h-full absolute inset-0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
        allowFullScreen
        title={title}
        style={{ border: 'none' }}
      />
      
      {/* End Screen Overlay - Covers YouTube suggestions */}
      {playerState === 'ended' && (
        <div className="absolute inset-0 bg-gradient-to-br from-gray-900 via-purple-900/50 to-gray-900 flex flex-col items-center justify-center z-10">
          <div className="text-center">
            <h3 className="text-white text-2xl font-bold mb-2">Video Complete!</h3>
            <p className="text-white/70 mb-6">Great job! The quiz will appear automatically.</p>
          </div>
        </div>
      )}
    </div>
  );
};


const VideoPlayerPage = () => {
  const { videoId } = useParams();
  const navigate = useNavigate();
  const videoRef = useRef(null);
  
  const [video, setVideo] = useState(null);
  const [quiz, setQuiz] = useState(null);
  const [watchProgress, setWatchProgress] = useState(0);
  const [showQuiz, setShowQuiz] = useState(false);
  const [quizAnswers, setQuizAnswers] = useState([]);
  const [quizResult, setQuizResult] = useState(null);
  const [nextVideo, setNextVideo] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchVideoData();
  }, [videoId]);

  useEffect(() => {
    const interval = setInterval(() => {
      if (videoRef.current && !videoRef.current.paused) {
        const progress = (videoRef.current.currentTime / videoRef.current.duration) * 100;
        setWatchProgress(progress);
        
        // Update progress every 10%
        if (progress % 10 < 1) {
          updateProgress(progress);
        }
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const fetchVideoData = async () => {
    try {
      const [videoData, progressData] = await Promise.all([
        courseService.getVideoById(videoId),
        courseService.getVideoProgress(videoId)
      ]);
      setVideo(videoData);
      setWatchProgress(progressData?.watch_percentage || 0);
      
      // Fetch quiz
      try {
        console.log('Fetching quiz for video:', videoId);
        const quizData = await courseService.getQuiz(videoId);
        console.log('Quiz data received:', quizData);
        setQuiz(quizData);
        setQuizAnswers(new Array(quizData.questions.length).fill(-1));
      } catch (error) {
        console.error('Quiz fetch error:', error);
      }
    } catch (error) {
      console.error('Failed to fetch video data:', error);
      toast.error('Failed to load video');
    } finally {
      setLoading(false);
    }
  };

  const fetchNextVideo = async () => {
    try {
      const response = await analyticsService.getNextRecommendation();
      setNextVideo(response.video);
    } catch (error) {
      console.error('Failed to fetch next video:', error);
    }
  };

  const updateProgress = async (percentage) => {
    try {
      if (percentage > watchProgress) {
        await courseService.updateVideoProgress(videoId, {
          watch_percentage: percentage,
          completed: percentage >= 90
        });
      }
    } catch (error) {
      console.error('Failed to update progress:', error);
    }
  };

  const handleVideoEnd = () => {
    console.log('Video ended, showing quiz...');
    updateProgress(100);
    if (quiz) {
      setShowQuiz(true);
    } else {
      toast.success('Video completed!');
    }
  };

  const handleQuizSubmit = async (e) => {
    e.preventDefault();
    
    if (quizAnswers.includes(-1)) {
      toast.error('Please answer all questions');
      return;
    }

    // Compute score locally to ensure accurate immediate feedback
    try {
      let correct = 0;
      for (let i = 0; i < quiz.questions.length; i++) {
        const userAns = quizAnswers[i];
        const correctAns = quiz.questions[i].correct_answer;
        if (userAns === correctAns) correct += 1;
      }

      const localScore = quiz.questions.length ? (correct / quiz.questions.length) * 100 : 0;

      // Show local result immediately
      const localResult = {
        id: `local-${Date.now()}`,
        user_id: null,
        quiz_id: quiz.id,
        video_id: quiz.video_id,
        score: localScore,
        timestamp: new Date().toISOString()
      };

      setQuizResult(localResult);
      toast.success(`Quiz completed! Score: ${Math.round(localScore)}%`);

      // Submit to backend (fire-and-update). If server returns authoritative result, update it.
      try {
        const serverResult = await courseService.submitQuiz({
          quiz_id: quiz.id,
          answers: quizAnswers
        });
        setQuizResult(serverResult);
      } catch (err) {
        console.error('Failed to submit quiz to server:', err);
        // keep local result shown
      }

      // Fetch next video recommendation
      fetchNextVideo();
    } catch (error) {
      console.error('Failed to compute/submit quiz:', error);
      toast.error('Failed to submit quiz');
    }
  };

  if (loading) {
    return (
      <div>
        <Navbar />
        <div className="container mx-auto px-4 py-12">
          <div className="animate-pulse space-y-6">
            <div className="aspect-video bg-muted rounded-lg" />
            <div className="h-24 bg-muted rounded-lg" />
          </div>
        </div>
      </div>
    );
  }

  if (!video) {
    return (
      <div>
        <Navbar />
        <div className="container mx-auto px-4 py-12 text-center">
          <p className="text-muted-foreground">Video not found</p>
          <Button onClick={() => navigate('/courses')} className="mt-4">
            Back to Courses
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen" data-testid="video-player-page">
      <Navbar />
      
      <div className="container mx-auto px-4 lg:px-8 py-8 max-w-6xl">
        <Button
          variant="ghost"
          onClick={() => navigate(-1)}
          className="mb-6 gap-2"
          data-testid="back-btn"
        >
          <ArrowLeft className="h-4 w-4" />
          Back
        </Button>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Video Area */}
          <div className="lg:col-span-2 space-y-6">
            {/* Video Player */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
            >
              <Card className="border-2">
                <CardContent className="p-0">
                  <div className="aspect-video bg-gradient-to-br from-gray-900 to-gray-800 rounded-t-lg overflow-hidden relative">
                    {video.url && (video.url.includes('youtube.com') || video.url.includes('youtu.be')) ? (
                      // Custom player wrapper for YouTube
                      <YouTubePlayerWrapper 
                        videoId={extractYouTubeId(video.url)} 
                        thumbnail={video.thumbnail}
                        title={video.title}
                        onVideoEnd={handleVideoEnd}
                      />
                    ) : (
                      // Native video player for non-YouTube videos
                      <video
                        ref={videoRef}
                        controls
                        onEnded={handleVideoEnd}
                        className="w-full h-full"
                        data-testid="video-player"
                      >
                        <source src={video.url} type="video/mp4" />
                        Your browser does not support the video tag.
                      </video>
                    )}
                  </div>
                  <div className="p-6">
                    <div className="flex items-center gap-2 mb-3">
                      <Badge>{video.difficulty}</Badge>
                      {video.topics.map((topic, idx) => (
                        <Badge key={idx} variant="outline">
                          {topic}
                        </Badge>
                      ))}
                    </div>
                    <h1 className="text-2xl font-heading font-bold mb-2">{video.title}</h1>
                    <p className="text-muted-foreground">{video.description}</p>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {/* Quiz Section */}
            {showQuiz && quiz && !quizResult && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
              >
                <Card className="border-2 border-primary/20">
                  <CardHeader>
                    <CardTitle className="font-heading">Complete the Quiz</CardTitle>
                    <CardDescription>
                      Test your understanding of the video content
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <form onSubmit={handleQuizSubmit} className="space-y-6" data-testid="quiz-form">
                      {quiz.questions.map((question, qIdx) => (
                        <div key={qIdx} className="space-y-3">
                          <Label className="text-base font-medium">
                            {qIdx + 1}. {question.question}
                          </Label>
                          <RadioGroup
                            value={quizAnswers[qIdx]?.toString()}
                            onValueChange={(value) => {
                              const newAnswers = [...quizAnswers];
                              newAnswers[qIdx] = parseInt(value);
                              setQuizAnswers(newAnswers);
                            }}
                          >
                            {question.options.map((option, oIdx) => (
                              <div key={oIdx} className="flex items-center space-x-2">
                                <RadioGroupItem
                                  value={oIdx.toString()}
                                  id={`q${qIdx}-o${oIdx}`}
                                  data-testid={`quiz-option-${qIdx}-${oIdx}`}
                                />
                                <Label
                                  htmlFor={`q${qIdx}-o${oIdx}`}
                                  className="font-normal cursor-pointer"
                                >
                                  {option}
                                </Label>
                              </div>
                            ))}
                          </RadioGroup>
                        </div>
                      ))}
                      <Button type="submit" className="w-full" data-testid="submit-quiz-btn">
                        Submit Quiz
                      </Button>
                    </form>
                  </CardContent>
                </Card>
              </motion.div>
            )}

            {/* Quiz Result */}
            {quizResult && (
              <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
              >
                <Card
                  className={`border-2 ${
                    quizResult.score >= 75
                      ? 'border-green-500/50 bg-green-500/5'
                      : 'border-yellow-500/50 bg-yellow-500/5'
                  }`}
                  data-testid="quiz-result-card"
                >
                  <CardContent className="p-8 text-center">
                    {quizResult.score >= 75 ? (
                      <CheckCircle2 className="h-16 w-16 text-green-600 mx-auto mb-4" />
                    ) : (
                      <XCircle className="h-16 w-16 text-yellow-600 mx-auto mb-4" />
                    )}
                    <h3 className="text-2xl font-heading font-bold mb-2">
                      {quizResult.score >= 75 ? 'Great Job!' : 'Keep Learning!'}
                    </h3>
                    <p className="text-4xl font-bold text-primary mb-4">
                      {Math.round(quizResult.score)}%
                    </p>
                    <p className="text-muted-foreground mb-6">
                      {quizResult.score >= 75
                        ? 'You have a strong understanding of this topic. Next video unlocked!'
                        : 'Score 75% or higher to unlock the next video'}
                    </p>
                    <div className="flex gap-4 justify-center">
                      <Button
                        onClick={() => navigate('/dashboard')}
                        data-testid="back-to-dashboard-btn"
                      >
                        Back to Dashboard
                      </Button>
                      <Button
                        variant="outline"
                        onClick={() => window.location.reload()}
                        data-testid="retake-quiz-btn"
                      >
                        Retake Quiz
                      </Button>
                      
                      {/* Next Video Button */}
                      <Button
                        className="gap-2"
                        onClick={() => {
                          if (nextVideo) {
                            navigate(`/video/${nextVideo.id}`);
                            window.location.reload(); // Force reload to reset state for new video
                          }
                        }}
                        disabled={quizResult.score < 75 || !nextVideo}
                        data-testid="next-video-btn"
                        title={quizResult.score < 75 ? "Score 75% or higher to unlock next video" : "Go to next recommended video"}
                      >
                        Next Video
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
            >
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg font-heading">Video Info</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4 text-sm">
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Duration</span>
                    <span className="font-medium">{Math.floor(video.duration / 60)} min</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-foreground">Difficulty</span>
                    <span className="font-medium">{video.difficulty}</span>
                  </div>
                  <div>
                    <span className="text-muted-foreground block mb-2">Topics</span>
                    <div className="flex flex-wrap gap-2">
                      {video.topics.map((topic, idx) => (
                        <Badge key={idx} variant="secondary">
                          {topic}
                        </Badge>
                      ))}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>

            {!showQuiz && quiz && (
              <motion.div
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
              >
                <Card className="border-primary/20">
                  <CardContent className="p-6 text-center">
                    <div className="w-12 h-12 bg-primary/10 rounded-full flex items-center justify-center mx-auto mb-3">
                      <CheckCircle2 className="w-6 h-6 text-primary" />
                    </div>
                    <p className="font-medium mb-1">Quiz Available</p>
                    <p className="text-sm text-muted-foreground">
                      {quiz.questions?.length || 4} questions will appear after the video ends
                    </p>
                  </CardContent>
                </Card>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default VideoPlayerPage;
