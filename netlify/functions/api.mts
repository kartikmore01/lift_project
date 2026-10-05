import type { Config } from "@netlify/functions";
import { eq } from "drizzle-orm";
import { db } from "../../db/index.js";
import { lifts, waiting } from "../../db/schema.js";

const NUM_FLOORS = 6;          // floor 0 se 5
const SEC_PER_FLOOR = 3;       // ek floor chadhne me kitne second
const SEC_PER_PERSON = 1.5;    // andar jitne log, utna extra time (stops ki wajah se)
const COMFORT_WEIGHT = 2;      // ranking me crowd ka asar (har insaan = 2 sec ka penalty)
const CAPACITY = 10;           // itne log ho to lift full
const OFFLINE_AFTER = 20;      // itne second data na aaye to lift offline
const CROWDED_AT = 6;          // camera itne log dekhe to floor "crowded"
const DISPATCH_LIFTS = [2, 3]; // bheed par Lift B aur Lift C bheji jaati hain

type LiftRow = typeof lifts.$inferSelect;

const now = () => Math.floor(Date.now() / 1000);
const clampFloor = (f: number) => Math.max(0, Math.min(NUM_FLOORS - 1, Math.round(f)));
const json = (data: unknown, status = 200) => Response.json(data, { status });

// ---- logic start ----
function etaSeconds(floor: number, direction: string, load: number, target: number) {
  const top = NUM_FLOORS - 1;
  let dist: number;
  if (direction === "idle" || floor === target) dist = Math.abs(floor - target);
  else if (direction === "up") dist = target >= floor ? target - floor : (top - floor) + (top - target);
  else dist = target <= floor ? floor - target : floor + target;
  const extra = dist > 0 ? load * SEC_PER_PERSON : 0;
  return Math.round(dist * SEC_PER_FLOOR + extra);
}

function crowdLevel(load: number) {
  if (load >= CAPACITY) return "full";
  if (load >= 7) return "high";
  if (load >= 4) return "medium";
  return "low";
}

function liftStatus(l: LiftRow, online: boolean, level: string) {
  if (l.maintenance) return "maintenance";
  if (!online) return "offline";
  if (level === "full") return "full";
  return "ok";
}

const isOnline = (l: LiftRow) => l.updated > 0 && now() - l.updated <= OFFLINE_AFTER;
// ---- logic end ----

function view(l: LiftRow) {
  const { dispatchFloor, dispatchStep, ...rest } = l;
  return { ...rest, dispatch_floor: dispatchFloor };
}

// Dispatch wali lifts ko time ke hisaab se target floor ki taraf aage badhao
async function loadLifts(): Promise<LiftRow[]> {
  await db.insert(lifts)
    .values([1, 2, 3].map(id => ({ id, name: "ABC"[id - 1] })))
    .onConflictDoNothing();
  const rows = await db.select().from(lifts).orderBy(lifts.id);
  const t = now();
  for (const l of rows) {
    if (l.dispatchFloor === null || l.dispatchStep === null) continue;
    if (l.maintenance) {
      Object.assign(l, { dispatchFloor: null, dispatchStep: null, direction: "idle" });
    } else {
      const steps = Math.floor((t - l.dispatchStep) / SEC_PER_FLOOR);
      const dist = l.dispatchFloor - l.floor;
      const moved = Math.min(steps, Math.abs(dist));
      l.floor += Math.sign(dist) * moved;
      l.dispatchStep += moved * SEC_PER_FLOOR;
      l.updated = t;
      if (l.floor === l.dispatchFloor) {
        Object.assign(l, { dispatchFloor: null, dispatchStep: null, direction: "idle" });
      } else {
        l.direction = dist > 0 ? "up" : "down";
      }
    }
    const { id, ...fields } = l;
    await db.update(lifts).set(fields).where(eq(lifts.id, id));
  }
  return rows;
}

async function loadWaiting() {
  const rows = await db.select().from(waiting);
  const out: Record<string, number> = {};
  rows.forEach(r => out[String(r.floor)] = r.count);
  return out;
}

async function setLift(body: any) {
  const id = Number(body.lift_id ?? 1);
  const all = await loadLifts();
  const l = all.find(x => x.id === id);
  if (!l) return json({ detail: "lift_id 1, 2 ya 3 hona chahiye" }, 404);
  // camera ne lift bheji hai to simulator ka data us safar tak ignore hota hai
  if (l.dispatchFloor !== null) return json(view(l));
  const fields = {
    floor: clampFloor(Number(body.floor) || 0),
    direction: ["up", "down", "idle"].includes(body.direction) ? body.direction : "idle",
    load: Math.max(0, Math.round(Number(body.load) || 0)),
    updated: now(),
  };
  const [row] = await db.update(lifts).set(fields).where(eq(lifts.id, id)).returning();
  return json(view(row));
}

async function setCrowd(body: any) {
  const floor = clampFloor(Number(body.floor) || 0);
  const count = Math.max(0, Math.round(Number(body.crowd_count) || 0));
  const t = now();
  await db.insert(waiting).values({ floor, count, updated: t })
    .onConflictDoUpdate({ target: waiting.floor, set: { count, updated: t } });

  const dispatched: string[] = [];
  if (count >= CROWDED_AT) {
    const all = await loadLifts();
    for (const l of all.filter(x => DISPATCH_LIFTS.includes(x.id) && !x.maintenance)) {
      dispatched.push(l.name);
      if (l.dispatchFloor === floor) continue;
      const fields = l.floor === floor
        ? { direction: "idle", dispatchFloor: null, dispatchStep: null, updated: t }
        : { direction: floor > l.floor ? "up" : "down", dispatchFloor: floor, dispatchStep: t, updated: t };
      await db.update(lifts).set(fields).where(eq(lifts.id, l.id));
    }
  }
  return json({ waiting: await loadWaiting(), crowded: count >= CROWDED_AT, dispatched });
}

async function setMaintenance(body: any) {
  const pin = Netlify.env.get("ADMIN_PIN") || "1234";
  if (String(body.pin ?? "") !== pin) return json({ detail: "Galat PIN" }, 403);
  const id = Number(body.lift_id);
  await loadLifts();
  const [row] = await db.update(lifts)
    .set({ maintenance: !!body.on, ...(body.on ? { dispatchFloor: null, dispatchStep: null } : {}) })
    .where(eq(lifts.id, id)).returning();
  if (!row) return json({ detail: "lift_id 1, 2 ya 3 hona chahiye" }, 404);
  return json(view(row));
}

async function recommend(url: URL) {
  const floor = Number(url.searchParams.get("floor") ?? 0);
  if (!Number.isInteger(floor) || floor < 0 || floor >= NUM_FLOORS) {
    return json({ detail: `floor 0 se ${NUM_FLOORS - 1} ke beech hona chahiye` }, 422);
  }
  const [all, wait] = await Promise.all([loadLifts(), loadWaiting()]);
  const out = all.map(l => {
    const online = isOnline(l);
    const level = crowdLevel(l.load);
    const status = liftStatus(l, online, level);
    const eta = status === "ok" ? etaSeconds(l.floor, l.direction, l.load, floor) : null;
    return { ...view(l), online, crowd_level: level, capacity: CAPACITY, status, eta };
  });

  const ok = out.filter(x => x.status === "ok") as (typeof out[number] & { eta: number })[];
  // ranking: eta + crowd ka comfort penalty
  ok.sort((a, b) => (a.eta + a.load * COMFORT_WEIGHT) - (b.eta + b.load * COMFORT_WEIGHT) || a.eta - b.eta);
  const ranking = ok.map(x => x.id);
  const best = ranking[0] ?? null;

  let reason = "Abhi koi lift available nahi hai";
  if (ok.length) {
    const fastest = ok.reduce((m, x) => (x.eta < m.eta ? x : m));
    reason = ok[0].id === fastest.id
      ? "Sabse jaldi pahunchegi"
      : `Thodi der se (+${ok[0].eta - fastest.eta} sec) par kam bheed wali`;
  }

  const waitingHere = wait[String(floor)] ?? 0;
  return json({
    floor, best, ranking, reason, lifts: out,
    waiting_here: waitingHere,
    floor_crowded: waitingHere >= CROWDED_AT,
    waiting: wait,
  });
}

export default async (req: Request) => {
  const url = new URL(req.url);
  const route = url.pathname.replace(/^\/api/, "").replace(/\/$/, "") || "/";
  const body = req.method === "POST" ? await req.json().catch(() => ({})) : {};

  if (req.method === "GET" && route === "/") return json({ message: "Lift backend chal raha hai. /api/recommend?floor=3 dekho." });
  if (req.method === "GET" && route === "/status") return json({ lifts: (await loadLifts()).map(view), waiting: await loadWaiting() });
  if (req.method === "GET" && route === "/recommend") return recommend(url);
  if (req.method === "POST" && route === "/lift") return setLift(body);
  if (req.method === "POST" && route === "/crowd") return setCrowd(body);
  if (req.method === "POST" && route === "/maintenance") return setMaintenance(body);
  return json({ detail: "Not found" }, 404);
};

export const config: Config = {
  path: ["/api", "/api/*"],
};
