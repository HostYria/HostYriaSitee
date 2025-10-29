import { useState, useEffect, useRef } from "react";
import { useMutation } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Terminal, Send, Loader2, Trash2 } from "lucide-react";

interface TerminalTabProps {
  repositoryId: string;
  isRunning: boolean;
}

interface TerminalOutput {
  timestamp: string;
  message: string;
  type: "info" | "error" | "success" | "command";
}

export function TerminalTab({ repositoryId, isRunning }: TerminalTabProps) {
  const [command, setCommand] = useState("");
  const [outputs, setOutputs] = useState<TerminalOutput[]>([]);
  const outputEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (outputEndRef.current) {
      outputEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [outputs]);

  const addOutput = (message: string, type: "info" | "error" | "success" | "command" = "info") => {
    setOutputs((prev) => [
      ...prev,
      {
        timestamp: new Date().toISOString(),
        message,
        type,
      },
    ]);
  };

  const executeCommandMutation = useMutation({
    mutationFn: async (cmd: string) => {
      return await apiRequest("POST", `/api/repositories/${repositoryId}/execute-command`, {
        command: cmd,
      });
    },
    onMutate: (cmd) => {
      addOutput(`$ ${cmd}`, "command");
    },
    onSuccess: (data: any) => {
      const output = data.output || data.message || "Command executed successfully";
      const type = data.success ? "success" : "info";
      addOutput(output, type);
      setCommand("");
      inputRef.current?.focus();
    },
    onError: (error: Error) => {
      addOutput(`Error: ${error.message}`, "error");
      inputRef.current?.focus();
    },
  });

  const handleExecute = (e: React.FormEvent) => {
    e.preventDefault();
    if (command.trim()) {
      executeCommandMutation.mutate(command.trim());
    }
  };

  const handleClear = () => {
    setOutputs([]);
  };

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString("ar-SA", { hour12: false });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold">Terminal</h2>
        {isRunning && (
          <div className="text-sm text-status-busy flex items-center gap-2">
            <div className="h-2 w-2 rounded-full bg-status-busy animate-pulse" />
            Repository is running
          </div>
        )}
      </div>

      <Card className="p-0 overflow-hidden border-2">
        <div className="bg-card-foreground/5 px-4 py-2 border-b flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Terminal className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm font-mono text-muted-foreground">
              Python Terminal - يمكنك تنفيذ أي أمر Python أو pip
            </span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleClear}
            disabled={outputs.length === 0}
          >
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>
        <div
          className="bg-card-foreground/[0.02] p-4 font-mono text-sm min-h-64 max-h-96 overflow-y-auto"
          data-testid="container-terminal"
        >
          {outputs.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground space-y-2">
              <Terminal className="h-8 w-8 opacity-50" />
              <p>ابدأ بكتابة أمر للتنفيذ...</p>
              <div className="text-xs space-y-1 text-center">
                <p>أمثلة:</p>
                <p className="font-mono">pip install requests</p>
                <p className="font-mono">pip list</p>
                <p className="font-mono">python --version</p>
              </div>
            </div>
          ) : (
            <div className="space-y-1">
              {outputs.map((output, index) => (
                <div
                  key={index}
                  className="flex gap-3"
                  data-testid={`terminal-output-${index}`}
                >
                  <span className="text-muted-foreground flex-shrink-0 text-xs">
                    [{formatTimestamp(output.timestamp)}]
                  </span>
                  <span
                    className={`flex-1 break-all ${
                      output.type === "error"
                        ? "text-destructive"
                        : output.type === "success"
                        ? "text-status-online"
                        : output.type === "command"
                        ? "text-blue-400 font-semibold"
                        : ""
                    }`}
                  >
                    {output.message}
                  </span>
                </div>
              ))}
              <div ref={outputEndRef} />
            </div>
          )}
        </div>
        <div className="border-t p-3 bg-card-foreground/[0.02]">
          <form onSubmit={handleExecute} className="flex gap-2">
            <div className="flex-1 flex items-center gap-2 bg-background border rounded-md px-3">
              <span className="text-muted-foreground font-mono">$</span>
              <Input
                ref={inputRef}
                placeholder="اكتب أمر Python أو pip... (مثال: pip install requests)"
                value={command}
                onChange={(e) => setCommand(e.target.value)}
                disabled={executeCommandMutation.isPending || isRunning}
                className="border-0 focus-visible:ring-0 font-mono"
                data-testid="input-terminal-command"
              />
            </div>
            <Button
              type="submit"
              disabled={!command.trim() || executeCommandMutation.isPending || isRunning}
              data-testid="button-execute-command"
            >
              {executeCommandMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              ) : (
                <Send className="h-4 w-4 mr-2" />
              )}
              تنفيذ
            </Button>
          </form>
        </div>
      </Card>

      <Card className="p-4 bg-blue-500/5 border-blue-500/20">
        <div className="flex items-start gap-3">
          <Terminal className="h-5 w-5 text-blue-500 mt-0.5" />
          <div className="space-y-2 text-sm">
            <p className="font-semibold text-blue-500">أمثلة على الأوامر المتاحة:</p>
            <div className="space-y-1 text-muted-foreground font-mono">
              <p>• pip install --user package_name - لتثبيت مكتبة</p>
              <p>• pip uninstall -y package_name - لإزالة مكتبة</p>
              <p>• pip list - لعرض جميع المكتبات المثبتة</p>
              <p>• pip freeze &gt; requirements.txt - لحفظ المكتبات (للمرجعية فقط)</p>
              <p>• python --version - لعرض إصدار Python</p>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}