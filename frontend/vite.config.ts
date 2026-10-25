import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
export default defineConfig({plugins:[react()],envDir:'..',build:{rolldownOptions:{output:{manualChunks:(id:string)=>{if(id.includes('recharts')||id.includes('d3-'))return 'charts';if(id.includes('@supabase'))return 'supabase';if(id.includes('node_modules/react'))return 'react';}}}},server:{host:'0.0.0.0',allowedHosts:['.e2b.app'],proxy:{'/api':'http://127.0.0.1:8000','/health':'http://127.0.0.1:8000'}}});
