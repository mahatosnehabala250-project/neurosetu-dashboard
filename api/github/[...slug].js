// Vercel serverless — GitHub API proxy
// Env: GITHUB_TOKEN

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(204).end();

  const TOKEN = (process.env.GITHUB_TOKEN || '').trim();
  if (!TOKEN) {
    return res.status(503).json({ error: 'GitHub token not configured' });
  }

  // Extract path after /api/github/
  const fullUrl = req.url || '';
  const prefix = '/api/github/';
  const idx = fullUrl.indexOf(prefix);
  let endpoint = '';
  if (idx >= 0) {
    endpoint = fullUrl.substring(idx + prefix.length);
  }
  // Strip Vercel internal query params
  endpoint = endpoint.replace(/\?\.*slug.*$/, '').replace(/&\.*slug.*$/, '');

  const url = `https://api.github.com/${endpoint}`;

  try {
    const resp = await fetch(url, {
      method: req.method,
      headers: {
        'Authorization': `token ${TOKEN}`,
        'Accept': 'application/vnd.github.v3+json',
        'User-Agent': 'NeuroSetu-Dashboard',
      },
    });

    const text = await resp.text();
    let data = null;
    if (text.trim()) {
      try { data = JSON.parse(text); } catch { data = text; }
    }

    return res.status(resp.status).json(data);
  } catch (err) {
    console.error('GitHub proxy error:', err);
    return res.status(500).json({ error: err.message });
  }
}
