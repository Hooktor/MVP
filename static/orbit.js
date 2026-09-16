/* Progressive enhancement; all business rules remain server-side. */
document.addEventListener('DOMContentLoaded', () => {
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
});

