import type { Express } from "express";
import { createServer, type Server } from "http";
import { WebSocketServer, WebSocket } from "ws";
import { storage } from "./storage";
import { isAuthenticated, hashPassword, verifyPassword } from "./auth";
import { pythonProcessManager } from "./pythonProcessManager";
import session from "express-session";
import connectPg from "connect-pg-simple";
import AdmZip from "adm-zip";
import {
  insertRepositorySchema,
  insertFileSchema,
} from "@shared/schema";
import {
  registerSchema,
  loginSchema,
} from "@shared/authSchema";

import { eq } from "drizzle-orm";
import { db } from "./db";
import { users } from "@shared/schema";
import bcrypt from "bcrypt";


function getSession() {
  const sessionTtl = 7 * 24 * 60 * 60 * 1000;
  const pgStore = connectPg(session);
  const sessionStore = new pgStore({
    conString: process.env.DATABASE_URL,
    createTableIfMissing: false,
    ttl: sessionTtl,
    tableName: "sessions",
  });
  return session({
    secret: process.env.SESSION_SECRET || "your-secret-key-change-in-production",
    store: sessionStore,
    resave: false,
    saveUninitialized: false,
    cookie: {
      httpOnly: true,
      secure: process.env.NODE_ENV === "production",
      maxAge: sessionTtl,
    },
  });
}

export async function registerRoutes(app: Express): Promise<Server> {
  app.set("trust proxy", 1);
  app.use(getSession());

  app.post("/api/auth/register", async (req, res) => {
    try {
      const data = registerSchema.parse(req.body);

      const existingUsername = await storage.getUserByUsername(data.username);
      if (existingUsername) {
        return res.status(400).json({ message: "Username already taken" });
      }

      const existingEmail = await storage.getUserByEmail(data.email);
      if (existingEmail) {
        return res.status(400).json({ message: "Email already registered" });
      }

      const hashedPassword = await hashPassword(data.password);
      // Automatically assign admin role to abojafar1327@gmail.com
      const isAdmin = data.email === "abojafar1327@gmail.com";
      const user = await storage.createUser(
        data.username,
        data.email,
        hashedPassword,
        isAdmin
      );

      req.session.userId = user.id;
      res.json({ id: user.id, username: user.username, email: user.email, isAdmin: user.isAdmin });
    } catch (error: any) {
      console.error("Registration error:", error);
      res.status(400).json({ message: error.message || "Registration failed" });
    }
  });

  app.post("/api/auth/login", async (req, res) => {
    try {
      const data = loginSchema.parse(req.body);

      let user = await storage.getUserByUsernameOrEmail(data.usernameOrEmail);
      if (!user) {
        return res.status(401).json({ message: "Invalid username/email or password" });
      }

      const isValid = await verifyPassword(data.password, user.password);
      if (!isValid) {
        return res.status(401).json({ message: "Invalid username/email or password" });
      }

      // Update admin status if this is the admin email and not already admin
      if (data.usernameOrEmail === "abojafar1327@gmail.com" && !user.isAdmin) {
        const updatedUser = await storage.updateUserAdminStatus(user.id, true);
        if (updatedUser) {
          user = updatedUser;
        }
      }

      req.session.userId = user.id;
      res.json({ id: user.id, username: user.username, email: user.email, isAdmin: user.isAdmin });
    } catch (error: any) {
      console.error("Login error:", error);
      res.status(400).json({ message: error.message || "Login failed" });
    }
  });

  app.post("/api/auth/logout", (req, res) => {
    req.session.destroy(() => {
      res.json({ message: "Logged out successfully" });
    });
  });

  app.get("/api/auth/user", isAuthenticated, async (req: any, res) => {
    try {
      const user = await storage.getUser(req.session.userId);
      if (!user) {
        return res.status(404).json({ message: "User not found" });
      }
      res.json(user);
    } catch (error) {
      console.error("Error fetching user:", error);
      res.status(500).json({ message: "Failed to fetch user" });
    }
  });

  app.get("/api/repositories", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.session.userId;
      const repos = await storage.getRepositories(userId);
      res.json(repos);
    } catch (error) {
      console.error("Error fetching repositories:", error);
      res.status(500).json({ message: "Failed to fetch repositories" });
    }
  });

  app.get("/api/repositories/:id", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.session.userId;
      const repo = await storage.getRepository(req.params.id, userId);

      if (!repo) {
        return res.status(404).json({ message: "Repository not found" });
      }

      // تزامن الحالة مع الحالة الفعلية للعملية
      const isActuallyRunning = pythonProcessManager.isRunning(req.params.id);
      if (repo.status === "running" && !isActuallyRunning) {
        // إذا كانت قاعدة البيانات تقول running لكن العملية غير موجودة
        await storage.updateRepositoryById(req.params.id, { status: "stopped" });
        repo.status = "stopped";
      } else if (repo.status === "stopped" && isActuallyRunning) {
        // إذا كانت قاعدة البيانات تقول stopped لكن العملية موجودة
        await storage.updateRepositoryById(req.params.id, { status: "running" });
        repo.status = "running";
      }

      res.json(repo);
    } catch (error) {
      console.error("Error fetching repository:", error);
      res.status(500).json({ message: "Failed to fetch repository" });
    }
  });

  app.post("/api/repositories", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.session.userId;
      const data = insertRepositorySchema.parse(req.body);
      const repo = await storage.createRepository(userId, data);
      res.json(repo);
    } catch (error: any) {
      console.error("Error creating repository:", error);
      res.status(400).json({ message: error.message || "Failed to create repository" });
    }
  });

  app.patch("/api/repositories/:id", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.session.userId;
      const repo = await storage.updateRepository(req.params.id, userId, req.body);

      if (!repo) {
        return res.status(404).json({ message: "Repository not found" });
      }

      res.json(repo);
    } catch (error: any) {
      console.error("Error updating repository:", error);
      res.status(400).json({ message: error.message || "Failed to update repository" });
    }
  });

  app.delete("/api/repositories/:id", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.session.userId;

      if (pythonProcessManager.isRunning(req.params.id)) {
        pythonProcessManager.stopRepository(req.params.id);
      }

      const deleted = await storage.deleteRepository(req.params.id, userId);

      if (!deleted) {
        return res.status(404).json({ message: "Repository not found" });
      }

      res.json({ message: "Repository deleted successfully" });
    } catch (error: any) {
      console.error("Error deleting repository:", error);
      res.status(500).json({ message: error.message || "Failed to delete repository" });
    }
  });

  app.post("/api/repositories/:id/start", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.session.userId;
      const repo = await storage.getRepository(req.params.id, userId);

      if (!repo) {
        return res.status(404).json({ message: "Repository not found" });
      }

      await pythonProcessManager.startRepository(req.params.id);
      res.json({ message: "Repository started successfully" });
    } catch (error: any) {
      console.error("Error starting repository:", error);
      res.status(400).json({ message: error.message || "Failed to start repository" });
    }
  });

  app.post("/api/repositories/:id/stop", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.session.userId;
      const repo = await storage.getRepository(req.params.id, userId);

      if (!repo) {
        return res.status(404).json({ message: "Repository not found" });
      }

      // إذا كانت العملية تعمل فعلياً، أوقفها
      if (pythonProcessManager.isRunning(req.params.id)) {
        pythonProcessManager.stopRepository(req.params.id);
      } else {
        // إذا لم تكن العملية تعمل، فقط حدّث الحالة في قاعدة البيانات
        await storage.updateRepositoryById(req.params.id, { status: "stopped" });
      }

      res.json({ message: "Repository stopped successfully" });
    } catch (error: any) {
      console.error("Error stopping repository:", error);
      res.status(400).json({ message: error.message || "Failed to stop repository" });
    }
  });

  app.post("/api/repositories/:id/execute-command", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.session.userId;
      const repo = await storage.getRepository(req.params.id, userId);

      if (!repo) {
        return res.status(404).json({ message: "Repository not found" });
      }

      if (pythonProcessManager.isRunning(req.params.id)) {
        return res.status(400).json({ message: "Cannot execute commands while repository is running. Please stop it first." });
      }

      const { command } = req.body;
      if (!command) {
        return res.status(400).json({ message: "Command is required" });
      }

      const output = await pythonProcessManager.executeCommand(req.params.id, command);
      res.json({ success: true, output });
    } catch (error: any) {
      console.error("Error executing command:", error);
      res.status(400).json({ message: error.message || "Failed to execute command" });
    }
  });

  app.post("/api/repositories/:id/install-package", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.session.userId;
      const repo = await storage.getRepository(req.params.id, userId);

      if (!repo) {
        return res.status(404).json({ message: "Repository not found" });
      }

      if (pythonProcessManager.isRunning(req.params.id)) {
        return res.status(400).json({ message: "Cannot install packages while repository is running. Please stop it first." });
      }

      const { packageName } = req.body;
      if (!packageName) {
        return res.status(400).json({ message: "Package name is required" });
      }

      const output = await pythonProcessManager.installPackage(req.params.id, packageName);
      res.json({ message: "Package installed successfully", output });
    } catch (error: any) {
      console.error("Error installing package:", error);
      res.status(400).json({ message: error.message || "Failed to install package" });
    }
  });

  app.post("/api/repositories/:id/uninstall-package", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.session.userId;
      const repo = await storage.getRepository(req.params.id, userId);

      if (!repo) {
        return res.status(404).json({ message: "Repository not found" });
      }

      if (pythonProcessManager.isRunning(req.params.id)) {
        return res.status(400).json({ message: "Cannot uninstall packages while repository is running. Please stop it first." });
      }

      const { packageName } = req.body;
      if (!packageName) {
        return res.status(400).json({ message: "Package name is required" });
      }

      const output = await pythonProcessManager.uninstallPackage(req.params.id, packageName);
      res.json({ message: "Package uninstalled successfully", output });
    } catch (error: any) {
      console.error("Error uninstalling package:", error);
      res.status(400).json({ message: error.message || "Failed to uninstall package" });
    }
  });

  app.get("/api/repositories/:id/files", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.session.userId;
      const repo = await storage.getRepository(req.params.id, userId);

      if (!repo) {
        return res.status(404).json({ message: "Repository not found" });
      }

      const files = await storage.getFiles(req.params.id);
      res.json(files);
    } catch (error) {
      console.error("Error fetching files:", error);
      res.status(500).json({ message: "Failed to fetch files" });
    }
  });

  app.post("/api/repositories/:id/files", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.session.userId;
      const repo = await storage.getRepository(req.params.id, userId);

      if (!repo) {
        return res.status(404).json({ message: "Repository not found" });
      }

      const data = insertFileSchema.parse(req.body);
      const file = await storage.createFile(req.params.id, data);
      res.json(file);
    } catch (error: any) {
      console.error("Error creating file:", error);
      res.status(400).json({ message: error.message || "Failed to create file" });
    }
  });

  app.post("/api/repositories/:id/folders", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.session.userId;
      const repo = await storage.getRepository(req.params.id, userId);

      if (!repo) {
        return res.status(404).json({ message: "Repository not found" });
      }

      const { name, path } = req.body;
      const folder = await storage.createFile(req.params.id, {
        name,
        path: path || "",
        content: "",
        size: 0,
        isDirectory: true,
      });
      res.json(folder);
    } catch (error: any) {
      console.error("Error creating folder:", error);
      res.status(400).json({ message: error.message || "Failed to create folder" });
    }
  });

  app.post("/api/repositories/:id/upload-zip", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.session.userId;
      const repo = await storage.getRepository(req.params.id, userId);

      if (!repo) {
        return res.status(404).json({ message: "Repository not found" });
      }

      const { zipContent, targetPath } = req.body;
      const zip = new AdmZip(Buffer.from(zipContent, 'base64'));
      const zipEntries = zip.getEntries();

      const createdFiles = [];

      for (const entry of zipEntries) {
        const fullPath = targetPath ? `${targetPath}/${entry.entryName}` : entry.entryName;
        const pathParts = fullPath.split('/');
        const fileName = pathParts.pop() || '';
        const filePath = pathParts.join('/');

        if (entry.isDirectory) {
          const folder = await storage.createFile(req.params.id, {
            name: fileName,
            path: filePath,
            content: "",
            size: 0,
            isDirectory: true,
          });
          createdFiles.push(folder);
        } else {
          const content = entry.getData().toString('utf8');
          const file = await storage.createFile(req.params.id, {
            name: fileName,
            path: filePath,
            content,
            size: content.length,
            isDirectory: false,
          });
          createdFiles.push(file);
        }
      }

      res.json({ message: "ZIP file extracted successfully", files: createdFiles });
    } catch (error: any) {
      console.error("Error uploading ZIP:", error);
      res.status(400).json({ message: error.message || "Failed to upload ZIP file" });
    }
  });

  app.patch("/api/repositories/:repositoryId/files/:fileId", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.session.userId;
      const repo = await storage.getRepository(req.params.repositoryId, userId);

      if (!repo) {
        return res.status(404).json({ message: "Repository not found" });
      }

      const { content } = req.body;
      const size = new Blob([content]).size;

      const updated = await storage.updateFile(req.params.fileId, req.params.repositoryId, {
        content,
        size,
      });

      if (!updated) {
        return res.status(404).json({ message: "File not found" });
      }

      res.json(updated);
    } catch (error: any) {
      console.error("Error updating file:", error);
      res.status(500).json({ message: error.message || "Failed to update file" });
    }
  });

  app.delete("/api/repositories/:repositoryId/files/:fileId", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.session.userId;
      const repo = await storage.getRepository(req.params.repositoryId, userId);

      if (!repo) {
        return res.status(404).json({ message: "Repository not found" });
      }

      const deleted = await storage.deleteFile(req.params.fileId, req.params.repositoryId);

      if (!deleted) {
        return res.status(404).json({ message: "File not found" });
      }

      res.json({ message: "File deleted successfully" });
    } catch (error: any) {
      console.error("Error deleting file:", error);
      res.status(500).json({ message: error.message || "Failed to delete file" });
    }
  });

  app.get("/api/repositories/:id/env", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.session.userId;
      const repo = await storage.getRepository(req.params.id, userId);

      if (!repo) {
        return res.status(404).json({ message: "Repository not found" });
      }

      const envVars = await storage.getEnvironmentVariables(req.params.id);
      res.json(envVars);
    } catch (error) {
      console.error("Error fetching environment variables:", error);
      res.status(500).json({ message: "Failed to fetch environment variables" });
    }
  });

  app.post("/api/repositories/:id/env", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.session.userId;
      const repo = await storage.getRepository(req.params.id, userId);

      if (!repo) {
        return res.status(404).json({ message: "Repository not found" });
      }

      const { variables } = req.body;

      if (!Array.isArray(variables)) {
        return res.status(400).json({ message: "Variables must be an array" });
      }

      await storage.setEnvironmentVariables(req.params.id, variables);
      res.json({ message: "Environment variables updated successfully" });
    } catch (error: any) {
      console.error("Error updating environment variables:", error);
      res.status(400).json({ message: error.message || "Failed to update environment variables" });
    }
  });

  const httpServer = createServer(app);

  const wss = new WebSocketServer({ server: httpServer, path: "/ws" });

  wss.on("connection", (ws: WebSocket) => {
    let subscribedRepositoryId: string | null = null;
    let logCallback: ((message: string) => void) | null = null;

    ws.on("message", (data: string) => {
      try {
        const message = JSON.parse(data.toString());

        if (message.type === "subscribe" && message.repositoryId) {
          if (subscribedRepositoryId && logCallback) {
            pythonProcessManager.unsubscribeFromLogs(subscribedRepositoryId, logCallback);
          }

          subscribedRepositoryId = message.repositoryId as string;
          logCallback = (logMessage: string) => {
            if (ws.readyState === WebSocket.OPEN) {
              ws.send(
                JSON.stringify({
                  type: "log",
                  repositoryId: subscribedRepositoryId,
                  message: logMessage,
                })
              );
            }
          };

          pythonProcessManager.subscribeToLogs(subscribedRepositoryId as string, logCallback);
        }
      } catch (error) {
        console.error("Error processing WebSocket message:", error);
      }
    });

    ws.on("close", () => {
      if (subscribedRepositoryId && logCallback) {
        pythonProcessManager.unsubscribeFromLogs(subscribedRepositoryId, logCallback);
      }
    });
  });

  return httpServer;
}