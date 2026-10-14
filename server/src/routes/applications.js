const express = require('express');
const router = express.Router();
const { body, query, validationResult } = require('express-validator');
const pool = require('../models/db');
const authMiddleware = require('../middleware/auth');

const VALID_STATUSES = ['Saved', 'Applied', 'Interview', 'Offer', 'Rejected'];

// All routes require auth
router.use(authMiddleware);

// GET /api/applications  — list with optional filters
router.get('/', async (req, res) => {
  const { status, search, location, sort } = req.query;
  const userId = req.user.id;

  let conditions = ['a.user_id = $1'];
  let params = [userId];
  let idx = 2;

  if (status && VALID_STATUSES.includes(status)) {
    conditions.push(`a.status = $${idx++}`);
    params.push(status);
  }
  if (location) {
    conditions.push(`a.location ILIKE $${idx++}`);
    params.push(`%${location}%`);
  }
  if (search) {
    conditions.push(`(a.company ILIKE $${idx} OR a.position ILIKE $${idx})`);
    params.push(`%${search}%`);
    idx++;
  }

  const orderBy =
    sort === 'deadline' ? 'a.deadline ASC NULLS LAST' :
    sort === 'company'  ? 'a.company ASC' :
    'a.created_at DESC';

  const sql = `
    SELECT a.*, u.name AS user_name
    FROM applications a
    JOIN users u ON u.id = a.user_id
    WHERE ${conditions.join(' AND ')}
    ORDER BY ${orderBy}
  `;

  try {
    const result = await pool.query(sql, params);
    res.json(result.rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Server error' });
  }
});

// POST /api/applications
router.post(
  '/',
  [
    body('company').trim().notEmpty().withMessage('Company is required'),
    body('position').trim().notEmpty().withMessage('Position is required'),
    body('status').optional().isIn(VALID_STATUSES).withMessage('Invalid status'),
    body('job_url').optional().isURL({ require_protocol: false }).withMessage('Invalid URL'),
    body('deadline').optional({ nullable: true }).isISO8601().withMessage('Invalid deadline date'),
    body('interview_date').optional({ nullable: true }).isISO8601().withMessage('Invalid interview date'),
  ],
  async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) return res.status(400).json({ errors: errors.array() });

    const { company, position, job_url, location, source, status, deadline, interview_date, notes } = req.body;

    try {
      const result = await pool.query(
        `INSERT INTO applications
          (user_id, company, position, job_url, location, source, status, deadline, interview_date, notes)
         VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10)
         RETURNING *`,
        [req.user.id, company, position, job_url || null, location || null, source || null,
         status || 'Saved', deadline || null, interview_date || null, notes || null]
      );
      const app = result.rows[0];

      // record initial status
      await pool.query(
        'INSERT INTO status_history (application_id, old_status, new_status) VALUES ($1,$2,$3)',
        [app.id, null, app.status]
      );

      res.status(201).json(app);
    } catch (err) {
      console.error(err);
      res.status(500).json({ error: 'Server error' });
    }
  }
);

// GET /api/applications/:id
router.get('/:id', async (req, res) => {
  try {
    const result = await pool.query(
      'SELECT * FROM applications WHERE id=$1 AND user_id=$2',
      [req.params.id, req.user.id]
    );
    if (!result.rows.length) return res.status(404).json({ error: 'Not found' });
    res.json(result.rows[0]);
  } catch (err) {
    res.status(500).json({ error: 'Server error' });
  }
});

// PATCH /api/applications/:id
router.patch(
  '/:id',
  [
    body('company').optional().trim().notEmpty(),
    body('position').optional().trim().notEmpty(),
    body('status').optional().isIn(VALID_STATUSES).withMessage('Invalid status'),
    body('job_url').optional({ nullable: true }),
    body('deadline').optional({ nullable: true }),
    body('interview_date').optional({ nullable: true }),
  ],
  async (req, res) => {
    const errors = validationResult(req);
    if (!errors.isEmpty()) return res.status(400).json({ errors: errors.array() });

    const { id } = req.params;
    const userId = req.user.id;

    try {
      // get current app
      const current = await pool.query(
        'SELECT * FROM applications WHERE id=$1 AND user_id=$2',
        [id, userId]
      );
      if (!current.rows.length) return res.status(404).json({ error: 'Not found' });

      const old = current.rows[0];
      const fields = ['company','position','job_url','location','source','status','deadline','interview_date','notes'];
      const updates = {};
      fields.forEach(f => {
        if (req.body[f] !== undefined) updates[f] = req.body[f];
      });

      if (!Object.keys(updates).length) return res.json(old);

      const setClauses = Object.keys(updates).map((k, i) => `${k}=$${i + 1}`);
      const values = Object.values(updates);
      values.push(id, userId);

      const result = await pool.query(
        `UPDATE applications SET ${setClauses.join(',')}
         WHERE id=$${values.length - 1} AND user_id=$${values.length}
         RETURNING *`,
        values
      );
      const updated = result.rows[0];

      // record status change
      if (updates.status && updates.status !== old.status) {
        await pool.query(
          'INSERT INTO status_history (application_id, old_status, new_status) VALUES ($1,$2,$3)',
          [id, old.status, updates.status]
        );
      }

      res.json(updated);
    } catch (err) {
      console.error(err);
      res.status(500).json({ error: 'Server error' });
    }
  }
);

// DELETE /api/applications/:id
router.delete('/:id', async (req, res) => {
  try {
    const result = await pool.query(
      'DELETE FROM applications WHERE id=$1 AND user_id=$2 RETURNING id',
      [req.params.id, req.user.id]
    );
    if (!result.rows.length) return res.status(404).json({ error: 'Not found' });
    res.json({ message: 'Deleted', id: req.params.id });
  } catch (err) {
    res.status(500).json({ error: 'Server error' });
  }
});

// GET /api/applications/:id/history
router.get('/:id/history', async (req, res) => {
  try {
    // verify ownership first
    const own = await pool.query(
      'SELECT id FROM applications WHERE id=$1 AND user_id=$2',
      [req.params.id, req.user.id]
    );
    if (!own.rows.length) return res.status(404).json({ error: 'Not found' });

    const result = await pool.query(
      'SELECT * FROM status_history WHERE application_id=$1 ORDER BY changed_at DESC',
      [req.params.id]
    );
    res.json(result.rows);
  } catch (err) {
    res.status(500).json({ error: 'Server error' });
  }
});

module.exports = router;
