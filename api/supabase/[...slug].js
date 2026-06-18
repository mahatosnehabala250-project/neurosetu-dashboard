// Vercel serverless — Supabase proxy
// Manual path extraction (Vercel catch-all slug unreliable)

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(204).end();

  const SERVICE_KEY = (process.env.SUPABASE_SERVICE_KEY || '').trim();
  const REF = (process.env.SUPABASE_REF || '').trim();

  if (!SERVICE_KEY || !REF) {
    return res.status(503).json({ error: 'Missing SUPABASE_SERVICE_KEY or SUPABASE_REF env vars' });
  }

  // Extract path AFTER /api/supabase/ manually
  const fullUrl = req.url || '';
  const prefix = '/api/supabase/';
  const idx = fullUrl.indexOf(prefix);
  let rest = '';
  if (idx >= 0) {
    rest = fullUrl.substring(idx + prefix.length);
  } else {
    // Fallback: remove query params
    rest = fullUrl.replace(/\?.*/, '').replace(/^\/+/, '');
  }
  
  // Remove Vercel's internal query params
  rest = rest.replace(/\?\.*slug.*$/, '').replace(/&\.*slug.*$/, '');

  const url = `https://${REF}.supabase.co/rest/v1/${rest}`;

  try {
    let body = null;
    if (!['GET', 'DELETE', 'OPTIONS'].includes(req.method)) {
      const chunks = [];
      for await (const c of req) chunks.push(c);
      body = Buffer.concat(chunks).toString() || null;
    }

    const resp = await fetch(url, {
      method: req.method,
      headers: {
        'apikey': SERVICE_KEY,
        'Authorization': `Bearer ${SERVICE_KEY}`,
        'Content-Type': 'application/json',
      },
      body: body,
    });

    const text = await resp.text();
    let data = null;
    if (text.trim()) {
      try { data = JSON.parse(text); } catch { data = text; }
    }

    return res.status(resp.status).json(data);
  } catch (err) {
    console.error('Proxy error:', err);
    return res.status(500).json({ error: err.message });
  }
}
