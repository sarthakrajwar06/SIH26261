import { createContext,useContext,useEffect,useState,useRef,ReactNode } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { supabase,api } from '../services/api';
interface Auth {user:any; profile:any; loading:boolean; error:unknown; refresh:()=>Promise<void>}
const AuthContext=createContext<Auth>({user:null,profile:null,loading:true,error:null,refresh:async()=>{}});
export function AuthProvider({children}:{children:ReactNode}){const queryClient=useQueryClient();const previousUser=useRef<string|null>(null);const [user,setUser]=useState<any>(null),[profile,setProfile]=useState<any>(null),[loading,setLoading]=useState(true),[error,setError]=useState<unknown>(null);
 const refresh=async()=>{try{const {data}=await supabase!.auth.getSession();const nextUser=data.session?.user?.id||null;if(previousUser.current!==nextUser){queryClient.clear();setProfile(null);previousUser.current=nextUser;}setUser(data.session?.user||null);setProfile(data.session?await api('/auth/me'):null);setError(null)}catch(e){setProfile(null);setError(e)}finally{setLoading(false)}};
 useEffect(()=>{if(!supabase){setLoading(false);return;}void refresh();const {data}=supabase.auth.onAuthStateChange(()=>{setTimeout(()=>void refresh(),0)});return()=>data.subscription.unsubscribe()},[]);
 return <AuthContext.Provider value={{user,profile,loading,error,refresh}}>{children}</AuthContext.Provider>}
export const useAuth=()=>useContext(AuthContext);
