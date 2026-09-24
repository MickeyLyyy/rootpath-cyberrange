// NimbusDrive front-end
(function () {
  function _d(s) { try { return atob(s); } catch (e) { return ""; } }
  // rutas de la API (ofuscadas en base64; decodificar para ver los endpoints)
  var R = {
    files: _d("L2FwaS92Mi9maWxlcy9leHBvcnQ="),
    admin: _d("L2FkbWluL3JlaW5kZXg="),
    cfg:   _d("L2FwcC9jb25maWcvYXBwLmVudg=="),
    sign:  _d("WC1TaWdu")
  };
  window.ND = R;

  window.exportFile = function (n) {
    var out = document.getElementById('out');
    out.textContent = '...';
    fetch(R.files + '?name=' + encodeURIComponent(n))
      .then(function (r) { return r.text(); })
      .then(function (t) { out.textContent = t; })
      .catch(function (e) { out.textContent = 'Error: ' + e; });
  };
})();
