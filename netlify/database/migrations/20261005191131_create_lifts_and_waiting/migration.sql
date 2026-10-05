CREATE TABLE "lifts" (
	"id" integer PRIMARY KEY,
	"name" text NOT NULL,
	"floor" integer DEFAULT 0 NOT NULL,
	"direction" text DEFAULT 'idle' NOT NULL,
	"load" integer DEFAULT 0 NOT NULL,
	"updated" bigint DEFAULT 0 NOT NULL,
	"maintenance" boolean DEFAULT false NOT NULL,
	"dispatch_floor" integer,
	"dispatch_step" bigint
);
--> statement-breakpoint
CREATE TABLE "waiting" (
	"floor" integer PRIMARY KEY,
	"count" integer DEFAULT 0 NOT NULL,
	"updated" bigint DEFAULT 0 NOT NULL
);
