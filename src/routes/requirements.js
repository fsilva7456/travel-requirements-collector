const express = require('express');
const router = express.Router();

// GET /api/requirements
router.get('/', async (req, res) => {
  try {
    res.json({ message: 'Get travel requirements' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// POST /api/requirements
router.post('/', async (req, res) => {
  try {
    res.json({ message: 'Create travel requirements' });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;