/* ConstruExpert · comportamento comum: menu de celular e janela de cadastro antes do download dos e-books. */
(function(){
  "use strict";
  var CADASTRO="https://chk.eduzz.com/89AXY5GE0D";

  /* Menu de celular */
  var top=document.querySelector(".top"), btn=document.querySelector(".menu-btn");
  if(top&&btn){
    btn.addEventListener("click",function(){
      var aberto=top.classList.toggle("aberto");
      btn.setAttribute("aria-expanded",aberto?"true":"false");
    });
    document.querySelectorAll(".menu-mob a").forEach(function(a){
      a.addEventListener("click",function(){top.classList.remove("aberto");btn.setAttribute("aria-expanded","false");});
    });
  }

  /* E-books: antes de baixar, oferece o cadastro gratuito na escola (Eduzz). Quem já se cadastrou ou já viu a janela nesta visita baixa direto. */
  var janela=document.getElementById("janela-ebook");
  if(!janela||typeof janela.showModal!=="function") return;
  function ler(k){try{return sessionStorage.getItem(k)||localStorage.getItem(k);}catch(e){return null;}}
  function gravar(k,v,longo){try{(longo?localStorage:sessionStorage).setItem(k,v);}catch(e){}}
  var atual=null;
  var titulo=janela.querySelector("[data-titulo]");
  var cad=janela.querySelector("[data-cadastrar]");
  var pular=janela.querySelector("[data-pular]");
  document.querySelectorAll("a[data-ebook]").forEach(function(a){
    a.addEventListener("click",function(ev){
      if(!/\.pdf$/i.test(a.getAttribute("href"))) return;           // link já trocado para o WhatsApp
      if(ler("ce-cadastro")||ler("ce-viu-janela")) return;         // segue direto para o PDF
      ev.preventDefault();
      atual=a;
      if(titulo) titulo.textContent=a.closest("article").querySelector("h3").textContent;
      cad.href=CADASTRO+"?utm_source=site&utm_medium=materiais&utm_campaign=ebook-"+(a.dataset.ebook||"");
      janela.showModal();
    });
  });
  cad.addEventListener("click",function(){
    gravar("ce-cadastro","1",true);           // o link abre a Eduzz em outra aba; os e-books também ficam na escola
    janela.close();
  });
  pular.addEventListener("click",function(){
    gravar("ce-viu-janela","1",false);
    if(atual) window.open(atual.href,"_blank","noopener");
    janela.close();
  });
  janela.querySelector(".fechar").addEventListener("click",function(){janela.close();});
  janela.addEventListener("click",function(ev){if(ev.target===janela) janela.close();});
})();
