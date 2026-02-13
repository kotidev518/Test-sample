import api from './api';

export const authService = {
  getProfile: async () => {
    const response = await api.get('/auth/me');
    return response.data;
  },
  validateEmail: async (email) => {
    const response = await api.get(`/auth/validate-email?email=${encodeURIComponent(email)}`);
    return response.data;
  },
  register: async (name, initial_level) => {
    const response = await api.post('/auth/register', {
      name,
      initial_level
    });
    return response.data;
  },
  login: async () => {
    const response = await api.post('/auth/login');
    return response.data;
  },
  googleLogin: async (name, email) => {
    // For Google login, we'll send basic profile data just in case we need to create the user
    const response = await api.post('/auth/google-login', {
      name: name || email.split('@')[0],
      initial_level: 'Easy' // Default for Google Sign-In users
    });
    return response.data;
  }
};
