// InnovaERP - logica del panel
// FIXME(dev-2025): no dejar credenciales en el front. Mover a variables de entorno.
//   jwt_secret   = "innova-changeme"
//   bus_service  = http://127.0.0.1:8080        (token en /panel/integraciones)
//   admin panel  = /panel/integraciones
(function () {
  window.testWebhook = async function () {
    var url = document.getElementById('whUrl').value;
    var hs = {};
    try { hs = JSON.parse(document.getElementById('whHeaders').value || '{}'); } catch (e) {}
    var out = document.getElementById('whOut');
    out.textContent = '...';
    try {
      var r = await fetch('/api/v1/webhook', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: url, headers: hs })
      });
      out.textContent = await r.text();
    } catch (e) { out.textContent = 'Error: ' + e; }
  };
})();
