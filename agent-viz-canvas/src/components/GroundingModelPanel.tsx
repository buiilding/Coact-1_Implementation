import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Brain, Target, ArrowRight } from "lucide-react";
import { useState, useEffect, useRef } from "react";

interface GroundingResult {
  modelName: string;
  inputText: string;
  predictedCoordinates: {
    x: number;
    y: number;
  } | null;
  confidence: number;
  processingTime: number;
  status: 'processing' | 'completed' | 'error';
}

export const GroundingModelPanel = () => {
  const [groundingResult, setGroundingResult] = useState<GroundingResult>({
    modelName: "No active model",
    inputText: "Waiting for grounding request...",
    predictedCoordinates: null,
    confidence: 0.0,
    processingTime: 0,
    status: "completed"
  });
  const websocketRef = useRef<WebSocket | null>(null);

  const getGroundingModelDisplayName = (fullModelString: string): string => {
    // Extract the grounding model name from complex model strings
    // e.g., "huggingface-local/OpenGVLab/InternVL3_5-4B+gemini/gemini-2.5-flash" -> "InternVL3_5-4B"
    const parts = fullModelString.split(/[/+]/);
    // Grounding model is typically at index 2 (after provider/org)
    return parts.length >= 3 ? parts[2] : parts[parts.length - 1] || fullModelString;
  };

  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = new WebSocket('ws://localhost:8765');

        ws.onopen = () => {
          console.log('📡 GroundingModelPanel connected to CoAct-1 WebSocket server');
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
          console.log('📡 GroundingModelPanel disconnected from CoAct-1 WebSocket server');
          setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = (error) => {
          console.error('GroundingModelPanel WebSocket error:', error);
        };

        websocketRef.current = ws;
      } catch (error) {
        console.error('Failed to connect GroundingModelPanel to WebSocket:', error);
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
      case 'grounding_update':
        if (data.coordinates === null) {
          // Grounding model started processing
          setGroundingResult({
            modelName: getGroundingModelDisplayName(data.model_name),
            inputText: data.instruction,
            predictedCoordinates: null,
            confidence: 0.0,
            processingTime: 0,
            status: 'processing'
          });
        } else {
          // Grounding model completed
          setGroundingResult({
            modelName: getGroundingModelDisplayName(data.model_name),
            inputText: data.instruction,
            predictedCoordinates: { x: data.coordinates[0], y: data.coordinates[1] },
            confidence: data.confidence,
            processingTime: Math.round(data.processing_time * 1000), // Convert to ms
            status: 'completed'
          });
        }
        break;

      case 'ui_reset':
        // Reset to initial state
        setGroundingResult({
          modelName: "No active model",
          inputText: "Waiting for grounding request...",
          predictedCoordinates: null,
          confidence: 0.0,
          processingTime: 0,
          status: "completed"
        });
        break;

      default:
        // Ignore other message types
        break;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'processing': return 'bg-warning/20 text-warning border-warning/30';
      case 'completed': return 'bg-success/20 text-success border-success/30';
      case 'error': return 'bg-destructive/20 text-destructive border-destructive/30';
      default: return 'bg-muted text-muted-foreground';
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'text-success';
    if (confidence >= 0.8) return 'text-warning';
    return 'text-destructive';
  };

  return (
    <Card className="h-full bg-gradient-to-br from-panel to-card border-panel-border">
      <CardHeader className="pb-2 px-2 pt-2">
        <CardTitle className="flex items-center gap-1 text-sm text-foreground">
          <Brain className="h-4 w-4 text-accent" />
          Grounding Model
        </CardTitle>
      </CardHeader>
      <CardContent className="p-2 space-y-2">
        {/* Model Info */}
        <div className="flex items-center justify-between">
          <Badge variant="outline" className="text-xs">
            {groundingResult.modelName}
          </Badge>
          <Badge className={`text-xs ${getStatusColor(groundingResult.status)}`}>
            {groundingResult.status === 'processing' && (
              <div className="w-1.5 h-1.5 bg-current rounded-full mr-1 animate-spin" />
            )}
            {groundingResult.status.toUpperCase()}
          </Badge>
        </div>

        {/* Input */}
        <div className="p-2 rounded bg-background/30 border border-panel-border">
          <div className="text-xs text-muted-foreground mb-1">Input Query:</div>
          <p className="text-xs text-foreground font-medium break-words">
            "{groundingResult.inputText}"
          </p>
        </div>

        {/* Processing Arrow */}
        <div className="flex items-center justify-center">
          <ArrowRight className={`h-4 w-4 text-accent ${
            groundingResult.status === 'processing' ? 'animate-pulse' : ''
          }`} />
        </div>

        {/* Output */}
        <div className="p-2 rounded bg-background/30 border border-panel-border">
          <div className="text-xs text-muted-foreground mb-1">Predicted Coordinates:</div>
          {groundingResult.predictedCoordinates ? (
            <div className="space-y-1">
              <div className="flex items-center gap-1">
                <Target className="h-3 w-3 text-accent" />
                <span className="text-sm font-mono text-foreground">
                  ({groundingResult.predictedCoordinates.x}, {groundingResult.predictedCoordinates.y})
                </span>
              </div>
              
              <div className="flex items-center justify-between text-xs">
                <span className="text-muted-foreground">
                  Confidence: 
                  <span className={`ml-1 font-medium ${getConfidenceColor(groundingResult.confidence)}`}>
                    {Math.round(groundingResult.confidence * 100)}%
                  </span>
                </span>
                <span className="text-muted-foreground">
                  {groundingResult.processingTime}ms
                </span>
              </div>
            </div>
          ) : (
            <div className="text-xs text-muted-foreground">
              No coordinates predicted
            </div>
          )}
        </div>

        {/* Status Indicator */}
        {groundingResult.status === 'processing' && (
          <div className="flex items-center justify-center gap-1 text-xs text-muted-foreground">
            <div className="w-3 h-3 border border-accent border-t-transparent rounded-full animate-spin" />
            Analyzing...
          </div>
        )}
      </CardContent>
    </Card>
  );
};