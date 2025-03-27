import React, { useState, useEffect } from 'react';
import './App.css';
import TaskInput from './components/TaskInput';
import AgentActivity from './components/AgentActivity';

function App() {
  const [taskId, setTaskId] = useState(null);
  const [taskStatus, setTaskStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isConnected, setIsConnected] = useState(true);

  // Simulate checking connection status
  useEffect(() => {
    const checkConnection = () => {
      // In a real app, this would check the API connection
      setIsConnected(true);
    };
    
    checkConnection();
    const interval = setInterval(checkConnection, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const handleTaskSubmit = (newTaskId) => {
    setTaskId(newTaskId);
    setIsLoading(true);
    setError(null);
  };

  const handleTaskStatusUpdate = (status) => {
    setTaskStatus(status);
    setIsLoading(false);
  };

  const handleError = (errorMessage) => {
    setError(errorMessage);
    setIsLoading(false);
  };

  return (
    <div className="min-h-screen bg-background text-foreground">
      <div className="container mx-auto px-4 py-8">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-primary">ATOM: Agent-based Task Orchestration Module</h1>
          <p className="text-muted-foreground mt-2">Enter your task below and let our AI agents handle it</p>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
          <div className="md:col-span-5 bg-card rounded-lg border shadow-sm p-6 relative">
            {isConnected && (
              <div className="absolute top-4 right-4 bg-green-500 text-xs text-black px-2 py-1 rounded-full flex items-center gap-1">
                <div className="h-2 w-2 rounded-full bg-black"></div>
                Connected
              </div>
            )}
            <TaskInput
              onTaskSubmit={handleTaskSubmit}
              isLoading={isLoading}
            />
            {error && (
              <div className="mt-4 p-4 bg-destructive/10 border border-destructive/30 rounded-md text-destructive">
                <p>Error: {error}</p>
              </div>
            )}
          </div>
          
          <div className="md:col-span-7 bg-card rounded-lg border shadow-sm p-6 max-h-[calc(100vh-180px)] overflow-y-auto">
            <AgentActivity
              taskId={taskId}
              taskStatus={taskStatus}
              onStatusUpdate={handleTaskStatusUpdate}
              onError={handleError}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;