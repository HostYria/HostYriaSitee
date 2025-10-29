import { useEffect, useState, useRef } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Download, Trash2, Terminal } from "lucide-react";
import { useToast } from "@/hooks/use-toast";

interface LogsTabProps {
  repositoryId: string;
  isRunning: boolean;
}

interface LogEntry {
  timestamp: string;
  message: string;
}

export function LogsTab({ repositoryId, isRunning }: LogsTabProps) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const logsContainerRef = useRef<HTMLDivElement>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    if (!isRunning) {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
      return;
    }

    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    
    console.log("Connecting to WebSocket:", wsUrl);
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("WebSocket connected, subscribing to repository:", repositoryId);
      ws.send(JSON.stringify({ type: "subscribe", repositoryId }));
      setLogs((prev) => [
        ...prev,
        {
          timestamp: new Date().toISOString(),
          message: "🔌 Connected to log stream",
        },
      ]);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "log" && data.repositoryId === repositoryId) {
          const lines = data.message.split('\n').filter((line: string) => line.trim());
          lines.forEach((line: string) => {
            setLogs((prev) => [
              ...prev,
              {
                timestamp: new Date().toISOString(),
                message: line,
              },
            ]);
          });
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      toast({
        title: "Connection error",
        description: "Lost connection to log stream",
        variant: "destructive",
      });
    };

    ws.onclose = () => {
      console.log("WebSocket disconnected");
      setLogs((prev) => [
        ...prev,
        {
          timestamp: new Date().toISOString(),
          message: "🔌 Disconnected from log stream",
        },
      ]);
    };

    wsRef.current = ws;

    return () => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [repositoryId, isRunning, toast]);

  useEffect(() => {
    if (autoScroll && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs, autoScroll]);

  const clearLogs = () => {
    setLogs([]);
    toast({
      title: "Logs cleared",
      description: "All logs have been cleared",
    });
  };

  const downloadLogs = () => {
    const logText = logs.map((log) => `[${log.timestamp}] ${log.message}`).join("\n");
    const blob = new Blob([logText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `logs-${repositoryId}-${new Date().toISOString()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast({
      title: "Logs downloaded",
      description: "Logs have been saved to your device",
    });
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString("en-US", { hour12: false });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-xl font-semibold">Logs</h2>
          {isRunning && (
            <div className="flex items-center gap-2">
              <div className="h-2 w-2 bg-status-online rounded-full animate-pulse" />
              <span className="text-sm text-muted-foreground">Live</span>
            </div>
          )}
        </div>
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <Switch
              id="auto-scroll"
              checked={autoScroll}
              onCheckedChange={setAutoScroll}
              data-testid="switch-auto-scroll"
            />
            <Label htmlFor="auto-scroll" className="text-sm cursor-pointer">
              Auto-scroll
            </Label>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={downloadLogs}
            disabled={logs.length === 0}
            data-testid="button-download-logs"
          >
            <Download className="h-4 w-4 mr-2" />
            Download
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={clearLogs}
            disabled={logs.length === 0}
            data-testid="button-clear-logs"
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Clear
          </Button>
        </div>
      </div>

      <Card className="p-0 overflow-hidden border-2">
        <div className="bg-card-foreground/5 px-4 py-2 border-b flex items-center gap-2">
          <Terminal className="h-4 w-4 text-muted-foreground" />
          <span className="text-sm font-mono text-muted-foreground">
            Application Output
          </span>
        </div>
        <div
          ref={logsContainerRef}
          className="bg-card-foreground/[0.02] p-4 font-mono text-sm min-h-96 max-h-96 overflow-y-auto"
          data-testid="container-logs"
        >
          {logs.length === 0 ? (
            <div className="flex items-center justify-center h-full text-muted-foreground">
              {isRunning
                ? "Waiting for application output..."
                : "Start the application to view logs"}
            </div>
          ) : (
            <div className="space-y-1">
              {logs.map((log, index) => (
                <div
                  key={index}
                  className="flex gap-3"
                  data-testid={`log-entry-${index}`}
                >
                  <span className="text-muted-foreground flex-shrink-0">
                    [{formatTimestamp(log.timestamp)}]
                  </span>
                  <span className="flex-1 break-all">{log.message}</span>
                </div>
              ))}
              <div ref={logsEndRef} />
            </div>
          )}
        </div>
      </Card>
    </div>
  );
}