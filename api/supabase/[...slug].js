// Vercel serverless — Supabase proxy
// Uses service_role key for full access

export default async function handler(req, res) {
  // CORS headers on everything
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(204).end();

  const SERVICE_KEY = (process.env.SUPABASE_SERVICE_KEY || '').trim();
  const ANON_KEY = (process.env.SUPABASE_ANON_KEY || '').trim();
  const REF = (process.env.SUPABASE_REF || '').trim();

  if (!SERVICE_KEY || !REF) {
    return res.status(503).json({ error: 'Missing SUPABASE_SERVICE_KEY or SUPABASE_REF env vars' });
  }

  // Build endpoint path
  const slug = req.query.slug || [];
  const qs = req.url.includes('?') ? req.url.split('?').slice(1).join('?') : '';
  const endpoint = slug.join('/') + (qs ? '?' + qs : '');
  const url = `https://${REF}.supabase.co/rest/v1/${endpoint}`;

  try {
    // Read body for non-GET requests
    let body = null;
    if (!['GET', 'DELETE', 'OPTIONS'].includes(req.method)) {
      const chunks = [];
      for await (const c of req) chunks.push(c);
      body = Buffer.concat(chunks).toString() || null;
    }

    const resp = await fetch(url, {
      method: req.method,
      headers: {
        // Use same key in both headers to avoid mismatch
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
