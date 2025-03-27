import React, { useState, useEffect } from 'react';
import { getTaskStatus } from '../services/api';
import ReactMarkdown from 'react-markdown';
import { Card, CardHeader, CardContent } from './ui/card';
import { Button } from './ui/button';
import { Badge } from './ui/badge';
import { ScrollArea } from './ui/scroll-area';
import { Brain, Globe, Code, RefreshCw } from 'lucide-react';

const AgentActivity = ({ taskId, onStatusUpdate, onError }) => {
  const [execution, setExecution] = useState(null);
  const [loading, setLoading] = useState(false);
  const [pollingInterval, setPollingInterval] = useState(null);

  // Function to fetch task status
  const fetchTaskStatus = async () => {
    if (!taskId) return;
    
    setLoading(true);
    try {
      const data = await getTaskStatus(taskId);
      setExecution(data);
      onStatusUpdate(data.status);
      
      // If task is completed or failed, stop polling
      if (data.status === 'completed' || data.status === 'failed') {
        clearInterval(pollingInterval);
        setPollingInterval(null);
      }
    } catch (error) {
      console.error('Error fetching task status:', error);
      onError('Failed to fetch task status');
      clearInterval(pollingInterval);
      setPollingInterval(null);
    } finally {
      setLoading(false);
    }
  };

  // Start polling when taskId changes
  useEffect(() => {
    if (taskId) {
      fetchTaskStatus();
      
      // Clear any existing interval
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
      
      // Set up new polling interval
      const interval = setInterval(fetchTaskStatus, 3000);
      setPollingInterval(interval);
    }
    
    // Cleanup function
    return () => {
      if (pollingInterval) {
        clearInterval(pollingInterval);
      }
    };
  }, [taskId]);

  // Render status badge
  const renderStatusBadge = (status) => {
    let variant = 'default';
    
    switch (status) {
      case 'pending':
        variant = 'outline';
        break;
      case 'planning':
      case 'executing':
        variant = 'warning';
        break;
      case 'completed':
        variant = 'success';
        break;
      case 'failed':
        variant = 'destructive';
        break;
      default:
        variant = 'outline';
    }
    
    return (
      <Badge variant={variant}>
        {status.toUpperCase()}
      </Badge>
    );
  };

  // Render agent icon
  const renderAgentIcon = (type) => {
    switch (type) {
      case 'browser':
        return <Globe className="h-5 w-5 text-green-400" />;
      case 'swe':
        return <Code className="h-5 w-5 text-purple-400" />;
      case 'planner':
        return <Brain className="h-5 w-5 text-blue-400" />;
      default:
        return null;
    }
  };

  // Render step result
  const renderStepResult = (step) => {
    if (!step.result) return null;
    
    if (step.type === 'browser' && step.result.steps) {
      return (
        <div className="space-y-4">
          {step.result.steps.map((browserStep, idx) => (
            <div key={idx} className="space-y-2">
              <p className="font-medium">Action: {browserStep.action}</p>
              {browserStep.screenshot && (
                <div className="mt-2">
                  <img
                    src={`data:image/png;base64,${browserStep.screenshot}`}
                    alt={`Screenshot from step ${idx}`}
                    className="rounded-md border border-border"
                  />
                </div>
              )}
              {browserStep.result && (
                <div className="mt-2">
                  <ReactMarkdown className="prose prose-sm dark:prose-invert max-w-none">
                    {browserStep.result}
                  </ReactMarkdown>
                </div>
              )}
              {browserStep.error && (
                <div className="p-3 bg-destructive/10 border border-destructive/30 rounded-md text-destructive">
                  {browserStep.error}
                </div>
              )}
            </div>
          ))}
        </div>
      );
    }
    
    if (step.type === 'swe' && step.result.result) {
      const { code, language, explanation } = step.result.result;
      return (
        <div className="space-y-3">
          {explanation && (
            <ReactMarkdown className="prose prose-sm dark:prose-invert max-w-none">
              {explanation}
            </ReactMarkdown>
          )}
          <div className="bg-black/20 p-3 rounded-md overflow-x-auto">
            <pre>
              <code className={language}>
                {code}
              </code>
            </pre>
          </div>
        </div>
      );
    }
    
    // Default rendering for other result types
    return (
      <pre className="bg-black/20 p-3 rounded-md overflow-x-auto text-sm">
        {JSON.stringify(step.result, null, 2)}
      </pre>
    );
  };

  // Manual refresh button handler
  const handleRefresh = () => {
    fetchTaskStatus();
  };

  if (!taskId) {
    return (
      <div className="h-full flex flex-col">
        <h3 className="text-xl font-semibold mb-4">Agent Activity</h3>
        <div className="flex-1 flex items-center justify-center">
          <p className="text-muted-foreground">
            No activity yet. Send a message to get started.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-semibold">Agent Activity</h3>
        <div>
          {loading ? (
            <div className="h-5 w-5 animate-spin rounded-full border-2 border-primary border-t-transparent"></div>
          ) : (
            <Button variant="outline" size="sm" onClick={handleRefresh}>
              <RefreshCw className="h-4 w-4 mr-1" />
              Refresh
            </Button>
          )}
        </div>
      </div>
      
      <ScrollArea className="flex-1">
        {execution ? (
          <div className="space-y-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between p-4">
                <div className="text-sm">Task ID: {execution.task_id}</div>
                {renderStatusBadge(execution.status)}
              </CardHeader>
              <CardContent className="p-4 pt-0">
                <h4 className="font-medium mb-2">Original Task</h4>
                <p className="text-sm">{execution.original_task}</p>
                
                {execution.error && (
                  <div className="mt-4 p-3 bg-destructive/10 border border-destructive/30 rounded-md text-destructive">
                    {execution.error}
                  </div>
                )}
              </CardContent>
            </Card>
            
            <h4 className="font-medium mt-6 mb-3">Execution Steps</h4>
            {execution.steps && execution.steps.length > 0 ? (
              <div className="space-y-4">
                {execution.steps.map((step, index) => (
                  <Card key={index} className={`border-l-4 ${
                    step.type === 'browser' ? 'border-l-green-500' : 
                    step.type === 'swe' ? 'border-l-purple-500' : 'border-l-primary'
                  }`}>
                    <CardHeader className="flex flex-row items-center justify-between p-4">
                      <div className="flex items-center gap-2">
                        {renderAgentIcon(step.type)}
                        <span className="font-medium">Step {step.step_index + 1}</span>
                        <Badge variant="outline" className="ml-2">
                          {step.type.toUpperCase()}
                        </Badge>
                      </div>
                      {renderStatusBadge(step.status)}
                    </CardHeader>
                    <CardContent className="p-4 pt-0">
                      <p className="mb-4">{step.instruction}</p>
                      
                      {step.status === 'running' && (
                        <div className="flex flex-col items-center justify-center py-6">
                          <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
                          <p className="text-muted-foreground mt-4">Executing...</p>
                        </div>
                      )}
                      
                      {step.status === 'completed' && renderStepResult(step)}
                      
                      {step.error && (
                        <div className="mt-4 p-3 bg-destructive/10 border border-destructive/30 rounded-md text-destructive">
                          {step.error}
                        </div>
                      )}
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-10">
                <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
                <p className="text-muted-foreground mt-4">Planning your task...</p>
              </div>
            )}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-full py-10">
            <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
            <p className="text-muted-foreground mt-4">Loading task details...</p>
          </div>
        )}
      </ScrollArea>
    </div>
  );
};

export default AgentActivity;