// Debug ver: Supabase proxy — shows what it receives
export default async function handler(req, res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  
  const slug = req.query.slug || [];
  const qs = req.url.includes('?') ? req.url.split('?').slice(1).join('?') : '';
  const endpoint = slug.join('/') + (qs ? '?' + qs : '');
  const REF = process.env.SUPABASE_REF || '';
  const url = `https://${REF}.supabase.co/rest/v1/${endpoint}`;
  
  res.json({
    url_received: req.url,
    slug: slug,
    qs: qs,
    endpoint: endpoint,
    target_url: url,
    has_ref: !!process.env.SUPABASE_REF,
    has_service: !!process.env.SUPABASE_SERVICE_KEY,
    method: req.method,
  });
}
