import express from 'express';
const router = express.Router();
import { startgame, getMatches, getParticipants, getTournamentStatus, reset } from '../controllers/gameController.js';

router.post('/start-game', startgame);
router.get('/get-matches', getMatches);
router.get('/get-participants', getParticipants);
router.get('/reset', reset);
router.get('/get-tournament-status', getTournamentStatus);

export default router;