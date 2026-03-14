import { Router, type IRouter } from "express";
import { GenerateGeminiImageBody } from "@workspace/api-zod";
import { generateImage } from "@workspace/integrations-gemini-ai/image";

const router: IRouter = Router();

router.post("/generate-image", async (req, res) => {
  const body = GenerateGeminiImageBody.parse(req.body);
  try {
    const { b64_json, mimeType } = await generateImage(body.prompt);
    res.json({ b64_json, mimeType });
  } catch (err) {
    console.error("Image generation error:", err);
    res.status(500).json({ error: "Failed to generate image" });
  }
});

export default router;
