import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ExternalLink, Monitor } from "lucide-react";

export const StatusMessage = () => {
  return (
    <Card className="bg-gradient-to-r from-panel/90 to-card/90 border-panel-border backdrop-blur-sm">
      <div className="p-3 flex items-center gap-3">
        <div className="flex items-center gap-2">
          <Monitor className="h-4 w-4 text-accent" />
          <span className="text-sm text-foreground">
            Live System State:
          </span>
        </div>
        
        <a 
          href="http://localhost:6008" 
          target="_blank" 
          rel="noopener noreferrer"
          className="flex items-center gap-1 text-sm text-accent hover:text-accent/80 transition-colors"
        >
          localhost:6008
          <ExternalLink className="h-3 w-3" />
        </a>
        
        <Badge variant="outline" className="text-xs">
          <div className="w-2 h-2 bg-success rounded-full mr-1 animate-pulse" />
          LIVE
        </Badge>
      </div>
      
      <div className="px-3 pb-3">
        <p className="text-xs text-muted-foreground">
          The screenshot shown above is currently being parsed by the Agent.
        </p>
      </div>
    </Card>
  );
};