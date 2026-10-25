// @vitest-environment jsdom
import React from 'react';
import {vi,it,expect,afterEach} from 'vitest';
import {render,screen,fireEvent,waitFor,cleanup} from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import {QueryClient,QueryClientProvider} from '@tanstack/react-query';
import {MemoryRouter,Routes,Route} from 'react-router-dom';
import Case from './Case';
const mocks=vi.hoisted(()=>({post:vi.fn().mockResolvedValue({id:'review'}),api:vi.fn()}));
vi.mock('../hooks/auth',()=>({useAuth:()=>({profile:{role:'reviewer'}})}));
vi.mock('../services/api',()=>({api:mocks.api,post:mocks.post,privateBlob:vi.fn(),download:vi.fn()}));
function mount(){return render(<QueryClientProvider client={new QueryClient({defaultOptions:{queries:{retry:false}}})}><MemoryRouter initialEntries={['/applications/case']}><Routes><Route path="/applications/:id" element={<Case/>}/></Routes></MemoryRouter></QueryClientProvider>)}
afterEach(()=>{cleanup();vi.clearAllMocks()});
it('reviewer inspects a real finding display and records a reasoned action',async()=>{
 mocks.api.mockImplementation(async(path:string)=>{
  if(path==='/applications/case')return {id:'case',reference:'DEMO-CASE',academic_year:'2026-27',category_id:'cat',status:'PRELIMINARY_REVIEW_COMPLETE'};
  if(path.endsWith('/findings'))return {items:[{id:'finding',status:'WARNING',category:'CONSISTENCY',severity:'WARNING',explanation:'Conflicting faculty counts',expected_value:'24',observed_value:'18',evidence:[],suggested_action:'Inspect original faculty evidence'}]};
  return {items:[]};
 });
 mount();await screen.findByText('DEMO-CASE');fireEvent.click(screen.getByRole('button',{name:/^Findings/}));expect(await screen.findByText('Conflicting faculty counts')).toBeVisible();
 fireEvent.click(screen.getByText(/Record disposition for this finding/));const record=screen.getByRole('button',{name:'Record action'});expect(record).toBeDisabled();
 fireEvent.change(screen.getByLabelText('Reason / evidence assessment'),{target:{value:'DEMO original faculty records inspected; clarification requested.'}});
 fireEvent.click(record);expect(screen.getByRole('dialog')).toBeVisible();expect(mocks.post).not.toHaveBeenCalled();fireEvent.click(screen.getByText('Confirm action'));
 await waitFor(()=>expect(mocks.post).toHaveBeenCalledWith('/findings/finding/review',expect.objectContaining({action:'OBSERVATION',reason:expect.stringContaining('clarification')})));
});
it('renders an unauthorized case error instead of evidence',async()=>{
 mocks.api.mockRejectedValue(new Error('Record not found or not authorized'));mount();await waitFor(()=>expect(screen.getByRole('alert')).toHaveTextContent('not authorized'));expect(screen.queryByText('Original document')).not.toBeInTheDocument();
});
