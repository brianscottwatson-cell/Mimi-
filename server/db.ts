import { drizzle } from "drizzle-orm/node-postgres";
import pg from "pg";
import * as schema from "../shared/schema.js";

const { Pool } = pg;

const DATABASE_URL = process.env.DATABASE_URL || "postgresql://user:password@localhost:5432/claudebot";

export const pool = new Pool({ connectionString: DATABASE_URL });
export const db = drizzle(pool, { schema });

export async function initDb() {
  try {
    await pool.query("SELECT 1");
    console.log("✓ Database connected");
  } catch (err) {
    console.error("✗ Database connection failed:", err);
    process.exit(1);
  }
}
