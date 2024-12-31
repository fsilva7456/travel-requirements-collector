const express = require('express');
const requirementsRouter = require('./routes/requirements');

const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());

// Routes
app.use('/api/requirements', requirementsRouter);

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});