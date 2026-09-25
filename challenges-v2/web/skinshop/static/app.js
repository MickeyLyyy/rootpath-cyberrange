// SkinShop front-end (legible a proposito)
function verItem(id) {
  var o = document.getElementById('out');
  o.textContent = '...';
  fetch('/item/' + id)
    .then(function (r) { return r.json(); })
    .then(function (j) {
      o.textContent = JSON.stringify(j, null, 2);
    });
}
