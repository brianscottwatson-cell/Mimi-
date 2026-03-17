import { db } from "./db.js";
import { configs, conversations, messages } from "../shared/schema.js";
import { eq, desc } from "drizzle-orm";
import { v4 as uuid } from "crypto";

export class Storage {
  async getConversations() {
    return await db.select().from(conversations).orderBy(desc(conversations.updatedAt));
  }

  async getConversation(id: string) {
    const [conversation] = await db.select().from(conversations).where(eq(conversations.id, id));
    return conversation || null;
  }

  async createConversation(title: string = "New Conversation") {
    const id = uuid().toString();
    const [created] = await db.insert(conversations).values({ id, title }).returning();
    return created;
  }

  async updateConversationTitle(id: string, title: string) {
    const [updated] = await db
      .update(conversations)
      .set({ title, updatedAt: new Date() })
      .where(eq(conversations.id, id))
      .returning();
    return updated;
  }

  async getMessages(conversationId: string) {
    return await db
      .select()
      .from(messages)
      .where(eq(messages.conversationId, conversationId))
      .orderBy(messages.createdAt);
  }

  async createMessage(conversationId: string, role: "user" | "assistant" | "system", content: string) {
    const id = uuid().toString();
    const [created] = await db
      .insert(messages)
      .values({ id, conversationId, role, content })
      .returning();
    
    // Update conversation timestamp
    await db.update(conversations).set({ updatedAt: new Date() }).where(eq(conversations.id, conversationId));
    
    return created;
  }

  async deleteConversation(id: string) {
    await db.delete(messages).where(eq(messages.conversationId, id));
    await db.delete(conversations).where(eq(conversations.id, id));
  }

  async getConfig(key: string) {
    const [config] = await db.select().from(configs).where(eq(configs.key, key));
    return config?.value || null;
  }

  async setConfig(key: string, value: string) {
    const existing = await this.getConfig(key);
    if (existing) {
      await db.update(configs).set({ value }).where(eq(configs.key, key));
    } else {
      await db.insert(configs).values({ key, value });
    }
  }
}

export const storage = new Storage();
