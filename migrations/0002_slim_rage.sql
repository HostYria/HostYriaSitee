ALTER TABLE "files" ALTER COLUMN "name" SET DATA TYPE varchar;--> statement-breakpoint
ALTER TABLE "files" ALTER COLUMN "content" SET DEFAULT '';--> statement-breakpoint
ALTER TABLE "files" ALTER COLUMN "size" SET DEFAULT 0;--> statement-breakpoint
ALTER TABLE "files" ADD COLUMN "path" varchar DEFAULT '' NOT NULL;--> statement-breakpoint
ALTER TABLE "files" ADD COLUMN "is_directory" boolean DEFAULT false NOT NULL;