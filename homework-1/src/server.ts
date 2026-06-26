import { app } from './app.js';

const PORT = process.env.PORT ? parseInt(process.env.PORT, 10) : 3000;

app.listen(PORT, () => {
  console.log(`Banking Transactions API running on http://localhost:${PORT}`);
});
