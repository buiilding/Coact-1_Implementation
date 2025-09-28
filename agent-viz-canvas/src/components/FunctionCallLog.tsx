import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Terminal, MousePointer, Keyboard, ArrowDown, Monitor } from "lucide-react";
import { useState, useEffect, useRef } from "react";

interface FunctionCall {
  id: string;
  agent: string;
  action: string;
  details: string;
  timestamp: Date;
  status: 'executing' | 'completed' | 'failed';
}

export const FunctionCallLog = () => {
  const [currentCall, setCurrentCall] = useState<FunctionCall | null>(null);
  const [recentCalls, setRecentCalls] = useState<FunctionCall[]>([]);
  const websocketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = new WebSocket('ws://localhost:8765');

        ws.onopen = () => {
          console.log('📡 FunctionCallLog connected to CoAct-1 WebSocket server');
        };

        ws.onmessage = (event) => {
          try {
            const message = JSON.parse(event.data);
            handleWebSocketMessage(message);
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        ws.onclose = () => {
          console.log('📡 FunctionCallLog disconnected from CoAct-1 WebSocket server');
          setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = (error) => {
          console.error('FunctionCallLog WebSocket error:', error);
        };

        websocketRef.current = ws;
      } catch (error) {
        console.error('Failed to connect FunctionCallLog to WebSocket:', error);
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

    switch (type) {
      case 'function_call_update':
        // Create new function call entry
        const newCall: FunctionCall = {
          id: `call-${Date.now()}`,
          agent: data.agent_name,
          action: data.function_name,
          details: formatFunctionCallDetails(data.function_name, data.parameters),
          timestamp: new Date(data.timestamp * 1000), // Convert from seconds to milliseconds
          status: "executing"
        };

        // Move current call to recent calls if exists
        if (currentCall) {
          setRecentCalls(prev => [currentCall, ...prev.slice(0, 2)]);
        }

        // Set new call as current
        setCurrentCall(newCall);

        // Auto-complete after a delay (simulate completion)
        setTimeout(() => {
          setCurrentCall(prev => prev ? { ...prev, status: "completed" } : null);
        }, 2000);
        break;

      case 'ui_reset':
        // Reset all function call state
        setCurrentCall(null);
        setRecentCalls([]);
        break;

      default:
        // Ignore other message types
        break;
    }
  };

  const getModelDisplayName = (fullModelString: string): string => {
    // Extract just the thinking model name from complex model strings
    // e.g., "huggingface-local/OpenGVLab/InternVL3_5-4B+gemini/gemini-2.5-flash" -> "gemini-2.5-flash"
    const parts = fullModelString.split(/[/+]/);
    return parts[parts.length - 1] || fullModelString;
  };

  const formatFunctionCallDetails = (functionName: string, parameters: any): string => {
    // Handle computer.* prefixed function names
    if (functionName.startsWith('computer.')) {
      const actionType = functionName.replace('computer.', '');
      switch (actionType) {
        case 'click':
        case 'left_click':
          const coord = parameters.coordinate || [0, 0];
          return `Click at coordinates (${coord[0]}, ${coord[1]})`;
        case 'type':
        case 'type_text':
          return `Type text: '${parameters.text || ''}'`;
        case 'keypress':
        case 'key':
        case 'hotkey':
          if (Array.isArray(parameters.keys)) {
            return `Press key(s): ${parameters.keys.join(' + ')}`;
          }
          return `Press key(s): ${parameters.text || 'unknown'}`;
        case 'scroll':
          const scrollCoord = parameters.coordinate || [0, 0];
          return `Scroll at (${scrollCoord[0]}, ${scrollCoord[1]}) by (${parameters.scroll_x || 0}, ${parameters.scroll_y || 0})`;
        case 'screenshot':
          return `Take screenshot`;
        case 'mouse_move':
        case 'move_cursor':
        case 'move':
          const moveCoord = parameters.coordinate || [0, 0];
          return `Move cursor to (${moveCoord[0]}, ${moveCoord[1]})`;
        default:
          return `${actionType} with parameters: ${JSON.stringify(parameters)}`;
      }
    }

    // Handle regular function names
    switch (functionName) {
      case 'click':
        return `Click at coordinates (${parameters.x}, ${parameters.y})`;
      case 'type':
        return `Type text: '${parameters.text || ''}'`;
      case 'scroll':
        return `Scroll by (${parameters.scroll_x || 0}, ${parameters.scroll_y || 0})`;
      case 'keypress':
        return `Press key(s): ${Array.isArray(parameters.keys) ? parameters.keys.join(' + ') : parameters.keys}`;
      default:
        return `${functionName} with parameters: ${JSON.stringify(parameters)}`;
    }
  };

  const getActionIcon = (action: string) => {
    // Handle computer.* prefixed function names
    if (action.startsWith('computer.')) {
      const actionType = action.replace('computer.', '');
      switch (actionType) {
        case 'click':
        case 'left_click':
          return MousePointer;
        case 'type':
        case 'type_text':
          return Keyboard;
        case 'keypress':
        case 'key':
        case 'hotkey':
          return Keyboard;
        case 'scroll':
          return ArrowDown;
        case 'mouse_move':
        case 'move_cursor':
        case 'move':
          return MousePointer;
        case 'screenshot':
          return Monitor;
        default:
          return Terminal;
      }
    }

    // Handle regular function names
    switch (action) {
      case 'click': return MousePointer;
      case 'type': return Keyboard;
      case 'scroll': return ArrowDown;
      default: return Terminal;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'executing': return 'bg-warning/20 text-warning border-warning/30';
      case 'completed': return 'bg-success/20 text-success border-success/30';
      case 'failed': return 'bg-destructive/20 text-destructive border-destructive/30';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  return (
    <Card className="h-full bg-gradient-to-br from-panel to-card border-panel-border">
      <CardHeader className="pb-2 px-2 pt-2">
        <CardTitle className="flex items-center gap-1 text-sm text-foreground">
          <Terminal className="h-4 w-4 text-accent" />
          Function Calls
        </CardTitle>
      </CardHeader>
      <CardContent className="p-2 space-y-2">
        {/* Current Call */}
        {currentCall ? (
          <div className="p-2 rounded bg-background/50 border border-panel-border">
            <div className="flex items-center gap-1 mb-1">
              <Badge className={`text-xs ${getStatusColor(currentCall.status)}`}>
                {currentCall.status === 'executing' && (
                  <div className="w-1.5 h-1.5 bg-current rounded-full mr-1 animate-pulse" />
                )}
                {currentCall.status.toUpperCase()}
              </Badge>
              <Badge variant="outline" className="text-xs">
                {getModelDisplayName(currentCall.agent)}
              </Badge>
            </div>

            <div className="flex items-start gap-1">
              {(() => {
                const Icon = getActionIcon(currentCall.action);
                return <Icon className="h-3 w-3 text-accent mt-0.5 flex-shrink-0" />;
              })()}
              <div className="flex-1 min-w-0">
                <p className="text-xs font-medium text-foreground">
                  The Agent wants to: {currentCall.action}
                </p>
                <p className="text-xs text-muted-foreground mt-1 break-words">
                  {currentCall.details}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {currentCall.timestamp.toLocaleTimeString()}
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-2 rounded bg-background/30 border border-panel-border/50">
            <p className="text-xs text-muted-foreground">Waiting for function call...</p>
          </div>
        )}

        {/* Recent Calls */}
        <div className="space-y-1">
          <h4 className="text-xs font-medium text-muted-foreground uppercase tracking-wide">
            Recent Actions
          </h4>
          {recentCalls.slice(0, 2).map((call) => {
            const Icon = getActionIcon(call.action);
            return (
              <div key={call.id} className="flex items-center gap-1 p-1.5 rounded border border-panel-border/50 bg-background/20">
                <Icon className="h-3 w-3 text-muted-foreground flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="text-xs text-muted-foreground truncate">
                    {getModelDisplayName(call.agent)}: {call.action}
                  </p>
                </div>
                <Badge className={`text-xs ${getStatusColor(call.status)}`}>
                  ✓
                </Badge>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};