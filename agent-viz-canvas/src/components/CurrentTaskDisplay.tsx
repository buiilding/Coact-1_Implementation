import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Target, ArrowRight, User } from "lucide-react";
import { useState, useEffect, useRef } from "react";

interface Task {
  id: string;
  description: string;
  assignedTo: 'User' | 'Orchestrator' | 'Programmer' | 'GUIOperator';
  status: 'active' | 'delegated' | 'completed';
  parentTask?: string;
}

export const CurrentTaskDisplay = () => {
  const [currentTask, setCurrentTask] = useState<Task>({
    id: "waiting",
    description: "Waiting for user task...",
    assignedTo: "User",
    status: "active"
  });

  const [taskHistory, setTaskHistory] = useState<Task[]>([]);
  const websocketRef = useRef<WebSocket | null>(null);

  // WebSocket connection for real-time updates
  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = new WebSocket('ws://localhost:8765');

        ws.onopen = () => {
          console.log('📡 Connected to CoAct-1 WebSocket server');
        };

        ws.onmessage = (event) => {
          console.log('📨 Received WebSocket message:', event.data);
          try {
            const message = JSON.parse(event.data);
            console.log('📨 Parsed message:', message);
            handleWebSocketMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        ws.onclose = () => {
          console.log('📡 Disconnected from CoAct-1 WebSocket server');

          // Reset to waiting state when disconnected
          setCurrentTask({
            id: "waiting",
            description: "Waiting for user task...",
            assignedTo: "User",
            status: "active"
          });
          setTaskHistory([]);

          // Try to reconnect after a delay
          setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = (error) => {
          console.error('WebSocket error:', error);
        };

        websocketRef.current = ws;
      } catch (error) {
        console.error('Failed to connect to WebSocket:', error);
        // Retry connection
        setTimeout(connectWebSocket, 3000);
      }
    };

    connectWebSocket();

    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, []);

  const handleWebSocketMessage = (message: any) => {
    const { type, data } = message;
    console.log('🎯 Handling WebSocket message type:', type, 'with data:', data);

    switch (type) {
      case 'user_task_started':
        // Set initial task assigned to Orchestrator
        setCurrentTask({
          id: "user-task",
          description: `Orchestrator: ${data.task}`,
          assignedTo: "Orchestrator" as Task['assignedTo'],
          status: "active"
        });
        break;

      case 'task_delegated':
        console.log(`📝 Received task_delegated: ${data.description} (id: ${data.task_id})`);
        console.log(`📝 Full message data:`, data);

        // Add the delegation to task history (with deduplication)
        setTaskHistory(prev => {
          // Check if task with this ID already exists
          const existingTask = prev.find(task => task.id === data.task_id);
          if (existingTask) {
            console.log(`⚠️ Task ${data.task_id} already exists in history, skipping duplicate`);
            return prev;
          }

          console.log(`📝 Adding to taskHistory: ${data.task_id} - ${data.description}`);
          console.log(`📝 Current taskHistory length: ${prev.length}, new length will be: ${prev.length + 1}`);
          return [...prev, {
            id: data.task_id,
            description: data.description,
            assignedTo: data.assigned_to as Task['assignedTo'],
            status: "active"
          }];
        });

        // Update current task to show the delegated task
        setCurrentTask({
          id: data.task_id,
          description: data.description,
          assignedTo: data.assigned_to as Task['assignedTo'],
          status: "active",
          parentTask: data.parent_task
        });
        break;

      case 'subtask_completed':
        // Mark current task as completed
        setCurrentTask(prev => ({
          ...prev,
          status: "completed" as const
        }));

        // Update the task in history
        setTaskHistory(prev => prev.map(task =>
          task.id === data.task_id
            ? { ...task, status: "completed" as const }
            : task
        ));
        break;

      case 'task_completed':
        // Main task completed
        setCurrentTask({
          id: "completed",
          description: `Task completed: ${data.task}`,
          assignedTo: "User",
          status: "completed"
        });
        break;

      case 'ui_reset':
        // Reset task display to initial state
        setCurrentTask({
          id: "waiting",
          description: "Waiting for user task...",
          assignedTo: "User",
          status: "active"
        });
        setTaskHistory([]);
        break;

      default:
        console.log('Unknown WebSocket message type:', type);
    }
  };

  const getAgentColor = (agent: string) => {
    switch (agent) {
      case 'User': return 'bg-info/20 text-info border-info/30';
      case 'Orchestrator': return 'bg-accent/20 text-accent border-accent/30';
      case 'Programmer': return 'bg-warning/20 text-warning border-warning/30';
      case 'GUIOperator': return 'bg-success/20 text-success border-success/30';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  return (
    <Card className="h-full bg-gradient-to-br from-panel to-card border-panel-border shadow-lg">
      <CardHeader className="pb-2 px-2 pt-2">
        <CardTitle className="flex items-center gap-1 text-sm text-foreground">
          <Target className="h-4 w-4 text-accent" />
          Current Task
        </CardTitle>
      </CardHeader>
      <CardContent className="p-2 space-y-2">
        {/* Current Task */}
        <div className="p-2 rounded bg-background/50 border border-panel-border">
          <div className="flex items-center gap-1 mb-1">
            <Badge className={`text-xs ${getAgentColor(currentTask.assignedTo)}`}>
              {currentTask.assignedTo}
            </Badge>
            {currentTask.status === 'active' && (
              <div className="w-1.5 h-1.5 bg-success rounded-full animate-pulse" />
            )}
          </div>
          <p className="text-xs text-foreground leading-relaxed">
            {currentTask.description}
          </p>
          {currentTask.parentTask && (
            <div className="flex items-center gap-1 mt-1 text-xs text-muted-foreground">
              <ArrowRight className="h-3 w-3" />
              Subtask of: {currentTask.parentTask}
            </div>
          )}
        </div>

        {/* Task Flow */}
        <div className="space-y-1">
          <h4 className="text-xs font-medium text-muted-foreground">Task Flow</h4>
          <div className="space-y-1 max-h-20 overflow-y-auto">
            {taskHistory.map((task) => (
              <div key={task.id} className="flex items-center gap-1 p-1 rounded border border-panel-border/50 bg-background/30">
                <User className="h-3 w-3 text-muted-foreground" />
                <span className="text-xs text-muted-foreground flex-1 truncate">
                  {task.description}
                </span>
                <Badge className={`text-xs ${getAgentColor(task.assignedTo)}`}>
                  {task.assignedTo}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      </CardContent>
    </Card>
  );
};