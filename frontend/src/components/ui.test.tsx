// @vitest-environment jsdom
import React from 'react';
import {describe,it,expect,vi} from 'vitest';
import {render,screen,fireEvent,cleanup} from '@testing-library/react';
import '@testing-library/jest-dom/vitest';
import {Badge,ErrorBox,Confirm,Empty} from './ui';
import Login from '../pages/Login';
describe('evidence and accessible states',()=>{
 it('labels simulation distinctly',()=>{render(<Badge>SIMULATED</Badge>);expect(screen.getByText('SIMULATED')).toBeInTheDocument();cleanup()});
 it('shows safe errors',()=>{render(<ErrorBox error={new Error('Not authorized')}/>);expect(screen.getByRole('alert')).toHaveTextContent('Not authorized');cleanup()});
 it('does not claim success in empty state',()=>{render(<Empty text="No findings generated"/>);expect(screen.getByText('No findings generated')).toBeVisible();cleanup()});
 it('requires confirmation for reviewer actions',()=>{const act=vi.fn();render(<Confirm title="Record action?" onConfirm={act}><button>Record</button></Confirm>);fireEvent.click(screen.getByText('Record'));expect(act).not.toHaveBeenCalled();expect(screen.getByRole('dialog')).toBeVisible();fireEvent.click(screen.getByText('Confirm action'));expect(act).toHaveBeenCalledTimes(1);cleanup()});
 it('shows unconfigured auth without a fake login',()=>{render(<Login/>);expect(screen.getByText('Supabase setup required')).toBeVisible();expect(screen.getByRole('button',{name:/Sign in securely/})).toBeDisabled();cleanup()});
});
