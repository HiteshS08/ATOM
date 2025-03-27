import axios from 'axios';

// Create axios instance with default config
const api = axios.create({
  baseURL: '/orchestrator',
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Execute a task
 * @param {string} task - The task to execute
 * @returns {Promise<Object>} - The response data
 */
export const executeTask = async (task) => {
  try {
    const response = await api.post('/execute', { task });
    return response.data;
  } catch (error) {
    console.error('Error executing task:', error);
    throw error;
  }
};

/**
 * Get the status of a task
 * @param {string} taskId - The ID of the task
 * @returns {Promise<Object>} - The response data
 */
export const getTaskStatus = async (taskId) => {
  try {
    const response = await api.get(`/status/${taskId}`);
    return response.data;
  } catch (error) {
    console.error('Error getting task status:', error);
    throw error;
  }
};

/**
 * Get all task executions
 * @returns {Promise<Object>} - The response data
 */
export const getExecutions = async () => {
  try {
    const response = await api.get('/executions');
    return response.data;
  } catch (error) {
    console.error('Error getting executions:', error);
    throw error;
  }
};

export default api;