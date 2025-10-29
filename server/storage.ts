import {
  users,
  repositories,
  files,
  environmentVariables,
  paymentMethods,
  balanceRequests,
  supportMessages,
  notifications,
  type User,
  type InsertUser,
  type Repository,
  type InsertRepository,
  type File,
  type InsertFile,
  type EnvironmentVariable,
  type InsertEnvironmentVariable,
  type PaymentMethod,
  type InsertPaymentMethod,
  type BalanceRequest,
  type InsertBalanceRequest,
  type SupportMessage,
  type InsertSupportMessage,
  type Notification,
  type InsertNotification,
} from "@shared/schema";
import { db } from "./db";
import { eq, and, sql } from "drizzle-orm";

export interface IStorage {
  getUser(id: string): Promise<User | undefined>;
  upsertUser(user: InsertUser): Promise<User>;

  getRepositories(userId: string): Promise<Repository[]>;
  getRepository(id: string, userId: string): Promise<Repository | undefined>;
  getRepositoryById(id: string): Promise<Repository | undefined>;
  createRepository(userId: string, repo: InsertRepository): Promise<Repository>;
  updateRepository(id: string, userId: string, repo: Partial<Omit<Repository, 'id' | 'userId' | 'createdAt' | 'updatedAt'>>): Promise<Repository | undefined>;
  updateRepositoryById(id: string, repo: Partial<Omit<Repository, 'id' | 'userId' | 'createdAt' | 'updatedAt'>>): Promise<Repository | undefined>;
  deleteRepository(id: string, userId: string): Promise<boolean>;

  getFiles(repositoryId: string): Promise<File[]>;
  getFile(id: string, repositoryId: string): Promise<File | undefined>;
  createFile(repositoryId: string, file: InsertFile): Promise<File>;
  updateFile(fileId: string, repositoryId: string, updates: { content?: string; size?: number }): Promise<File | null>;
  deleteFile(fileId: string, repositoryId: string): Promise<boolean>;

  getEnvironmentVariables(repositoryId: string): Promise<EnvironmentVariable[]>;
  setEnvironmentVariables(repositoryId: string, vars: Array<{ key: string; value: string }>): Promise<void>;

  getPaymentMethods(): Promise<PaymentMethod[]>;
  getPaymentMethod(id: string): Promise<PaymentMethod | undefined>;
  createPaymentMethod(data: InsertPaymentMethod): Promise<PaymentMethod>;
  updatePaymentMethod(id: string, data: Partial<Omit<PaymentMethod, 'id' | 'createdAt'>>): Promise<PaymentMethod | undefined>;
  deletePaymentMethod(id: string): Promise<boolean>;

  getBalanceRequests(): Promise<BalanceRequest[]>;
  getBalanceRequest(id: string): Promise<BalanceRequest | undefined>;
  getUserBalanceRequests(userId: string): Promise<BalanceRequest[]>;
  createBalanceRequest(data: Omit<InsertBalanceRequest, 'id' | 'createdAt' | 'status'>): Promise<BalanceRequest>;
  updateBalanceRequestStatus(id: string, status: string, adminNotes?: string): Promise<BalanceRequest | undefined>;
  updateUserBalance(userId: string, amount: number): Promise<User | undefined>;

  // Notifications
  createNotification(notification: InsertNotification): Promise<Notification>;
  getNotifications(userId: string): Promise<Notification[]>;
  getUnreadNotificationsCount(userId: string): Promise<number>;
  markNotificationAsRead(id: string): Promise<Notification | undefined>;

  // Support Messages
  createSupportMessage(data: InsertSupportMessage): Promise<SupportMessage>;
  getAllSupportMessages(): Promise<SupportMessage[]>;
}

export class DatabaseStorage implements IStorage {
  async getUser(id: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.id, id));
    return user;
  }

  async upsertUser(userData: InsertUser): Promise<User> {
    const [user] = await db
      .insert(users)
      .values(userData)
      .onConflictDoUpdate({
        target: users.id,
        set: {
          ...userData,
          updatedAt: new Date(),
        },
      })
      .returning();
    return user;
  }

  async getRepositories(userId: string): Promise<Repository[]> {
    return await db
      .select()
      .from(repositories)
      .where(eq(repositories.userId, userId))
      .orderBy(repositories.createdAt);
  }

  async getRepository(id: string, userId: string): Promise<Repository | undefined> {
    const [repo] = await db
      .select()
      .from(repositories)
      .where(and(eq(repositories.id, id), eq(repositories.userId, userId)));
    return repo;
  }

  async getRepositoryById(id: string): Promise<Repository | undefined> {
    const [repo] = await db
      .select()
      .from(repositories)
      .where(eq(repositories.id, id));
    return repo;
  }

  async createRepository(userId: string, repo: InsertRepository): Promise<Repository> {
    const [created] = await db
      .insert(repositories)
      .values({ ...repo, userId })
      .returning();
    return created;
  }

  async updateRepository(
    id: string,
    userId: string,
    repo: Partial<Omit<Repository, 'id' | 'userId' | 'createdAt' | 'updatedAt'>>
  ): Promise<Repository | undefined> {
    const [updated] = await db
      .update(repositories)
      .set({ ...repo, updatedAt: new Date() })
      .where(and(eq(repositories.id, id), eq(repositories.userId, userId)))
      .returning();
    return updated;
  }

  async updateRepositoryById(
    id: string,
    repo: Partial<Omit<Repository, 'id' | 'userId' | 'createdAt' | 'updatedAt'>>
  ): Promise<Repository | undefined> {
    const [updated] = await db
      .update(repositories)
      .set({ ...repo, updatedAt: new Date() })
      .where(eq(repositories.id, id))
      .returning();
    return updated;
  }

  async deleteRepository(id: string, userId: string): Promise<boolean> {
    const result = await db
      .delete(repositories)
      .where(and(eq(repositories.id, id), eq(repositories.userId, userId)));
    return result.rowCount !== null && result.rowCount > 0;
  }

  async getFiles(repositoryId: string): Promise<File[]> {
    return await db
      .select()
      .from(files)
      .where(eq(files.repositoryId, repositoryId))
      .orderBy(files.name);
  }

  async getFile(id: string, repositoryId: string): Promise<File | undefined> {
    const [file] = await db
      .select()
      .from(files)
      .where(and(eq(files.id, id), eq(files.repositoryId, repositoryId)));
    return file;
  }

  async createFile(repositoryId: string, file: InsertFile): Promise<File> {
    const [created] = await db
      .insert(files)
      .values({ ...file, repositoryId })
      .returning();
    return created;
  }

  async updateFile(
    fileId: string,
    repositoryId: string,
    updates: { content?: string; size?: number }
  ): Promise<File | null> {
    const result = await db
      .update(files)
      .set({
        ...updates,
        updatedAt: new Date(),
      })
      .where(and(eq(files.id, fileId), eq(files.repositoryId, repositoryId)))
      .returning();
    return result[0] || null;
  }

  async deleteFile(fileId: string, repositoryId: string): Promise<boolean> {
    const result = await db
      .delete(files)
      .where(and(eq(files.id, fileId), eq(files.repositoryId, repositoryId)))
      .returning();
    return result.length > 0;
  }

  async getEnvironmentVariables(repositoryId: string): Promise<EnvironmentVariable[]> {
    return await db
      .select()
      .from(environmentVariables)
      .where(eq(environmentVariables.repositoryId, repositoryId))
      .orderBy(environmentVariables.key);
  }

  async setEnvironmentVariables(
    repositoryId: string,
    vars: Array<{ key: string; value: string }>
  ): Promise<void> {
    await db
      .delete(environmentVariables)
      .where(eq(environmentVariables.repositoryId, repositoryId));

    if (vars.length > 0) {
      await db.insert(environmentVariables).values(
        vars.map((v) => ({
          repositoryId,
          key: v.key,
          value: v.value,
        }))
      );
    }
  }

  async createUser(username: string, email: string, password: string, isAdmin: boolean = false) {
    const [user] = await db
      .insert(users)
      .values({ username, email, password, isAdmin })
      .returning();
    return user;
  }

  async getUserByEmail(email: string) {
    const [user] = await db.select().from(users).where(eq(users.email, email));
    return user;
  }

  async getUserByUsername(username: string) {
    const [user] = await db.select().from(users).where(eq(users.username, username));
    return user;
  }

  async getUserByUsernameOrEmail(usernameOrEmail: string) {
    const [user] = await db
      .select()
      .from(users)
      .where(
        sql`${users.username} = ${usernameOrEmail} OR ${users.email} = ${usernameOrEmail}`
      );
    return user;
  }

  async updateUserAdminStatus(userId: string, isAdmin: boolean): Promise<User | undefined> {
    const [updated] = await db
      .update(users)
      .set({ isAdmin, updatedAt: new Date() })
      .where(eq(users.id, userId))
      .returning();
    return updated;
  }

  async getPaymentMethods(): Promise<PaymentMethod[]> {
    return await db.select().from(paymentMethods).orderBy(paymentMethods.createdAt);
  }

  async getAllUsers(): Promise<User[]> {
    return await db.select().from(users).orderBy(users.createdAt);
  }

  async updateUserPassword(userId: string, hashedPassword: string): Promise<boolean> {
    const result = await db
      .update(users)
      .set({ password: hashedPassword })
      .where(eq(users.id, userId));
    return result.rowCount !== null && result.rowCount > 0;
  }

  async getPaymentMethod(id: string): Promise<PaymentMethod | undefined> {
    const [method] = await db.select().from(paymentMethods).where(eq(paymentMethods.id, id));
    return method;
  }

  async createPaymentMethod(data: InsertPaymentMethod): Promise<PaymentMethod> {
    const [created] = await db.insert(paymentMethods).values(data).returning();
    return created;
  }

  async updatePaymentMethod(id: string, data: Partial<Omit<PaymentMethod, 'id' | 'createdAt'>>): Promise<PaymentMethod | undefined> {
    const [updated] = await db
      .update(paymentMethods)
      .set(data)
      .where(eq(paymentMethods.id, id))
      .returning();
    return updated;
  }

  async deletePaymentMethod(id: string): Promise<boolean> {
    const result = await db.delete(paymentMethods).where(eq(paymentMethods.id, id));
    return result.rowCount !== null && result.rowCount > 0;
  }

  async getBalanceRequests(): Promise<BalanceRequest[]> {
    return await db.select().from(balanceRequests).orderBy(balanceRequests.createdAt);
  }

  async getBalanceRequest(id: string): Promise<BalanceRequest | undefined> {
    const [request] = await db.select().from(balanceRequests).where(eq(balanceRequests.id, id));
    return request;
  }

  async getUserBalanceRequests(userId: string): Promise<BalanceRequest[]> {
    return await db.select().from(balanceRequests).where(eq(balanceRequests.userId, userId)).orderBy(balanceRequests.createdAt);
  }

  async createBalanceRequest(data: Omit<InsertBalanceRequest, 'id' | 'createdAt' | 'status'>): Promise<BalanceRequest> {
    const [created] = await db.insert(balanceRequests).values(data).returning();
    return created;
  }

  async updateBalanceRequestStatus(id: string, status: string, adminNotes?: string): Promise<BalanceRequest | undefined> {
    const [updated] = await db
      .update(balanceRequests)
      .set({ status })
      .where(eq(balanceRequests.id, id))
      .returning();

    if (updated && status === 'approved') {
      const request = updated;
      const amountInUsd = parseFloat(request.amountSent);
      await this.updateUserBalance(request.userId, amountInUsd);
    }

    return updated;
  }

  async updateUserBalance(userId: string, amount: number): Promise<User | undefined> {
    const [updated] = await db
      .update(users)
      .set({ 
        balance: sql`(CAST(${users.balance} AS NUMERIC) + ${amount})::TEXT`,
        updatedAt: new Date() 
      })
      .where(eq(users.id, userId))
      .returning();
    return updated;
  }

  // Notifications
  async createNotification(notification: InsertNotification): Promise<Notification> {
    const [created] = await db.insert(notifications).values(notification).returning();
    return created;
  }

  async getNotifications(userId: string): Promise<Notification[]> {
    return await db.select().from(notifications).where(eq(notifications.userId, userId)).orderBy(notifications.createdAt);
  }

  async getUnreadNotificationsCount(userId: string): Promise<number> {
    const [result] = await db
      .select({ count: sql<number>`COUNT(*)` })
      .from(notifications)
      .where(and(eq(notifications.userId, userId), eq(notifications.isRead, false)));
    return Number(result.count);
  }

  async markNotificationAsRead(id: string): Promise<Notification | undefined> {
    const [updated] = await db
      .update(notifications)
      .set({ isRead: true })
      .where(eq(notifications.id, id))
      .returning();
    return updated;
  }

  // Support Messages
  async createSupportMessage(data: InsertSupportMessage): Promise<SupportMessage> {
    const [message] = await db.insert(supportMessages).values(data).returning();
    return message;
  }

  async getAllSupportMessages(): Promise<SupportMessage[]> {
    const messages = await db.select().from(supportMessages).orderBy(supportMessages.createdAt);

    // Get user info for each message
    const messagesWithUsers = await Promise.all(
      messages.map(async (msg) => {
        const user = await this.getUser(msg.userId);
        return {
          ...msg,
          user: user ? { id: user.id, username: user.username, email: user.email } : undefined,
        };
      })
    );

    return messagesWithUsers;
  }
}

export const storage = new DatabaseStorage();