// Vercel serverless — Combined API proxy (GitHub + Supabase)
// Env: SUPABASE_REF, SUPABASE_SERVICE_KEY, GITHUB_TOKEN

export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');

  if (req.method === 'OPTIONS') return res.status(204).end();

  const url = req.url || '';
  
  try {
    // === GITHUB PROXY ===
    if (url.startsWith('/api/github/')) {
      const TOKEN = (process.env.GITHUB_TOKEN || '').trim();
      if (!TOKEN) return res.status(503).json({ error: 'GitHub token not configured' });
      
      const endpoint = url.replace('/api/github/', '').replace(/\?.*$/, '');
      const ghUrl = `https://api.github.com/${endpoint}`;
      
      const resp = await fetch(ghUrl, {
        method: req.method,
        headers: {
          'Authorization': `token ${TOKEN}`,
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'NeuroSetu-Dashboard',
        },
      });
      const text = await resp.text();
      return res.status(resp.status).json(text ? JSON.parse(text) : null);
    }
    
    // === SUPABASE PROXY ===
    if (url.startsWith('/api/supabase/')) {
      const SERVICE_KEY = (process.env.SUPABASE_SERVICE_KEY || '').trim();
      const REF = (process.env.SUPABASE_REF || '').trim();
      if (!SERVICE_KEY || !REF) return res.status(503).json({ error: 'Supabase not configured' });
      
      const endpoint = url.substring(url.indexOf('/api/supabase/') + '/api/supabase/'.length);
      const sbUrl = `https://${REF}.supabase.co/rest/v1/${endpoint.replace(/\?.*$/, '')}` + (url.includes('?') ? '?' + url.split('?').slice(1).join('?').replace(/&?\.*slug[^&]*/g, '') : '');
      
      let body = null;
      if (!['GET', 'DELETE', 'OPTIONS'].includes(req.method)) {
        const chunks = [];
        for await (const c of req) chunks.push(c);
        body = Buffer.concat(chunks).toString() || null;
      }
      
      const resp = await fetch(sbUrl, {
        method: req.method,
        headers: { 'apikey': SERVICE_KEY, 'Authorization': `Bearer ${SERVICE_KEY}`, 'Content-Type': 'application/json' },
        body: body,
      });
      const text = await resp.text();
      return res.status(resp.status).json(text.trim() ? JSON.parse(text) : null);
    }

    return res.status(404).json({ error: 'Not found' });
  } catch (err) {
    console.error('Proxy error:', err);
    return res.status(500).json({ error: err.message });
  }
}
