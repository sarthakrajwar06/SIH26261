export const workflowLabel=(value:string)=>value.replaceAll('_',' ');
export const formatBytes=(value:number)=>value>=1048576?`${(value/1048576).toFixed(1)} MB`:`${Math.ceil(value/1024)} KB`;
