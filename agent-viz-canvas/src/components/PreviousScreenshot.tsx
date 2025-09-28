import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { History, Clock } from "lucide-react";
import { useState, useEffect, useRef } from "react";

export const PreviousScreenshot = () => {
  const [previousScreenshot, setPreviousScreenshot] = useState<string | null>(null);
  const [timestamp, setTimestamp] = useState<Date | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = new WebSocket('ws://localhost:8765');

        ws.onopen = () => {
          console.log('📡 PreviousScreenshot connected to CoAct-1 WebSocket server');
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
          console.log('📡 PreviousScreenshot disconnected from CoAct-1 WebSocket server');
          setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = (error) => {
          console.error('PreviousScreenshot WebSocket error:', error);
        };

        websocketRef.current = ws;
      } catch (error) {
        console.error('Failed to connect PreviousScreenshot to WebSocket:', error);
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
        if (data.screenshot_type === 'previous') {
          setPreviousScreenshot(data.screenshot_data);
          setTimestamp(new Date(data.timestamp * 1000));
        }
        break;

      case 'ui_reset':
        // Reset previous screenshot state
        setPreviousScreenshot(null);
        setTimestamp(null);
        break;

      default:
        // Ignore other message types
        break;
    }
  };

  const getTimeAgo = (date: Date | null): string => {
    if (!date) return '';

    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSeconds = Math.floor(diffMs / 1000);

    if (diffSeconds < 60) {
      return `${diffSeconds}s ago`;
    } else if (diffSeconds < 3600) {
      return `${Math.floor(diffSeconds / 60)}m ago`;
    } else {
      return `${Math.floor(diffSeconds / 3600)}h ago`;
    }
  };

  return (
    <Card className="h-full bg-gradient-to-br from-panel to-card border-panel-border">
      <CardHeader className="pb-2 px-2 pt-2">
        <CardTitle className="flex items-center gap-1 text-sm text-foreground">
          <History className="h-4 w-4 text-muted-foreground" />
          Previous
        </CardTitle>
      </CardHeader>
      <CardContent className="p-2 h-[calc(100%-3rem)]">
        <div className="relative h-full bg-gradient-to-br from-slate-800 to-slate-700 rounded border border-panel-border overflow-hidden">
          {/* Display actual previous screenshot */}
          {previousScreenshot ? (
            <>
              <img
                src={`data:image/png;base64,${previousScreenshot}`}
                alt="Previous Screenshot"
                className="absolute inset-0 w-full h-full object-contain"
              />

              {/* Timestamp Badge */}
              <div className="absolute top-1 right-1">
                <Badge variant="secondary" className="text-xs bg-background/80">
                  <Clock className="h-3 w-3 mr-1" />
                  {getTimeAgo(timestamp)}
                </Badge>
              </div>

              {/* Dimmed Overlay */}
              <div className="absolute inset-0 bg-background/20" />
            </>
          ) : (
            <div className="absolute inset-0 flex items-center justify-center text-muted-foreground">
              No previous screenshot
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};