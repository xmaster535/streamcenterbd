export default {
  async fetch(request, env) {
    // আপনার GitHub রিপোজিটরির Raw JSON লিঙ্ক
    const url = "https://raw.githubusercontent.com/xmaster535/streamcenterbd/refs/heads/main/strmcntr_cache.json";
    
    const response = await fetch(url);
    const data = await response.json();

    return new Response(JSON.stringify(data), {
      headers: { 
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*" 
      },
    });
  },
};
