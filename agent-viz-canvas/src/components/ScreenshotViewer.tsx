import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Monitor } from "lucide-react";
import { useState, useEffect, useRef } from "react";


interface AgentAction {
  type: 'click' | 'type' | 'scroll';
  x?: number;
  y?: number;
  text?: string;
}

export const ScreenshotViewer = () => {
  const [currentScreenshot, setCurrentScreenshot] = useState<string | null>(null);
  const [agentAction, setAgentAction] = useState<AgentAction | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = new WebSocket('ws://localhost:8765');

        ws.onopen = () => {
          console.log('📡 ScreenshotViewer connected to CoAct-1 WebSocket server');
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
          console.log('📡 ScreenshotViewer disconnected from CoAct-1 WebSocket server');
          // Try to reconnect after a delay
          setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = (error) => {
          console.error('ScreenshotViewer WebSocket error:', error);
        };

        websocketRef.current = ws;
      } catch (error) {
        console.error('Failed to connect ScreenshotViewer to WebSocket:', error);
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
      case 'screenshot_update':
        if (data.screenshot_type === 'current') {
          setCurrentScreenshot(data.screenshot_data);
          // Clear agent action when new screenshot arrives
          setAgentAction(null);
        } else if (data.screenshot_type === 'guioperator_realtime' || data.screenshot_type === 'programmer_realtime' || data.screenshot_type === 'screenshot_after_function') {
          // Update current screenshot with real-time sub-agent screenshot
          setCurrentScreenshot(data.screenshot_data);
          // Keep agent action for real-time updates
        }
        break;


      case 'grounding_update':
        // Update agent action based on grounding results
        if (data.coordinates) {
          setAgentAction({
            type: 'click',
            x: data.coordinates[0],
            y: data.coordinates[1]
          });
        }
        break;

      case 'function_call_update':
        // Handle function call updates
        const actionType = data.function_name === 'click' ? 'click' :
                          data.function_name === 'type' ? 'type' : 'click';

        if (data.parameters && data.parameters.x && data.parameters.y) {
          setAgentAction({
            type: actionType,
            x: data.parameters.x,
            y: data.parameters.y,
            text: data.parameters.text
          });
        }
        break;

      case 'ui_reset':
        // Reset all screenshot viewer state
        setCurrentScreenshot(null);
        setAgentAction(null);
        break;

      default:
        console.log('Unknown WebSocket message type in ScreenshotViewer:', type);
    }
  };

  return (
    <Card className="h-full bg-gradient-to-br from-panel to-card border-panel-border shadow-xl">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2 text-foreground">
            <Monitor className="h-5 w-5 text-accent" />
            Current Screenshot
          </CardTitle>
          <div className="flex items-center gap-2">
            <div className="text-xs text-muted-foreground mr-2">
              See the real-time operating system on{" "}
              <a
                href="http://localhost:8006"
                target="_blank"
                rel="noopener noreferrer"
                className="text-accent hover:text-accent/80 underline"
              >
                localhost:8006
              </a>
              , this is the current screenshot parsed to the agent
            </div>
            <Badge variant="outline" className="text-xs">
              1920x1080
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="h-[calc(100%-5rem)]">
        <div className="relative h-full bg-gradient-to-br from-slate-900 to-slate-800 rounded-lg border border-panel-border overflow-hidden">
          {/* Display actual screenshot */}
          {currentScreenshot ? (
            <img
              src={`data:image/png;base64,${currentScreenshot}`}
              alt="Current Screenshot"
              className="absolute inset-0 w-full h-full object-contain"
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
              Waiting for screenshot...
            </div>
          )}


          {/* Agent Action Indicator */}
          {agentAction && agentAction.x && agentAction.y && (
            <div
              className="absolute pointer-events-none"
              style={{
                left: `${agentAction.x - 10}px`,
                top: `${agentAction.y - 10}px`,
              }}
            >
              {agentAction.type === 'click' && (
                <div className="w-5 h-5 border-2 border-warning bg-warning/20 rounded-full animate-ping" />
              )}
              {agentAction.type === 'type' && (
                <div className="w-1 h-6 bg-accent animate-pulse" />
              )}
            </div>
          )}

        </div>
      </CardContent>
    </Card>
  );
};