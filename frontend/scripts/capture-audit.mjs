// Capture a read-only authenticated runtime DOM for deterministic style auditing.
import { chromium } from 'playwright';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import path from 'node:path';
const root=path.resolve(import.meta.dirname,'../..');
const output=path.resolve(root,process.argv[2]||'design/rounds/3');
mkdirSync(output,{recursive:true});
const browser=await chromium.launch();
try {
 const page=await browser.newPage({viewport:{width:1440,height:1000}});
 await page.goto('http://127.0.0.1:3310');
 await page.getByLabel('本地身份凭证').fill(readFileSync(path.join(root,'.launchcase/browser-token'),'utf8').trim());
 await page.getByRole('button',{name:'进入工作区 →'}).click();
 await page.locator('.case-row').last().click();
 await page.getByRole('tab',{name:'总览',exact:true}).waitFor();
 const html=await page.evaluate(()=>{const clone=document.documentElement.cloneNode(true);clone.querySelectorAll('script,link').forEach(e=>e.remove());const style=document.createElement('style');style.textContent=Array.from(document.styleSheets).map(s=>Array.from(s.cssRules).map(r=>r.cssText).join('\n')).join('\n');clone.querySelector('head').append(style);return '<!doctype html>'+clone.outerHTML;});
 writeFileSync(path.join(output,'workbench-render.html'),html);
 for(const width of [1440,390]){
  await page.setViewportSize({width,height:width===390?844:1000});
  await page.evaluate(()=>window.scrollTo(0,0));
  const button=await page.getByRole('button',{name:'查看真实样品验证待办 →'}).boundingBox();
  if(!button || button.y+button.height> (width===390?844:1000)) throw Error('Next action is outside first viewport');
 }
 console.log('Authenticated DOM snapshot captured; current next action visible in both first viewports.');
} finally {await browser.close();}
