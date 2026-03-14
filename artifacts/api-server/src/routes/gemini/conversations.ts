import { Router, type IRouter } from "express";
import { eq } from "drizzle-orm";
import { db, conversations, messages } from "@workspace/db";
import {
  CreateGeminiConversationBody,
  GetGeminiConversationParams,
  DeleteGeminiConversationParams,
} from "@workspace/api-zod";

const router: IRouter = Router();

router.get("/conversations", async (_req, res) => {
  const rows = await db
    .select()
    .from(conversations)
    .orderBy(conversations.createdAt);
  res.json(rows);
});

router.post("/conversations", async (req, res) => {
  const body = CreateGeminiConversationBody.parse(req.body);
  const [created] = await db
    .insert(conversations)
    .values({ title: body.title })
    .returning();
  res.status(201).json(created);
});

router.get("/conversations/:id", async (req, res) => {
  const { id } = GetGeminiConversationParams.parse({
    id: Number(req.params.id),
  });
  const conversation = await db.query.conversations.findFirst({
    where: eq(conversations.id, id),
  });
  if (!conversation) {
    res.status(404).json({ error: "Conversation not found" });
    return;
  }
  const msgs = await db
    .select()
    .from(messages)
    .where(eq(messages.conversationId, id))
    .orderBy(messages.createdAt);
  res.json({ ...conversation, messages: msgs });
});

router.delete("/conversations/:id", async (req, res) => {
  const { id } = DeleteGeminiConversationParams.parse({
    id: Number(req.params.id),
  });
  const [deleted] = await db
    .delete(conversations)
    .where(eq(conversations.id, id))
    .returning();
  if (!deleted) {
    res.status(404).json({ error: "Conversation not found" });
    return;
  }
  res.status(204).end();
});

export default router;
