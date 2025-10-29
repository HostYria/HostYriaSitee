import {
  users,
  repositories,
  files,
  environmentVariables,
  type User,
  type UpsertUser,
  type Repository,
  type InsertRepository,
  type File,
  type InsertFile,
  type EnvironmentVariable,
  type InsertEnvironmentVariable,
} from "@shared/schema";
import { db } from "./db";
import { eq, and, sql } from "drizzle-orm";

export interface IStorage {
  getUser(id: string): Promise<User | undefined>;
  upsertUser(user: UpsertUser): Promise<User>;

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
}

export class DatabaseStorage implements IStorage {
  async getUser(id: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.id, id));
    return user;
  }

  async upsertUser(userData: UpsertUser): Promise<User> {
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

  async createUser(username: string, email: string, password: string) {
    const [user] = await db
      .insert(users)
      .values({ username, email, password })
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
}

export const storage = new DatabaseStorage();