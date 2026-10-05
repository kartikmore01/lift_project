import { bigint, boolean, integer, pgTable, text } from "drizzle-orm/pg-core";

export const lifts = pgTable("lifts", {
  id: integer().primaryKey(),
  name: text().notNull(),
  floor: integer().notNull().default(0),
  direction: text().notNull().default("idle"),
  load: integer().notNull().default(0),
  // last time (unix sec) data aayi — offline check ke liye
  updated: bigint({ mode: "number" }).notNull().default(0),
  maintenance: boolean().notNull().default(false),
  // camera ne bheed dekhi to lift is floor par bheji jaati hai
  dispatchFloor: integer("dispatch_floor"),
  // dispatch wali lift ka last step kab hua (unix sec)
  dispatchStep: bigint("dispatch_step", { mode: "number" }),
});

export const waiting = pgTable("waiting", {
  floor: integer().primaryKey(),
  count: integer().notNull().default(0),
  updated: bigint({ mode: "number" }).notNull().default(0),
});
