import api from './api';

export const courseService = {
  getAllCourses: async () => {
    const response = await api.get('/courses');
    return response.data;
  },
  getCourseById: async (id) => {
    const response = await api.get(`/courses/${id}`);
    return response.data;
  },
  getVideos: async (courseId) => {
      const params = courseId ? { course_id: courseId } : {};
      const response = await api.get('/videos', { params });
      return response.data;
  },
  getVideoById: async (id) => {
      const response = await api.get(`/videos/${id}`);
      return response.data;
  },
  getVideoProgress: async (id) => {
      const response = await api.get(`/videos/${id}/progress`);
      return response.data;
  },
  updateVideoProgress: async (videoId, data) => {
      const response = await api.post(`/videos/${videoId}/progress`, data);
      return response.data;
  },
  getQuiz: async (videoId) => {
      const response = await api.get(`/quizzes/${videoId}`);
      return response.data;
  },
  submitQuiz: async (data) => {
      const response = await api.post('/quizzes/submit', data);
      return response.data;
  },
  chatWithVideo: async (videoId, message) => {
      const response = await api.post(`/videos/${videoId}/chat`, { message });
      return response.data;
  }
};
