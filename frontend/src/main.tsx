import React,{useState} from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter,Routes,Route,Navigate,Link } from 'react-router-dom';
import { QueryClient,QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider,useAuth } from './hooks/auth';
import Shell from './layouts/Shell';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Applications from './pages/Applications';
import Wizard from './pages/Wizard';
import Case from './pages/Case';
import { Integrations,Rules,Users,Notifications,Audit } from './pages/System';
import { ErrorBox } from './components/ui';
import { supabase } from './services/api';
import './styles.css';
const client=new QueryClient({defaultOptions:{queries:{retry:1,staleTime:10000}}});
function Reset(){const [password,setPassword]=useState(''),[error,setError]=useState<unknown>(null),[done,setDone]=useState(false);return <div className="panel form-panel"><h1>Set a new password</h1><ErrorBox error={error}/>{done?<Link to="/">Return to workspace</Link>:<form onSubmit={async e=>{e.preventDefault();const r=await supabase?.auth.updateUser({password});if(r?.error)setError(r.error);else setDone(true)}}><label>New password<input type="password" minLength={12} required value={password} onChange={e=>setPassword(e.target.value)}/></label><button className="primary">Update password</button></form>}</div>}
function App(){const {user,profile,loading,error}=useAuth();if(loading)return <div className="empty">Loading secure workspace…</div>;return <Routes><Route path="/reset-password" element={<Reset/>}/>{!user?<Route path="*" element={<Login/>}/>:!profile?<Route path="*" element={<div className="panel form-panel"><h1>Account access required</h1><ErrorBox error={error}/><p>Ask an administrator to provision an active profile for your Supabase Auth account.</p><button className="secondary" onClick={()=>supabase?.auth.signOut()}>Sign out</button></div>}/>:<Route element={<Shell/>}><Route index element={<Dashboard/>}/><Route path="applications" element={<Applications/>}/><Route path="applications/new" element={profile.role==='reviewer'?<Navigate to="/applications"/>:<Wizard/>}/><Route path="applications/:id" element={<Case/>}/><Route path="rules" element={<Rules/>}/><Route path="integrations" element={<Integrations/>}/><Route path="notifications" element={<Notifications/>}/><Route path="users" element={profile.role==='admin'?<Users/>:<Navigate to="/"/>}/><Route path="audit" element={profile.role==='admin'?<Audit/>:<Navigate to="/"/>}/><Route path="*" element={<div className="empty"><h1>404 · Page not found</h1><Link to="/">Return to overview</Link></div>}/></Route>}</Routes>}
class ErrorBoundary extends React.Component<{children:React.ReactNode},{error:boolean}>{state={error:false};static getDerivedStateFromError(){return {error:true}}render(){return this.state.error?<div className="empty"><h1>Workspace could not be displayed</h1><p>Reload the page. If the problem persists, check the API configuration.</p></div>:this.props.children}}
ReactDOM.createRoot(document.getElementById('root')!).render(<React.StrictMode><ErrorBoundary><QueryClientProvider client={client}><BrowserRouter><AuthProvider><App/></AuthProvider></BrowserRouter></QueryClientProvider></ErrorBoundary></React.StrictMode>);
