import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { GitBranch, Bot, Code, Monitor, Brain } from "lucide-react";
import { useState, useEffect, useRef } from "react";

interface Agent {
  id: string;
  name: string;
  status: 'idle' | 'active' | 'processing' | 'error';
  icon: React.ComponentType<{ className?: string }>;
  children?: Agent[];
}

export const AgentTree = () => {
  const [agents, setAgents] = useState<Agent>({
    id: "orchestrator",
    name: "Orchestrator",
    status: "idle",
    icon: Bot,
    children: [
      {
        id: "programmer",
        name: "Programmer",
        status: "idle",
        icon: Code
      },
      {
        id: "gui-operator",
        name: "GUIOperator",
        status: "idle",
        icon: Monitor,
        children: [
          {
            id: "grounding-model",
            name: "Grounding Model",
            status: "idle",
            icon: Brain
          }
        ]
      }
    ]
  });
  const websocketRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connectWebSocket = () => {
      try {
        const ws = new WebSocket('ws://localhost:8765');

        ws.onopen = () => {
          console.log('📡 AgentTree connected to CoAct-1 WebSocket server');
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
          console.log('📡 AgentTree disconnected from CoAct-1 WebSocket server');
          setTimeout(connectWebSocket, 3000);
        };

        ws.onerror = (error) => {
          console.error('AgentTree WebSocket error:', error);
        };

        websocketRef.current = ws;
      } catch (error) {
        console.error('Failed to connect AgentTree to WebSocket:', error);
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

    if (type === 'agent_state') {
      setAgents(prevAgents => ({
        ...prevAgents,
        status: data.orchestrator || 'idle',
        children: [
          {
            ...prevAgents.children![0],
            status: data.programmer || 'idle'
          },
          {
            ...prevAgents.children![1],
            status: data.gui_operator || 'idle',
            children: [
              {
                ...prevAgents.children![1].children![0],
                status: data.grounding_model || 'idle'
              }
            ]
          }
        ]
      }));
    } else if (type === 'ui_reset') {
      // Reset all agents to idle state
      setAgents(prevAgents => ({
        ...prevAgents,
        status: 'idle',
        children: [
          {
            ...prevAgents.children![0],
            status: 'idle'
          },
          {
            ...prevAgents.children![1],
            status: 'idle',
            children: [
              {
                ...prevAgents.children![1].children![0],
                status: 'idle'
              }
            ]
          }
        ]
      }));
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'processing': return 'bg-green-500/20 text-green-500 border-green-500/30';
      case 'active': return 'bg-agent-active/20 text-agent-active border-agent-active/30';
      case 'error': return 'bg-agent-error/20 text-agent-error border-agent-error/30';
      default: return 'bg-muted text-muted-foreground border-muted';
    }
  };

  const getStatusIndicator = (status: string) => {
    switch (status) {
      case 'processing':
        return <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />;
      case 'active':
        return <div className="w-2 h-2 bg-agent-active rounded-full animate-pulse" />;
      case 'error':
        return <div className="w-2 h-2 bg-agent-error rounded-full animate-ping" />;
      default:
        return <div className="w-2 h-2 bg-muted rounded-full" />;
    }
  };

  const renderTreeGraph = () => {
    return (
      <div className="relative h-full flex flex-col items-center justify-start pt-6">
        {/* Orchestrator Node */}
        <div className="relative mb-2">
          <div className={`w-16 h-16 rounded-full border-2 flex items-center justify-center transition-all duration-200 ${
            agents.status === 'processing' ? 'border-green-500 bg-green-500/20 shadow-[0_0_8px_rgba(34,197,94,0.4)]' :
            agents.status === 'active' ? 'border-agent-active bg-agent-active/20 shadow-[0_0_8px_hsl(var(--agent-active)/0.4)]' :
            'border-panel-border bg-background'
          }`}>
            <Bot className="h-5 w-5 text-accent" />
          </div>
          <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 text-xs font-medium text-foreground whitespace-nowrap">
            Orchestrator
          </div>
        </div>

        {/* Connection Lines */}
        <div className="relative w-32 h-4 mb-2">
          <div className="absolute top-0 left-1/2 w-px h-3 bg-panel-border" />
          <div className="absolute top-3 left-2 right-2 h-px bg-panel-border" />
          <div className="absolute top-3 left-2 w-px h-3 bg-panel-border" />
          <div className="absolute top-3 right-2 w-px h-3 bg-panel-border" />
        </div>

        {/* Child Nodes */}
        <div className="flex gap-16">
          {/* Programmer Node */}
          <div className="relative">
            <div className={`w-12 h-12 rounded-full border-2 flex items-center justify-center transition-all duration-200 ${
              agents.children?.[0]?.status === 'processing' ? 'border-green-500 bg-green-500/20 shadow-[0_0_6px_rgba(34,197,94,0.3)]' :
              agents.children?.[0]?.status === 'active' ? 'border-agent-active bg-agent-active/20 shadow-[0_0_6px_hsl(var(--agent-active)/0.3)]' :
              'border-panel-border bg-background'
            }`}>
              <Code className="h-4 w-4 text-accent" />
            </div>
            <div className="absolute -bottom-5 left-1/2 transform -translate-x-1/2 text-xs text-foreground whitespace-nowrap">
              Programmer
            </div>
          </div>

          {/* GUIOperator Node with Grounding Model */}
          <div className="relative">
            <div className={`w-12 h-12 rounded-full border-2 flex items-center justify-center transition-all duration-200 ${
              agents.children?.[1]?.status === 'processing' ? 'border-green-500 bg-green-500/20 shadow-[0_0_6px_rgba(34,197,94,0.3)]' :
              agents.children?.[1]?.status === 'active' ? 'border-agent-active bg-agent-active/20 shadow-[0_0_6px_hsl(var(--agent-active)/0.3)]' :
              'border-panel-border bg-background'
            }`}>
              <Monitor className="h-4 w-4 text-accent" />
            </div>
            <div className="absolute -bottom-5 left-1/2 transform -translate-x-1/2 text-xs text-foreground whitespace-nowrap">
              GUIOperator
            </div>
            
            {/* Connection to Grounding Model */}
            <div className="absolute top-12 left-1/2 w-px h-8 bg-panel-border" />

            {/* Grounding Model Node */}
            <div className="absolute top-20 left-1/2 transform -translate-x-1/2">
              <div className={`w-10 h-10 rounded-full border-2 flex items-center justify-center transition-all duration-200 ${
                agents.children?.[1]?.children?.[0]?.status === 'processing' ? 'border-green-500 bg-green-500/20 shadow-[0_0_4px_rgba(34,197,94,0.3)]' :
                agents.children?.[1]?.children?.[0]?.status === 'active' ? 'border-agent-active bg-agent-active/20 shadow-[0_0_4px_hsl(var(--agent-active)/0.3)]' :
                'border-panel-border bg-background'
              }`}>
                <Brain className="h-3 w-3 text-accent" />
              </div>
              <div className="absolute -bottom-4 left-1/2 transform -translate-x-1/2 text-xs text-foreground whitespace-nowrap">
                Grounding
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  return (
    <Card className="h-full bg-gradient-to-br from-panel to-card border-panel-border">
      <CardHeader className="pb-2 px-2 pt-2">
        <CardTitle className="flex items-center gap-1 text-sm text-foreground">
          <GitBranch className="h-4 w-4 text-accent" />
          Agent Hierarchy
        </CardTitle>
      </CardHeader>
      <CardContent className="p-2 h-[calc(100%-3rem)]">
        {renderTreeGraph()}
      </CardContent>
    </Card>
  );
};