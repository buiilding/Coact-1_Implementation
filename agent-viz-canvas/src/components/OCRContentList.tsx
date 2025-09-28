import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Eye, Hash } from "lucide-react";
import { ScrollArea } from "@/components/ui/scroll-area";
import { useState, useEffect, useRef } from "react";

interface OCRResult {
  id: string;
  text: string;
  confidence: number;
  bbox: {
    x: number;
    y: number;
    width: number; 
    height: number;
  };
}

export const OCRContentList = () => {
  const [ocrResults, setOcrResults] = useState<OCRResult[]>([]);
  const websocketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = new WebSocket('ws://localhost:8765');

        ws.onopen = () => {
          console.log('📡 OCRContentList connected to CoAct-1 WebSocket server');
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
          console.log('📡 OCRContentList disconnected from CoAct-1 WebSocket server');
          setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = (error) => {
          console.error('OCRContentList WebSocket error:', error);
        };

        websocketRef.current = ws;
      } catch (error) {
        console.error('Failed to connect OCRContentList to WebSocket:', error);
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
      case 'ocr_update':
        // Convert OCR results to component format
        const newResults: OCRResult[] = data.ocr_results.map((ocr: any) => ({
          id: ocr.id,
          text: ocr.text,
          confidence: ocr.confidence,
          bbox: {
            x: ocr.bbox.x,
            y: ocr.bbox.y,
            width: ocr.bbox.width,
            height: ocr.bbox.height
          }
        }));
        setOcrResults(newResults.slice(0, 8)); // Keep only latest 8 results
        break;

      case 'ui_reset':
        // Reset OCR results
        setOcrResults([]);
        break;

      default:
        // Ignore other message types
        break;
    }
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'bg-success/20 text-success border-success/30';
    if (confidence >= 0.8) return 'bg-warning/20 text-warning border-warning/30';
    return 'bg-destructive/20 text-destructive border-destructive/30';
  };

  return (
    <Card className="h-full bg-gradient-to-br from-panel to-card border-panel-border">
      <CardHeader className="pb-2 px-2 pt-2">
        <CardTitle className="flex items-center gap-1 text-sm text-foreground">
          <Eye className="h-4 w-4 text-accent" />
          OCR Content
        </CardTitle>
        <div className="flex items-center gap-1 text-xs text-muted-foreground">
          <Hash className="h-3 w-3" />
          {ocrResults.length} elements
        </div>
      </CardHeader>
      <CardContent className="p-2 h-[calc(100%-5rem)]">
        <ScrollArea className="h-full">
          <div className="space-y-1">
            {ocrResults.slice(0, 6).map((result, index) => (
              <div 
                key={result.id}
                className="p-2 rounded border border-panel-border bg-background/30 hover:bg-background/50 transition-colors"
              >
                <div className="flex items-start justify-between gap-1 mb-1">
                  <span className="text-xs font-medium text-foreground flex-1 truncate">
                    "{result.text}"
                  </span>
                  <Badge className={`text-xs ${getConfidenceColor(result.confidence)}`}>
                    {Math.round(result.confidence * 100)}%
                  </Badge>
                </div>
                
                <div className="text-xs text-muted-foreground">
                  ({result.bbox.x}, {result.bbox.y}) {result.bbox.width}×{result.bbox.height}
                </div>
                
                {index === 0 && (
                  <div className="flex items-center gap-1 mt-1">
                    <div className="w-1.5 h-1.5 bg-success rounded-full animate-pulse" />
                    <span className="text-xs text-success">Latest</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
};