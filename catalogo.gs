// ============================================================
//  GLOBAL ELECTRONICS — Catálogo de Precios en Vivo
//  Deploy: Implementar > App web > Ejecutar como: Yo > Cualquier persona
// ============================================================

var SPREADSHEET_ID = '1hoE3vl1EzHy8VBdU82MeE-oc9pcwrfiStAe678F4R5o';
var BANNER_FILE_ID = '1J81QzHmeh6esiGHcZ3FIbG0u7bGeAMjT';

var SKU_IMAGES = {
  '40X60': '1DXKUz2NPnFWx-buwpYIG3EQFO7P_8i9q',
  '8 EN 1': '1Q-GXTORlHJBOfW1jZUaSohnOym1irSgZ',
  '10 EN 1': '1kDpvHuik2B3Lelp-ahL7vawu0JXPyAaj',
  'REPUESTOS MAY': '1EEg-Cy1tNETXkMluXStUegq4Y4A5ybT0',
  'CAJAS PARA IT': '1jZCAiw2q4OGe_2b21I7hoET7y0Q9cCz7',
  '4 EN 1': '13J9t85zm8tJnI240iK20woRH-w76p7FR',
  'TAZAS': '1chgAmPF7AJhjtujqSZv94lI2aGdTdNoj',
  'GORRA': '1GgkuK8maP98jsYmN67QAI1J8O7vpC4d1',
  '5 EN 1': '1Ju9I14shYbiONsVSNPd4GnqbnUTxVN4Q',
  'DOMÓTICA': '1LxnHa1L7Zbln3_5dqYJG35jP5iGvDbKc',
  'PORTA BANNER': '1GXU9gODF5RBfcwdEfcsQFfxT1EplTd69',
  'PLACA PVC': '16PGXaP0AwPLuHVM6hvDr6hLJihgVyqRv',
  'LUZ DE EMERGENCIA': '1Ob60OURUTtrkSAtXwnz_WkuVlD1w5ST6',
  'PISO VINILICO': '1eadiQDO-QyvWCOhXF_cB7KZgoZuv3MNU',
  'REVESTIMIENTO PARED': '1esivK7MLuqTX2tSFxeVwaCcMe_kQ77Pm',
  'CINTAS': '1XqZRPLqq8X5jkxpot1nww9V67VI3lOrF',
  'CARGADORES DE BATERÍA DE AUTO': '1skkwJzlNtxKNxhWsVZoje21jPWEFXtpO',
  'HERRAMIENTAS': '1HEstucgjCEghKoq3OuBINi5W_uruDl7B',
  'POLARIZADO': '1DKtjZY_jBLx9-KF0gj08tfGu1bybAFBz',
  'PPF': '1gcSyvjk_J4amBQfv_fH731z7MDuQaEjS',
  'PAPELES LL': '1o0Y792w7aIvymk3DfG2vcDUXRhuVd-4Z',
  'MATTE': '1x1IzHloxrkSXVsPBY3Qp6ygWQzDcWCNi',
  'TRANSPARENTE ': '1PwEzUuUhfyw4pTGfvYFrtBRlyI3ZygxN',
  'BASE AGUA': '1Ftt5ppezs2Cz3rMklVd7DuuLSXMbF4fo',
  'HOLOGRÁFICO': '1e4pj5FHZAzrpkaCKMXwqcyVIt7UTmcjx',
  'CANVAS': '1IWFrvKPTfwQ7ZNzSphunvbsy6jyTgDCR',
  'OBRA': '1jqIGXylv6QEr9NBNDWedFFTCyZtQ2sSH',
  'TATTOO': '1hed7yrSfkLUAWsQ6Vxd7l8OS9DFYusjc',
  'MAGNÉTICO': '1ahYWx8yuULhEY_pB6Ipg2YkdLt3Ypj2b',
  'LUSTER': '18BI6oWCRQP63W4SEJVFxuKl80ptqoezK',
  'KRAFT': '1utoll4iNdai4evqNwBHeeKzKQ4JqTPam',
  'TRANSFER': '1T3w4qCX7FzxsnOISnXOkl7NN3xAJuSQh',
  'SUBLIMACIÓN': '1oI4EX20iHFxDW6_l-VsiEYqSo01DGaRA',
  'GLOSSY': '1cLjyg5W0a9ItvTGa84J5t78krN6XvaKU',
  'FOILS': '1eRlzKo19o2dcZ4pC6SG0ysxH_jjdzf1Q',
  'ROLLOS': '171CAtRYdxd0PVnTIzzZYr2UaDYMrd3Fp',
  'REPUESTOS': '1n6eXxM66obbqgvpwNqgGkoGseaBSi0M9',
  'POUCH': '1cxYiRAsWmHTImriE3hxrEm6iln03Ixya',
  'LAMINADORAS': '17n3mXlmm4VOJKg72GFo3nlmWafJAWzFE',
  'ESPIRALADORAS': '1YSx7zuRPdy9Bb4VEcmoTZVzOM1RPB61h',
  'REGLA': '1XwGjI8hU9Fllk68KbhcUgJRLeqc0rKfP',
  'BISTURÍ': '1Cr9Zia5tqB2KTkyab1C2cilOnxN7a5fa',
  'CUTMAT': '1yvzAfpHHXO04ws28MXNFTRqQkfnEZ5_M',
  'GUILLOTINA': '1x4KPOfc2m0uB7dPpuERVauMSJwQpb1wx',
  'CUTTER': '18LSjzEVgDUY76XaxM69qcGLAjGLi0IN_',
  'ANILLADORAS': '1P17XFAy5cMGOrPsQQBD9U0ZDKM6noPVw',
  'PLOTTER DE CORTE': '1B6vDVSBBblilRlfoQtoTasuPwFKf3KdD',
  'CIZALLAS': '1v2Bw1lBj85szrZLzy_bGPDoboAQraU3m',
  'MÁQUINAS DE CÓSER ': '1_EzVK0wZsxfy8EZs0CxGvMGRfOxMetE-',
  'COMBOS': '1YvyUQF18j3qtKLBpTjzvz6Tp_IQrFP8C',
  'ANILLADORA': '1L0pkR_nOIGznFfsPZ7zKeEfX4qUh5wCg',
  'TINTAS': '1C68A8cRGzNz8iC9PyNRyO0gMUI6Ji9zy',
  'PORTADA ML': '1o_EjenFP6Bq0Ks1r2i_cAWU8Qr0Nl9FM',
  'PORTADA WEB': '131InxabZmTA96ELRwVh2SHCPuXRnm9QA',
  'PUPRINT': '1SgOIZSPqzc5NZEZQ4XSzM8L69fw2Lspn',
  'PVC': '1p7sOLZnKOebBABsC2hVkv3iTgeYvx4w3',
  'FLOCKPU': '1bn5p-ZADEhQ3HtCnCZKbmhzBFFT4L9Mn',
  '3DPUFF': '1GeT-4SRPlQsAM9WcYoIJPmOstna9jhy1',
  'PU': '1PcGlvf3mAXac435RqbjX4qC0OL3L02hG',
  'GLITPU': '1l9IDEHc-H7w2w66s6n55NwQDkKAlJSPb',
  'CHOPPSUB-GLS-FROST-16OZ': '1f1y7qBUBz2z0zhGDV8BTMD7k6vV27y94',
  'COMBOS PLANCHAS': '1xCWbeZYVsJkllZmg1qhhVzm4zPwVZbJ5',
  'REMERAS': '1A-IjM3sK-rxFjaR7p3PxYcjoa9BDsA7a',
  'TERMO': '14zYVp0n0SqsmPESJg8GYPVW7iItLEjH8',
  'TELA': '1rTG5YbkQ8X8IBn_OVNF2P_kgdso65k2S',
  'CENTRADO DE REMERAS': '1rgqU2_y7foT2C_3Rmzlid9Va3ysAmsCC',
  'GORRAS': '1UK3S9A0CEDPrKqjD4jTJLf3o8je8K6Cy',
  'ROMPECABEZAS': '1k1pZkPanu64UCPqgcG601UceYUJfti-n',
  'PLANCHAS': '1dHNLHT8mmZ86YHkAlmhpLdUwp-rUDoi8',
  'PAPELES': '1c5DlGzU1X3BiqXJJjFHMPaAntosBki5O',
  'PAPELES ROLLOS': '1ov3HQzyxmu9RRuajIRL1033J1d_c7olf',
  'LLAVEROS': '134Da6xs1_MhfVM93OiF_KIxHh_4L6U5U',
  'PORTA VASOS': '15oA7p3wf1yXShzvCVI8sHyBIaorD7FjI',
  'MOUSEPADS': '17Bwo2syH3F38qXzhujaV_ZP-Io2p4dmN',
  'BOTELLAS': '1PDYKUsaxc7SJNOHTepLZkIg9DwS3Fcaq'
};

function getImgUrl(sku) {
  var up = sku.toUpperCase();
  if (SKU_IMAGES[up]) return 'https://drive.google.com/thumbnail?id=' + SKU_IMAGES[up] + '&sz=w400';
  var keys = Object.keys(SKU_IMAGES);
  for (var i = 0; i < keys.length; i++) {
    if (up.indexOf(keys[i]) !== -1 || keys[i].indexOf(up) !== -1)
      return 'https://drive.google.com/thumbnail?id=' + SKU_IMAGES[keys[i]] + '&sz=w400';
  }
  return '';
}

function parseSheet(sheet) {
  var data = sheet.getDataRange();
  var rows = data.getValues();
  var formulas = data.getFormulas();

  // Build row (1-indexed) → image URL from floating over-grid images
  var rowImgMap = {};
  try {
    var imgs = sheet.getImages();
    for (var ii = 0; ii < imgs.length; ii++) {
      var r = imgs[ii].getAnchorCell().getRow();
      var u = '';
      try { u = imgs[ii].getUrl(); } catch(e) {}
      if (u) rowImgMap[r] = u;
    }
  } catch(e) {}

  var products = [], currentCat = '';
  for (var i = 0; i < rows.length; i++) {
    var row = rows[i];
    if (!row[0]) continue;
    var cell = String(row[0]).trim();
    if (cell === 'GLOBAL' || cell === 'SKU' || cell === 'Echeq 30' ||
        cell.indexOf('LISTA DE PRECIOS') !== -1 || cell.indexOf('Vigencia') !== -1) continue;
    if (row.length < 3 || !row[2]) { currentCat = cell; continue; }
    if (String(row[3]).indexOf('Cant') !== -1 || String(row[3]).indexOf('mt2') !== -1) continue;
    if (!row[2] || (String(row[2]) !== 'DISPONIBLE' && String(row[2]) !== 'SIN STOCK')) {
      currentCat = cell; continue;
    }

    // Try IMAGE formula in col J (index 9), then floating image
    var imgFromSheet = '';
    if (formulas[i] && formulas[i][9]) {
      var fm = formulas[i][9];
      var fm_match = fm.match(/IMAGE\(["\']([^"\']+)["\']/i);
      if (fm_match) imgFromSheet = fm_match[1];
    }
    if (!imgFromSheet && rowImgMap[i + 1]) imgFromSheet = rowImgMap[i + 1];

    products.push({
      sku: String(row[0]),
      nombre: String(row[1]),
      stock: String(row[2]),
      categoria: currentCat || sheet.getName(),
      cant1: String(row[3] || ''), precio1: String(row[4] || ''),
      cant2: String(row[5] || ''), precio2: String(row[6] || ''),
      cant3: String(row[7] || ''), precio3: String(row[8] || ''),
      imgFromSheet: imgFromSheet
    });
  }
  return products;
}

function formatPrice(pr) {
  if (!pr || pr === '-' || pr === '') return pr;
  var s = String(pr);
  var m = s.match(/^([A-Za-z$\s]*)([\d,.]+)(.*)/);
  if (!m) return pr;
  var num = parseFloat(m[2].replace(',', '.'));
  if (isNaN(num)) return pr;
  return m[1] + num.toFixed(2) + m[3];
}

function buildCard(p) {
  var avail = p.stock === 'DISPONIBLE';
  var img = p.imgFromSheet || getImgUrl(p.sku);
  var imgHtml = img
    ? '<img src="' + img + '" alt="' + p.sku + '" onerror="this.parentElement.innerHTML=\'<div class=no-img>📷</div>\'">'
    : '<div class="no-img">📷</div>';
  var badge = avail
    ? '<span class="avail">✓ Disponible</span>'
    : '<span class="unavail">✗ Sin stock</span>';
  var prices = '';
  var tiers = [[p.cant1,p.precio1],[p.cant2,p.precio2],[p.cant3,p.precio3]];
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
    + '<div class="card-body">'
    + '<div class="card-sku">' + p.sku + '</div>'
    + '<div class="card-name">' + nombre + '</div>'
    + badge
    + (prices ? '<div class="prices">' + prices + '</div>' : '')
    + '</div></div>';
}

function buildSection(sheetName, products) {
  var meta = {
    'Sublimación':               {icon:'🔥', color:'#FF6B35', label:'Sublimación'},
    'Laminación':                {icon:'✨', color:'#26A69A', label:'Laminación'},
    'Papelería':                 {icon:'📄', color:'#5C6BC0', label:'Papelería'},
    'Kraft':                     {icon:'📦', color:'#8D6E63', label:'Kraft'},
    'Domótica':                  {icon:'🏠', color:'#00897B', label:'Domótica'},
    'Automotor':                 {icon:'🚗', color:'#E53935', label:'Automotor'},
    'Revestimiento':             {icon:'🪟', color:'#7B1FA2', label:'Revestimiento'},
    'Cartelería':                {icon:'🖼️', color:'#F4511E', label:'Cartelería & Gran Formato'},
    'Vinilos Termotransferibles':{icon:'👕', color:'#D81B60', label:'Vinilos Termotransferibles'},
    'Combos':                    {icon:'🎁', color:'#00BCD4', label:'Combos'}
  };
  var m = meta[sheetName] || {icon:'📦', color:'#00BCD4', label:sheetName};
  var avail = products.filter(function(p){return p.stock==='DISPONIBLE';}).length;
  
  // Group by subcategory
  var byCat = {};
  var catOrder = [];
  for (var i = 0; i < products.length; i++) {
    var cat = products[i].categoria;
    if (!byCat[cat]) { byCat[cat] = []; catOrder.push(cat); }
    byCat[cat].push(products[i]);
  }
  
  var cardsHtml = '';
  for (var ci = 0; ci < catOrder.length; ci++) {
    var cat = catOrder[ci];
    var ps = byCat[cat];
    if (cat && cat !== sheetName) {
      cardsHtml += '<div class="subcat-label">' + cat + '</div>';
    }
    for (var pi = 0; pi < ps.length; pi++) {
      cardsHtml += buildCard(ps[pi]);
    }
  }
  
  return '<section class="cat-section" id="sec-' + sheetName.replace(/[^a-zA-Z]/g,'') + '">'
    + '<div class="cat-head" style="--accent:' + m.color + '">'
    + '<div class="cat-head-left">'
    + '<div class="cat-icon-wrap" style="background:' + m.color + '">' + m.icon + '</div>'
    + '<div><div class="cat-tag">Categoría</div>'
    + '<h2>' + m.label + '</h2></div></div>'
    + '<div class="cat-badge">' + avail + ' disponibles</div>'
    + '</div>'
    + '<div class="cards-grid">' + cardsHtml + '</div>'
    + '</section>';
}

function doGet() {
  var ss = SpreadsheetApp.openById(SPREADSHEET_ID);
  var vigencia = '';
  
  var sheetOrder = ['Sublimación','Laminación','Papelería','Kraft','Automotor',
                    'Domótica','Revestimiento','Cartelería','Vinilos Termotransferibles'];
  
  var navLinks = '';
  var sectionsHtml = '';
  
  for (var si = 0; si < sheetOrder.length; si++) {
    var sheetName = sheetOrder[si];
    var sheet = ss.getSheetByName(sheetName);
    if (!sheet) continue;
    
    // Get vigencia from row 3
    if (!vigencia) {
      var v = sheet.getRange('A3').getValue();
      vigencia = v ? String(v) : 'Mayo 2026';
    }
    
    var products = parseSheet(sheet);
    if (products.length === 0) continue;
    
    var meta = {
      'Sublimación':'🔥','Laminación':'✨','Papelería':'📄','Kraft':'📦',
      'Domótica':'🏠','Automotor':'🚗','Revestimiento':'🪟',
      'Cartelería':'🖼️','Vinilos Termotransferibles':'👕'
    };
    navLinks += '<a href="#sec-' + sheetName.replace(/[^a-zA-Z]/g,'') + '" class="nav-link">'
      + (meta[sheetName]||'📦') + ' ' + sheetName + '</a>';
    sectionsHtml += buildSection(sheetName, products);
  }
  
  var bannerUrl = 'https://drive.google.com/thumbnail?id=' + BANNER_FILE_ID + '&sz=w1200';
  
  var html = HtmlService.createHtmlOutput(getHtml(vigencia, navLinks, sectionsHtml, bannerUrl));
  html.setTitle('Catálogo Global Electronics');
  html.setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  return html;
}

function getHtml(vigencia, navLinks, sectionsHtml, bannerUrl) {
  return '<!DOCTYPE html><html lang="es"><head>'
  + '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
  + '<title>Catálogo Global Electronics</title>'
  + '<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap" rel="stylesheet">'
  + '<style>' + getCSS() + '</style></head><body>'
  
  // NAV
  + '<nav class="topnav"><div class="nav-logo"><img src="https://drive.google.com/thumbnail?id=1RNGyq8BzBzuo9KbDkelo8XgxcwYVVxn5&sz=w300" alt="Global Electronics"></div>'
  + '<div class="nav-links">' + navLinks + '</div>'
  + '<div class="nav-vigencia">📅 ' + vigencia + '</div></nav>'
  
  // COVER
  + '<div class="cover">'
  + '<div class="cover-eyebrow">📘 CATÁLOGO MAYORISTA</div>'
  + '<h1>Lista de Precios<em>Oficial</em></h1>'
  + '<p class="cover-sub">Equipos, insumos y artículos para profesionales del estampado, la impresión y la papelería.</p>'
  + '<div class="cover-banner"><img src="' + bannerUrl + '" alt="Productos Global Electronics"/></div>'
  + '<p class="cover-bottom">globalecom.ar · ' + vigencia + ' · Precios en USD sin IVA</p>'
  + '</div>'
  
  // SECTIONS
  + '<div class="catalog">' + sectionsHtml + '</div>'
  
  // FOOTER
  + '<footer><strong>Global Electronics</strong> · globalecom.ar<br>'
  + vigencia + ' · Precios en USD sin IVA · Sujeto a cambios sin previo aviso</footer>'
  + '</body></html>';
}

function getCSS() {
  return ':root{--teal:#00BCD4;--teal-dark:#0097A7;--teal-light:#E0F7FA;--text:#1C2B36;--gray:#6B7C8D;--bg:#F5F9FB;--white:#fff;--radius:16px}'
  + '*{box-sizing:border-box;margin:0;padding:0}'
  + 'body{font-family:Nunito,sans-serif;background:var(--bg);color:var(--text)}'
  
  + '.topnav{position:sticky;top:0;z-index:100;background:linear-gradient(135deg,#006064,#00BCD4);'
  + 'padding:12px 24px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;'
  + 'box-shadow:0 2px 12px rgba(0,0,0,.2)}'
  + '.nav-logo img{height:44px;width:auto;display:block}'
  + '.nav-links{display:flex;gap:8px;flex-wrap:wrap;flex:1}'
  + '.nav-link{background:rgba(255,255,255,.15);color:white;text-decoration:none;'
  + 'padding:6px 14px;border-radius:50px;font-size:.78rem;font-weight:700;'
  + 'transition:background .2s;white-space:nowrap}'
  + '.nav-link:hover{background:rgba(255,255,255,.3)}'
  + '.nav-vigencia{color:rgba(255,255,255,.7);font-size:.78rem;font-weight:700;white-space:nowrap}'
  
  + '.cover{background:linear-gradient(160deg,#006064 0%,#00BCD4 55%,#4DD0E1 100%);'
  + 'padding:60px 24px;display:flex;flex-direction:column;align-items:center;text-align:center}'
  + '.cover-eyebrow{background:rgba(255,255,255,.15);border:1.5px solid rgba(255,255,255,.3);'
  + 'color:white;padding:6px 18px;border-radius:50px;font-weight:800;font-size:.8rem;'
  + 'letter-spacing:2px;margin-bottom:16px}'
  + '.cover h1{color:white;font-size:clamp(2.5rem,6vw,5rem);font-weight:900;line-height:1.05;margin-bottom:12px}'
  + '.cover h1 em{font-style:normal;color:#B2EBF2;display:block;font-size:.7em}'
  + '.cover-sub{color:rgba(255,255,255,.8);font-size:1rem;max-width:500px;margin-bottom:32px;line-height:1.7}'
  + '.cover-banner{width:100%;max-width:900px;border-radius:16px;overflow:hidden;'
  + 'box-shadow:0 20px 60px rgba(0,0,0,.25);margin-bottom:32px}'
  + '.cover-banner img{width:100%;display:block}'
  + '.cover-bottom{color:rgba(255,255,255,.5);font-size:.8rem}'
  
  + '.catalog{max-width:1280px;margin:0 auto;padding:40px 16px}'
  + '.cat-section{background:white;border-radius:20px;margin-bottom:36px;'
  + 'box-shadow:0 2px 16px rgba(0,0,0,.06);overflow:hidden}'
  + '.cat-head{padding:24px 28px;display:flex;align-items:center;justify-content:space-between;'
  + 'gap:16px;flex-wrap:wrap;border-left:6px solid var(--accent)}'
  + '.cat-head-left{display:flex;align-items:center;gap:16px}'
  + '.cat-icon-wrap{width:56px;height:56px;border-radius:14px;display:flex;align-items:center;'
  + 'justify-content:center;font-size:1.8rem;flex-shrink:0}'
  + '.cat-tag{font-size:.68rem;font-weight:900;letter-spacing:2px;color:var(--gray);text-transform:uppercase;margin-bottom:2px}'
  + '.cat-head h2{font-size:1.4rem;font-weight:900;color:var(--text)}'
  + '.cat-badge{background:var(--teal-light);color:var(--teal-dark);padding:6px 16px;'
  + 'border-radius:50px;font-weight:800;font-size:.8rem;white-space:nowrap}'
  
  + '.subcat-label{grid-column:1/-1;background:#F0F4F8;padding:10px 16px;'
  + 'font-size:.78rem;font-weight:900;color:var(--gray);text-transform:uppercase;letter-spacing:1px}'
  
  + '.cards-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));'
  + 'gap:1px;background:#F0F4F8}'
  + '.card{background:white;display:flex;flex-direction:column;transition:box-shadow .2s}'
  + '.card:hover{box-shadow:0 6px 24px rgba(0,188,212,.15);z-index:1;position:relative}'
  + '.card.dim{opacity:.4}'
  + '.card-img{height:180px;overflow:hidden;background:#F5F9FB;display:flex;'
  + 'align-items:center;justify-content:center}'
  + '.card-img img{width:100%;height:100%;object-fit:cover;transition:transform .3s}'
  + '.card:hover .card-img img{transform:scale(1.05)}'
  + '.no-img{font-size:3rem;color:#CBD5E0}'
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
  + '@media(max-width:600px){.topnav{flex-direction:column;align-items:flex-start}'
  + '.cards-grid{grid-template-columns:repeat(auto-fill,minmax(150px,1fr))}}';
}
