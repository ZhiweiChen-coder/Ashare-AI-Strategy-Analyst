export default {
  async fetch(request, env) {
    try {
      const url = new URL(request.url);
      
      // 所有路由都返回 index.html
      const html = await env.ASSETS.fetch(new Request("index.html"));
      return new Response(html.body, {
        headers: { 
          "content-type": "text/html;charset=UTF-8",
          // 添加安全相关头部
          "X-Content-Type-Options": "nosniff",
          "X-Frame-Options": "DENY",
          "Content-Security-Policy": "default-src 'self' 'unsafe-inline'"
        },
      });
      
    } catch (err) {
      return new Response("Internal Server Error", { 
        status: 500,
        headers: { "content-type": "text/plain;charset=UTF-8" }
      });
    }
  }
};
