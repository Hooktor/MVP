/* Progressive enhancement; all business rules remain server-side. */
const initializeOrbit = () => {
 const sidebar=document.querySelector('#sidebar');
 sidebar?.addEventListener('pointerenter',e=>{if(e.pointerType==='mouse'||e.pointerType==='pen')sidebar.classList.add('hover-active');});
 sidebar?.addEventListener('pointerleave',e=>{if(e.pointerType==='mouse'||e.pointerType==='pen')sidebar.classList.remove('hover-active');});
 let keyboardNavigation=false;
 document.addEventListener('keydown',e=>{if(e.key==='Tab')keyboardNavigation=true;});
 document.addEventListener('pointerdown',()=>{keyboardNavigation=false;sidebar?.classList.remove('keyboard-active');});
 sidebar?.addEventListener('focusin',()=>{if(keyboardNavigation)sidebar.classList.add('keyboard-active');});
 sidebar?.addEventListener('focusout',()=>{requestAnimationFrame(()=>{if(!sidebar.contains(document.activeElement))sidebar.classList.remove('keyboard-active');});});
 const modal=document.querySelector('#modal');
 const show=(html)=>{document.querySelector('#modal-body').innerHTML=html;if(!modal.open)modal.showModal();};
 document.addEventListener('click',e=>{
   if(e.target.closest('[data-menu]')){
     const sidebar=document.querySelector('#sidebar');if(sidebar){sidebar.classList.toggle('open');document.querySelector('[aria-controls="sidebar"]').setAttribute('aria-expanded',sidebar.classList.contains('open'));}
   }
   if(e.target.closest('[data-close]'))modal.close();
   if(e.target.closest('[data-help]'))show(document.querySelector('#help-content').innerHTML);
 });
 document.addEventListener('keydown',e=>{if(e.key==='Escape'){document.querySelector('#sidebar')?.classList.remove('open');document.querySelector('[aria-controls="sidebar"]')?.setAttribute('aria-expanded','false');}});
 document.addEventListener('submit',e=>{
   const form=e.target;
   if(form.dataset.confirm && !form.dataset.confirmed){
     e.preventDefault();
     show('<p class="eyebrow">CONFIRMATION</p><h2>Confirmer cette action</h2><p id="confirm-copy"></p><div class="form-actions"><button class="button" data-close>Annuler</button><button class="button primary" id="confirm-action">Confirmer</button></div>');
     document.querySelector('#confirm-copy').textContent=form.dataset.confirm;
     document.querySelector('#confirm-action').onclick=()=>{form.dataset.confirmed='1';modal.close();form.requestSubmit();};
     return;
   }
   if(!form.hasAttribute('hx-post')) form.querySelectorAll('[data-once]').forEach(button=>{button.disabled=true;});
 });
 document.body.addEventListener('htmx:afterSwap',e=>{if(e.detail.target.id==='modal-body' && !modal.open)modal.showModal();});
 document.body.addEventListener('htmx:responseError',()=>{document.querySelector('#request-error').hidden=false;});
 document.body.addEventListener('htmx:sendError',()=>{document.querySelector('#request-error').hidden=false;});
 document.body.addEventListener('htmx:beforeRequest',()=>{document.querySelector('#request-error').hidden=true;});
 document.querySelectorAll('[data-file-drop]').forEach(drop=>{
   const input=drop.querySelector('[data-file-input]');
   const picker=drop.querySelector('[data-file-picker]');
   const selection=drop.querySelector('[data-file-selection]');
   const workspace=drop.closest('[data-import-workspace]');
   const sizeLabel=workspace.querySelector('[data-file-size]');
   const summary=workspace.querySelector('[data-file-summary]');
   const clear=workspace.querySelector('[data-file-clear]');
   const submit=workspace.querySelector('[data-import-action]');
   const displayFile=(file)=>{
     if(!file){selection.textContent='';sizeLabel.textContent='';summary.hidden=true;submit.disabled=true;drop.classList.remove('has-file');return;}
     const size=file.size<1024*1024?`${Math.ceil(file.size/1024)} Ko`:`${(file.size/1024/1024).toFixed(1)} Mo`;
     selection.textContent=file.name; sizeLabel.textContent=size; summary.hidden=false; submit.disabled=false; drop.classList.add('has-file');
   };
   picker.addEventListener('click',()=>input.click());
   input.addEventListener('change',()=>displayFile(input.files[0]));
   ['dragenter','dragover'].forEach(event=>drop.addEventListener(event,(e)=>{e.preventDefault();drop.classList.add('is-dragging');}));
   ['dragleave','drop'].forEach(event=>drop.addEventListener(event,(e)=>{e.preventDefault();drop.classList.remove('is-dragging');}));
   drop.addEventListener('drop',(e)=>{
     const file=e.dataTransfer?.files?.[0]; if(!file)return;
     const transfer=new DataTransfer(); transfer.items.add(file); input.files=transfer.files;
     input.dispatchEvent(new Event('change',{bubbles:true}));
   });
   clear.addEventListener('click',()=>{input.value='';displayFile();picker.focus();});
 });
};

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeOrbit, { once: true });
} else {
  initializeOrbit();
}
