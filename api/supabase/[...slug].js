// Vercel serverless function — proxies ALL /api/supabase/* to Supabase REST API
// Supports GET, POST, PATCH, DELETE
// Env vars: SUPABASE_REF, SUPABASE_ANON_KEY, SUPABASE_SERVICE_KEY

export default async function handler(req, res) {
  // Handle CORS preflight
  if (req.method === 'OPTIONS') {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type, apikey, Authorization');
    return res.status(204).end();
  }

  const SUPABASE_REF = process.env.SUPABASE_REF;
  const SUPABASE_ANON_KEY = process.env.SUPABASE_ANON_KEY;
  const SUPABASE_SERVICE_KEY = process.env.SUPABASE_SERVICE_KEY;

  if (!SUPABASE_REF || !SUPABASE_SERVICE_KEY) {
    return res.status(503).json({ error: 'Supabase not configured' });
  }

  // Extract endpoint path from the catch-all slug
  // req.query.slug is an array of path segments
  const pathSegments = req.query.slug || [];
  const queryString = req.url.includes('?') ? req.url.split('?').slice(1).join('?') : '';
  const endpoint = pathSegments.join('/') + (queryString ? '?' + queryString : '');

  const url = `https://${SUPABASE_REF}.supabase.co/rest/v1/${endpoint}`;

  try {
    const fetchOptions = {
      method: req.method,
      headers: {
        'apikey': SUPABASE_ANON_KEY,
        'Authorization': `Bearer ${SUPABASE_SERVICE_KEY}`,
        'Content-Type': 'application/json',
        'User-Agent': 'NeuroSetu-Vercel',
      },
    };

    if (req.method !== 'GET' && req.method !== 'DELETE') {
      // Read body for POST/PATCH/PUT
      const chunks = [];
      for await (const chunk of req) {
        chunks.push(chunk);
      }
      const body = Buffer.concat(chunks).toString();
      if (body) {
        fetchOptions.body = body;
      }
    }

    const response = await fetch(url, fetchOptions);
    const contentType = response.headers.get('content-type') || '';
    let data = null;
    const text = await response.text();
    if (text.trim()) {
      try {
        data = JSON.parse(text);
      } catch (e) {
        data = text;
      }
    }

    // Forward response headers
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Expose-Headers', '*');
    res.setHeader('Content-Type', 'application/json');

    return res.status(response.status).json(data !== null ? data : {});
  } catch (error) {
    console.error('Supabase proxy error:', error);
    res.setHeader('Access-Control-Allow-Origin', '*');
    return res.status(500).json({ error: error.message });
  }
}
