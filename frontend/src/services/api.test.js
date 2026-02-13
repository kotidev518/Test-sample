import api, { setAuthToken } from './api';

// Mock axios since we are testing the wrapper
jest.mock('axios', () => ({
  create: jest.fn(() => ({
    defaults: {
      headers: {
        common: {}
      }
    }
  }))
}));

describe('API Service Utils', () => {
  it('should set Authorization header when token is provided', () => {
    const token = 'test-token';
    // Use the mocked api instance
    setAuthToken(token);
    expect(api.defaults.headers.common['Authorization']).toBe(`Bearer ${token}`);
  });

  it('should remove Authorization header when token is null', () => {
    setAuthToken(null);
    expect(api.defaults.headers.common['Authorization']).toBeUndefined();
  });
});
