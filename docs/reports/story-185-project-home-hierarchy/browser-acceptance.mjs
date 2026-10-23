// CUA browser acceptance on representative local projects.
// New Bible/Cut disclosures restore focus. Existing ExportModal is checked for reachability/closure.
export const verifyHome = async function(tab, viewport, fs, options) {
  const {project,width,height,label,healthy,outDir}=options;
  const checks=[];
  const check=(name,pass,detail)=>{checks.push({name,pass,detail});if(!pass)throw new Error(name+': '+JSON.stringify(detail));};
  await viewport.set({width,height});
  if(await tab.playwright.evaluate(()=>location.pathname)!=='/'+project) await tab.goto('http://127.0.0.1:5174/'+project);
  await tab.playwright.locator('.screenplay-editor').waitFor({state:'visible'});
  const snapshot=await tab.playwright.domSnapshot();
  const layout=await tab.playwright.evaluate(()=>{const r=document.querySelector('.screenplay-editor').getBoundingClientRect();return {script:{top:r.top,left:r.left,width:r.width,height:r.height},width:innerWidth,height:innerHeight,scrollWidth:document.documentElement.scrollWidth};});
  check('Screenplay starts in initial viewport',layout.script.top>=0&&layout.script.top<height*.7,layout);
  check('No page horizontal overflow',layout.scrollWidth<=width,layout);
  check('Scenes visible without chat',await tab.playwright.getByRole('link',{name:'Scenes',exact:true}).isVisible());
  check('No persistent Artifact Health card',await tab.playwright.getByText('Artifact Health',{exact:true}).count()===0);
  check('No persistent Final Output card',await tab.playwright.getByText('Final Output',{exact:true}).count()===0);
  check('Actionable alert follows real health',snapshot.includes('artifacts need review.')===!healthy);
  await fs.writeFile(outDir+'/'+label+'.png',await tab.screenshot({fullPage:false}));
  for (const [trigger,title] of [['Script Bible','Script Bible'],['Project Cut','Project Cut'],['Export','Export Project']]) {
    await tab.playwright.getByRole('button',{name:trigger,exact:true}).click();
    const dialog=tab.playwright.getByRole('dialog',{name:title,exact:true});
    await dialog.waitFor({state:'visible'});
    const current=await tab.playwright.domSnapshot();
    const bounds=await tab.playwright.evaluate(()=>{const d=document.querySelector('[role="dialog"]');const r=d.getBoundingClientRect();return {x:r.x,y:r.y,right:r.right,bottom:r.bottom,scrollTop:d.scrollTop,clientWidth:d.clientWidth,scrollWidth:d.scrollWidth};});
    check(trigger+' fits viewport',bounds.x>=0&&bounds.y>=0&&bounds.right<=width&&bounds.bottom<=height&&bounds.scrollWidth<=bounds.clientWidth,bounds);
    if(trigger==='Script Bible')check('Bible retains story details',current.includes('heading "Synopsis"')&&current.includes('heading "Act Structure"'));
    if(trigger==='Project Cut')check('Clip and scene count labels',current.includes(healthy?'0 generated clips · 6 scenes':'10 generated clips · 6 scenes'));
    if(trigger==='Export')check('Screenplay and project data exports reachable',current.includes('tab "Screenplay"')&&current.includes('tab "Project Data"'));
    await fs.writeFile(outDir+'/'+label+'-'+trigger.toLowerCase().replaceAll(' ','-')+'.png',await tab.screenshot({fullPage:false}));
    await dialog.press('Escape');
    await dialog.waitFor({state:'hidden'});
    if(trigger!=='Export') {const focus=await tab.playwright.evaluate(()=>document.activeElement?.textContent?.trim());check(trigger+' restores focus',focus===trigger,focus);}
    else check('Existing export closes',await dialog.count()===0);
  }
  const result={project,width,height,label,healthy,layout,checks,consoleErrors:await tab.dev.logs({levels:['error'],limit:100})};
  await fs.writeFile(outDir+'/'+label+'.json',JSON.stringify(result,null,2)+'\n');
  return result;
};
