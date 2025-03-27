import React, { useState } from 'react';
import { executeTask } from '../services/api';
import { Button } from './ui/button';
import { Textarea } from './ui/textarea';

const TaskInput = ({ onTaskSubmit, isLoading }) => {
  const [task, setTask] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!task.trim()) {
      return;
    }
    
    try {
      const response = await executeTask(task);
      onTaskSubmit(response.task_id);
    } catch (error) {
      console.error('Error submitting task:', error);
    }
  };

  return (
    <div className="task-input">
      <h3 className="text-xl font-semibold mb-4">Agent Chat</h3>
      
      <form className="flex flex-col h-full" onSubmit={handleSubmit}>
        <div className="flex-grow mb-4">
          <Textarea
            className="min-h-[200px] resize-none"
            placeholder="e.g., Find the latest news about artificial intelligence and create a summary in markdown format"
            value={task}
            onChange={(e) => setTask(e.target.value)}
            disabled={isLoading}
          />
        </div>
        
        <Button
          type="submit"
          disabled={isLoading || !task.trim()}
          className="w-full"
        >
          {isLoading ? (
            <>
              <div className="mr-2 h-4 w-4 animate-spin rounded-full border-2 border-background border-t-foreground"></div>
              Processing...
            </>
          ) : (
            'Execute Task'
          )}
        </Button>
      </form>
      
      {isLoading && (
        <div className="text-center mt-4">
          <p className="text-muted-foreground">
            Our AI agents are working on your task. This may take a few moments...
          </p>
        </div>
      )}
    </div>
  );
};

export default TaskInput;