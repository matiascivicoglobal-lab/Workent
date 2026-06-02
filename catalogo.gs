// ============================================================
//  GLOBAL ELECTRONICS — Catálogo de Precios en Vivo
//  Deploy: Implementar > App web > Ejecutar como: Yo > Cualquier persona
// ============================================================

var SPREADSHEET_ID = '1hoE3vl1EzHy8VBdU82MeE-oc9pcwrfiStAe678F4R5o';
var BANNER_FILE_ID  = '1J81QzHmeh6esiGHcZ3FIbG0u7bGeAMjT';
var LOGO_FILE_ID    = '1RNGyq8BzBzuo9KbDkelo8XgxcwYVVxn5';

// ---------------------------------------------------------------
// Logo — lo busca en Drive al momento de renderizar el servidor,
// lo convierte a base64 y lo cachea 1 hora.
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
  } catch(e) {
    return '';
  }
}

// ---------------------------------------------------------------
// SKU → Drive file ID map (288 imágenes desde CATEGORÍAS MATIAS PM)
// ---------------------------------------------------------------

var SKU_IMAGES = {
  '10 EN 1': '1kDpvHuik2B3Lelp-ahL7vawu0JXPyAaj',
  '1000ML GLOBAL': '1RM7RBdURk5QidFripdy2RgpIn01eC2m1',
  '100ML GLOBAL': '1C68A8cRGzNz8iC9PyNRyO0gMUI6Ji9zy',
  '250ML GLOBAL': '1AiauCSpP44hIUPzhStwNRT8yHJTFQF4n',
  '4 EN 1': '13J9t85zm8tJnI240iK20woRH-w76p7FR',
  '40X60': '1DXKUz2NPnFWx-buwpYIG3EQFO7P_8i9q',
  '5 EN 1': '1Ju9I14shYbiONsVSNPd4GnqbnUTxVN4Q',
  '8 EN 1': '1Q-GXTORlHJBOfW1jZUaSohnOym1irSgZ',
  'ANILLADORAALAMBRE-M-A4': '1L0pkR_nOIGznFfsPZ7zKeEfX4qUh5wCg',
  'ASPIROBOTV6SPRO-BK': '17mDS6SgYt1tqcYvvpZ6pZfi1DQQqnzqz',
  'AUTOR-75G-A4': '1X4LP_7_IQ2z_EqkmdpWoLRYOkvSw5O56',
  'AUTOR-75G-OF': '1jqIGXylv6QEr9NBNDWedFFTCyZtQ2sSH',
  'AUTOR-80G-A4': '1D2tkfzJkjdGmHv_bDm93EqslEGKhHL-E',
  'AUTOR-80G-OF': '1pp0I-KX7hL7zuqftZjYvpTObQBgV4TRp',
  'BOTSUB-ALU-2TOPS-500ML-W': '1D8S5eNoFVDSbf2Ux7QxDgr-ZYvjjAv2I',
  'BOTSUB-ALU-PORTLID-500ML-W': '1gUmvDMvFNboS_HsbR8sAMrI2GydqLpCE',
  'BOTSUB-ALU-SPORTCAP-500ML-W': '1PDYKUsaxc7SJNOHTepLZkIg9DwS3Fcaq',
  'CAJAS PARA IT': '1jZCAiw2q4OGe_2b21I7hoET7y0Q9cCz7',
  'CHOPPSUB-GLS-FROST-16OZ': '1f1y7qBUBz2z0zhGDV8BTMD7k6vV27y94',
  'CINTACORTE-UCN015-50M': '1XqZRPLqq8X5jkxpot1nww9V67VI3lOrF',
  'CINTACORTE-UCN015-5M': '1JqJORowGBCxf7RccM8N6X9Adi01Rq8mZ',
  'CIZALLA-130CM': '1v2Bw1lBj85szrZLzy_bGPDoboAQraU3m',
  'CIZALLA-A4-12EN1': '1DpIzYITe3cV1497SROFCBDSUh2wk8s_z',
  'CIZALLA-A4-5EN1': '1X20lo8huN9FDMhmMMrIg5g62rL22mPMC',
  'CIZALLA-A4-PORTATIL': '1D1eT6ghXuFvkzR_XgPO_U-nU-zHfaudb',
  'COFMUGSUB-DTEMP-500ML-W': '15-RcGZ5tVPR1Dohll2nt0I2FLBqFyi3o',
  'COMBO PLANCHA-SUB-30X38': '1jEGK6ik7VC6lgfFf6EN_4tze4ipxdGuU',
  'COMBO PLANCHA-SUB-30X38-10EN1': '12MeVGKlTyqO4snX80ElOxRbf_Wnr7z7o',
  'COMBO PLANCHA-SUB-30X38-5EN1': '1HUeX5gpQNXVrZwbuly-FNXshXiwbHnvc',
  'COMBO PLANCHA-SUB-40X60': '1k6ePNnAa6vAJ0g-HK2vJ8JS3wxgofyyL',
  'COMBO PLANCHA-SUB-AUTO-GORRA': '1xCWbeZYVsJkllZmg1qhhVzm4zPwVZbJ5',
  'COMBO PLANCHA-SUB-GORRA': '1IZxFE7JnBWXlQtrW8sNw0ZVCyEX0LtOp',
  'COMBO PLANCHA-SUB-TAZA': '1s6CGOoxpvyjqn1iVFxOjaRe823Nq1yPX',
  'COMBO PLANCHA-SUB-TERMO': '16r3Q3pVnOxM6bVALwO5vH2L02MZjeq2v',
  'CRAFTKNIFE': '1Cr9Zia5tqB2KTkyab1C2cilOnxN7a5fa',
  'CUTMAT / CUTTERROTA-45MM CRAFTKNIFE / WEEDINGTOOLS-SETX6': '1YvyUQF18j3qtKLBpTjzvz6Tp_IQrFP8C',
  'CUTTER-UCN001': '1V08eFkp8Dw1oL5nIrJ9wKCYyjOs-zK8o',
  'CUTTER-UCN003N': '18LSjzEVgDUY76XaxM69qcGLAjGLi0IN_',
  'CUTTERCIRCLE': '1hLaC9WzkEHBrWCE06JlAK0aLkw6JkH8b',
  'CUTTERROTA-45MM': '1InN6drzjVs-6H1cU9u6DEhxpLDFWcEXD',
  'DOBLEWIRE-2:1-M-A4': '1Ml7c3rBII5thUVQmXeOsKnuWTq8emAt-',
  'DUPLITUC-70G-A4': '1wsxiPLlDPN1FE5YUMT3ObAgu0YlyOhWi',
  'EMERLIGHT-30LED': '1LqdJMLsfKeKTbDKOlHKnLYosAN9CP8tr',
  'EMERLIGHT-60LED': '1Ob60OURUTtrkSAtXwnz_WkuVlD1w5ST6',
  'ESCOBILLA-UA14-21CM': '1HEstucgjCEghKoq3OuBINi5W_uruDl7B',
  'ESPIRALADORA-M-A4': '17Eu4Q7sjYnGL__lFu8A65YSeYILSLEnG',
  'ESPIRALADORA-M-A4-2': '1YSx7zuRPdy9Bb4VEcmoTZVzOM1RPB61h',
  'ESPIRALADORA-M-A4-R': '1Uhs-PcBS4l97GQ0wxiZ3ZKCKm6TAZwwz',
  'EXPANSIONDISC-A4-G': '1tgoNBts59MalLq5wP7jyHB1X7O_KJVyW',
  'EXPANSIONDISC-A4-P': '1m7O3Dtqnoq6VcJsaQsBrQO37T0zTxODy',
  'EXPDISC-32MM-X11': '1P17XFAy5cMGOrPsQQBD9U0ZDKM6noPVw',
  'EXPDISC-CORA-24MM-X11': '1bh5758SLWt5Osbghb9TkptHIsDwEEkdt',
  'FOILBLACK-G-32X6MT': '16msF6qZ9nyq_XwlvFve2oHVC9vTndJNK',
  'FOILBLUE-G-32X6MT': '1NH_i-00Tt7w4XBI79M13XaIb5vbPdfyj',
  'FOILCOPPER-G-32X6MT': '1hwp7enm17MpltVfRtcIxVX3r0AxF2Y4h',
  'FOILGOLD-G-32X6MT': '1VLxo6u1PJoYe7ZBK2E5rXwWFoj53LF9X',
  'FOILGOLD-M-32X6MT': '1DmH5W2JwKHNpygCP81-XEE95zkG_kHxw',
  'FOILGREEN-G-32X6MT': '1VO_fwJdFomDqiTpuxX-xQU0N_BO5WHsI',
  'FOILHOLOBLUERAINBOW-G-32X6MT': '1B5FbiADDCx946Nn4OywJmiOqhHKKKiyQ',
  'FOILHOLOGOLDRAINBOW-G-32X6MT': '16Pla6Fp812Ch_4R0jTbPQ5SiNGFmS9TO',
  'FOILHOLOMULTICOLOR-G-32X6MT': '18fzL5Xc-Rqnw2Nyw5POZ0FGmIjiCXE4O',
  'FOILHOLOSILVERRAINBOW-G-32X6MT': '1z4zjPs2l_oZwx3ZJfwPaLwhWkVAGbWbj',
  'FOILMINTBLUE-G-32X6MT': '1iZPr8hrV8d361Zv2OzgQe8i31-0ROOVz',
  'FOILPINK-G-32X6MT': '1hRrJTmehQTAaNUQAt64AVJ7u2kHENGaW',
  'FOILPURPLE-G-32X6MT': '1hNHe7wHN33lfqMVqxVz8X08Z73-f2OzP',
  'FOILRED-G-32X6MT': '1qEBVo-pAHaA2LdehhcgsRNZsW5ag6Rt2',
  'FOILROSEGOLD-G-32X6MT': '1d-LzAP7atDgQ-rNTHu9_ntkOHevsMHpf',
  'FOILROSERED-G-32X6MT': '163OVBQ86eargkRoZvtyaL-Euz50m0G2O',
  'FOILSILVER-G-32X6MT': '114JTXbHQxdHE7q2ElxZY_0h0YqwE2oLi',
  'FOILSILVER-M-32X6MT': '1eRlzKo19o2dcZ4pC6SG0ysxH_jjdzf1Q',
  'GORRA': '1GgkuK8maP98jsYmN67QAI1J8O7vpC4d1',
  'GORRAS': '1UK3S9A0CEDPrKqjD4jTJLf3o8je8K6Cy',
  'GUILLOTINA-A3-METAL': '1bgzB983mb_otTxq3Guhieu2TNl0Fjppx',
  'GUILLOTINA-A4-METAL': '1x4KPOfc2m0uB7dPpuERVauMSJwQpb1wx',
  'HOLOGRAFICOS': '1OVTY3HH0Z1yUMz5J2D_JfQ3GqHyw54qM',
  'HTV-PUPRINT-WHITE-M-50X25MT': '1SgOIZSPqzc5NZEZQ4XSzM8L69fw2Lspn',
  'JS10000-3IN1-AIRP-SC-USBC': '1aMrR7-AJ3oOmhV_Pkoadqry7m_ueTdCF',
  'JS10000-SC-USBC': '1bzxX5RHdOS7QzvKaf1q4lmA5CijCH2HB',
  'JS8000-SC-220V': '18xwytDR8rUJ6G8ZnM4wFxwvXrFDx1ojX',
  'JS8000-SC-USBC': '1d-gxAtYc3f3AcQT7lwL6tTydW0RL_Rg3',
  'LAM-POUCH-G-110X175MM-1/4OFICIO-150MIC': '1cxYiRAsWmHTImriE3hxrEm6iln03Ixya',
  'LAM-POUCH-G-225X175MM-1/2OFICIO-150MIC': '1bUCIrxOPBi4xj6MCqN-YJ4KioNJCbBBm',
  'LAM-POUCH-G-225X303MM-125MIC': '1CWyWvtl-bh22I7J5oWHzW0vUf6vfNoUi',
  'LAM-POUCH-G-225X303MM-150MIC': '17JXMYJM6H3_aPZ3RIwu3vq3gJGzznmZe',
  'LAM-POUCH-G-225X303MM-80MIC': '1SxRtquhO_Wo8QRgOF2M3jM6iObHkXkK0',
  'LAM-POUCH-G-225X362MM-150MIC': '1KD3EZ_5EEN5_2fTW9AbWOP7u3-lLv8Mc',
  'LAM-POUCH-G-303X426MM-125MIC': '1n_oBowoOMJwSwwdOq_V9nVxvKUb8XgYD',
  'LAM-POUCH-G-303X426MM-150MIC': '1kSJqIaCdGmFW8Pm0b3sR3UN4orpme6b-',
  'LAM-POUCH-G-303X426MM-80MIC': '1Po5PiE9ZCWmDVQQfNoB4ZDOeRYi7DF9Y',
  'LAM-POUCH-G-59X83MM-150MIC': '1FBcQa3rCcktntpKBIonCX13wgi_JnntY',
  'LAM-POUCH-G-60X90MM-150MIC': '18sdprJ6SSGqRoGUj3e1RjcQOwnx5cV1R',
  'LAM-POUCH-G-67X98MM-150MIC': '1q_6jIcZq3rvoiVFff5egkoBrGQfw_hwi',
  'LAM-POUCH-G-83X120MM-150MIC': '1R7O9SRInXqINJudjs7eEnlOKv57u1J9X',
  'LAM-POUCH-G-90X130MM-150MIC': '1MtNSDA_3nrq0HV-jgXZ5QTraJ1i8Htxs',
  'LAM-ROLL-G-330MM-150MTS-25MIC': '1O3kG1piuT2XgZ_0FFN0ZZaNOtZ33oXLU',
  'LAM-ROLL-G-330MM-150MTS-28MIC': '1-Tpfjzd-f5WgAIV9D5lGeCymh-YkUhiQ',
  'LAM-ROLL-G-330MM-150MTS-32MIC': '1MFL0zBoSS0E3y9zVlqAGdODRe55q4Guw',
  'LAM-ROLL-M-330MM-150MTS-25MIC': '1RAUx7YiacZmZ46p0pxhbFDKpIxc9BXY9',
  'LAM-ROLL-M-330MM-150MTS-28MIC': '1x3cG9rncEpxUNjYN9Yqec8ABGY3HKVWN',
  'LAM-ROLL-M-330MM-150MTS-32MIC': '171CAtRYdxd0PVnTIzzZYr2UaDYMrd3Fp',
  'LAMINATOR-230MM': '1_qhdr81tJgGyCQRxTDUtIrG3T1ZVfitO',
  'LAMINATOR-230MM-V2': '11TkIPeabEOlW7pw1lywrhAOVJH8MDOzY',
  'LAMINATOR-240MM': '1Z8mYoMPyRGOTfM80g1A9CRWI9DHQ5deo',
  'LAMINATOR-240MM-V2': '1keHz9sIWGHSon1XgdBRBtPCDxQJZXhTq',
  'LAMINATOR-330MM': '1NwqVuemwo9kPZNCpap_0JP_NEc-MsoIy',
  'LAMINATOR-330MM-PRO': '1QGKtxdcaCx_e84LIBfd4foaD6ZHqY21L',
  'LAMINATOR-330MM-V2': '17n3mXlmm4VOJKg72GFo3nlmWafJAWzFE',
  'LEDESMA-NAT-75G-A4': '1CIeOywo4KGWamaAM4ILCXxAwuFq7Lyuo',
  'LLAVSUB-MTL-DESTAPADOR': '134Da6xs1_MhfVM93OiF_KIxHh_4L6U5U',
  'LLAVSUB-PL-CAMISETA': '1MxH508iAl2HagEPh8UzCQTjMeZ7WjV0f',
  'MATESUB-MSTRAW-W': '14zYVp0n0SqsmPESJg8GYPVW7iItLEjH8',
  'MPADGAMER-RGB-80X30': '17Bwo2syH3F38qXzhujaV_ZP-Io2p4dmN',
  'MPADSUB-ROUND-20': '1HUUjA-zEGHjaIPxrwve0NNFpefu2CwFO',
  'MPADSUB-SQUARE-20X20': '1fqiVAKIXlnbbd2HmHnH4hIp7jWd9Sxei',
  'MÁGICAS': '1chgAmPF7AJhjtujqSZv94lI2aGdTdNoj',
  'PAPEL INMANTADO PAPERMAGNETIC640A4': '1OdM1_RFnRqEQWsz5M2LtwS2Z8w23Im2t',
  'PAPEL LUSTER RC MICROPOROSO PAPERLUSTER260A4': '1Y_dyu-GgWRQsp9fW3ywPFXNxqu10Ue96',
  'PAPEL TATTOO': '1XzBk147QFTWqbOplYtz4n-vrGA6CamTL',
  'PAPERAARTWLEATHER160A3-100': '1thXyL2ykllx0L2FyOEJgu74w5D8NrfTF',
  'PAPERAARTWLEATHER160A4-100': '1IWFrvKPTfwQ7ZNzSphunvbsy6jyTgDCR',
  'PAPERAARTWLEATHER160A4-20': '1zJEJpjRVM-d1ToS_F66f8QExv3Ie00cj',
  'PAPERAARTWLEATHER230A4-20': '16jAiqSLMb2Kjf3CXUq-FHslbpBO6W-9D',
  'PAPERAG115A4-100': '1QyjAoGgGeBWcv_NH0j0WAGfjVDXRM7XG',
  'PAPERAG115A4-20': '1vaUmZ4GXFbUlo0x7bzoToFOZJbhEI2WE',
  'PAPERAG135A3-100': '1YsHicGkIT3kpfbFqwrVxO7YIsiOJPzHI',
  'PAPERAG135A3-20': '18bHYY8j817fcONXRCT57Rj6bJYwFqr41',
  'PAPERAG135A4-100': '1QEDEd5aFpOD18goIrQoQ08fAZtDlKPN3',
  'PAPERAG135A4-20': '1GqC5tnoooNkaXHunyG3uwNBGYaTNe09q',
  'PAPERAHOLODIAMONDA4': '1N4vgbvdFtNBVzHSXJdRf-meIjNknewxi',
  'PAPERAHOLODROPSA4': '1e4pj5FHZAzrpkaCKMXwqcyVIt7UTmcjx',
  'PAPERAHOLODSNOWA4': '1ak6gYZpDSSCO3yOYdJHbLmCAcscfnFdE',
  'PAPERAHOLOINCLINEDA4': '1ZYxpDnDQqHkGLNFy6s6o-Y7C47UvLDZ9',
  'PAPERAHOLOLOVEA4': '1ZuReBOZPgV_ByIMnfRydF5Sa7Ik2u6mr',
  'PAPERAHOLOMIXA4': '1GK20_Wr_nLKxcIkQF7TBkmPwO9v9ymPp',
  'PAPERAHOLOSNAKEA4': '1VCvAsk2jHISsEj8lG4E1KoxcHCQ_fbY1',
  'PAPERAHOLOSQUAREA4': '19FQS4LlfHShQCJ4iloOuAa5kO2taqX7m',
  'PAPERAHOLOTRANSPA4': '1N2mIBvsOVlxKbRWC3rpehIafK1mPrHVB',
  'PAPERAHOLOWAVEA4': '1l9-fUflTi65iyjyzTfF__08WQ8cxax44',
  'PAPERAKRAFT180A3-100': '1fGjvAGaC5zwnMs3Bn4q9ZcZA2ty-GJwJ',
  'PAPERAKRAFT180A4-100': '1f7ElFaUSe4CpyGDpe9qPYgRyx22iCdYQ',
  'PAPERAKRAFT180A4-20': '15125ZT_dHrlpVKak5EjrylW_D-pZ-pkf',
  'PAPERAM108A4-100': '1cLjyg5W0a9ItvTGa84J5t78krN6XvaKU',
  'PAPERAM108A4-20': '1GNnwQjOLctpC8xiMWiJ7dx7ARlfXF6e0',
  'PAPERATRANSPETRC120A3-10': '1HcUROBTLbPwIkjCjau-v6Q3o5LdVbY3H',
  'PAPERATRANSPETRC120A3-100': '1Gg-SGSOWXLh_qNMSQUC8u2nCGtxx3ZCU',
  'PAPERATRANSPETRC120A4-10': '1PwEzUuUhfyw4pTGfvYFrtBRlyI3ZygxN',
  'PAPERATRANSPP160A4-100': '1dYLJvzoVKGlYzr5iKzDPdmyPImVzeOe0',
  'PAPERATRANSPP160A4-20': '1O_Mt1xql8poL-LVvoGMtb36zny4V_Svh',
  'PAPERATRANSPVC120A4-10': '1HivwhMLW0euywuY5_kHGsv-brHzsr5wW',
  'PAPERATRANSPVC120A4-100': '13FaIID7QyUfbLg7DhLJdoms4L8XzzA0y',
  'PAPERAWPETRC120A3': '17g17d1pzNagcgrjwzGfgakQdvEQ2QI8c',
  'PAPERAWPETRC120A4': '1Udr4jx1KVPSW8DN18Vo0C88R7kuNjG3W',
  'PAPERAWPETRC120A4-20': '1Ftt5ppezs2Cz3rMklVd7DuuLSXMbF4fo',
  'PAPERDFG180A4-20': '1Ez-_ngVd_swpe3FisYk78HrCFAL9vKGP',
  'PAPERDFG220A4-100': '1MVt8uzTnd5CO0n6KHbbVSSxP2sz3onMy',
  'PAPERDFG220A4-20': '1VhwixR4DXPgry5-srTxQ0pEOQGC7LDv0',
  'PAPERDFM220A4-100': '1dmt53tbSOzNlGw4Rul62kj5_KVJ2mvLI',
  'PAPERDFM220A4-20': '1hQ4patXMBWU2Gv969QabnL5Ee4B8WYDX',
  'PAPERG140A4-100': '1OrCFzMlcd5DESACadd6qrVH13LRM-HZZ',
  'PAPERG140A4-20': '1g4sf17-vMaY9AtwrOnx0vEwlQANVqmNI',
  'PAPERG180A4-100': '16bSiobrnFxeep_QcLXtqfSSwkx1tq_z-',
  'PAPERG180A4-20': '1TyrZ00tQD_BwY0G5w_PyxUBj8IAFbCl9',
  'PAPERG180LGL-100': '1pLMf3gIeiNhZ542KufTkrDlseGkBFysc',
  'PAPERG180LGL-20': '1gVmSG1LY5xlAEEYqNaFqF4lKfTmy-uWr',
  'PAPERG20010X15-100': '1wffVZy_vA17w0c8fxG-cmJt_oU9tlVjG',
  'PAPERG20010X15-20': '1WrPuKJLVzlAc4GXi8CocHn_LK0L7hjEE',
  'PAPERG20013X18-100': '1EgKOOqeAhPkSN8xXByV_u3bfAj2PBJyb',
  'PAPERG20013X18-20': '1nkTJFkLw9mN5WAeZxtZCAViQuSoptUNK',
  'PAPERG20015X20-100': '1x1sR9DpsZM-EAEXpClWPm5ePIZchoc_5',
  'PAPERG20015X20-20': '15WXOckbuwxE8hZCeMSrhy-Yb8OQSdDJJ',
  'PAPERG200A3-100': '1DSqGLsdidY1PsuSwnFZ3CmF7_hndYc_o',
  'PAPERG200A3-20': '1fgV6s-4Dz7vOye-BrhPtC3qOi0WDFsX-',
  'PAPERG200A4-100': '1A1l9xzFzgUE3DHdwEQ5W4OKGJiVufAKO',
  'PAPERG200A4-20': '1LHv8uRK_Y9-c3wKEpcx2xFLdAyKvsLSM',
  'PAPERG260A4': '1kJJoLxqc1O1smDVmxdtykKZO7bjrga3z',
  'PAPERG260A4-100': '1RIe1ijSnH1bozmB0HSxZCDBJEljFWG5y',
  'PAPERG260A4-20': '1F7j-hZw2x9TdKa4Eqpsux0JPeiDrE2rV',
  'PAPERKRAFT125A4-100': '12eQiCpVvv4gFRmBR8FhBmDFY9mEWc81e',
  'PAPERKRAFT125A4-20': '1RiXo8MO5eY3N4F4JQhcK5iy1YH3Po5N9',
  'PAPERKRAFT200A4-100': '1Cut8KUwtFtSgVoM7jouYQN1SObqF2d_w',
  'PAPERKRAFT200A4-20': '1utoll4iNdai4evqNwBHeeKzKQ4JqTPam',
  'PAPERLUSTER260A4-50': '18BI6oWCRQP63W4SEJVFxuKl80ptqoezK',
  'PAPERM110A3-100': '1sKR--DTn-nVARQHPsGg_oBi6ypgQiHAY',
  'PAPERM110A3-20': '19QdnU8JiwCTwZbvmNXA7ThnUdhAiu3Ov',
  'PAPERM110A4': '1CF_9oqkqR7jUhyQh6NT7wW3U1L0qzoDg',
  'PAPERM110A4-100': '1c5DlGzU1X3BiqXJJjFHMPaAntosBki5O',
  'PAPERM110LGL-100': '1DoSWIQJtSDbTZTk2b-G2_2zN-2zP2uwE',
  'PAPERM110LGL-20': '1oGHBTinssqCjVLIAZDkze1r4SYNzqllW',
  'PAPERM150A4-100': '1ds5IZIV_eclHVtCkldl93LzbDmmGYNq1',
  'PAPERM180A3-100': '1YpdDX9wTZQySqKVzT8aca8LZQzs4SyVX',
  'PAPERM180A4-100': '10Fqk6BYCz1Hi0D3Cm3gn_5N-XS0-6a9x',
  'PAPERM19010X15-100': '1lmLaX9_Q7iakf9eh8-oCpPNYKHL-XsKK',
  'PAPERM19010X15-20': '1EjNencGX_L_fCy9VTob1HsOBSajRcLWF',
  'PAPERM19013X18-100': '1TnTlheXHgknKVUFqjKZkfRcRMeLuoeTe',
  'PAPERM19013X18-20': '1K_BKoPMLqWzdDMVdUmsV9KbvtdWoUM_E',
  'PAPERM210A3-100': '1x1IzHloxrkSXVsPBY3Qp6ygWQzDcWCNi',
  'PAPERM240A3-100': '1SlDEF7bX0Bd1l0ezrBjrU8S66VBmAcIZ',
  'PAPERMAGNETIC640A4': '1tgOhJfBm3BzwvVHxuCH-Q9lbLABRUR3G',
  'PAPERMAGNETIC640A4-10': '1ahYWx8yuULhEY_pB6Ipg2YkdLt3Ypj2b',
  'PAPERMCYAN180A4-100': '1dMgoTnBDyRL4FTcyDav8QZEGLxCBFgl1',
  'PAPERMCYAN240A4-100': '1N9vy6MOiNuY4CEmwM8jQgVJrPTWiwnp7',
  'PAPERMOPALINAMIX180A4-100': '169htRkhyry69f6rCf2E24rXJV9QJwJne',
  'PAPERMOPALINAMIX240A4-100': '1E5kjEUippDLtVwOfis6zXCzjkl6VdtqY',
  'PAPERMYELLOW180A4-100': '1RcYs3Ak1KYeepTh7CN1Ua9vukKfFaYit',
  'PAPERMYELLOW240A4-100': '1JPM826nLcImIEXeksTqMi6NTT3zyiTD9',
  'PAPERSUBLI100A3-20': '1nVbvR2nsvzM0vB7SSPZuDf-NvjJEHD_A',
  'PAPERSUBLI100A4-100': '1SHtdTNgLA_2dg_Xg9PZ7Un1Rlw1BaWPs',
  'PAPERSUBLI100A4-20': '1m23SxBT5ywycEqbFmYCqYc2A-9ObkWCD',
  'PAPERSUBLI100ROLL-1100X50M': '1ov3HQzyxmu9RRuajIRL1033J1d_c7olf',
  'PAPERSUBLI100ROLL-1340X50M': '14_tRObWy2ljZpMWjoMvZYQbL0kmfXvfN',
  'PAPERSUBLI100ROLL-210X100M': '1D4LR0EGghh0kyAtP3nJa48-SFPli0deh',
  'PAPERSUBLI100ROLL-330X100M': '1htlq1Yht8GuyI3aN2RlGIz--8s1_tJFo',
  'PAPERSUBLI100ROLL-610X50M': '1QbCYHGD5kDq5a9AyIC9adH_DD0HzRh2L',
  'PAPERSUBLI45ROLL-1620X300M': '1U6e3qppBLEcQw_gYbrXJrNiM89jzRilo',
  'PAPERSUBLI57ROLL-1620X300M': '1_EOeUt6hkv4xYko4eEMqsACA4G8LSEHP',
  'PAPERSUBLI73ROLL-1620X200M': '1OuL24Zhu2F9k6WeQqiGl_2fySioTrSLK',
  'PAPERSUBLI90ROLL-1110X100M': '1_wi1FC0bDaEGv5gS5ghYj3kWAZWAWi6r',
  'PAPERSUBLI90ROLL-1620X100M': '18_LOC9pn-oCZyVKoAM-07hEcZdbUCGNU',
  'PAPERTATTOOA4': '15edrpMz4ab7FKcXrQm8MUoQsR6ilTQCv',
  'PAPERTATTOOA4-10': '1hed7yrSfkLUAWsQ6Vxd7l8OS9DFYusjc',
  'PAPERTRANSFERA3D': '1XWgndDzf2qf742baffxaFKj8JTFe_hcz',
  'PAPERTRANSFERA3L': '1T3w4qCX7FzxsnOISnXOkl7NN3xAJuSQh',
  'PAPERTRANSFERA4D': '1M8tdU2Qiq7faRhm-b9pollN4abR3xgXj',
  'PAPERTRANSFERA4L': '1XVR601POt34bQzVOsGd_ejr9IvvyohB4',
  'PLANCHA-SUB-26X26-PORT': '1dHNLHT8mmZ86YHkAlmhpLdUwp-rUDoi8',
  'PLANCHA-SUB-30X30-8EN1': '1BGDOR_QhCeCG87R3D1o896q_mpTuq2iP',
  'PLANCHA-SUB-30X38': '15CoPYZ_jc63b2O0M3LG4e4puGJn1Nhlo',
  'PLANCHA-SUB-30X38-10EN1': '1-HbxcjJlH-KVQtDE7R3WJjQy2r_kuiu9',
  'PLANCHA-SUB-30X38-4EN1': '1jgJ8tgesbPZJbk75771TnG273C_wC7JI',
  'PLANCHA-SUB-30X38-5EN1': '1kMlJf3HR_YyVN0tGkH6JPhxTS-qDHoKf',
  'PLANCHA-SUB-30X38-8EN1': '1ENHJZPWCyMW8OAgXtkYYYLR2KqOBoJp6',
  'PLANCHA-SUB-40X60': '16EMJqCwl2EHI_pkKiXgi0ksjJ6plzFy1',
  'PLANCHA-SUB-AUTO-38X38': '10Qn1_5-TwizkAwqP4eN4g-IGw-1aude5',
  'PLANCHA-SUB-AUTO-GORRA': '15IYki5CuzfCSFOdyNjQMt-UROV0QHp8z',
  'PLANCHA-SUB-AUTO-TERMO': '1PePnHH75MCqb4hvk-Y1rZSWOLskya1Dz',
  'PLANCHA-SUB-GORRA-PORT': '1MDZ91QeoGAVSKWDuimvBxZr3kSHphND1',
  'PLANCHA-SUB-GORRAS': '1-ERd2AQgeywgXeGuq94bEnrGxdML78f8',
  'PLANCHA-SUB-PORTATIL': '13I4DSBIozy0OzPCF9n8FvkWVjVPdSjXl',
  'PLANCHA-SUB-TAZA': '1Wpgo3148xEay6Nw6rTfm8Lc2lSQIcNeI',
  'PLANCHA-SUB-TAZAS- 4EN1': '18p5c1D_9vihLk_bDRtyrOGMPz3AfolsE',
  'PLANCHA-SUB-TERMO': '1d8idClyiM5iTP8ccjTb-DTuaImEA1-qg',
  'PLOTTER G430Q3': '1JZVlYpSdUIby8gDUigWN8R-RwKfKWlIO',
  'PORTABANROLLUP-PVC-85X200': '1GXU9gODF5RBfcwdEfcsQFfxT1EplTd69',
  'PORTADA ML': '1o_EjenFP6Bq0Ks1r2i_cAWU8Qr0Nl9FM',
  'PORTADA WEB': '131InxabZmTA96ELRwVh2SHCPuXRnm9QA',
  'PPF-BKG-152X15': '1gcSyvjk_J4amBQfv_fH731z7MDuQaEjS',
  'PPF-BKM-152X15': '1xVBs9IReo_MDs0ATJFyE3_l5vKNm2xh7',
  'PPF-G-152X15': '14Mol0lbAPkS79pDNO6PPMX-weSZDt2D2',
  'PPF-M-152X15': '1PEavBXvwaWVQE5u_9TDPw_FMPgOcGz_8',
  'PUNAX-75G-A4': '1NGQRStlnzf6KrHHptMYKdFvTiEwJbKpn',
  'PVCFOAM-W-10MM-122X244MT': '13mdPYE0CzolrrmyKsDKY0TiXkAq4U_yt',
  'PVCFOAM-W-2MM-122X244MT': '1WfuAlJ995ljT1CYGMU9Vw3W-LQI18JiV',
  'PVCFOAM-W-3MM-122X244MT': '16PGXaP0AwPLuHVM6hvDr6hLJihgVyqRv',
  'PVCFOAM-W-5MM-122X244MT': '1pAXTT4qtOKYbrggXftskgVmKZHdVc4Yg',
  'PVSUB-MDF-ROUND': '1CDAb_Xz3UwrF26Vzx-5bvNkKyFvfsENg',
  'PVSUB-MDF-SQUARE': '15oA7p3wf1yXShzvCVI8sHyBIaorD7FjI',
  'RCSUB-CORA-16P': '1k1pZkPanu64UCPqgcG601UceYUJfti-n',
  'RCSUB-SQUARE-40P': '1fjSJiGj1NH_umAMqxYIRYQzw_5faWXXz',
  'REPUESTOS MAY': '104RSmEgKidZjrCnOo8DAa9sKEop-12vM',
  'REVESTIMIENTO PARED': '1esivK7MLuqTX2tSFxeVwaCcMe_kQ77Pm',
  'SEW-12ST': '1fRNuedYVLOgECJ6ZfNpDrSSMFYBullWw',
  'SEW-MINI': '1_EzVK0wZsxfy8EZs0CxGvMGRfOxMetE-',
  'SPC-1220X180X4MM-0.5L-1IX-W1357L': '14MGpUADeWvWQP1CYGFuhSfx-K0cyLHRZ',
  'SPC-1220X180X4MM-0.5L-6099-9': '1eadiQDO-QyvWCOhXF_cB7KZgoZuv3MNU',
  'SPC-1220X180X4MM-0.5L-M0051-1': '1afz2S8W8zFQ6CtZjI6nS8pTY3WFzIpi5',
  'SPC-1220X180X4MM-0.5L-W1357L': '1xTVI4EfClNkt6xiqbIS_tsjr3z5-XEBP',
  'SSRULE-60CM': '1XwGjI8hU9Fllk68KbhcUgJRLeqc0rKfP',
  'SWFBK-15%-152X30': '1DKtjZY_jBLx9-KF0gj08tfGu1bybAFBz',
  'TAZAS': '1LYHg-9DZ23Ey8gF95jmv4E10QMYTVsRg',
  'TELATEFLON-SUB-30X38': '1ihBg7RqSc4MyXdxG7Pf8qOO1vDDd7Rmt',
  'TELATEFLON-SUB-40X60': '1rTG5YbkQ8X8IBn_OVNF2P_kgdso65k2S',
  'TEMPO-75G-A4': '1e7Ve-es5fTQCAq4s_8alm6010mIk_nYS',
  'TEMPO-75G-OFICIO': '1-afqeraW8Dd0LlEpoGHAPScni7QQOeSp',
  'TEMPO-NAT-75G-A4': '1WkfL-QWX7fEr1Zjrv7yZLP2TrH9DZaMQ',
  'TERMOSUB-ALU-500ML-W': '1Cj2tX504M1BpSVajtYu44Q1iSt1tLLxe',
  'TERMOSUB-DTEMP-500ML-W': '1heykS0GsPzIm5yG1I-yUqG8uwNGEvInZ',
  'TSHIRTGUIDERULE-AIO': '1rgqU2_y7foT2C_3Rmzlid9Va3ysAmsCC',
  'TSHIRTSUB-POLY': '1A-IjM3sK-rxFjaR7p3PxYcjoa9BDsA7a',
  'TSHIRTSUB-POLY-2': '1nm4lRh3NIQltUZyQZQtkxr17-oRRPJ1c',
  'TUBEQ-LAM-230MM': '1ECN8J1pdN4iTuuLjyAgKDzDf_uISGwkX',
  'TUBEQ-LAM-240MM': '1_0HnA4FjrRo8lvzdfvfvzijvu-Co6tmo',
  'TUBEQ-LAM-330MM': '1n6eXxM66obbqgvpwNqgGkoGseaBSi0M9',
  'TUMBLERSUB-ALU-1200ML-W': '1v3xGtwtHZ5b0faSftDPwfJPpr77e_VOw',
  'VENDEDORES CARGADORES DE BATERÍA': '1skkwJzlNtxKNxhWsVZoje21jPWEFXtpO',
  'WFBK-15%-152X30': '18fVWhcYMXGzh-QlZUW4Y7Q9-SPJ2e5LF',
  'WFBK-35%-152X30': '1T3CEHMYIyiVtX2kqqZeeSbuxNOEBx2uD',
  'WFBK-5%-152X30': '1uNAGBDiaUlHAGdWxXgRvdPxU2_V3E-wQ',
  'WFSLV-15%-152X30': '185Ffe1fD9fq2n_1MNc6NOVhxx65iubSr'
};

function findFileIdForSku(sku) {
  if (!sku) return null;
  var s    = sku.trim().toUpperCase();
  var keys = Object.keys(SKU_IMAGES);

  // 1. Exact match (case-insensitive)
  for (var i = 0; i < keys.length; i++) {
    if (keys[i].toUpperCase() === s) return SKU_IMAGES[keys[i]];
  }

  // 2. Strip suffix segments one by one (GORRATRUCKERSUB-BK → GORRATRUCKERSUB → ...)
  var parts = s.split('-');
  for (var si = parts.length - 1; si >= 1; si--) {
    var cand = parts.slice(0, si).join('-');
    for (var j = 0; j < keys.length; j++) {
      if (keys[j].toUpperCase() === cand) return SKU_IMAGES[keys[j]];
    }
  }

  // 3. Longest key that is a prefix of s (TAZASUB-... → TAZAS)
  var best = null, bestLen = 0;
  for (var ki = 0; ki < keys.length; ki++) {
    var ku = keys[ki].toUpperCase();
    if (s.indexOf(ku) === 0 && ku.length > bestLen) {
      best = keys[ki]; bestLen = ku.length;
    }
  }
  if (best) return SKU_IMAGES[best];

  return null;
}

// ---------------------------------------------------------------
// Imágenes de productos — llamado desde el cliente via google.script.run.
// Busca el Drive file ID para cada SKU, descarga thumbnails en paralelo
// y los devuelve como base64 data URLs. Cache 24 h por fileId.
// ---------------------------------------------------------------

function getSheetImages(sheetName) {
  var result = {};
  var token  = ScriptApp.getOAuthToken();
  var cache  = CacheService.getScriptCache();

  var sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName(sheetName);
  if (!sheet) return {};

  var values       = sheet.getDataRange().getValues();
  var fileIdToRows = {};
  var rowToFileId  = {};

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

  // Check cache
  var cacheKeys    = fileIds.map(function(id){ return 'drv_' + id; });
  var cachedValues = cache.getAll(cacheKeys);
  var needFetch    = [];

  for (var fi = 0; fi < fileIds.length; fi++) {
    var fid  = fileIds[fi];
    var cval = cachedValues['drv_' + fid];
    if (cval) {
      var rows = fileIdToRows[fid];
      for (var ri = 0; ri < rows.length; ri++) result[rows[ri]] = cval;
    } else {
      needFetch.push(fid);
    }
  }

  if (needFetch.length === 0) return result;

  // Batch-fetch Drive thumbnails in parallel
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

    // URL directa si la col J tiene fórmula =IMAGE("url")
    var imgUrl = '';
    if (formulas[i] && formulas[i][9]) {
      var m = formulas[i][9].match(/IMAGE\(["\']([^"\']+)["\']/i);
      if (m) imgUrl = m[1];
    }

    products.push({
      sku:       String(row[0]),
      nombre:    String(row[1]),
      stock:     String(row[2]),
      categoria: currentCat || sheet.getName(),
      cant1: String(row[3] || ''), precio1: String(row[4] || ''),
      cant2: String(row[5] || ''), precio2: String(row[6] || ''),
      cant3: String(row[7] || ''), precio3: String(row[8] || ''),
      sheetRow: i + 1,
      imgUrl:   imgUrl
    });
  }
  return products;
}

// ---------------------------------------------------------------
// Renderizado de tarjetas y secciones
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
  var avail = p.stock === 'DISPONIBLE';

  // Si hay URL directa (formula IMAGE), úsala; sino carga lazy desde Drive
  var imgHtml;
  if (p.imgUrl) {
    imgHtml = '<img src="' + p.imgUrl + '" alt="' + p.sku
            + '" loading="lazy" onerror="this.style.display=\'none\'">';
  } else {
    imgHtml = '<img src="" class="lazy-img"'
            + ' data-sheet="' + sheetName + '"'
            + ' data-row="'   + p.sheetRow + '"'
            + ' alt="'        + p.sku + '">';
  }

  var badge = avail
    ? '<span class="avail">✓ Disponible</span>'
    : '<span class="unavail">✗ Sin stock</span>';
  var prices = '';
  var tiers = [[p.cant1, p.precio1],[p.cant2, p.precio2],[p.cant3, p.precio3]];
  for (var t = 0; t < tiers.length; t++) {
    var c = tiers[t][0], pr = tiers[t][1];
    if (pr && pr !== '-' && pr !== '') {
      var cls = t === 1 ? ' price-best' : '';
      prices += '<div class="price-row' + cls + '"><span>x' + c + ' u.</span>'
              + '<span>' + formatPrice(pr) + '</span></div>';
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
    var ps  = byCat[cat];
    if (cat && cat !== sheetName)
      cardsHtml += '<div class="subcat-label">' + cat + '</div>';
    for (var pi = 0; pi < ps.length; pi++)
      cardsHtml += buildCard(ps[pi], sheetName);
  }

  return '<section class="cat-section" id="sec-' + sheetName.replace(/[^a-zA-Z]/g,'') + '">'
    + '<div class="cat-head" style="--accent:' + m.color + '">'
    + '<div class="cat-head-left">'
    + '<div class="cat-icon-wrap" style="background:' + m.color + '">' + m.icon + '</div>'
    + '<div><div class="cat-tag">Categoría</div><h2>' + label + '</h2></div></div>'
    + '<div class="cat-badge">' + avail + ' disponibles</div>'
    + '</div>'
    + '<div class="cards-grid">' + cardsHtml + '</div>'
    + '</section>';
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
    var icons = {'Sublimación':'🔥','Laminación':'✨','Papelería':'📄','Kraft':'📦',
                 'Domótica':'🏠','Automotor':'🚗','Revestimiento':'🪟',
                 'Cartelería':'🖼️','Vinilos Termotransferibles':'👕'};
    navLinks += '<a href="#sec-' + sheetName.replace(/[^a-zA-Z]/g,'') + '" class="nav-link">'
              + (icons[sheetName]||'📦') + ' ' + sheetName + '</a>';
    sectionsHtml += buildSection(sheetName, products);
  }

  var logoDataUrl = getLogoDataUrl();
  var bannerUrl   = 'https://drive.google.com/thumbnail?id=' + BANNER_FILE_ID + '&sz=w1200';

  var html = HtmlService.createHtmlOutput(
    getHtml(vigencia, navLinks, sectionsHtml, bannerUrl, logoDataUrl, JSON.stringify(sheetOrder))
  );
  html.setTitle('Catálogo Global Electronics');
  html.setXFrameOptionsMode(HtmlService.XFrameOptionsMode.ALLOWALL);
  return html;
}

// ---------------------------------------------------------------
// HTML
// ---------------------------------------------------------------

function getHtml(vigencia, navLinks, sectionsHtml, bannerUrl, logoDataUrl, sheetOrderJson) {
  var logoHtml = logoDataUrl
    ? '<img src="' + logoDataUrl + '" alt="Global Electronics" class="logo-img">'
    : '<svg class="logo-img" viewBox="0 0 160 52" xmlns="http://www.w3.org/2000/svg">'
      + '<rect width="160" height="52" rx="8" fill="rgba(255,255,255,.2)"/>'
      + '<text x="80" y="30" text-anchor="middle" font-family="Nunito,sans-serif" font-weight="900" font-size="24" fill="white">Global</text>'
      + '<text x="80" y="45" text-anchor="middle" font-family="Nunito,sans-serif" font-weight="700" font-size="10" fill="rgba(255,255,255,.75)" letter-spacing="2">ELECTRONICS</text>'
      + '</svg>';

  var lazyScript = '<script>'
    + '(function(){'
    + '  if(typeof google==="undefined"||!google.script)return;'
    + '  var sheets=' + sheetOrderJson + ';'
    + '  function load(sn){'
    + '    google.script.run'
    + '      .withSuccessHandler((function(s){return function(m){'
    + '        if(!m)return;'
    + '        var rows=Object.keys(m);'
    + '        for(var i=0;i<rows.length;i++){'
    + '          var imgs=document.querySelectorAll(\'.lazy-img[data-sheet="\'+s+\'"][data-row="\'+rows[i]+\'"]\');'
    + '          for(var j=0;j<imgs.length;j++)imgs[j].src=m[rows[i]];'
    + '        }'
    + '      };})(sn))'
    + '      .withFailureHandler(function(){})'
    + '      .getSheetImages(sn);'
    + '  }'
    + '  if(document.readyState==="loading"){'
    + '    document.addEventListener("DOMContentLoaded",function(){sheets.forEach(load);});'
    + '  } else { sheets.forEach(load); }'
    + '})();'
    + '</script>';

  return '<!DOCTYPE html><html lang="es"><head>'
    + '<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
    + '<title>Catálogo Global Electronics</title>'
    + '<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800;900&display=swap" rel="stylesheet">'
    + '<style>' + getCSS() + '</style></head><body>'

    + '<nav class="topnav">'
    + '<div class="nav-logo">' + logoHtml + '</div>'
    + '<div class="nav-links">' + navLinks + '</div>'
    + '<div class="nav-vigencia">📅 ' + vigencia + '</div>'
    + '</nav>'

    + '<div class="cover">'
    + '<div class="cover-eyebrow">📘 CATÁLOGO MAYORISTA</div>'
    + '<h1>Lista de Precios<em>Oficial</em></h1>'
    + '<p class="cover-sub">Equipos, insumos y artículos para profesionales del estampado, la impresión y la papelería.</p>'
    + '<div class="cover-banner"><img src="' + bannerUrl + '" alt="Productos Global Electronics"/></div>'
    + '<p class="cover-bottom">globalecom.ar · ' + vigencia + ' · Precios en USD sin IVA</p>'
    + '</div>'

    + '<div class="catalog">' + sectionsHtml + '</div>'

    + '<footer><strong>Global Electronics</strong> · globalecom.ar<br>'
    + vigencia + ' · Precios en USD sin IVA · Sujeto a cambios sin previo aviso</footer>'

    + lazyScript
    + '</body></html>';
}

// ---------------------------------------------------------------
// CSS
// ---------------------------------------------------------------

function getCSS() {
  return ':root{--teal:#00BCD4;--teal-dark:#0097A7;--teal-light:#E0F7FA;--text:#1C2B36;--gray:#6B7C8D;--bg:#F5F9FB;--white:#fff;--radius:16px}'
    + '*{box-sizing:border-box;margin:0;padding:0}'
    + 'body{font-family:Nunito,sans-serif;background:var(--bg);color:var(--text)}'

    + '.topnav{position:sticky;top:0;z-index:100;background:linear-gradient(135deg,#006064,#00BCD4);'
    + 'padding:12px 24px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;'
    + 'box-shadow:0 2px 12px rgba(0,0,0,.2)}'
    + '.nav-logo{display:flex;align-items:center}'
    + '.logo-img{height:44px;width:auto;display:block}'
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
    + '.card-img img:not([src]){display:none}'
    + '.card-img img[src=""]{display:none}'
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
