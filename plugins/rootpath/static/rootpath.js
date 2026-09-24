(function () {
  function esc(s){return String(s==null?"":s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c];});}
  async function loadPaths(){
    var root=document.getElementById('rp-paths'); if(!root) return;
    try{
      var r=await fetch('/plugins/rootpath/api/paths',{credentials:'same-origin'});
      var j=await r.json(); var h='';
      if(!j.data.length){root.innerHTML='<p>No hay rutas configuradas.</p>';return;}
      j.data.forEach(function(c){
        h+='<div class="rp-cert"><div class="rp-cert-h"><h3>'+esc(c.name)+'</h3><span class="rp-badge">'+c.score+'%</span></div>';
        h+='<p class="rp-desc">'+esc(c.description)+'</p><div class="rp-bar"><i style="width:'+c.score+'%"></i></div>';
        c.domain_detail.forEach(function(d){
          h+='<details class="rp-dom"><summary>'+esc(d.name)+' ('+d.challenges.length+')</summary><ul class="rp-list">';
          d.challenges.forEach(function(ch){
            h+='<li class="'+(ch.solved?'rp-ok':'')+'"><span>'+(ch.solved?'&#10004;':'&#9675;')+'</span> <a href="/challenges#'+ch.id+'">'+esc(ch.name)+'</a> <small>'+esc(ch.category)+' - '+ch.value+' pts'+(ch.hints_used?' - '+ch.hints_used+' pista(s)':'')+'</small></li>';
          });
          h+='</ul></details>';
        });
        h+='</div>';
      });
      root.innerHTML=h;
    }catch(e){root.innerHTML='<p>Error cargando rutas: '+esc(e)+'</p>';}
  }
  function startForm(){
    return '<div class="rp-exam-start"><h3>Iniciar simulacro</h3>'+
      '<label>Certificacion: <select id="rp-cert"><option value="">Todos los retos</option></select></label> '+
      '<label>Duracion (min): <input id="rp-dur" type="number" value="180" min="1" style="width:80px"></label> '+
      '<button id="rp-start" class="rp-btn">Comenzar</button></div>';
  }
  async function loadExam(){
    var root=document.getElementById('rp-exam'); if(!root) return;
    async function refresh(){
      var r=await fetch('/plugins/rootpath/api/exam/status',{credentials:'same-origin'});
      var j;
      try{ j=await r.json(); }catch(e){ root.innerHTML='<p>Inicia sesion para usar el modo examen.</p>'; return; }
      if(!j.active){
        root.innerHTML=(j.expired?'<p class="rp-warn">Tu examen expiro.</p>':'')+startForm();
        var sel=document.getElementById('rp-cert');
        try{
          var rp=await fetch('/plugins/rootpath/api/paths',{credentials:'same-origin'});
          var jp=await rp.json();
          jp.data.forEach(function(c){var o=document.createElement('option');o.value=c.id;o.textContent=c.name;sel.appendChild(o);});
        }catch(e){}
        document.getElementById('rp-start').onclick=async function(){
          var cert=document.getElementById('rp-cert').value;
          var dur=parseInt(document.getElementById('rp-dur').value||'180');
          var body={duration_minutes:dur}; if(cert) body.cert_id=parseInt(cert);
          var rr=await fetch('/plugins/rootpath/api/exam/start',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
          var jj=await rr.json();
          if(!jj.success){alert(jj.error||'Error');} else {alert('Examen iniciado: '+jj.challenges+' retos, '+jj.duration_minutes+' min. Pistas deshabilitadas.');}
          refresh();
        };
        return;
      }
      var mm=Math.floor(j.remaining/60), ss=j.remaining%60;
      var h='<div class="rp-exam-active"><h3>Examen en curso</h3>'+
        '<p class="rp-timer">Tiempo restante: <b id="rp-timer">'+mm+'m '+ss+'s</b></p>'+
        '<p class="rp-warn">Las pistas estan deshabilitadas durante el examen.</p><ul class="rp-list">';
      j.challenges.forEach(function(c){h+='<li class="'+(c.solved?'rp-ok':'')+'"><span>'+(c.solved?'&#10004;':'&#9675;')+'</span>'+esc(c.name)+' <small>'+esc(c.category)+'</small></li>';});
      h+='</ul><label>Informe final (Markdown):<textarea id="rp-report" rows="12" style="width:100%;margin-top:6px"></textarea></label>'+
        '<div><button id="rp-save" class="rp-btn">Guardar borrador</button> <button id="rp-finish" class="rp-btn rp-danger">Finalizar y entregar informe</button></div></div>';
      root.innerHTML=h;
      var rem=j.remaining;
      var t=setInterval(function(){ rem--; if(rem<=0){clearInterval(t);root.innerHTML='<p class="rp-warn">Tiempo agotado.</p>';return;} var e=document.getElementById('rp-timer'); if(e){e.textContent=Math.floor(rem/60)+'m '+(rem%60)+'s';} },1000);
      async function save(finish){
        var content=document.getElementById('rp-report').value;
        var url=finish?'/plugins/rootpath/api/exam/finish':'/plugins/rootpath/api/exam/report';
        var rr=await fetch(url,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:content,report:content})});
        var jj=await rr.json();
        alert(jj.success?(finish?'Informe entregado. Examen finalizado.':'Borrador guardado.'):('Error: '+(jj.error||'')));
        if(finish) refresh();
      }
      document.getElementById('rp-save').onclick=function(){save(false);};
      document.getElementById('rp-finish').onclick=function(){save(true);};
    }
    refresh();
  }
  document.addEventListener('DOMContentLoaded',function(){ loadPaths(); loadExam(); });
})();

(function(){
  async function loadAnalytics(){
    var root=document.getElementById('rp-analytics'); if(!root) return;
    try{
      var r=await fetch('/plugins/rootpath/api/analytics',{credentials:'same-origin'});
      if(r.status!==200){root.innerHTML='<p>Inicia sesion para ver las analiticas.</p>';return;}
      var d=(await r.json()).data;
      var h='<div class="rp-cert"><h3>Resumen</h3><p>Retos: '+d.challenges+' &middot; Usuarios: '+d.users+' &middot; Resoluciones: '+d.solves+' &middot; Pistas usadas: '+d.hint_unlocks+'</p></div>';
      h+='<div class="rp-cert"><h3>Retos mas dificiles (menor tasa de resolucion)</h3><ul class="rp-list">';
      d.hardest.forEach(function(c){h+='<li'+(c.flag?' class="rp-warn"':'')+'>'+c.name+' <small>'+c.solves+' solves &middot; '+c.solve_rate+'%'+(c.flag?' &middot; REVISAR':'')+'</small></li>';});
      h+='</ul></div>';
      h+='<div class="rp-cert"><h3>Por categoria</h3><ul class="rp-list">';
      d.by_category.forEach(function(c){h+='<li>'+c.category+': '+c.challenges+' retos &middot; '+c.solves+' solves</li>';});
      h+='</ul></div>';
      h+='<div class="rp-cert"><h3>Top usuarios</h3><ul class="rp-list">';
      d.top_users.forEach(function(u){h+='<li>'+u.user+' <small>'+u.score+' pts</small></li>';});
      h+='</ul></div>';
      root.innerHTML=h;
    }catch(e){root.innerHTML='<p>Error cargando analiticas: '+e+'</p>';}
  }
  document.addEventListener('DOMContentLoaded',function(){ loadAnalytics(); });
})();
