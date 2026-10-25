import { createClient } from '@supabase/supabase-js';
const env = (import.meta as unknown as {env:Record<string,string>}).env;
export const configured = !!(env.VITE_SUPABASE_URL && env.VITE_SUPABASE_PUBLISHABLE_KEY);
// No fallback connection, local credentials, or alternate authentication provider.
export const supabase = configured ? createClient(env.VITE_SUPABASE_URL,env.VITE_SUPABASE_PUBLISHABLE_KEY) : null;
export async function api<T=any>(path:string, options:RequestInit={}):Promise<T> {
  const session=await supabase?.auth.getSession();
  const response=await fetch('/api/v1'+path,{...options,headers:{...(options.body instanceof FormData?{}:{'Content-Type':'application/json'}),Authorization:'Bearer '+(session?.data.session?.access_token||''),...options.headers}});
  if(!response.ok){const error=await response.json().catch(()=>({detail:'Server unavailable'}));throw new Error(typeof error.detail==='string'?error.detail:JSON.stringify(error.detail));}
  if(response.headers.get('content-type')?.includes('application/pdf')||options.headers && (options.headers as Record<string,string>).Accept==='application/octet-stream') return await response.blob() as T;
  return response.json();
}
export const post=(path:string,data:unknown={})=>api(path,{method:'POST',body:JSON.stringify(data)});
export async function privateBlob(path:string){return api<Blob>(path,{headers:{Accept:'application/octet-stream'}});}
export function download(blob:Blob,name:string){const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),5000);}
