import { spawn, type ChildProcess } from "child_process";
import * as fs from "fs";
import * as path from "path";
import { storage } from "./storage";
import chokidar from "chokidar";

interface ProcessInfo {
  process: ChildProcess;
  repositoryId: string;
}

class PythonProcessManager {
  private processes: Map<string, ProcessInfo> = new Map();
  private logCallbacks: Map<string, Array<(message: string) => void>> = new Map();
  private fileWatchers: Map<string, any> = new Map();

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

    // Start file watcher for auto-sync (will restart if already running)
    this.startFileWatcher(repositoryId, workDir);

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
            // Use --user flag and --break-system-packages for Render/externally-managed environments
            const pipInstall = spawn("python3", ["-m", "pip", "install", "--user", "--break-system-packages", "-r", requirementsPath], {
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

  startFileWatcher(repositoryId: string, workDir: string): void {
    // إيقاف المراقب القديم إذا كان موجوداً
    if (this.fileWatchers.has(repositoryId)) {
      this.fileWatchers.get(repositoryId).close();
    }

    const watcher = chokidar.watch(workDir, {
      ignored: /(^|[\/\\])\../, // تجاهل الملفات المخفية
      persistent: true,
      ignoreInitial: true,
      awaitWriteFinish: {
        stabilityThreshold: 200, // تقليل وقت الانتظار لتحديث أسرع
        pollInterval: 50
      }
    });

    watcher
      .on('addDir', async (dirPath: string) => {
        try {
          const relativePath = path.relative(workDir, dirPath);
          if (!relativePath) return; // تجاهل المجلد الجذر
          
          const pathParts = relativePath.split(path.sep);
          const folderName = pathParts.pop() || '';
          const parentDir = pathParts.join('/');

          const existing = await storage.getFileByPath(repositoryId, relativePath.replace(/\\/g, '/'));
          if (!existing) {
            await storage.createFile(repositoryId, {
              name: folderName,
              path: parentDir,
              content: '',
              size: 0,
              isDirectory: true
            });
            console.log(`[File Sync] New folder detected and saved: ${relativePath}`);
            this.emitLog(repositoryId, `📁 تم إنشاء المجلد تلقائيًا: ${relativePath}\n`);
            this.emitFileSync(repositoryId, 'folder_created');
          }
        } catch (error: any) {
          console.error('Error syncing new folder:', error);
        }
      })
      .on('add', async (filePath: string) => {
        try {
          const relativePath = path.relative(workDir, filePath);
          const pathParts = relativePath.split(path.sep);
          const fileName = pathParts.pop() || '';
          const fileDir = pathParts.join('/');

          const content = fs.readFileSync(filePath, 'utf-8');
          const size = Buffer.byteLength(content, 'utf-8');

          const existing = await storage.getFileByPath(repositoryId, relativePath.replace(/\\/g, '/'));
          if (!existing) {
            await storage.createFile(repositoryId, {
              name: fileName,
              path: fileDir,
              content,
              size,
              isDirectory: false
            });
            console.log(`[File Sync] New file detected and saved: ${relativePath}`);
            this.emitLog(repositoryId, `✅ تم حفظ الملف الجديد تلقائيًا: ${relativePath}\n`);
            this.emitFileSync(repositoryId, 'file_created');
          }
        } catch (error: any) {
          console.error('Error syncing new file:', error);
        }
      })
      .on('change', async (filePath: string) => {
        try {
          const relativePath = path.relative(workDir, filePath);
          const content = fs.readFileSync(filePath, 'utf-8');
          const size = Buffer.byteLength(content, 'utf-8');

          const existing = await storage.getFileByPath(repositoryId, relativePath.replace(/\\/g, '/'));
          if (existing) {
            await storage.updateFile(existing.id, repositoryId, { content, size });
            console.log(`[File Sync] File change detected and saved: ${relativePath}`);
            this.emitLog(repositoryId, `💾 تم حفظ التغييرات تلقائيًا: ${relativePath}\n`);
            this.emitFileSync(repositoryId, 'file_updated');
          }
        } catch (error: any) {
          console.error('Error syncing file change:', error);
        }
      })
      .on('unlink', async (filePath: string) => {
        try {
          const relativePath = path.relative(workDir, filePath);
          const existing = await storage.getFileByPath(repositoryId, relativePath.replace(/\\/g, '/'));
          if (existing) {
            await storage.deleteFile(existing.id, repositoryId);
            console.log(`[File Sync] File deletion detected and synced: ${relativePath}`);
            this.emitLog(repositoryId, `🗑️ تم حذف الملف تلقائيًا: ${relativePath}\n`);
            this.emitFileSync(repositoryId, 'file_deleted');
          }
        } catch (error: any) {
          console.error('Error syncing file deletion:', error);
        }
      })
      .on('unlinkDir', async (dirPath: string) => {
        try {
          const relativePath = path.relative(workDir, dirPath);
          const existing = await storage.getFileByPath(repositoryId, relativePath.replace(/\\/g, '/'));
          if (existing) {
            await storage.deleteFile(existing.id, repositoryId);
            console.log(`[File Sync] Folder deletion detected and synced: ${relativePath}`);
            this.emitLog(repositoryId, `🗑️ تم حذف المجلد تلقائيًا: ${relativePath}\n`);
            this.emitFileSync(repositoryId, 'folder_deleted');
          }
        } catch (error: any) {
          console.error('Error syncing folder deletion:', error);
        }
      });

    this.fileWatchers.set(repositoryId, watcher);
  }

  private emitFileSync(repositoryId: string, action: string): void {
    const callbacks = this.logCallbacks.get(repositoryId);
    if (callbacks) {
      callbacks.forEach((callback) => callback(`__FILE_SYNC__:${action}`));
    }
  }

  stopRepository(repositoryId: string): void {
    const processInfo = this.processes.get(repositoryId);
    
    // لا نقوم بإيقاف مراقب الملفات - يستمر في العمل حتى عند إيقاف العملية
    // هذا يسمح بالتزامن التلقائي للملفات حتى عندما يكون المستودع متوقفًا
    
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

  async syncRuntimeFilesToDatabase(repositoryId: string): Promise<void> {
    const workDir = path.join(process.cwd(), "runtime", repositoryId);
    
    if (!fs.existsSync(workDir)) {
      return;
    }

    const scanDirectory = async (dirPath: string, relativePath: string = ""): Promise<void> => {
      const items = fs.readdirSync(dirPath, { withFileTypes: true });

      for (const item of items) {
        const itemPath = path.join(dirPath, item.name);
        const itemRelativePath = relativePath ? `${relativePath}/${item.name}` : item.name;

        if (item.isDirectory()) {
          // Check if folder exists in DB
          const existingFolder = await storage.getFileByPath(repositoryId, itemRelativePath);
          if (!existingFolder) {
            await storage.createFile(repositoryId, {
              name: item.name,
              path: relativePath,
              content: "",
              size: 0,
              isDirectory: true,
            });
          }
          // Recursively scan subdirectories
          await scanDirectory(itemPath, itemRelativePath);
        } else {
          // Check if file exists in DB
          const existingFile = await storage.getFileByPath(repositoryId, itemRelativePath);
          const content = fs.readFileSync(itemPath, "utf-8");
          const size = Buffer.byteLength(content, "utf-8");

          if (existingFile) {
            // Update if content changed
            if (existingFile.content !== content) {
              await storage.updateFile(existingFile.id, repositoryId, { content, size });
            }
          } else {
            // Create new file
            await storage.createFile(repositoryId, {
              name: item.name,
              path: relativePath,
              content,
              size,
              isDirectory: false,
            });
          }
        }
      }
    };

    await scanDirectory(workDir);
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

      const pipInstall = spawn("python3", ["-m", "pip", "install", "--user", "--break-system-packages", packageName], {
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

      // Use --break-system-packages for Render/externally-managed environments
      const pipUninstall = spawn("python3", ["-m", "pip", "uninstall", "-y", "--break-system-packages", packageName], {
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
