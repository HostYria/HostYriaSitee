import express, { type Express } from "express";
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
import multer from "multer";
import path from "path";
import fs from "fs";

const uploadDir = path.join(process.cwd(), "attached_assets", "uploads");
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

const upload = multer({ dest: uploadDir });


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

  app.get("/health", (_req, res) => {
    res.status(200).json({ status: "ok", timestamp: new Date().toISOString() });
  });

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

      // Sync runtime files to database after stopping
      await pythonProcessManager.syncRuntimeFilesToDatabase(req.params.id);

      res.json({ message: "Repository stopped successfully" });
    } catch (error: any) {
      console.error("Error stopping repository:", error);
      res.status(400).json({ message: error.message || "Failed to stop repository" });
    }
  });

  app.post("/api/repositories/:id/sync-files", isAuthenticated, async (req: any, res) => {
    try {
      const userId = req.session.userId;
      const repo = await storage.getRepository(req.params.id, userId);

      if (!repo) {
        return res.status(404).json({ message: "Repository not found" });
      }

      await pythonProcessManager.syncRuntimeFilesToDatabase(req.params.id);
      res.json({ message: "Files synced successfully" });
    } catch (error: any) {
      console.error("Error syncing files:", error);
      res.status(400).json({ message: error.message || "Failed to sync files" });
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
      
      // Start file watcher if not already running
      const workDir = path.join(process.cwd(), "runtime", req.params.id);
      if (!fs.existsSync(workDir)) {
        fs.mkdirSync(workDir, { recursive: true });
      }
      pythonProcessManager.startFileWatcher(req.params.id, workDir);
      
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
      const createdFolders = new Set<string>();

      // First pass: create all directories
      for (const entry of zipEntries) {
        if (entry.isDirectory) {
          const fullPath = targetPath ? `${targetPath}/${entry.entryName}` : entry.entryName;
          const cleanPath = fullPath.replace(/\/$/, ''); // إزالة / النهائية
          const pathParts = cleanPath.split('/').filter(p => p);
          
          // إنشاء المجلدات الفرعية تدريجياً
          for (let i = 0; i < pathParts.length; i++) {
            const currentPath = pathParts.slice(0, i).join('/');
            const folderName = pathParts[i];
            const folderFullPath = currentPath ? `${currentPath}/${folderName}` : folderName;
            
            if (!createdFolders.has(folderFullPath)) {
              const existing = await storage.getFileByPath(req.params.id, folderFullPath);
              if (!existing) {
                const folder = await storage.createFile(req.params.id, {
                  name: folderName,
                  path: currentPath,
                  content: "",
                  size: 0,
                  isDirectory: true,
                });
                createdFiles.push(folder);
              }
              createdFolders.add(folderFullPath);
            }
          }
        }
      }

      // Second pass: create all files
      for (const entry of zipEntries) {
        if (!entry.isDirectory) {
          const fullPath = targetPath ? `${targetPath}/${entry.entryName}` : entry.entryName;
          const pathParts = fullPath.split('/').filter(p => p);
          const fileName = pathParts.pop() || '';
          const filePath = pathParts.join('/');

          // إنشاء المجلدات الأب إذا لم تكن موجودة
          if (filePath && !createdFolders.has(filePath)) {
            const folderParts = filePath.split('/');
            for (let i = 0; i < folderParts.length; i++) {
              const currentPath = folderParts.slice(0, i).join('/');
              const folderName = folderParts[i];
              const folderFullPath = currentPath ? `${currentPath}/${folderName}` : folderName;
              
              if (!createdFolders.has(folderFullPath)) {
                const existing = await storage.getFileByPath(req.params.id, folderFullPath);
                if (!existing) {
                  await storage.createFile(req.params.id, {
                    name: folderName,
                    path: currentPath,
                    content: "",
                    size: 0,
                    isDirectory: true,
                  });
                }
                createdFolders.add(folderFullPath);
              }
            }
          }

          const content = entry.getData().toString('utf8');
          const existing = await storage.getFileByPath(req.params.id, fullPath);
          
          if (existing) {
            await storage.updateFile(existing.id, req.params.id, { content, size: content.length });
          } else {
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

  app.get("/api/admin/users", isAuthenticated, async (req: any, res) => {
    try {
      const user = await storage.getUser(req.session.userId);
      if (!user?.isAdmin) {
        return res.status(403).json({ message: "Unauthorized" });
      }

      const allUsers = await storage.getAllUsers();
      res.json(allUsers);
    } catch (error) {
      console.error("Error fetching users:", error);
      res.status(500).json({ message: "Failed to fetch users" });
    }
  });

  app.get("/api/admin/users/:userId/repositories", isAuthenticated, async (req: any, res) => {
    try {
      const user = await storage.getUser(req.session.userId);
      if (!user?.isAdmin) {
        return res.status(403).json({ message: "Unauthorized" });
      }

      const repos = await storage.getRepositories(req.params.userId);
      res.json(repos);
    } catch (error) {
      console.error("Error fetching user repositories:", error);
      res.status(500).json({ message: "Failed to fetch repositories" });
    }
  });

  app.post("/api/admin/change-user-password", isAuthenticated, async (req: any, res) => {
    try {
      const user = await storage.getUser(req.session.userId);
      if (!user?.isAdmin) {
        return res.status(403).json({ message: "Unauthorized" });
      }

      const { userId, newPassword } = req.body;
      if (!userId || !newPassword) {
        return res.status(400).json({ message: "User ID and new password are required" });
      }

      const hashedPassword = await hashPassword(newPassword);
      const updated = await storage.updateUserPassword(userId, hashedPassword);

      if (!updated) {
        return res.status(404).json({ message: "User not found" });
      }

      res.json({ message: "Password updated successfully" });
    } catch (error: any) {
      console.error("Error changing password:", error);
      res.status(500).json({ message: error.message || "Failed to change password" });
    }
  });

  app.get("/api/payment-methods", async (_req, res) => {
    try {
      const methods = await storage.getPaymentMethods();
      res.json(methods);
    } catch (error) {
      console.error("Error fetching payment methods:", error);
      res.status(500).json({ message: "Failed to fetch payment methods" });
    }
  });

  app.post("/api/payment-methods", isAuthenticated, async (req: any, res) => {
    try {
      const user = await storage.getUser(req.session.userId);
      if (!user?.isAdmin) {
        return res.status(403).json({ message: "Unauthorized" });
      }

      const method = await storage.createPaymentMethod(req.body);
      res.json(method);
    } catch (error: any) {
      console.error("Error creating payment method:", error);
      res.status(400).json({ message: error.message || "Failed to create payment method" });
    }
  });

  app.patch("/api/payment-methods/:id", isAuthenticated, async (req: any, res) => {
    try {
      const user = await storage.getUser(req.session.userId);
      if (!user?.isAdmin) {
        return res.status(403).json({ message: "Unauthorized" });
      }

      const method = await storage.updatePaymentMethod(req.params.id, req.body);
      if (!method) {
        return res.status(404).json({ message: "Payment method not found" });
      }
      res.json(method);
    } catch (error: any) {
      console.error("Error updating payment method:", error);
      res.status(400).json({ message: error.message || "Failed to update payment method" });
    }
  });

  app.delete("/api/payment-methods/:id", isAuthenticated, async (req: any, res) => {
    try {
      const user = await storage.getUser(req.session.userId);
      if (!user?.isAdmin) {
        return res.status(403).json({ message: "Unauthorized" });
      }

      const deleted = await storage.deletePaymentMethod(req.params.id);
      if (!deleted) {
        return res.status(404).json({ message: "Payment method not found" });
      }
      res.json({ message: "Payment method deleted successfully" });
    } catch (error: any) {
      console.error("Error deleting payment method:", error);
      res.status(500).json({ message: error.message || "Failed to delete payment method" });
    }
  });

  app.get("/api/balance-requests", isAuthenticated, async (req: any, res) => {
    try {
      const user = await storage.getUser(req.session.userId);
      if (!user) {
        return res.status(404).json({ message: "User not found" });
      }

      const requests = user.isAdmin
        ? await storage.getBalanceRequests()
        : await storage.getUserBalanceRequests(req.session.userId);

      // Replace "Unknown" with actual user data
      const enrichedRequests = await Promise.all(requests.map(async (req) => {
        const user = await storage.getUser(req.userId);
        return {
          ...req,
          user: user ? { id: user.id, username: user.username, email: user.email } : { id: null, username: "Unknown", email: "Unknown" },
        };
      }));

      res.json(enrichedRequests);
    } catch (error) {
      console.error("Error fetching balance requests:", error);
      res.status(500).json({ message: "Failed to fetch balance requests" });
    }
  });

  app.post("/api/balance-requests", isAuthenticated, upload.single("screenshot"), async (req: any, res) => {
    try {
      if (!req.file) {
        return res.status(400).json({ message: "Screenshot is required" });
      }

      const screenshotUrl = `/uploads/${req.file.filename}`;
      const balanceRequest = await storage.createBalanceRequest({
        userId: req.session.userId,
        paymentMethodId: req.body.paymentMethodId,
        amountSent: req.body.amountSent.toString(),
        transactionId: req.body.transactionId,
        screenshotUrl,
      });

      res.json(balanceRequest);
    } catch (error: any) {
      console.error("Error creating balance request:", error);
      res.status(400).json({ message: error.message || "Failed to create balance request" });
    }
  });

  app.patch("/api/balance-requests/:id/status", isAuthenticated, async (req: any, res) => {
    try {
      const user = await storage.getUser(req.session.userId);
      if (!user?.isAdmin) {
        return res.status(403).json({ message: "Unauthorized" });
      }

      const { status } = req.body;
      if (!["approved", "rejected"].includes(status)) {
        return res.status(400).json({ message: "Invalid status" });
      }

      const updatedRequest = await storage.updateBalanceRequestStatus(
        req.params.id,
        req.body.status
      );

      // Create notification for user
      if (updatedRequest) {
        const isApproved = req.body.status === 'approved';
        await storage.createNotification({
          userId: updatedRequest.userId,
          title: isApproved ? '✅ تمت الموافقة على طلب الإيداع' : '❌ تم رفض طلب الإيداع',
          message: isApproved
            ? `تمت الموافقة على طلب إيداع بقيمة ${updatedRequest.amountSent} وتم إضافة المبلغ إلى رصيدك.`
            : `تم رفض طلب الإيداع الخاص بك. يرجى التواصل مع الدعم للمزيد من التفاصيل.`,
          type: isApproved ? 'balance_approved' : 'balance_rejected',
          relatedId: updatedRequest.id,
        });
      }

      res.json(updatedRequest);
    } catch (error: any) {
      console.error("Error updating balance request status:", error);
      res.status(400).json({ message: error.message || "Failed to update balance request status" });
    }
  });

  // Admin support endpoints
  app.get("/api/admin/support/messages", isAuthenticated, async (req: any, res) => {
    try {
      const user = await storage.getUser(req.session.userId);
      if (!user?.isAdmin) {
        return res.status(403).json({ message: "Unauthorized" });
      }

      const messages = await storage.getAllSupportMessages();
      res.json(messages);
    } catch (error) {
      console.error("Error fetching all support messages:", error);
      res.status(500).json({ message: "Failed to fetch messages" });
    }
  });

  app.post("/api/admin/support/messages/:userId/reply", isAuthenticated, async (req: any, res) => {
    try {
      const user = await storage.getUser(req.session.userId);
      if (!user?.isAdmin) {
        return res.status(403).json({ message: "Unauthorized" });
      }

      const { message } = req.body;
      if (!message) {
        return res.status(400).json({ message: "Message is required" });
      }

      const supportMessage = await storage.createSupportMessage({
        userId: req.params.userId,
        message,
        isFromUser: false,
      });

      // Create notification for user
      await storage.createNotification({
        userId: req.params.userId,
        title: '💬 رد من الدعم الفني',
        message: 'لديك رد جديد من فريق الدعم الفني',
        type: 'support_message',
        relatedId: supportMessage.id,
      });

      res.json(supportMessage);
    } catch (error: any) {
      console.error("Error sending support reply:", error);
      res.status(500).json({ message: error.message || "Failed to send reply" });
    }
  });

  // Notes routes
  app.get("/api/notes", isAuthenticated, async (req: any, res) => {
    try {
      const notes = await storage.getNotes(req.session.userId);
      res.json(notes);
    } catch (error) {
      console.error("Error fetching notes:", error);
      res.status(500).json({ message: "Failed to fetch notes" });
    }
  });

  app.get("/api/notes/:id", isAuthenticated, async (req: any, res) => {
    try {
      const note = await storage.getNote(req.params.id, req.session.userId);
      if (!note) {
        return res.status(404).json({ message: "Note not found" });
      }
      res.json(note);
    } catch (error) {
      console.error("Error fetching note:", error);
      res.status(500).json({ message: "Failed to fetch note" });
    }
  });

  app.post("/api/notes", isAuthenticated, async (req: any, res) => {
    try {
      const { insertNoteSchema } = await import("@shared/schema");
      const validatedData = insertNoteSchema.parse(req.body);

      const note = await storage.createNote(req.session.userId, validatedData);
      res.status(201).json(note);
    } catch (error: any) {
      if (error.name === 'ZodError') {
        return res.status(400).json({ message: "Invalid input data", errors: error.errors });
      }
      console.error("Error creating note:", error);
      res.status(500).json({ message: "Failed to create note" });
    }
  });

  app.patch("/api/notes/:id", isAuthenticated, async (req: any, res) => {
    try {
      const { insertNoteSchema } = await import("@shared/schema");
      const validatedData = insertNoteSchema.partial().parse(req.body);

      const note = await storage.updateNote(req.params.id, req.session.userId, validatedData);
      if (!note) {
        return res.status(404).json({ message: "Note not found" });
      }
      res.json(note);
    } catch (error: any) {
      if (error.name === 'ZodError') {
        return res.status(400).json({ message: "Invalid input data", errors: error.errors });
      }
      console.error("Error updating note:", error);
      res.status(500).json({ message: "Failed to update note" });
    }
  });

  app.delete("/api/notes/:id", isAuthenticated, async (req: any, res) => {
    try {
      const deleted = await storage.deleteNote(req.params.id, req.session.userId);
      if (!deleted) {
        return res.status(404).json({ message: "Note not found" });
      }
      res.json({ message: "Note deleted successfully" });
    } catch (error) {
      console.error("Error deleting note:", error);
      res.status(500).json({ message: "Failed to delete note" });
    }
  });

  app.use("/uploads", (req, res, next) => {
    res.setHeader("Cross-Origin-Resource-Policy", "cross-origin");
    // Set content-type to display images in browser instead of downloading
    const ext = req.path.split('.').pop()?.toLowerCase();
    if (ext === 'jpg' || ext === 'jpeg') {
      res.setHeader("Content-Type", "image/jpeg");
    } else if (ext === 'png') {
      res.setHeader("Content-Type", "image/png");
    } else if (ext === 'gif') {
      res.setHeader("Content-Type", "image/gif");
    } else if (ext === 'webp') {
      res.setHeader("Content-Type", "image/webp");
    } else {
      // For files without extension, try to detect from content
      res.setHeader("Content-Type", "image/jpeg");
    }
    res.setHeader("Content-Disposition", "inline");
    next();
  });
  app.use("/uploads", express.static(uploadDir));

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