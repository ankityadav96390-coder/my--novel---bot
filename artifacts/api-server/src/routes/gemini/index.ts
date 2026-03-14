import { Router, type IRouter } from "express";
import conversationsRouter from "./conversations";
import messagesRouter from "./messages";
import imageRouter from "./image";

const router: IRouter = Router();

router.use(conversationsRouter);
router.use(messagesRouter);
router.use(imageRouter);

export default router;
