
import { sql } from "drizzle-orm";
import {
  index,
  jsonb,
  pgTable,
  timestamp,
  varchar,
  text,
  integer,
  boolean,
  uuid,
  numeric,
} from "drizzle-orm/pg-core";
import { relations } from "drizzle-orm";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

// Session storage table (required for Replit Auth)
export const sessions = pgTable(
  "sessions",
  {
    sid: varchar("sid").primaryKey(),
    sess: jsonb("sess").notNull(),
    expire: timestamp("expire").notNull(),
  },
  (table) => [index("IDX_session_expire").on(table.expire)]
);

// User storage table (required for Replit Auth)
export const users = pgTable("users", {
  id: uuid("id").defaultRandom().primaryKey(),
  username: text("username").notNull().unique(),
  email: text("email").notNull().unique(),
  password: text("password").notNull(),
  balance: text("balance").notNull().default("0"),
  isAdmin: boolean("is_admin").notNull().default(false),
  telegramUsername: text("telegram_username"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

// Payment Methods table
export const paymentMethods = pgTable("payment_methods", {
  id: uuid("id").defaultRandom().primaryKey(),
  name: text("name").notNull(),
  imageUrl: text("image_url").notNull(),
  instructions: text("instructions").notNull(),
  currency: text("currency").notNull(),
  usdRate: text("usd_rate").notNull(),
  isActive: boolean("is_active").notNull().default(true),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export type PaymentMethod = typeof paymentMethods.$inferSelect;
export type InsertPaymentMethod = typeof paymentMethods.$inferInsert;

// Balance Requests table
export const balanceRequests = pgTable("balance_requests", {
  id: uuid("id").defaultRandom().primaryKey(),
  userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  paymentMethodId: uuid("payment_method_id").notNull().references(() => paymentMethods.id),
  amountSent: text("amount_sent").notNull(),
  transactionId: text("transaction_id").notNull(),
  screenshotUrl: text("screenshot_url").notNull(),
  status: text("status").notNull().default("pending"),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export type BalanceRequest = typeof balanceRequests.$inferSelect;
export type InsertBalanceRequest = typeof balanceRequests.$inferInsert;

// Support Messages table
export const supportMessages = pgTable("support_messages", {
  id: uuid("id").defaultRandom().primaryKey(),
  userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  message: text("message").notNull(),
  isFromUser: boolean("is_from_user").notNull().default(true),
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export type SupportMessage = typeof supportMessages.$inferSelect;
export type InsertSupportMessage = typeof supportMessages.$inferInsert;

// Repositories table
export const repositories = pgTable("repositories", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  name: varchar("name", { length: 255 }).notNull(),
  description: text("description"),
  mainFile: varchar("main_file", { length: 255 }),
  pythonVersion: varchar("python_version", { length: 20 }).notNull().default("3.11"),
  autoInstallRequirements: boolean("auto_install_requirements").notNull().default(false),
  status: varchar("status", { length: 20 }).notNull().default("stopped"),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

export const repositoriesRelations = relations(repositories, ({ one, many }) => ({
  user: one(users, {
    fields: [repositories.userId],
    references: [users.id],
  }),
  files: many(files),
  environmentVariables: many(environmentVariables),
}));

export const insertRepositorySchema = createInsertSchema(repositories).omit({
  id: true,
  userId: true,
  createdAt: true,
  updatedAt: true,
  status: true,
});

export type InsertRepository = z.infer<typeof insertRepositorySchema>;
export type Repository = typeof repositories.$inferSelect;

// Files table
export const files = pgTable("files", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  repositoryId: varchar("repository_id").notNull().references(() => repositories.id, { onDelete: "cascade" }),
  name: varchar("name").notNull(),
  path: varchar("path").notNull().default(""),
  content: text("content").notNull().default(""),
  size: integer("size").notNull().default(0),
  isDirectory: boolean("is_directory").notNull().default(false),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

export const filesRelations = relations(files, ({ one }) => ({
  repository: one(repositories, {
    fields: [files.repositoryId],
    references: [repositories.id],
  }),
}));

export const insertFileSchema = createInsertSchema(files).pick({
  name: true,
  path: true,
  content: true,
  size: true,
  isDirectory: true,
});

export type InsertFile = z.infer<typeof insertFileSchema>;
export type File = typeof files.$inferSelect;

// Environment variables table
export const environmentVariables = pgTable("environment_variables", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  repositoryId: varchar("repository_id").notNull().references(() => repositories.id, { onDelete: "cascade" }),
  key: varchar("key", { length: 255 }).notNull(),
  value: text("value").notNull(),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

export const environmentVariablesRelations = relations(environmentVariables, ({ one }) => ({
  repository: one(repositories, {
    fields: [environmentVariables.repositoryId],
    references: [repositories.id],
  }),
}));

export const insertEnvironmentVariableSchema = createInsertSchema(environmentVariables).omit({
  id: true,
  repositoryId: true,
  createdAt: true,
  updatedAt: true,
});

export type InsertEnvironmentVariable = z.infer<typeof insertEnvironmentVariableSchema>;
export type EnvironmentVariable = typeof environmentVariables.$inferSelect;



// Notifications table
export const notifications = pgTable("notifications", {
  id: uuid("id").defaultRandom().primaryKey(),
  userId: uuid("user_id").notNull().references(() => users.id, { onDelete: "cascade" }),
  title: text("title").notNull(),
  message: text("message").notNull(),
  type: text("type").notNull(), // 'balance_approved', 'balance_rejected', 'support_message', 'general'
  isRead: boolean("is_read").notNull().default(false),
  relatedId: uuid("related_id"), // Reference to related entity (balance request, support message, etc.)
  createdAt: timestamp("created_at").defaultNow().notNull(),
});

export type Notification = typeof notifications.$inferSelect;
export type InsertNotification = typeof notifications.$inferInsert;
