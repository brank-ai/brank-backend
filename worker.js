export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // Replace this with your EXACT GCP Service URL (no https://)
    const targetHost = "brank-backend-btgdgszhsq-uc.a.run.app";

    url.hostname = targetHost;

    // Create a new request with the updated URL
    // This automatically sets the 'Host' header to the .run.app domain
    // which satisfies Google Cloud Run's requirements.
    const newRequest = new Request(url.toString(), request);

    return fetch(newRequest);
  },
};