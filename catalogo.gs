// ============================================================
//  GLOBAL ELECTRONICS — Catálogo de Precios en Vivo
//  Deploy: Implementar > App web > Ejecutar como: Yo > Cualquier persona
// ============================================================

var SPREADSHEET_ID   = '1hoE3vl1EzHy8VBdU82MeE-oc9pcwrfiStAe678F4R5o';
var BANNER_FILE_ID   = '1J81QzHmeh6esiGHcZ3FIbG0u7bGeAMjT';
var LOGO_FILE_ID     = '1RNGyq8BzBzuo9KbDkelo8XgxcwYVVxn5';
var SKU_MAPPING_FILE = '1D48rIJhPlav7wYsRRM09ih65v3nAvWcy'; // sku_mapping.json en Drive

// ---------------------------------------------------------------
// SKU map — cargado desde Drive, cacheado 24 h
// ---------------------------------------------------------------

function getSkuMap() {
  var cache = CacheService.getScriptCache();
  var hit   = cache.get('sku_map');
  if (hit) return JSON.parse(hit);
  var text = DriveApp.getFileById(SKU_MAPPING_FILE).getBlob().getDataAsString();
  var map  = JSON.parse(text);
  try { cache.put('sku_map', text, 86400); } catch(e) {}
  return map;
}

function findFileIdForSku(sku) {
  if (!sku) return null;
  var s   = sku.trim().toUpperCase();
  var map = getSkuMap();
  var keys = Object.keys(map);

  for (var i = 0; i < keys.length; i++) {
    if (keys[i].toUpperCase() === s) return map[keys[i]];
  }

  var parts = s.split('-');
  for (var si = parts.length - 1; si >= 1; si--) {
    var cand = parts.slice(0, si).join('-');
    for (var j = 0; j < keys.length; j++) {
      if (keys[j].toUpperCase() === cand) return map[keys[j]];
    }
  }

  var best = null, bestLen = 0;
  for (var ki = 0; ki < keys.length; ki++) {
    var ku = keys[ki].toUpperCase();
    if (s.indexOf(ku) === 0 && ku.length > bestLen) { best = keys[ki]; bestLen = ku.length; }
  }
  return best ? map[best] : null;
}

// ---------------------------------------------------------------
// Logo
// ---------------------------------------------------------------

function getLogoDataUrl() {
  try {
    var cache = CacheService.getScriptCache();
    var cached = cache.get('global_logo_b64');
    if (cached) return cached;
    var resp = UrlFetchApp.fetch(
      'https://drive.google.com/thumbnail?id=' + LOGO_FILE_ID + '&sz=w220',
      {headers: {Authorization: 'Bearer ' + ScriptApp.getOAuthToken()}, muteHttpExceptions: true}
    );
    if (resp.getResponseCode() !== 200) return '';
    var ct = resp.getBlob().getContentType() || 'image/png';
    var dataUrl = 'data:' + ct + ';base64,' + Utilities.base64Encode(resp.getBlob().getBytes());
    cache.put('global_logo_b64', dataUrl, 3600);
    return dataUrl;
  } catch(e) { return ''; }
}

// ---------------------------------------------------------------
// Imágenes lazy (llamado desde el cliente via google.script.run)
// ---------------------------------------------------------------

function getSheetImages(sheetName) {
  var result = {};
  var token  = ScriptApp.getOAuthToken();
  var cache  = CacheService.getScriptCache();
  var sheet  = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(sheetName);
  if (!sheet) return {};

  var values = sheet.getDataRange().getValues();
  var fileIdToRows = {}, rowToFileId = {};

  for (var vi = 0; vi < values.length; vi++) {
    var v = values[vi][0];
    if (!v) continue;
    var sku    = String(v).trim();
    var row    = vi + 1;
    var fileId = findFileIdForSku(sku);
    if (!fileId) continue;
    rowToFileId[row] = fileId;
    if (!fileIdToRows[fileId]) fileIdToRows[fileId] = [];
    fileIdToRows[fileId].push(row);
  }

  var fileIds = Object.keys(fileIdToRows);
  if (fileIds.length === 0) return {};

  var cacheKeys    = fileIds.map(function(id){ return 'drv_' + id; });
  var cachedValues = cache.getAll(cacheKeys);
  var needFetch    = [];

  for (var fi = 0; fi < fileIds.length; fi++) {
    var fid  = fileIds[fi];
    var cval = cachedValues['drv_' + fid];
    if (cval) {
      var rows = fileIdToRows[fid];
      for (var ri = 0; ri < rows.length; ri++) result[rows[ri]] = cval;
    } else { needFetch.push(fid); }
  }

  if (needFetch.length === 0) return result;

  var requests = needFetch.map(function(fid) {
    return {
      url: 'https://drive.google.com/thumbnail?id=' + fid + '&sz=w400',
      headers: {Authorization: 'Bearer ' + token},
      muteHttpExceptions: true
    };
  });

  var responses = UrlFetchApp.fetchAll(requests);

  for (var ri2 = 0; ri2 < responses.length; ri2++) {
    var resp = responses[ri2];
    var fid  = needFetch[ri2];
    if (resp.getResponseCode() !== 200) continue;
    var blob    = resp.getBlob();
    var ct      = blob.getContentType() || 'image/jpeg';
    var dataUrl = 'data:' + ct + ';base64,' + Utilities.base64Encode(blob.getBytes());
    var rows2 = fileIdToRows[fid];
    for (var ri3 = 0; ri3 < rows2.length; ri3++) result[rows2[ri3]] = dataUrl;
    if (dataUrl.length < 95000) cache.put('drv_' + fid, dataUrl, 86400);
  }

  return result;
}

// ---------------------------------------------------------------
// Parseo de hojas
// ---------------------------------------------------------------

function parseSheet(sheet) {
  var data     = sheet.getDataRange();
  var rows     = data.getValues();
  var formulas = data.getFormulas();
  var products = [], currentCat = '';

  for (var i = 0; i < rows.length; i++) {
    var row  = rows[i];
    if (!row[0]) continue;
    var cell = String(row[0]).trim();
    if (cell === 'GLOBAL' || cell === 'SKU' || cell === 'Echeq 30' ||
        cell.indexOf('LISTA DE PRECIOS') !== -1 || cell.indexOf('Vigencia') !== -1) continue;
    if (row.length < 3 || !row[2]) { currentCat = cell; continue; }
    if (String(row[3]).indexOf('Cant') !== -1 || String(row[3]).indexOf('mt2') !== -1) continue;
    if (String(row[2]) !== 'DISPONIBLE' && String(row[2]) !== 'SIN STOCK') {
      currentCat = cell; continue;
    }
    var imgUrl = '';
    if (formulas[i] && formulas[i][9]) {
      var m = formulas[i][9].match(/IMAGE\(["\']([^"\']+)["\']/i);
      if (m) imgUrl = m[1];
    }
    products.push({
      sku: String(row[0]), nombre: String(row[1]), stock: String(row[2]),
      categoria: currentCat || sheet.getName(),
      cant1: String(row[3]||''), precio1: String(row[4]||''),
      cant2: String(row[5]||''), precio2: String(row[6]||''),
      cant3: String(row[7]||''), precio3: String(row[8]||''),
      sheetRow: i + 1, imgUrl: imgUrl
    });
  }
  return products;
}

// ---------------------------------------------------------------
// Renderizado
// ---------------------------------------------------------------

function formatPrice(pr) {
  if (!pr || pr === '-' || pr === '') return pr;
  var s = String(pr);
  var m = s.match(/^([A-Za-z$\s]*)([\d,.]+)(.*)/);
  if (!m) return pr;
  var num = parseFloat(m[2].replace(',', '.'));
  if (isNaN(num)) return pr;
  return m[1] + num.toFixed(2) + m[3];
}

function buildCard(p, sheetName) {
  var avail   = p.stock === 'DISPONIBLE';
  var imgHtml = '<img src="" class="lazy-img" data-sheet="' + sheetName + '" data-row="' + p.sheetRow + '" alt="' + p.sku + '">';
  var badge  = avail ? '<span class="avail">✓ Disponible</span>' : '<span class="unavail">✗ Sin stock</span>';
  var prices = '';
  var tiers  = [[p.cant1,p.precio1],[p.cant2,p.precio2],[p.cant3,p.precio3]];
  for (var t = 0; t < tiers.length; t++) {
    var c = tiers[t][0], pr = tiers[t][1];
    if (pr && pr !== '-' && pr !== '') {
      var cls = t === 1 ? ' price-best' : '';
      prices += '<div class="price-row' + cls + '"><span>x' + c + ' u.</span><span>' + formatPrice(pr) + '</span></div>';
    }
  }
  var nombre = p.nombre.length > 72 ? p.nombre.substring(0, 72) + '…' : p.nombre;
  return '<div class="card' + (avail ? '' : ' dim') + '">'
    + '<div class="card-img">' + imgHtml + '</div>'
    + '<div class="card-body"><div class="card-sku">' + p.sku + '</div>'
    + '<div class="card-name">' + nombre + '</div>' + badge
    + (prices ? '<div class="prices">' + prices + '</div>' : '')
    + '</div></div>';
}

function buildSection(sheetName, products) {
  var meta = {
    'Sublimación':               {icon:'🔥', color:'#FF6B35'},
    'Laminación':                {icon:'✨', color:'#26A69A'},
    'Papelería':                 {icon:'📄', color:'#5C6BC0'},
    'Kraft':                     {icon:'📦', color:'#8D6E63'},
    'Domótica':                  {icon:'🏠', color:'#00897B'},
    'Automotor':                 {icon:'🚗', color:'#E53935'},
    'Revestimiento':             {icon:'🪟', color:'#7B1FA2'},
    'Cartelería':                {icon:'🖼️', color:'#F4511E', label:'Cartelería & Gran Formato'},
    'Vinilos Termotransferibles':{icon:'👕', color:'#D81B60'}
  };
  var m     = meta[sheetName] || {icon:'📦', color:'#00BCD4'};
  var label = m.label || sheetName;
  var avail = products.filter(function(p){return p.stock==='DISPONIBLE';}).length;
  var byCat = {}, catOrder = [];
  for (var i = 0; i < products.length; i++) {
    var cat = products[i].categoria;
    if (!byCat[cat]) { byCat[cat] = []; catOrder.push(cat); }
    byCat[cat].push(products[i]);
  }
  var cardsHtml = '';
  for (var ci = 0; ci < catOrder.length; ci++) {
    var cat = catOrder[ci];
    if (cat && cat !== sheetName) cardsHtml += '<div class="subcat-label">' + cat + '</div>';
    for (var pi = 0; pi < byCat[cat].length; pi++) cardsHtml += buildCard(byCat[cat][pi], sheetName);
  }
  return '<section class="cat-section" id="sec-' + sheetName.replace(/[^a-zA-Z]/g,'') + '">'
    + '<div class="cat-head" style="--accent:' + m.color + '">'
    + '<div class="cat-head-left"><div class="cat-icon-wrap" style="background:' + m.color + '">' + m.icon + '</div>'
    + '<div><div class="cat-tag">Categoría</div><h2>' + label + '</h2></div></div>'
    + '<div class="cat-badge">' + avail + ' disponibles</div></div>'
    + '<div class="cards-grid">' + cardsHtml + '</div></section>';
}

// ---------------------------------------------------------------
// Entry point
// ---------------------------------------------------------------

function doGet() {
  var ss         = SpreadsheetApp.openById(SPREADSHEET_ID);
  var vigencia   = '';
  var sheetOrder = ['Sublimación','Laminación','Papelería','Kraft','Automotor',
                    'Domótica','Revestimiento','Cartelería','Vinilos Termotransferibles'];
  var navLinks = '', sectionsHtml = '';
  var icons = {'Sublimación':'🔥','Laminación':'✨','Papelería':'📄','Kraft':'📦',
               'Domótica':'🏠','Automotor':'🚗','Revestimiento':'🪟',
               'Cartelería':'🖼️','Vinilos Termotransferibles':'👕'};

  for (var si = 0; si < sheetOrder.length; si++) {
    var sheetName = sheetOrder[si];
    var sheet     = ss.getSheetByName(sheetName);
    if (!sheet) continue;
    if (!vigencia) {
      var v = sheet.getRange('A3').getValue();
      vigencia = v ? String(v) : 'Junio 2026';
    }
    var products = parseSheet(sheet);
    if (products.length === 0) continue;
    navLinks     += '<a href="#sec-' + sheetName.replace(/[^a-zA-Z]/g,'') + '" class="nav-link">' + (icons[sheetName]||'📦') + ' ' + sheetName + '</a>';
    sectionsHtml += buildSection(sheetName, products);
  }

  var logoDataUrl = getLogoDataUrl();
  var bannerUrl   = 'https://drive.google.com/thumbnail?id=' + BANNER_FILE_ID + '&sz=w1200';
  var html = HtmlService.createHtmlOutput(getHtml(vigencia, navLinks, sectionsHtml, bannerUrl, logoDataUrl, JSON.stringify(sheetOrder)));
  html.setTitle('Catálogo Global Electronics');
  html.setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  return html;
}

// ---------------------------------------------------------------
// HTML + CSS
// ---------------------------------------------------------------

function getHtml(vigencia, navLinks, sectionsHtml, bannerUrl, logoDataUrl, sheetOrderJson) {
  var logoHtml = logoDataUrl
    ? '<img src="' + logoDataUrl + '" alt="Global Electronics" class="logo-img">'
    : '<svg class="logo-img" viewBox="0 0 160 52" xmlns="http://www.w3.org/2000/svg">'
      + '<rect width="160" height="52" rx="8" fill="rgba(255,255,255,.2)"/>'
      + '<text x="80" y="30" text-anchor="middle" font-family="Nunito,sans-serif" font-weight="900" font-size="24" fill="white">Global</text>'
      + '<text x="80" y="45" text-anchor="middle" font-family="Nunito,sans-serif" font-weight="700" font-size="10" fill="rgba(255,255,255,.75)" letter-spacing="2">ELECTRONICS</text>'
      + '</svg>';

  var lazyScript = '<script>(function(){'
    + 'if(typeof google==="undefined"||!google.script)return;'
    + 'var sheets=' + sheetOrderJson + ';'
    + 'function load(sn){google.script.run'
    + '.withSuccessHandler((function(s){return function(m){'
    + 'if(!m)return;var rows=Object.keys(m);'
    + 'for(var i=0;i<rows.length;i++){'
    + 'var imgs=document.querySelectorAll(\'.lazy-img[data-sheet="\'+s+\'"][data-row="\'+rows[i]+\'"]\');'
    + 'for(var j=0;j<imgs.length;j++)imgs[j].src=m[rows[i]];}'
    + '};})(sn)).withFailureHandler(function(){}).getSheetImages(sn);}'
    + 'if(document.readyState==="loading"){document.addEventListener("DOMContentLoaded",function(){sheets.forEach(load);});}'
    + 'else{sheets.forEach(load);}})();<\/script>';

  return '<!DOCTYPE html><html lang="es"><head>'
    + '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    + '<title>Catálogo Global Electronics</title>'
    + '<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap" rel="stylesheet">'
    + '<style>' + getCSS() + '</style></head><body>'
    + '<nav class="topnav"><div class="nav-logo">' + logoHtml + '</div>'
    + '<div class="nav-links">' + navLinks + '</div>'
    + '<div class="nav-vigencia">📅 ' + vigencia + '</div></nav>'
    + '<div class="cover"><div class="cover-eyebrow">📘 CATÁLOGO MAYORISTA</div>'
    + '<h1>Lista de Precios<em>Oficial</em></h1>'
    + '<p class="cover-sub">Equipos, insumos y artículos para profesionales del estampado, la impresión y la papelería.</p>'
    + '<div class="cover-banner"><img src="' + bannerUrl + '" alt="Productos Global Electronics"/></div>'
    + '<p class="cover-bottom">globalecom.ar · ' + vigencia + ' · Precios en USD sin IVA</p></div>'
    + '<div class="catalog">' + sectionsHtml + '</div>'
    + '<footer><strong>Global Electronics</strong> · globalecom.ar<br>'
    + vigencia + ' · Precios en USD sin IVA · Sujeto a cambios sin previo aviso</footer>'
    + lazyScript + '</body></html>';
}

function getCSS() {
  return ':root{--teal:#00BCD4;--teal-dark:#0097A7;--teal-light:#E0F7FA;--text:#1C2B36;--gray:#6B7C8D;--bg:#F5F9FB;--white:#fff;--radius:16px}'
    + '*{box-sizing:border-box;margin:0;padding:0}'
    + 'body{font-family:Nunito,sans-serif;background:var(--bg);color:var(--text)}'
    + '.topnav{position:sticky;top:0;z-index:100;background:linear-gradient(135deg,#006064,#00BCD4);padding:12px 24px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;box-shadow:0 2px 12px rgba(0,0,0,.2)}'
    + '.nav-logo{display:flex;align-items:center}.logo-img{height:44px;width:auto;display:block}'
    + '.nav-links{display:flex;gap:8px;flex-wrap:wrap;flex:1}'
    + '.nav-link{background:rgba(255,255,255,.15);color:white;text-decoration:none;padding:6px 14px;border-radius:50px;font-size:.78rem;font-weight:700;transition:background .2s;white-space:nowrap}'
    + '.nav-link:hover{background:rgba(255,255,255,.3)}'
    + '.nav-vigencia{color:rgba(255,255,255,.7);font-size:.78rem;font-weight:700;white-space:nowrap}'
    + '.cover{background:linear-gradient(160deg,#006064 0%,#00BCD4 55%,#4DD0E1 100%);padding:60px 24px;display:flex;flex-direction:column;align-items:center;text-align:center}'
    + '.cover-eyebrow{background:rgba(255,255,255,.15);border:1.5px solid rgba(255,255,255,.3);color:white;padding:6px 18px;border-radius:50px;font-weight:800;font-size:.8rem;letter-spacing:2px;margin-bottom:16px}'
    + '.cover h1{color:white;font-size:clamp(2.5rem,6vw,5rem);font-weight:900;line-height:1.05;margin-bottom:12px}'
    + '.cover h1 em{font-style:normal;color:#B2EBF2;display:block;font-size:.7em}'
    + '.cover-sub{color:rgba(255,255,255,.8);font-size:1rem;max-width:500px;margin-bottom:32px;line-height:1.7}'
    + '.cover-banner{width:100%;max-width:900px;border-radius:16px;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.25);margin-bottom:32px}'
    + '.cover-banner img{width:100%;display:block}.cover-bottom{color:rgba(255,255,255,.5);font-size:.8rem}'
    + '.catalog{max-width:1280px;margin:0 auto;padding:40px 16px}'
    + '.cat-section{background:white;border-radius:20px;margin-bottom:36px;box-shadow:0 2px 16px rgba(0,0,0,.06);overflow:hidden}'
    + '.cat-head{padding:24px 28px;display:flex;align-items:center;justify-content:space-between;gap:16px;flex-wrap:wrap;border-left:6px solid var(--accent)}'
    + '.cat-head-left{display:flex;align-items:center;gap:16px}'
    + '.cat-icon-wrap{width:56px;height:56px;border-radius:14px;display:flex;align-items:center;justify-content:center;font-size:1.8rem;flex-shrink:0}'
    + '.cat-tag{font-size:.68rem;font-weight:900;letter-spacing:2px;color:var(--gray);text-transform:uppercase;margin-bottom:2px}'
    + '.cat-head h2{font-size:1.4rem;font-weight:900;color:var(--text)}'
    + '.cat-badge{background:var(--teal-light);color:var(--teal-dark);padding:6px 16px;border-radius:50px;font-weight:800;font-size:.8rem;white-space:nowrap}'
    + '.subcat-label{grid-column:1/-1;background:#F0F4F8;padding:10px 16px;font-size:.78rem;font-weight:900;color:var(--gray);text-transform:uppercase;letter-spacing:1px}'
    + '.cards-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:1px;background:#F0F4F8}'
    + '.card{background:white;display:flex;flex-direction:column;transition:box-shadow .2s}'
    + '.card:hover{box-shadow:0 6px 24px rgba(0,188,212,.15);z-index:1;position:relative}'
    + '.card.dim{opacity:.4}'
    + '.card-img{height:180px;overflow:hidden;background:#F5F9FB;display:flex;align-items:center;justify-content:center}'
    + '.card-img img{width:100%;height:100%;object-fit:cover;transition:transform .3s}'
    + '.card-img img:not([src]){display:none}.card-img img[src=""]{display:none}'
    + '.card:hover .card-img img{transform:scale(1.05)}'
    + '.card-body{padding:12px;display:flex;flex-direction:column;gap:6px;flex:1}'
    + '.card-sku{font-size:.66rem;color:var(--teal-dark);font-weight:900;letter-spacing:.5px;text-transform:uppercase}'
    + '.card-name{font-size:.8rem;color:var(--text);font-weight:600;line-height:1.4;flex:1}'
    + '.avail{background:#E8F5E9;color:#2E7D32;font-size:.68rem;font-weight:800;padding:2px 8px;border-radius:20px;width:fit-content}'
    + '.unavail{background:#FFEBEE;color:#C62828;font-size:.68rem;font-weight:800;padding:2px 8px;border-radius:20px;width:fit-content}'
    + '.prices{display:flex;flex-direction:column;gap:2px;margin-top:2px}'
    + '.price-row{display:flex;justify-content:space-between;font-size:.74rem;padding:3px 6px;border-radius:6px;background:#F5F9FB}'
    + '.price-best{background:var(--teal-light);font-weight:800;color:var(--teal-dark)}'
    + 'footer{background:#0E1F26;color:rgba(255,255,255,.5);padding:28px;text-align:center;font-size:.8rem}'
    + 'footer strong{color:white}'
    + '@media(max-width:600px){.topnav{flex-direction:column;align-items:flex-start}.cards-grid{grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}}';
}

// ---------------------------------------------------------------
// Limpia TODOS los cachés: sku_map + todas las miniaturas drv_FILEID
// Ejecutar manualmente desde el editor si se actualizaron imágenes en Drive
// ---------------------------------------------------------------
function clearAllCaches() {
  var cache = CacheService.getScriptCache();
  var fixed = ['sku_map', 'global_logo_b64'];
  cache.removeAll(fixed);

  // Leer el mapa directamente de Drive (sin caché) para obtener todos los fileIds
  try {
    var text    = DriveApp.getFileById(SKU_MAPPING_FILE).getBlob().getDataAsString();
    var map     = JSON.parse(text);
    var fileIds = Object.keys(map).map(function(k){ return map[k]; });
    // Deduplicar
    var seen = {}, unique = [];
    for (var i = 0; i < fileIds.length; i++) {
      if (!seen[fileIds[i]]) { seen[fileIds[i]] = true; unique.push('drv_' + fileIds[i]); }
    }
    // removeAll acepta max 1000 keys a la vez
    var BATCH = 500;
    for (var b = 0; b < unique.length; b += BATCH) {
      cache.removeAll(unique.slice(b, b + BATCH));
    }
    Logger.log('Cachés eliminados: ' + fixed.length + ' fijos + ' + unique.length + ' imágenes');
  } catch(e) {
    Logger.log('clearAllCaches error: ' + e);
  }
}
