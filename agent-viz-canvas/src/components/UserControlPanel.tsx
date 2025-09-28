import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Play, Pause, RefreshCw, Settings, Activity } from "lucide-react";
import { useState } from "react";

export const UserControlPanel = () => {
  const [isRunning, setIsRunning] = useState(true);
  const [autoRefresh, setAutoRefresh] = useState(true);

  return (
    <div className="h-full px-6 flex items-center justify-between bg-gradient-to-r from-panel via-background to-panel border-b border-panel-border">
      {/* Left - System Status */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Activity className="h-5 w-5 text-success" />
          <span className="text-lg font-bold text-foreground">Multi-Agent Dashboard</span>
        </div>
        <Badge variant="secondary" className="bg-success/20 text-success border-success/30">
          <div className="w-2 h-2 bg-success rounded-full mr-2 animate-pulse" />
          ACTIVE
        </Badge>
      </div>

      {/* Center - Main Controls */}
      <div className="flex items-center gap-3">
        <Button
          variant={isRunning ? "destructive" : "default"}
          size="sm"
          onClick={() => setIsRunning(!isRunning)}
          className="min-w-20"
        >
          {isRunning ? (
            <>
              <Pause className="h-4 w-4 mr-2" />
              Pause
            </>
          ) : (
            <>
              <Play className="h-4 w-4 mr-2" />
              Resume
            </>
          )}
        </Button>

        <Button
          variant="outline"
          size="sm"
          onClick={() => window.location.reload()}
        >
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>

        <Button variant="ghost" size="sm">
          <Settings className="h-4 w-4 mr-2" />
          Settings
        </Button>
      </div>

      {/* Right - Status Indicators */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <div className="w-2 h-2 bg-success rounded-full animate-pulse" />
          Auto-refresh: {autoRefresh ? 'ON' : 'OFF'}
        </div>
        <div className="text-sm text-muted-foreground">
          Last update: {new Date().toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};