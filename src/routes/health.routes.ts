import { Router } from 'express';
import { live, ready } from '../controllers/health.controller.js';

export const healthRouter: Router = Router();

healthRouter.get('/', live);
healthRouter.get('/ready', ready);
