import React, { createContext, useContext, useState, useEffect } from 'react';
import { 
  createUserWithEmailAndPassword, 
  signInWithEmailAndPassword, 
  signOut, 
  onAuthStateChanged 
} from 'firebase/auth';
import { auth } from '@/firebase';
import { setAuthToken } from '@/services/api';
import { authService } from '@/services/authService';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [firebaseUser, setFirebaseUser] = useState(null);
  const [token, setToken] = useState(null);
  const [loading, setLoading] = useState(true);

  // Listen to Firebase auth state changes
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (fbUser) => {
      setFirebaseUser(fbUser);
      
      if (fbUser) {
        try {
          // Get Firebase ID token
          const idToken = await fbUser.getIdToken();
          setToken(idToken);
          setAuthToken(idToken);
          
          // Fetch user profile from backend
          await checkUser();
        } catch (error) {
           // Ignore 404s (user might not be registered in backend yet)
           // The login/register flows will handle backend user creation
           if (error.response && error.response.status === 404) {
             setUser(null);
           } else {
             console.error('Failed to fetch user profile:', error);
             setUser(null);
           }
        }
      } else {
        setToken(null);
        setAuthToken(null);
        setUser(null);
      }
      
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  const checkUser = async () => {
    try {
      const userProfile = await authService.getProfile();
      setUser(userProfile);
      return userProfile;
    } catch (error) {
      if (error.response && error.response.status === 404) {
        // User authenticated in Firebase but not in DB -> clear user profile
        setUser(null);
      } else {
        throw error;
      }
    }
  };

  // Refresh token periodically (Firebase tokens expire after 1 hour)
  useEffect(() => {
    if (!firebaseUser) return;

    const refreshToken = async () => {
      try {
        const newToken = await firebaseUser.getIdToken(true);
        setToken(newToken);
        setAuthToken(newToken);
      } catch (error) {
        console.error('Failed to refresh token:', error);
      }
    };

    // Refresh token every 55 minutes
    const interval = setInterval(refreshToken, 55 * 60 * 1000);
    return () => clearInterval(interval);
  }, [firebaseUser]);

  const login = async (email, password) => {
    const userCredential = await signInWithEmailAndPassword(auth, email, password);
    const idToken = await userCredential.user.getIdToken();
    setToken(idToken);
    setAuthToken(idToken);
    
    // Fetch user profile
    const userProfile = await authService.getProfile();
    setUser(userProfile);
    
    return userProfile;
  };

  const register = async (email, password, name, initial_level) => {
    // Create Firebase user
    const userCredential = await createUserWithEmailAndPassword(auth, email, password);
    const idToken = await userCredential.user.getIdToken();
    setToken(idToken);
    setAuthToken(idToken);
    
    // Create user profile in backend
    const userProfile = await authService.register(name, initial_level);
    
    setUser(userProfile);
    return userProfile;
  };

  const logout = async () => {
    await signOut(auth);
    setToken(null);
    setAuthToken(null);
    setUser(null);
  };

  const getAxiosConfig = () => ({
    headers: { Authorization: `Bearer ${token}` }
  });

  return (
    <AuthContext.Provider
      value={{
        user,
        token,
        loading,
        login,
        register,
        logout,
        checkUser,
        getAxiosConfig,
        isAuthenticated: !!token && !!user
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};
