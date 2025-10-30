import { spawn, type ChildProcess } from "child_process";
import * as fs from "fs";
import * as path from "path";
import { storage } from "./storage";

interface ProcessInfo {
  process: ChildProcess;
  repositoryId: string;
}

class PythonProcessManager {
  private processes: Map<string, ProcessInfo> = new Map();
  private logCallbacks: Map<string, Array<(message: string) => void>> = new Map();

  async startRepository(repositoryId: string): Promise<void> {
    if (this.processes.has(repositoryId)) {
      throw new Error("Repository is already running");
    }

    const repository = await storage.getRepositoryById(repositoryId);
    if (!repository) {
      throw new Error("Repository not found");
    }

    if (!repository.mainFile) {
      throw new Error("No main file configured. Please set a main file in settings.");
    }

    const workDir = path.join(process.cwd(), "runtime", repositoryId);
    
    // Create work directory if it doesn't exist
    if (!fs.existsSync(workDir)) {
      fs.mkdirSync(workDir, { recursive: true });
    }

    this.emitLog(repositoryId, `📁 Preparing files in: ${workDir}\n`);

    const files = await storage.getFiles(repositoryId);
    
    // Write all files to disk
    for (const file of files) {
      if (file.isDirectory) {
        const dirPath = file.path ? path.join(workDir, file.path, file.name) : path.join(workDir, file.name);
        if (!fs.existsSync(dirPath)) {
          fs.mkdirSync(dirPath, { recursive: true });
        }
        continue;
      }
      
      const relativePath = file.path ? path.join(file.path, file.name) : file.name;
      
      if (relativePath.includes("..")) {
        throw new Error(`Invalid file path: ${relativePath}`);
      }
      
      const filePath = path.join(workDir, relativePath);
      const fileDir = path.dirname(filePath);
      
      if (!fs.existsSync(fileDir)) {
        fs.mkdirSync(fileDir, { recursive: true });
      }
      
      fs.writeFileSync(filePath, file.content, "utf-8");
      this.emitLog(repositoryId, `  ✓ Written: ${relativePath}\n`);
    }

    // Verify main file exists
    const mainFilePath = path.join(workDir, repository.mainFile);
    if (!fs.existsSync(mainFilePath)) {
      const errorMsg = `Main file not found: ${repository.mainFile}`;
      this.emitLog(repositoryId, `❌ ${errorMsg}\n`);
      await storage.updateRepositoryById(repositoryId, { status: "error" });
      throw new Error(errorMsg);
    }
    
    this.emitLog(repositoryId, `✓ Main file found: ${repository.mainFile}\n`);

    const envVars = await storage.getEnvironmentVariables(repositoryId);
    const env = { ...process.env };
    for (const envVar of envVars) {
      env[envVar.key] = envVar.value;
    }

    // Check if requirements.txt exists and handle auto-installation
    const requirementsFile = files.find((f) => f.name === "requirements.txt" && !f.isDirectory);
    if (requirementsFile && requirementsFile.content.trim()) {
      this.emitLog(repositoryId, "ℹ️ requirements.txt detected.\n");
      
      if (repository.autoInstallFromRequirements) {
        this.emitLog(repositoryId, "📦 Auto-installing packages from requirements.txt...\n");
        
        try {
          const requirementsPath = path.join(workDir, "requirements.txt");
          
          // Install packages using pip
          const installOutput = await new Promise<string>((resolve, reject) => {
            const pipInstall = spawn("python3", ["-m", "pip", "install", "--user", "-r", requirementsPath], {
              cwd: workDir,
            });

            let output = "";
            let errorOutput = "";

            pipInstall.stdout?.on("data", (data) => {
              const message = data.toString();
              output += message;
              this.emitLog(repositoryId, message);
            });

            pipInstall.stderr?.on("data", (data) => {
              const message = data.toString();
              errorOutput += message;
              this.emitLog(repositoryId, message);
            });

            pipInstall.on("close", (code) => {
              if (code !== 0) {
                reject(new Error(errorOutput || `pip install failed with code ${code}`));
              } else {
                resolve(output);
              }
            });

            pipInstall.on("error", (error) => {
              reject(error);
            });
          });

          this.emitLog(repositoryId, "\n✅ Packages installed successfully from requirements.txt\n");
        } catch (error: any) {
          this.emitLog(repositoryId, `\n❌ Failed to install packages: ${error.message}\n`);
          this.emitLog(repositoryId, "ℹ️ You can install packages manually from the Terminal tab\n");
        }
      } else {
        this.emitLog(repositoryId, "ℹ️ Auto-install from requirements.txt is disabled.\n");
        this.emitLog(repositoryId, "ℹ️ Please install packages manually using the Terminal tab:\n");
        this.emitLog(repositoryId, "ℹ️ Run: pip install --user -r requirements.txt\n");
      }
    }

    this.emitLog(repositoryId, `\n🚀 Starting ${repository.mainFile}...\n`);
    this.emitLog(repositoryId, `Working directory: ${workDir}\n`);

    const childProcess = spawn("python3", ["-u", repository.mainFile], {
      cwd: workDir,
      env,
      stdio: ['pipe', 'pipe', 'pipe'],
    });

    if (!childProcess.pid) {
      const errorMsg = "Failed to spawn Python process";
      this.emitLog(repositoryId, `❌ ${errorMsg}\n`);
      await storage.updateRepositoryById(repositoryId, { status: "error" });
      throw new Error(errorMsg);
    }

    this.emitLog(repositoryId, `✓ Process started with PID: ${childProcess.pid}\n`);

    this.processes.set(repositoryId, {
      process: childProcess,
      repositoryId,
    });

    childProcess.stdout?.on("data", (data) => {
      const message = data.toString();
      if (message) {
        this.emitLog(repositoryId, message);
      }
    });

    childProcess.stderr?.on("data", (data) => {
      const message = data.toString();
      if (message) {
        this.emitLog(repositoryId, `[ERROR] ${message}`);
      }
    });

    childProcess.on("error", (error) => {
      this.emitLog(repositoryId, `❌ Process error: ${error.message}`);
      this.processes.delete(repositoryId);
      storage.updateRepositoryById(repositoryId, { status: "error" });
    });

    childProcess.on("exit", (code, signal) => {
      let status: "stopped" | "error" | "completed";
      if (code === 0) {
        status = "completed";
        this.emitLog(repositoryId, `✅ Process completed successfully (exit code ${code})`);
      } else {
        status = "error";
        this.emitLog(repositoryId, `❌ Process exited with code ${code}${signal ? ` and signal ${signal}` : ''}`);
      }
      this.processes.delete(repositoryId);
      storage.updateRepositoryById(repositoryId, { status });
    });

    await storage.updateRepositoryById(repositoryId, { status: "running" });
    this.emitLog(repositoryId, "\n✓ Application is now running\n\n--- Application Output ---\n");
  }

  stopRepository(repositoryId: string): void {
    const processInfo = this.processes.get(repositoryId);
    
    if (!processInfo) {
      // إذا لم تكن العملية تعمل، فقط حدّث الحالة
      storage.updateRepositoryById(repositoryId, { status: "stopped" });
      return;
    }

    processInfo.process.kill();
    this.processes.delete(repositoryId);
    this.emitLog(repositoryId, "⏹️ Process stopped");
    storage.updateRepositoryById(repositoryId, { status: "stopped" });
  }

  isRunning(repositoryId: string): boolean {
    return this.processes.has(repositoryId);
  }

  subscribeToLogs(repositoryId: string, callback: (message: string) => void): void {
    if (!this.logCallbacks.has(repositoryId)) {
      this.logCallbacks.set(repositoryId, []);
    }
    this.logCallbacks.get(repositoryId)!.push(callback);
  }

  unsubscribeFromLogs(repositoryId: string, callback: (message: string) => void): void {
    const callbacks = this.logCallbacks.get(repositoryId);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index !== -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  private emitLog(repositoryId: string, message: string): void {
    const callbacks = this.logCallbacks.get(repositoryId);
    if (callbacks) {
      callbacks.forEach((callback) => callback(message));
    }
  }

  async executeCommand(repositoryId: string, command: string): Promise<string> {
    return new Promise((resolve, reject) => {
      const workDir = path.join(process.cwd(), "runtime", repositoryId);
      
      if (!fs.existsSync(workDir)) {
        fs.mkdirSync(workDir, { recursive: true });
      }

      // Parse command into command and args
      const parts = command.split(" ");
      const cmd = parts[0];
      const args = parts.slice(1);

      // Execute the command
      const proc = spawn(cmd, args, {
        cwd: workDir,
        shell: true,
      });

      let output = "";
      let errorOutput = "";

      proc.stdout?.on("data", (data) => {
        output += data.toString();
      });

      proc.stderr?.on("data", (data) => {
        errorOutput += data.toString();
      });

      proc.on("close", (code) => {
        const fullOutput = output + (errorOutput ? `\n${errorOutput}` : "");
        if (code !== 0 && !output) {
          reject(new Error(errorOutput || `Command failed with code ${code}`));
        } else {
          resolve(fullOutput || "Command executed successfully");
        }
      });

      proc.on("error", (error) => {
        reject(error);
      });
    });
  }

  async installPackage(repositoryId: string, packageName: string): Promise<string> {
    return new Promise((resolve, reject) => {
      const workDir = path.join(process.cwd(), "runtime", repositoryId);
      
      if (!fs.existsSync(workDir)) {
        fs.mkdirSync(workDir, { recursive: true });
      }

      const pipInstall = spawn("python3", ["-m", "pip", "install", "--user", packageName], {
        cwd: workDir,
      });

      let output = "";
      let errorOutput = "";

      pipInstall.stdout?.on("data", (data) => {
        output += data.toString();
      });

      pipInstall.stderr?.on("data", (data) => {
        errorOutput += data.toString();
      });

      pipInstall.on("close", (code) => {
        if (code !== 0) {
          reject(new Error(errorOutput || `Failed to install ${packageName}`));
        } else {
          resolve(output);
        }
      });

      pipInstall.on("error", (error) => {
        reject(error);
      });
    });
  }

  async uninstallPackage(repositoryId: string, packageName: string): Promise<string> {
    return new Promise((resolve, reject) => {
      const workDir = path.join(process.cwd(), "runtime", repositoryId);

      // Use virtual environment pip if it exists
      const venvPipPath = path.join(workDir, ".venv", "bin", "pip");
      const pipCommand = fs.existsSync(venvPipPath) ? venvPipPath : "python3";
      const pipArgs = fs.existsSync(venvPipPath) ? ["uninstall", "-y", packageName] : ["-m", "pip", "uninstall", "-y", packageName];

      const pipUninstall = spawn(pipCommand, pipArgs, {
        cwd: workDir,
      });

      let output = "";
      let errorOutput = "";

      pipUninstall.stdout?.on("data", (data) => {
        output += data.toString();
      });

      pipUninstall.stderr?.on("data", (data) => {
        errorOutput += data.toString();
      });

      pipUninstall.on("close", (code) => {
        if (code !== 0) {
          reject(new Error(errorOutput || `Failed to uninstall ${packageName}`));
        } else {
          resolve(output);
        }
      });

      pipUninstall.on("error", (error) => {
        reject(error);
      });
    });
  }
}

export const pythonProcessManager = new PythonProcessManager();
