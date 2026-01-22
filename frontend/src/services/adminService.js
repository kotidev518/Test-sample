import api from './api';

export const adminService = {
  /**
   * Import a YouTube playlist as a course
   * @param {string} playlistUrl - YouTube playlist URL
   * @param {string} difficulty - Course difficulty (Easy, Medium, Hard)
   * @returns {Promise} Import result with course details
   */
  importPlaylist: async (playlistUrl, difficulty = 'Medium') => {
    const response = await api.post('/admin/import-playlist', {
      playlist_url: playlistUrl,
      difficulty
    });
    return response.data;
  },

  /**
   * Get all courses with admin metadata
   * @returns {Promise} List of all courses
   */
  getCourses: async () => {
    const response = await api.get('/admin/courses');
    return response.data;
  },

  /**
   * Delete a course and all its videos
   * @param {string} courseId - Course ID to delete
   * @returns {Promise} Deletion result
   */
  deleteCourse: async (courseId) => {
    const response = await api.delete(`/admin/courses/${courseId}`);
    return response.data;
  }
};
