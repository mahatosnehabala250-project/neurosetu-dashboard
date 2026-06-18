// Debug: returns what Vercel sends us
export default function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.json({
    url: req.url,
    query: req.query,
    slug: req.query.slug,
    method: req.method,
    headers: {
      host: req.headers.host,
      'content-type': req.headers['content-type'],
    },
    env: {
      has_ref: !!process.env.SUPABASE_REF,
      has_anon: !!process.env.SUPABASE_ANON_KEY,
      has_service: !!process.env.SUPABASE_SERVICE_KEY,
      ref_val: process.env.SUPABASE_REF,
    }
  });
}
